# Agentic Research & Action Assistant

## 🌐 Live Demo

Try the deployed Streamlit app here:

https://agentic-research-assistant-hw-ksc3gvcnkvxflrtvbufzgu.streamlit.app/

You can run tasks, explore evaluation results, and view the observability dashboard directly in the browser — no setup required.


A **multi-agent system** that answers business questions using project documents and produces **client-ready, structured deliverables**. Built with **LangGraph**, it orchestrates a **Planner → Researcher → Writer → Verifier** pipeline with vector retrieval (FAISS), citation-grounded outputs, and a verification layer that refuses to hallucinate when evidence is missing.

---

## Quick Start

```bash
git clone https://github.com/adeabajraktarii/agentic-research-assistant-hw.git
cd agentic-research-assistant-hw

python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Mac/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the project root with your OpenAI API key:

```env
OPENAI_API_KEY=your_api_key_here
```

Run a task (CLI):

```bash
python run_local.py --task_key compare_approaches
```

Run the Streamlit UI:

```bash
streamlit run app/app.py
```

---

## Overview

The assistant:

- **Searches** project documents via FAISS vector retrieval
- **Produces** grounded outputs with inline citations
- **Refuses to hallucinate** when evidence is missing (enforces “Not found in sources”)
- **Exposes** full trace logs of agent actions
- **Runs** an evaluation suite with pass/fail results
- **Provides** a Streamlit UI for interactive runs and observability

---

## Supported Tasks

| Task | Description |
|------|-------------|
| **Top 5 risks + mitigations** | Summarize risks and propose mitigations from project docs |
| **Client update email** | Generate a client-ready weekly update from report content |
| **Compare approaches** | Compare two options and recommend one with citations |
| **Deadlines + owners** | Extract action items with owners and due dates |
| **Confluence page** | Draft an internal Confluence-style summary page |

All outputs are grounded in project documents, fully cited, and verified by the Verifier agent.

---

## Architecture

### Multi-Agent Workflow

```
Planner → Researcher → Writer → Verifier
```

| Agent | Role |
|-------|------|
| **Planner** | Breaks the user request into steps and selects the research plan |
| **Researcher** | Queries the FAISS knowledge base and returns grounded notes with citations |
| **Writer** | Produces the deliverable (deterministic writers for strict tasks; LLM for flexible tasks) |
| **Verifier** | Ensures citations exist, blocks hallucinations, enforces “Not found in sources” when needed |

### Key Features

- **Grounded retrieval (RAG)** — FAISS vector DB, chunked markdown docs, citation tracking per claim
- **Deterministic task writers** — Rule-based writers for compare approaches, deadlines extraction, strict top-5 risks
- **Evaluation suite** — 10 evaluation cases with automatic pass/fail checks
- **Observability** — Streamlit sidebar: run history, latency, retrieved chunks, citation counts, pass/fail status
- **Streamlit UI** — Run tasks, run eval cases, view answers, citations, and agent trace logs

---

## Project Structure

```
agentic-research-assistant-hw/
├── agents/           # Planner, Researcher, Writer, Verifier
├── orchestration/    # LangGraph workflow
├── retrieval/        # FAISS indexing + search
├── tasks/            # Research plans and task definitions
├── eval/             # Evaluation dataset + runner
├── app/              # Streamlit UI
├── data/docs/        # Sample project documents
├── run_local.py      # CLI runner
├── requirements.txt
└── README.md
```

---

## Setup & Usage

### 1. Clone and install

```bash
git clone https://github.com/adeabajraktarii/agentic-research-assistant-hw.git
cd agentic-research-assistant-hw

python -m venv .venv
```

**Activate the environment:**

- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **Mac/Linux:** `source .venv/bin/activate`

```bash
pip install -r requirements.txt
```

### 2. Configure API key

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
```

### 3. Run from CLI

```bash
python run_local.py --task_key compare_approaches
```

**Available task keys:**

| Task key |
|----------|
| `compare_approaches` |
| `extract_deadlines_and_owners` |
| `top5_risks_mitigations_strict` |
| `top_risks_mitigations` |
| `client_update_email` |
| `draft_confluence_page` |

### 4. Run the evaluation suite

```bash
python eval/run_eval.py
```

Expected output (all passing):

```
Total: 10
Passed: 10
Failed: 0
```

### 5. Run the Streamlit app

```bash
streamlit run app/app.py
```

From the UI you can:

- Run tasks interactively
- Run evaluation cases
- View answers and citations
- Inspect agent trace logs
- Use the run history / observability dashboard

---

## Acceptance Criteria

| Requirement | Status |
|-------------|--------|
| Multi-agent orchestration (Planner → Researcher → Writer → Verifier) | ✅ |
| Shared state object | ✅ |
| Document retrieval tool (FAISS) | ✅ |
| Grounded outputs with citations | ✅ |
| Verifier enforcing “I don’t know” / no hallucination | ✅ |
| Agent trace logs | ✅ |
| 5+ end-to-end example tasks | ✅ |
| Evaluation set (10 tests + pass/fail) | ✅ |
| Observability dashboard (Streamlit) | ✅ |
| Streamlit UI | ✅ |

---

## Notes

- The project uses **sample documents only**; no confidential data is included in the repository.

---

## Author

**Adea Bajraktari**