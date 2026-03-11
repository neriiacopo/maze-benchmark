
DF_PATH = "data/maze_database.tsv"
IMGS_DIR = "data/images/"
IMGS_SUBDIR ={"high":"highres", "low":"thumbnails"}

MAX_STEPS = 50
MAX_HALLUCINATIONS_PER_STEP = 3
BACKTRACKING_THRESHOLD = 7
MAX_BACKTRACKING_ATTEMPTS = 5

MAX_ATTEMPTS_BEFORE_FAILED_CALL = 5

LOG_KEYS = ["travel_logs", "decision_logs", "analysis_logs", "prompt_logs", "last_notes", "end_causes"]

SYS_PROMPT = f"You are an participating in an experiment to test your reasoning and navigational skills. You are traveling through a Maze and your task it so go from room 1 to room 45, and back, in the shortest amount of steps possible. At each step, you will be given a description of the room you are in, and an image of the room. You will also be given a map of your previous steps, a log with the notes you take along your exploration as well as some final notes left for you from previous fellow explorers. Based on this information, at each step you must choose which door to go through next. Finally, you will have to solve the riddle contained in room 45, which solution is to be found along your journey. All elements of the text and in the images are clues to help you make the best decision. Remember you must also explain your reasoning for choosing any door, and what information you are taking note of for the return journey and the final riddle. IMPORTANT: You must always populate the travel_log_update field with any observations, clues, or notes worth remembering for the journey and the final riddle — never leave it empty. You are allowed to make a maximum of {MAX_HALLUCINATIONS_PER_STEP} errors per room such as attempting to enter a door that is not present, before the experiment is over. Good luck! JSON"

def last_wish_msg(cause, current_room=None):
    causes_death = {
    "trapped": f"You are trapped in Room {current_room} which has no exits — Room {current_room} = DEAD END.",
    "hallucinated":"You have exceeded the maximum number of hallucinations allowed per step.",
    "exhausted":"You have exceeded the maximum number of steps allowed to complete the maze.",
    "looping":"You are in loop, going back and forth between the same rooms without making progress towards the goal.",
    }

    return f"GAME OVER: {causes_death.get(cause, 'Unknown reason')}. Now, review your journey through your notes. You have the chance to leave a final message to your future self. REQUIRED: (1) List every room you visited more than once using the format 'Room X → Room Y → Room X = LOOP'. (2) List any dead ends you found using the format 'Room X = DEAD END'. Then describe why you failed and what doors to avoid. STRICT RULE: Do not use conversational filler, bullet points, or headers inside JSON values."

def hallucination_door_msg(room_id, attempted_door):
    return f"You attempted to open door to room {attempted_door} which is not present in room {room_id}."
            