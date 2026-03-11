import config
from utils.utils import preprocess_df, check_loop
from utils.actions import run_maze_step, run_prologue_step, game_over


class Agent:
    def __init__(self, model, last_notes=""):
        self.model = model
        self.alive = True
        self.status = "exploring"
        self.last_notes = last_notes
        self.looping = 0

class Room:
    def __init__(self, room_id, description, img_url, valid_doors):
        self.room_id = room_id
        self.description = description
        self.img_url = img_url
        self.valid_doors = valid_doors

class Maze:
    def __init__(self, df_path=config.DF_PATH, imgs_dir=config.IMGS_DIR, subdirs=config.IMGS_SUBDIR):
        self.df = preprocess_df(df_path)
        self.imgs_dir = imgs_dir
        self.subdirs = subdirs
        self.img_res = "low" 

    def get_room_img_url(self, room_id):
        return f"{self.imgs_dir}/{self.subdirs[self.img_res]}/room{room_id}.jpg"
    
    def get_img_url(self, img_name):
        return f"{self.imgs_dir}/{self.subdirs[self.img_res]}/{img_name}.jpg"
    
    def get_room(self, room_id):
        room_row = self.df[self.df['Room'] == room_id].iloc[0]
        return Room(room_id, room_row['Description'], self.get_room_img_url(room_id), room_row['Connections'])



def explore_maze(agent, maze, start_room=1, max_steps=config.MAX_STEPS):
    current_room_id = start_room
    travel_history = []
    decision_history = []
    analysis_history = []
    prompt_logs = []

    # Prologue step
    init_response = run_prologue_step(agent, maze)
    travel_history = [{
        "step": 0,
        "room": 0,
        "note": f"META CLUES: {init_response.meta_observations} | STRATEGY: {init_response.strategy_notes}"
    }]
    
    print(f"AI Ready: {init_response.ready_to_start}")

    # Start Navigation
    step = 1
    while agent.status =="exploring" and step <= max_steps + 1:

        room = maze.get_room(current_room_id)

        # Max steps reached -> last wish
        if step == max_steps + 1 :
            print("Max steps reached! Ending exploration.")
            agent.status = "exhausted"
            break

        # Dead End -> last wish 
        if len(room.valid_doors) == 0:
            print(f"Room {current_room_id} has no exits! Agent is trapped!")
            agent.status = "trapped"
            break

        # Attempt to move to the next room
        response, agent, prompt_log = run_maze_step(agent, room, travel_history)
        picked = response.decision.room_picked

        # If the move is valid, update histories and current room
        if response.valid_move:
            print(f"Step {step}: Moved from Room {current_room_id} to Room {picked} ➡️")

            travel_history.append({
                    "step": step,
                    "room": current_room_id,
                    "picked": picked,
                    "note": response.travel_log_update,
                    "hallucinations": response.hallucinations
                })

            decision_history.append({
                "step": step,
                "current_room": current_room_id,
                "picked": picked,
                "reasoning": response.decision.reasoning
            })

            analysis_history.append({
                "step": step,
                "current_room": current_room_id,
                "available_doors": response.analysis.available_doors,
                "visual_clues": response.analysis.visual_clues,
                "textual_clues": response.analysis.textual_clues
            })

            prompt_logs.append({
                "step": step,
                "current_room": current_room_id,
                "picked": picked,
                **prompt_log,
            })

            current_room_id = picked

            if current_room_id == 45:
                print("First Goal Reached! --> room 45")

            step += 1

        # If the move is invalid -> last wish
        else:
            print("Max attempts reached. Agent is hallucinated")
            travel_history.append({
                    "step": step,
                    "room": current_room_id,
                    "picked": "",
                    "note": response.travel_log_update,
                    "hallucinations": response.hallucinations
                })
            
        # Check for loops
        if check_loop(picked, travel_history, backtracking=config.BACKTRACKING_THRESHOLD):
            agent.looping += 1
        
            print("Agent is backtracking...")
            if agent.looping >= config.MAX_BACKTRACKING_ATTEMPTS:
                print("Backtracking threshold reached. Agent is looping.")
                agent.status = "looping"
                break
        else:
            if agent.looping > 0:
                print("Agent entered a new room and exited the loop")
            agent.looping = 0
            

        

    if agent.status != "exploring":
        last_note = game_over(agent, travel_history, current_room_id)

    new_data = {
        "travel_logs": travel_history,
        "decision_logs": decision_history,
        "analysis_logs": analysis_history,
        "prompt_logs": prompt_logs,
        "last_notes": last_note.model_dump(),
        "end_causes": agent.status
    }

    return new_data, agent