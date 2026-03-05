import time
import socket
import config
from utils.schema import MazeResponse, PrologueAnalysis, LastWish
from utils.utils import encode_image, stringify_history
from langchain_core.prompts import ChatPromptTemplate

class Call:
    def __init__(self, agent, room=None, maze=None, history=None, prologue=False, last_wish=None):
        self.agent = agent
        self.room = room
        self.maze = maze
        self.history = history
        self.prologue = prologue
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
            content.append({"type": "text", "text": f"Final Message: {self.last_wish}\n\nHistory: {self.history}\n\nNotes from previous Attempts: {self.agent.last_notes}"})

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
        schema = PrologueAnalysis if self.prologue else MazeResponse if self.last_wish is None else LastWish
      
        structured_llm = self.agent.model.with_structured_output(schema)
        prompt = self.make_prompt()
        chain = prompt | structured_llm

        for attempt in range(3):
            try:
                return chain.invoke({})
            except (socket.timeout, Exception) as e:
                print(f"Connection issue: {e}. Retrying in 5 seconds... (Attempt {attempt+1}/3)")
                time.sleep(5)
        
        raise Exception("Model failed to respond after 3 attempts.")



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


def game_over(agent, history):
    last_wish =config.last_wish_msg(agent.status)  
    message = stringify_history(history)

    return Call(agent=agent, history=message, last_wish=last_wish).run_step()