import yaml
from pydantic import create_model, Field, ConfigDict
from typing import List

import config


# Field types are structural (code concern), descriptions are prompt text (config concern).
# Keys map to schema names in the YAML; values map field names to (type, default).
# Use ... for required fields, a value for optional fields.
FIELD_TYPES = {
    "Analysis": {
        "available_doors": (List[int], ...),
        "visual_clues": (str, ...),
        "textual_clues": (str, ...),
    },
    "Decision": {
        "current_room": (int, ...),
        "room_picked": (int, ...),
        "reasoning": (str, ...),
    },
    "MazeResponse": {
        "travel_log_update": (str, ""),
    },
    "PrologueAnalysis": {
        "meta_observations": (str, ...),
        "strategy_notes": (str, ...),
        "ready_to_start": (bool, ...),
    },
    "LastWish": {
        "rating": (int, ...),
        "failure_reasons": (str, ...),
        "pivotal_discovery": (str, ...),
        "abandoned_hypotheses": (List[str], ...),
        "prev_notes_value": (bool, ...),
        "advice_for_future_self": (str, ...),
    },
    "ResumeNote": {
        "strategy": (str, ...),
    },
}

# Fields from LastWish that are shared across notes strategies (survey, advices, etc.)
SHARED_NOTES = ["failure_reasons", "pivotal_discovery", "abandoned_hypotheses", "advice_for_future_self"]


def _build_schemas(schema_descriptions: dict) -> dict:
    """Build Pydantic model classes from YAML field descriptions."""
    models = {}

    for name, field_defs in FIELD_TYPES.items():
        if name == "MazeResponse":
            continue  # built separately below (composes Analysis + Decision)

        descriptions = schema_descriptions.get(name, {})
        fields = {}
        for field_name, (ftype, default) in field_defs.items():
            desc = descriptions.get(field_name, "")
            if default is ...:
                fields[field_name] = (ftype, Field(description=desc))
            else:
                fields[field_name] = (ftype, Field(default=default, description=desc))
        models[name] = create_model(name, **fields)

    # MazeResponse composes Analysis + Decision + its own fields
    mr_descs = schema_descriptions.get("MazeResponse", {})
    mr_fields = {
        "analysis": (models["Analysis"], ...),
        "decision": (models["Decision"], ...),
        "travel_log_update": (str, Field(default="", description=mr_descs.get("travel_log_update", ""))),
    }
    models["MazeResponse"] = create_model(
        "MazeResponse",
        __config__=ConfigDict(extra="allow"),
        **mr_fields,
    )

    return models


class PromptConfig:
    """Loads a YAML prompt config, builds Pydantic schemas, and provides template helpers."""

    def __init__(self, raw: dict, schemas: dict, system_prompt: str):
        self.raw = raw
        self.schemas = schemas
        self.system_prompt = system_prompt

    @classmethod
    def load(cls, path: str = "prompts/default.yaml") -> "PromptConfig":
        with open(path) as f:
            raw = yaml.safe_load(f)

        required = {"system_prompt", "messages", "history_format", "schemas"}
        missing = required - raw.keys()
        if missing:
            raise ValueError(f"Prompt config missing keys: {missing}")

        schemas = _build_schemas(raw["schemas"])
        system_prompt = raw["system_prompt"].format(
            max_hallucinations=config.MAX_HALLUCINATIONS_PER_STEP
        )

        return cls(raw=raw, schemas=schemas, system_prompt=system_prompt)

    # --- Template helpers ---

    def format_template(self, key: str, **kwargs) -> str:
        return self.raw["messages"][key].format(**kwargs)

    def last_wish_msg(self, cause: str, current_room=None) -> str:
        causes = self.raw["messages"]["last_wish_causes"]
        cause_text = causes.get(cause, "Unknown reason").format(current_room=current_room)
        return self.raw["messages"]["last_wish_suffix"].format(cause_text=cause_text)

    def hallucination_door_msg(self, room_id, attempted_door) -> str:
        return self.raw["messages"]["hallucination_door"].format(
            room_id=room_id, attempted_door=attempted_door
        )

    def format_path_line(self, **kwargs) -> str:
        return self.raw["history_format"]["path_line"].format(**kwargs)

    def format_note_line(self, **kwargs) -> str:
        return self.raw["history_format"]["note_line"].format(**kwargs)
