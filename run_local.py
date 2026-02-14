from __future__ import annotations

import argparse
from typing import Optional

from retrieval.index_store import ensure_index
from orchestration.graph import run_task
from tasks.examples import EXAMPLE_TASKS


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--rebuild-index", action="store_true")
    parser.add_argument("--task_key", type=str, help="Task key from EXAMPLE_TASKS")

    args = parser.parse_args()

    # Always ensure index exists
    if args.rebuild_index:
        print("Rebuilding FAISS index from data/docs ...")
        ensure_index(docs_dir="data/docs", force_rebuild=True)
        print("✅ Index rebuilt.")
        return
    else:
        ensure_index(docs_dir="data/docs", force_rebuild=False)

    # If no task provided → just ensure index
    if not args.task_key:
        print("✅ Index ready. Provide --task_key to run a task.")
        return

    if args.task_key not in EXAMPLE_TASKS:
        print(f"❌ Unknown task_key: {args.task_key}")
        print("Available task_keys:")
        for k in EXAMPLE_TASKS:
            print(" -", k)
        return

    task_item = EXAMPLE_TASKS[args.task_key]
    task_text = task_item["task"]

    print(f"\nRunning task: {args.task_key}\n")

    result = run_task(task_text, task_key=args.task_key)

    print("\n================ FINAL OUTPUT ================\n")
    print(result.get("final_output", ""))

    print("\n================ TRACE LOG ===================\n")
    for row in result.get("trace", []):
        print(
            f"- {row['step']:7} | {row['agent']:10} | "
            f"{row['action']} -> {row['outcome']}"
        )


if __name__ == "__main__":
    main()
