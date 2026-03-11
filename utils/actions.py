import time
import socket
import config
from utils.schema import MazeResponse, PrologueAnalysis, LastWish, ResumeNote
from utils.utils import encode_image, stringify_history
from langchain_core.prompts import ChatPromptTemplate

class Call:
    def __init__(self, agent, room=None, maze=None, history=None, prologue=False, prev_notes=None, last_wish=None):
        self.agent = agent
        self.room = room
        self.maze = maze
        self.history = history
        self.prologue = prologue
        self.prev_notes = prev_notes
        self.last_wish = last_wish

    def make_prompt(self, sys_prompt=config.SYS_PROMPT):
        content = []
        b64s = []

        # Textual content
        if self.prologue: # Prologue step
            room = self.maze.get_room(0)
            content.append({"type": "text", "text": f"Prologue Instructions: {room.description}\n\nNotes from previous Attempts: {self.agent.last_notes}"})
            
            for img_key in ["frontcover", "directions"]:
                path = self.maze.get_img_url(img_key)
                b64s.append(encode_image(path))

        elif self.last_wish: # Last Wish step
            content.append({"type": "text", "text": f"{self.last_wish}\n\nYour Journey: {self.history}\n\nNotes from previous Attempts: {self.agent.last_notes}"})

        elif self.prev_notes: # Synthesizing past notes into strategy
            content.append({"type": "text", "text": f"Read the notes from previous failed runs: {self.prev_notes}"})

        else: # Maze step
            text = f"Current Room: {self.room.room_id}\nPage Text: {self.room.description}\n\nHistory: {self.history}\n\nNotes from previous Attempts: {self.agent.last_notes}"
            content.append({"type": "text", "text": text})
            b64s.append(encode_image(self.room.img_url))

        # Add images to content
        if len(b64s) > 0:
            for b64 in b64s:
                content.append({
                    "type": "image_url", 
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })

        return ChatPromptTemplate.from_messages([   
            ("system", sys_prompt),
            ("user", content)
        ])


    def run_step(self):
        if self.prologue:
            schema = PrologueAnalysis
            temp = 0.2 
        elif self.last_wish:
            schema = LastWish
            temp = 0.0 
        elif self.prev_notes:
            schema = ResumeNote
            temp = 0.0
        else:
            schema = MazeResponse
            temp = 0.7  
        
        structured_llm = self.agent.model.bind(temperature=temp).with_structured_output(schema, method="function_calling")
        
        prompt = self.make_prompt()
        chain = prompt | structured_llm

        for attempt in range(config.MAX_ATTEMPTS_BEFORE_FAILED_CALL):
            try:
                response = chain.invoke({})
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
        
    while not valid_move:

        history_pre_turn[-1]["hallucinations"] = hallucinations_this_turn
        message = stringify_history(history_pre_turn)

        response = Call(agent=agent, room=room, history=message).run_step()

        if not response.travel_log_update:
            print(f"⚠️ Warning: travel_log_update is empty for room {room.room_id}.")

        picked = response.decision.room_picked

        # Topology check
        if picked in room.valid_doors:
            valid_move = True
            response.hallucinations = hallucinations_this_turn
            response.valid_move = True
            return response, agent
        
        else:
            hallucinations_this_turn.append(config.hallucination_door_msg(room.room_id, picked))
            print(f"Hallucination detected: Room {picked} is not a valid exit from Room {room.room_id}.")

            # Limit retries to prevent infinite loops
            if len(hallucinations_this_turn) > config.MAX_HALLUCINATIONS_PER_STEP:
                agent.status = "hallucinated" 
                response.hallucinations = hallucinations_this_turn
                response.valid_move = False
                return response, agent




def resume_notes(agent, prev_notes: list):
    if not prev_notes:
        return ""
    
    response = Call(agent=agent, prev_notes=prev_notes).run_step()

    return response.strategy

def game_over(agent, history):
    last_wish =config.last_wish_msg(agent.status)  
    message = stringify_history(history)

    response = Call(agent=agent, history=message, last_wish=last_wish).run_step()
    return response