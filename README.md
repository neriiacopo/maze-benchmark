The image and text assets for this benchmark are sourced from [Al Sweigart's mazewebsite](https://github.com/asweigart/mazewebsite). This repository is for educational and research purposes only, specifically for benchmarking AI visual reasoning.

## Running the Benchmark

Use `run.py` to run benchmark iterations from the command line.

```
python run.py --model <model-name> [options]
```

### Providers

| Provider | `--provider` | Requirement |
|---|---|---|
| OpenAI (default) | `openai` | `OPENAI_API_KEY` env var |
| Google Gemini | `gemini` | `GOOGLE_API_KEY` env var |
| LMStudio (local) | `lmstudio` | LMStudio running at `http://127.0.0.1:1234/v1` |

### Examples

```bash
# OpenAI
python run.py --model gpt-4o-mini --iterations 25

# Gemini
python run.py --model gemini-2.0-flash --provider gemini --iterations 10

# LMStudio
python run.py --model ministral-3-3b --provider lmstudio --iterations 10

# Custom output directory and step limit
python run.py --model gpt-4o-mini --output-dir outputs/experiment_1 --max-steps 50

# Use only the last 5 notes from prior runs
python run.py --model gpt-4o-mini --notes last-n --last-n 5
```

Runs resume automatically if the output directory already contains data.

### All Options

| Flag | Default | Description |
|---|---|---|
| `--model` | *(required)* | Model name, e.g. `gpt-4o-mini`, `gemini-2.0-flash` |
| `--provider` | `openai` | `openai`, `gemini`, or `lmstudio` |
| `--iterations` | `25` | Number of iterations to run |
| `--output-dir` | `outputs/<model>` | Directory for output JSON files |
| `--max-steps` | `32` | Maximum navigation steps per iteration |
| `--notes` | `all` | Prior note injection strategy (see below) |
| `--last-n` | `3` | N for `--notes last-n` |
| `--lmstudio-url` | `http://127.0.0.1:1234/v1` | LMStudio server URL |

### Note Injection Strategies (`--notes`)

| Value | Behaviour |
|---|---|
| `all` | All past advice strings, passed raw (default) |
| `last` | Only the most recent advice |
| `last-n` | Last N advice strings (set N with `--last-n`) |
| `survey` | Last note formatted as a structured survey |
| `synthesized` | All past advice compressed into one via an extra LLM call |
| `none` | No prior notes injected |
