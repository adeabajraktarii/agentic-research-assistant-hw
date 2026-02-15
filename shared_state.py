from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, TypedDict


class Citation(TypedDict):
    source_id: str          
    quote: str              
    location: str           


class ResearchNote(TypedDict):
    claim: str
    citations: List[Citation]


class TraceLogRow(TypedDict):
    step: str              
    agent: str              
    action: str             
    outcome: str           


@dataclass
class SharedState:
    task: str
    task_key: Optional[str] = None
    task_text: Optional[str] = None

    plan: List[str] = field(default_factory=list)

    research_notes: List[ResearchNote] = field(default_factory=list)

    draft: Optional[str] = None

    verification_notes: List[str] = field(default_factory=list)

    final_output: Optional[str] = None
    
    trace: List[TraceLogRow] = field(default_factory=list)

    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
