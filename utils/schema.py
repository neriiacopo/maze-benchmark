from pydantic import BaseModel, Field
from typing import List


class Analysis(BaseModel):
    available_doors: List[int] = Field(description="List of door numbers you see in the image.")
    visual_clues: str = Field(description="Observations of symbols, light, numbers, or architecture.")
    textual_clues: str = Field(description="Interpretation of puns or hints in the room description.")

class Decision(BaseModel):
    current_room: int = Field(description="The number of the current room.")
    room_picked: int = Field(description="The number of the door you intend to enter.")
    reasoning: str = Field(description="Why you are choosing this specific door based on the Prologue's clues.")

class MazeResponse(BaseModel):
    model_config = {"extra": "allow"}
    analysis: Analysis
    decision: Decision
    travel_log_update: str = Field(description="Information to remember for the overall journey or the final riddle.")

class PrologueAnalysis(BaseModel):
    meta_observations: str = Field(description="Analyze the cover and prologue for themes, hidden text, or symbolic clues.")
    strategy_notes: str = Field(description="Based on the prologue's instructions, how will you evaluate the rooms?")
    ready_to_start: bool = Field(description="Set to True if you have understood the instructions and are ready to enter Room 1.")

class LastWish(BaseModel):
    note: str = Field(description="A final message to your future self, who will attempt the maze again. What advice would you give them?")