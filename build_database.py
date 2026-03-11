"""
Regenerate data/maze_database.tsv from the source JSON files.
Only needed if you edit rooms_text.json or image_map.json.

Usage:
    python build_database.py
"""

import json
import pandas as pd

ROOMS_TEXT = "data/rooms_text.json"
IMAGE_MAP  = "data/image_map.json"
OUTPUT_TSV = "data/maze_database.tsv"

# Room 0 is the prologue, not in the image map
PROLOGUE = "This is a building in the shape of a book . . . a maze. Each numbered page depicts a room in the Maze. The doors in each room lead to other pages, other rooms. The object of this book is to find your way from the entrance (room 1) to the center of the Maze (room 45) and return to the entrance. The shortest path there and back is a round trip of 16 steps. A map of the rooms visited, a description of each room, and an illustration of each room are given. Clues to the solution of the Maze are hidden in the illustrations. Good luck."

with open(ROOMS_TEXT) as f:
    text = {int(k): v for k, v in json.load(f).items()}

with open(IMAGE_MAP) as f:
    image_map = {int(k): v for k, v in json.load(f).items()}

# Build connections string for each room (semicolon-delimited door numbers)
# Room 29 has a manual extra link not in the image map
connections = {
    k: ";".join(item[0] for item in doors)
    for k, doors in image_map.items()
}
connections[29] = connections.get(29, "") + ";17"

rooms = sorted(set(text.keys()) | {0})
df = pd.DataFrame({
    "Room": rooms,
    "Description": [text.get(r, PROLOGUE) for r in rooms],
    "Connections": [connections.get(r, "1" if r == 0 else "") for r in rooms],
})

df.to_csv(OUTPUT_TSV, sep="\t", index=False)
print(f"Wrote {len(df)} rooms to {OUTPUT_TSV}")
