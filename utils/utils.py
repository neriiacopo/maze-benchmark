import base64
import os
import json
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from utils.prompt_config import SHARED_NOTES
from config import LOG_KEYS

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def format_maze_history(history, prompt_config):
    """Returns (path_str, notes_str) for use in the maze step prompt."""
    path_lines = []
    note_lines = []

    for s in history:
        path_lines.append(prompt_config.format_path_line(step=s['step'], room=s['room']))
        errors = s.get("hallucinations", [])
        errors_str = f" | ERRORS: {'; '.join(errors)}" if errors else ""
        note_lines.append(prompt_config.format_note_line(step=s['step'], note=s.get('note', ''), errors_str=errors_str))

    return "\n".join(path_lines), "\n".join(note_lines)

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

def get_survey(notes, prompt_config):
    last_wish_schema = prompt_config.schemas["LastWish"]
    formatted_parts = []

    for key in SHARED_NOTES:
        description = last_wish_schema.model_fields[key].description
        value = notes.get(key) if isinstance(notes, dict) else getattr(notes, key)

        if isinstance(value, list):
            value = ", ".join(value)

        formatted_parts.append(f"{description} {value}")

    string = "\n".join(formatted_parts)
    return string


def get_advices(notes, num_advices=int(3)):
    data = []
    list = notes["last_notes"][- num_advices:]

    for l in list:
        data.append(l['data']["advice_for_future_self"])

    return data


def build_model(provider: str, model_name: str, lmstudio_url: str):
    if provider == "gemini":
        return ChatGoogleGenerativeAI(model=model_name, request_timeout=180, max_retries=3)

    if provider == "lmstudio":
        return ChatOpenAI(
            base_url=lmstudio_url,
            api_key="not-needed",
            model=model_name,
            request_timeout=180,
            max_retries=5,
            max_tokens=8192,
            seed=42,
            model_kwargs={"response_format": {"type": "json_object"}},
        )

    # default: openai
    return ChatOpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        model=model_name,
        request_timeout=180,
        max_retries=5,
        max_tokens=8192,
        seed=42,
    )


def load_data(output_dir: str) -> dict:
    data = {}
    for key in LOG_KEYS:
        path = os.path.join(output_dir, f"{key}.json")
        if os.path.exists(path):
            with open(path) as f:
                data[key] = json.load(f)
        else:
            data[key] = []
    return data


def save_data(data: dict, output_dir: str):
    for key, content in data.items():
        path = os.path.join(output_dir, f"{key}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=4)
