from pydantic import BaseModel, Field
from typing import List


class Analysis(BaseModel):
    available_doors: List[int] = Field(description="List of door numbers you see in the image.")
    visual_clues: str = Field(description="Observations of symbols, light, numbers, or architecture.")
    textual_clues: str = Field(description="Interpretation of puns or hints in the room description.")

class Decision(BaseModel):
    current_room: int = Field(description="The number of the current room.")
    room_picked: int = Field(description="The number of the door you intend to enter.")
    reasoning: str = Field(description="Why you are choosing this specific door.")

class MazeResponse(BaseModel):
    model_config = {"extra": "allow"}
    analysis: Analysis
    decision: Decision
    travel_log_update: str = Field(description="Information to remember for the overall journey or the final riddle.")

class PrologueAnalysis(BaseModel):
    meta_observations: str = Field(description="Analyze the cover and prologue for themes, hidden text, or symbolic clues.")
    strategy_notes: str = Field(description="Based on the prologue's instructions, how will you evaluate the rooms?") # Note, this is not currently being used in the next calls
    ready_to_start: bool = Field(description="Set to True if you have understood the instructions and are ready to enter Room 1.")

# class LastWish(BaseModel):
#     note: str = Field(description="A final message to your future self, who will attempt the maze again. What advice would you give them?")

class LastWish(BaseModel):
    rating: int = Field(description="On a scale of 1 to 10, how would you rate your failed attempt at the maze?")    
    failure_reasons: str = Field(
        description="What went wrong?"
    )    
    pivotal_discovery: str = Field(
        description="What did you discover?"
    )
    abandoned_hypotheses: List[str] = Field(
        description="Is there any previous assumption that you proved wrong?"
    )
    prev_notes_value: bool = Field(description="Were the previous notes helpful or misleading?")
    advice_for_future_self: str = Field(
        description="Which advice would you give to your future self to help them succeed in the maze where you failed?"
    )

shared_notes = ["failure_reasons", "pivotal_discovery", "abandoned_hypotheses", "advice_for_future_self"]


class ResumeNote(BaseModel):
    strategy: str = Field(description="Which strategy should I adopt this run?")