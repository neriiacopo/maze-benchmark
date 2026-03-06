import base64
import pandas as pd

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def stringify_history(history):

    # Errors are extracted only for current room
    hallucinations = history[-1].get("hallucinations", []) if history else []

    message = [f"STEP {s['step']} | ROOM: {s['room']} | NOTE: {s['note']} | ERRORS: {"; ".join([f"{h}" for h in hallucinations]) if len(hallucinations)>0 else "NONE"}" for i, s in enumerate(history)]

    return message

def preprocess_df(path):
    df = pd.read_csv(path, sep="\t")
    df["Connections"] = df["Connections"].apply(
        lambda x: tuple(int(i) for i in x.strip().split(";")) if isinstance(x, str) else tuple()
    )

    return df

def check_loop(picked, travel_history, backtracking=3):
    if len(travel_history) < backtracking:
        return False
    
    last_rooms_id = [entry["room"] for entry in travel_history[-backtracking:]]
    
    return picked in last_rooms_id