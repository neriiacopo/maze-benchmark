
DF_PATH = "data/maze_database.tsv"
IMGS_DIR = "data/images/"
IMGS_SUBDIR ={"high":"highres", "low":"thumbnails"}

MAX_STEPS = 50
MAX_HALLUCINATIONS_PER_STEP = 3
BACKTRACKING_THRESHOLD = 4
MAX_BACKTRACKING_ATTEMPTS = 2

SYS_PROMPT = f"You are an participating in an experiment to test your reasoning and navigational skills. You are traveling through a Maze and your task it so go from room 1 to room 45, and back, in the shortest amount of steps possible. At each step, you will be given a description of the room you are in, and an image of the room. You will also be given a map of your previous steps, a log with the notes you take along your exploration as well as some final notes left for you from previous fellow explorers. Based on this information, at each step you must choose which door to go through next. Finally, you will have to solve the riddle contained in room 45, which solution is to be found along your journey. All elements of the text and in the images are clues to help you make the best decision. Remember you must also explain your reasoning for choosing any door, and what information you are taking note of for the return journey and the final riddle. You are allowed to make a maximum of {MAX_HALLUCINATIONS_PER_STEP} errors per room such as attempting to enter a door that is not present, before the experiment is over. Good luck!"

def last_wish_msg(cause): 
    causes_death = {
    "trapped":"You are trapped in a room with no exits.", 
    "hallucinated":"You have exceeded the maximum number of hallucinations allowed per step.",
    "exhausted":"You have exceeded the maximum number of steps allowed to complete the maze.",
    "looping":"You are in loop, going back and forth between the same rooms without making progress towards the goal.",
    }

    return f"GAME OVER: {causes_death.get(cause, 'Unknown reason')}. Review your journey and your notes. You have the chance to leave a final message to your future self, who will attempt the maze again. What do you think went wrong? What advice would you give them?"

def hallucination_door_msg(room_id, attempted_door):
    return f"You attempted to open door to room {attempted_door} which is not present in room {room_id}."
            