from __future__ import annotations

from typing import Any, Dict

from langgraph.graph import END, StateGraph

from shared_state import SharedState
from agents.planner import planner_agent
from agents.researcher import researcher_agent
from agents.writer import writer_agent
from agents.verifier import verifier_agent


def build_graph():
    """
    Required workflow:
    planner -> researcher -> writer -> verifier -> END
    """
    graph = StateGraph(SharedState)

    graph.add_node("planner", planner_agent)
    graph.add_node("researcher", researcher_agent)
    graph.add_node("writer", writer_agent)
    graph.add_node("verifier", verifier_agent)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "writer")
    graph.add_edge("writer", "verifier")
    graph.add_edge("verifier", END)

    return graph.compile()


def run_task(task: str, task_key: str | None = None) -> Dict[str, Any]:
    """
    Convenience runner for local testing / UI.
    Always returns a plain dict (safe for run_local.py).
    """
    app = build_graph()

    state = SharedState(task=task, task_key=task_key, task_text=task)

    final_state = app.invoke(state)

    if isinstance(final_state, dict):
        return final_state

    if hasattr(final_state, "__dict__"):
        return final_state.__dict__  # SharedState dataclass

    return {"final_state": str(final_state)}
