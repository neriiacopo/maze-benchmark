import time
import socket
import config
from utils.utils import encode_image, format_maze_history
from langchain_core.messages import HumanMessage, SystemMessage

class Call:
    def __init__(self, agent, room=None, maze=None, history=None, prologue=False, prev_notes=None, last_wish=None):
        self.agent = agent
        self.room = room
        self.maze = maze
        self.history = history
        self.prologue = prologue
        self.prev_notes = prev_notes
        self.last_wish = last_wish
        self.pc = agent.prompt_config

    def make_prompt(self):
        content = []
        b64s = []

        # Textual content
        if self.prologue: # Prologue step
            room = self.maze.get_room(0)
            text = self.pc.format_template(
                "prologue_template",
                room_description=room.description,
                last_notes=self.agent.last_notes,
            )
            content.append({"type": "text", "text": text})

            for img_key in ["frontcover", "directions"]:
                path = self.maze.get_img_url(img_key)
                b64s.append(encode_image(path))

        elif self.last_wish: # Last Wish step
            path_str, notes_str = format_maze_history(self.history, self.pc)
            text = self.pc.format_template(
                "last_wish_template",
                last_wish_text=self.last_wish,
                path_str=path_str,
                notes_str=notes_str,
                last_notes=self.agent.last_notes,
            )
            content.append({"type": "text", "text": text})

        elif self.prev_notes: # Synthesizing past notes into strategy
            text = self.pc.format_template("synthesize_template", prev_notes=self.prev_notes)
            content.append({"type": "text", "text": text})

        else: # Maze step
            path_str, notes_str = format_maze_history(self.history, self.pc)
            text = self.pc.format_template(
                "maze_step_template",
                last_notes=self.agent.last_notes,
                path_str=path_str,
                notes_str=notes_str,
                room_id=self.room.room_id,
                description=self.room.description,
            )
            content.append({"type": "text", "text": text})
            b64s.append(encode_image(self.room.img_url))

        # Add images to content
        if len(b64s) > 0:
            for b64 in b64s:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })

        return [SystemMessage(content=self.pc.system_prompt), HumanMessage(content=content)]


    def run_step(self):
        if self.prologue:
            schema = self.pc.schemas["PrologueAnalysis"]
            temp = 0.2
        elif self.last_wish:
            schema = self.pc.schemas["LastWish"]
            temp = 0.0
        elif self.prev_notes:
            schema = self.pc.schemas["ResumeNote"]
            temp = 0.0
        else:
            schema = self.pc.schemas["MazeResponse"]
            temp = 0.7

        structured_llm = self.agent.model.bind(temperature=temp).with_structured_output(schema, method="function_calling")

        messages = self.make_prompt()

        for attempt in range(config.MAX_ATTEMPTS_BEFORE_FAILED_CALL):
            try:
                response = structured_llm.invoke(messages)
                return response

            except Exception as e:
                print(f"⚠️ Step Failed: {type(e).__name__}: {e}")
                time.sleep(2)

        raise Exception(f"Model failed to respond after {config.MAX_ATTEMPTS_BEFORE_FAILED_CALL} attempts.")


def run_prologue_step(agent, maze):
    response = Call(agent=agent, maze=maze, prologue=True).run_step()
    return response


def run_maze_step(agent, room, history={}):
    valid_move = False
    history_pre_turn = history.copy()
    hallucinations_this_turn = []
    pc = agent.prompt_config

    while not valid_move:

        history_pre_turn[-1]["hallucinations"] = hallucinations_this_turn

        response = Call(agent=agent, room=room, history=history_pre_turn).run_step()

        if not response.travel_log_update:
            print(f"⚠️ Warning: travel_log_update is empty for room {room.room_id}.")

        picked = response.decision.room_picked

        # Topology check
        if picked in room.valid_doors:
            valid_move = True
            response.hallucinations = hallucinations_this_turn
            response.valid_move = True
            path_str, notes_str = format_maze_history(history_pre_turn, pc)
            prompt_log = {
                "prompt_text": pc.format_template(
                    "maze_step_template",
                    last_notes=agent.last_notes,
                    path_str=path_str,
                    notes_str=notes_str,
                    room_id=room.room_id,
                    description="(omitted from log)",
                ),
                "model_response": response.model_dump(),
            }
            return response, agent, prompt_log

        else:
            hallucinations_this_turn.append(pc.hallucination_door_msg(room.room_id, picked))
            print(f"Hallucination detected: Room {picked} is not a valid exit from Room {room.room_id}.")

            # Limit retries to prevent infinite loops
            if len(hallucinations_this_turn) > config.MAX_HALLUCINATIONS_PER_STEP:
                agent.status = "hallucinated"
                response.hallucinations = hallucinations_this_turn
                response.valid_move = False
                path_str, notes_str = format_maze_history(history_pre_turn, pc)
                prompt_log = {
                    "prompt_text": pc.format_template(
                        "maze_step_template",
                        last_notes=agent.last_notes,
                        path_str=path_str,
                        notes_str=notes_str,
                        room_id=room.room_id,
                        description="(omitted from log)",
                    ),
                    "model_response": response.model_dump(),
                }
                return response, agent, prompt_log




def resume_notes(agent, prev_notes: list):
    if not prev_notes:
        return ""

    response = Call(agent=agent, prev_notes=prev_notes).run_step()

    return response.strategy

def game_over(agent, history, current_room=None):
    last_wish = agent.prompt_config.last_wish_msg(agent.status, current_room)

    response = Call(agent=agent, history=history, last_wish=last_wish).run_step()
    return response
