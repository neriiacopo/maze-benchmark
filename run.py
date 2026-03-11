"""
Maze Benchmark runner.

Examples:
  python run.py --model gpt-4o-mini --iterations 25
  python run.py --model gpt-4o-mini --iterations 25 --provider openai
  python run.py --model ministral-3-3b --provider lmstudio --iterations 10
  python run.py --model gemini-2.0-flash --provider gemini --iterations 10
  python run.py --model gpt-4o-mini --output-dir outputs/my_run --max-steps 40 --notes all
"""

import argparse
import os

from utils.actions import resume_notes
from utils.navigation import Agent, Maze, explore_maze
from utils.utils import get_advices, get_survey, build_model, load_data, save_data


def inject_notes(agent: Agent, data: dict, strategy: str, last_n: int):
    if not data["last_notes"]:
        return

    if strategy == "all":
        agent.last_notes = "\n".join(
            f"Attempt {note['iteration']}: {note['data']['advice_for_future_self']}"
            for note in data["last_notes"]
        )
    elif strategy == "synthesized":
        raw = "\n".join(
            f"Attempt {note['iteration']}: {note['data']['advice_for_future_self']}"
            for note in data["last_notes"]
        )
        agent.last_notes = resume_notes(agent, raw)
    elif strategy == "last":
        agent.last_notes = data["last_notes"][-1]["data"]["advice_for_future_self"]
    elif strategy == "survey":
        agent.last_notes = get_survey(data["last_notes"][-1]["data"])
    elif strategy == "last-n":
        agent.last_notes = get_advices(data, last_n)


def parse_args():
    parser = argparse.ArgumentParser(description="Run the Maze Benchmark.")

    parser.add_argument("--model", required=True, help="Model name (e.g. gpt-4o-mini, gemini-2.0-flash)")
    parser.add_argument(
        "--provider",
        choices=["openai", "gemini", "lmstudio"],
        default="openai",
        help="Model provider (default: openai)",
    )
    parser.add_argument("--lmstudio-url", default="http://127.0.0.1:1234/v1", help="LMStudio base URL")
    parser.add_argument("--iterations", type=int, default=25, help="Number of iterations to run (default: 25)")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: outputs/<model>)")
    parser.add_argument("--max-steps", type=int, default=32, help="Max steps per iteration (default: 32)")
    parser.add_argument(
        "--notes",
        choices=["all", "synthesized", "last", "survey", "last-n", "none"],
        default="all",
        help="Strategy for injecting prior notes (default: all)",
    )
    parser.add_argument("--last-n", type=int, default=3, help="N for --notes last-n (default: 3)")

    return parser.parse_args()


def main():
    args = parse_args()

    output_dir = args.output_dir or os.path.join("outputs", args.model)
    os.makedirs(output_dir, exist_ok=True)

    model = build_model(args.provider, args.model, args.lmstudio_url)
    data = load_data(output_dir)

    initial_iteration = len(data["travel_logs"])
    last_iteration = initial_iteration + args.iterations

    print(f"Model:      {args.model} ({args.provider})")
    print(f"Output dir: {output_dir}")
    print(f"Iterations: {initial_iteration} → {last_iteration - 1}")
    print(f"Notes:      {args.notes}")

    for i in range(initial_iteration, last_iteration):
        print(f"\n--- Iteration {i} ---\n")

        maze = Maze()
        agent = Agent(model=model)

        if args.notes != "none":
            inject_notes(agent, data, args.notes, args.last_n)

        new_data, agent = explore_maze(agent, maze, max_steps=args.max_steps)

        for key, value in new_data.items():
            data.setdefault(key, []).append({"iteration": i, "data": value})

        save_data(data, output_dir)


if __name__ == "__main__":
    main()
