
> [!IMPORTANT]
> **AUTONOMOUS ARCHITECTURE UPDATE**
> This project has been updated to run autonomously. 
> - The 5-step interactive frontend wizard has been replaced by a **React Dashboard**.
> - The backend uses **APScheduler** to automatically trigger the review fetch and LangGraph analysis pipeline every day at 11:00 AM UTC.
> - The MCP Approval Gate remains the only manual step, which is actioned from the new Frontend Dashboard.
>
> *(Note: The original documentation below describes the manual 5-step UI, which is now superseded by the autonomous dashboard model.)*

# Groww AI Product Feedback Intelligence — Architecture

---

## 1. Architecture Overview

This document defines the complete technical architecture for the **Groww AI Product Feedback Intelligence & Support Workflow** application. The system ingests real Google Play reviews for the Groww Android app (`com.nextbillion.groww`), runs an AI-powered analysis pipeline using **LangChain + LangGraph** orchestrated with **Groq LLM**, and produces two actionable outputs — a Weekly Product Pulse and a Customer Fee Explainer — behind an explicit human-approval gate.

### High-Level System Diagram

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + TypeScript + Tailwind)     │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │ Screen 1 │→ │ Screen 2 │→ │ Screen 3 │→ │ Screen 4 │→ │  S5  │ │
│  │  Fetch   │  │ Progress │  │Dashboard │  │ Outputs  │  │Approv│ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │ REST API (HTTP / SSE)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI — Python)                   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    API Router Layer                           │   │
│  │  /api/reviews/fetch  │ /api/analysis/run  │ /api/approval/*  │   │
│  └──────────────────────┴───────────────────┴──────────────────┘   │
│                             │                                       │
│  ┌──────────────────────────▼──────────────────────────────────┐   │
│  │              LangChain / LangGraph Agent Layer               │   │
│  │                                                              │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │   │
│  │  │ Review     │  │ Analysis   │  │ Output Generation      │ │   │
│  │  │ Ingestion  │→ │ Pipeline   │→ │ Pipeline               │ │   │
│  │  │ Chain      │  │ (LangGraph │  │ (LangChain LCEL)       │ │   │
│  │  │            │  │  Graph)    │  │                        │ │   │
│  │  └────────────┘  └────────────┘  └────────────────────────┘ │   │
│  │                         │                                    │   │
│  │                    ChatGroq (Groq LLM)                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────────────────▼──────────────────────────────────┐   │
│  │                    Service Layer                             │   │
│  │                                                              │   │
│  │  ┌─────────────┐  ┌───────────────┐  ┌──────────────────┐  │   │
│  │  │ Google Play  │  │ Official      │  │ MCP Write        │  │   │
│  │  │ Scraper      │  │ Source        │  │ Actions          │  │   │
│  │  │ Service      │  │ Retriever     │  │ (Approval-Gated) │  │   │
│  │  └─────────────┘  └───────────────┘  └──────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────────────────▼──────────────────────────────────┐   │
│  │                    Data Layer (SQLite / In-Memory)           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
      ┌──────────┐   ┌──────────┐   ┌──────────┐
      │ Google   │   │ Groww    │   │ Gmail    │
      │ Play     │   │ Official │   │ API /    │
      │ Store    │   │ Website  │   │ Google   │
      │          │   │          │   │ Docs API │
      └──────────┘   └──────────┘   └──────────┘
```

---

## 2. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 18+ with TypeScript | Single-page application with multi-step workflow UI |
| **Styling** | Tailwind CSS 3+ | Utility-first CSS for clean, professional dashboard design |
| **Backend** | FastAPI (Python 3.11+) | Async REST API server with SSE support for progress streaming |
| **AI Orchestration** | LangChain + LangGraph | Agent framework for chaining LLM calls, tool use, and stateful workflows |
| **LLM Provider** | Groq (via `langchain-groq`) | Ultra-fast inference using `ChatGroq` with `llama-3.3-70b-versatile` |
| **Review Scraping** | `google-play-scraper` (Python) | Public Google Play review retrieval with pagination |
| **Web Scraping** | `httpx` + `BeautifulSoup4` | Retrieve official Groww documentation for fee verification |
| **Gmail Integration** | Google Gmail API (`google-api-python-client`) | Create Gmail drafts (OAuth 2.0) |
| **Document Store** | Google Docs API or local JSON append | Internal knowledge repository |
| **Database** | PostgreSQL (via `asyncpg`) | Persistent review storage, analysis results, and audit trail |
| **State Management** | Zustand (frontend) | Lightweight React state management for workflow state |
| **Build Tool** | Vite | Fast frontend build and dev server |

---

## 3. App Configuration

All Groww-specific configuration is externalized in a `.env` file and loaded via `pydantic-settings`:

```env
# === Groww App Config ===
APP_NAME=Groww
PLATFORM=Google Play
PACKAGE_NAME=com.nextbillion.groww
REVIEW_LOOKBACK_DAYS=7

# === Groq LLM Config ===
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL_NAME=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.1
GROQ_MAX_TOKENS=4096

# === Google OAuth Config (Gmail + Docs) ===
GOOGLE_CLIENT_ID=xxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# === Server Config ===
BACKEND_PORT=8000
FRONTEND_PORT=5173
DATABASE_URL=sqlite:///./data/groww_intelligence.db
```

### Configuration Model (Python)

```python
# backend/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Groww App
    app_name: str = "Groww"
    platform: str = "Google Play"
    package_name: str = "com.nextbillion.groww"
    review_lookback_days: int = 7

    # Groq
    groq_api_key: str
    groq_model_name: str = "llama-3.3-70b-versatile"
    groq_temperature: float = 0.1
    groq_max_tokens: int = 4096

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/callback"

    # Server
    backend_port: int = 8000
    database_url: str = "postgresql://user:pass@host/db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## 4. Project Directory Structure

```text
groww-product-intelligence/
├── .env                              # Environment variables (git-ignored)
├── .env.example                      # Template for environment variables
├── docker-compose.yml                # Optional: containerized deployment
├── README.md
├── problemStatement.md
├── architecture.md
│
├── backend/                          # FastAPI Python backend
│   ├── main.py                       # FastAPI app entry point
│   ├── requirements.txt              # Python dependencies
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                 # Pydantic settings (see §3)
│   │   └── database.py               # PostgreSQL connection + session management
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── review.py                 # Review data model
│   │   ├── theme.py                  # Theme + ThemeEvidence models
│   │   ├── fee_issue.py              # FeeIssue + Source models
│   │   ├── outputs.py                # ProductPulse + FeeExplainer models
│   │   └── approval.py               # ApprovalRequest + MCPActionResult models
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── review_scraper.py         # Google Play review retrieval
│   │   ├── review_cleaner.py         # Review quality checks + normalization
│   │   ├── source_retriever.py       # Official Groww documentation scraping
│   │   ├── gmail_service.py          # Gmail API draft creation
│   │   ├── document_service.py       # Internal document append (Google Docs / JSON)
│   │   └── approval_gate.py          # Application-level approval state machine
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── llm.py                    # ChatGroq initialization + shared LLM instance
│   │   ├── graph.py                  # LangGraph workflow graph definition
│   │   ├── state.py                  # TypedDict state schema for the graph
│   │   │
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── classify_reviews.py   # Per-review classification node
│   │   │   ├── cluster_themes.py     # Theme clustering node
│   │   │   ├── rank_themes.py        # Theme ranking + top-3 selection node
│   │   │   ├── detect_fee.py         # Fee/charge confusion detection node
│   │   │   ├── extract_quotes.py     # Verbatim quote extraction node
│   │   │   ├── analyze_trends.py     # Temporal trend analysis node
│   │   │   ├── verify_sources.py     # Official Groww source verification node
│   │   │   ├── generate_pulse.py     # Weekly Product Pulse generation node
│   │   │   └── generate_explainer.py # Fee Explainer generation node
│   │   │
│   │   └── prompts/
│   │       ├── classify.py           # Classification prompt templates
│   │       ├── cluster.py            # Clustering prompt templates
│   │       ├── fee_detection.py      # Fee detection prompt templates
│   │       ├── pulse.py              # Product Pulse prompt templates
│   │       └── explainer.py          # Fee Explainer prompt templates
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py                 # Main API router aggregation
│   │   ├── reviews.py                # /api/reviews/* endpoints
│   │   ├── analysis.py               # /api/analysis/* endpoints
│   │   ├── outputs.py                # /api/outputs/* endpoints
│   │   ├── approval.py               # /api/approval/* endpoints
│   │   └── auth.py                   # /api/auth/* Google OAuth endpoints
│   │
│   └── data/
│       └── groww_intelligence.db      # SQLite database (auto-created)
│
└── frontend/                          # React + TypeScript frontend
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── index.html
    │
    ├── public/
    │   └── groww-logo.svg
    │
    └── src/
        ├── main.tsx                   # React entry point
        ├── App.tsx                    # Root app with routing
        │
        ├── api/
        │   └── client.ts              # Axios/fetch API client
        │
        ├── store/
        │   └── workflowStore.ts       # Zustand store for workflow state
        │
        ├── types/
        │   └── index.ts               # TypeScript interfaces mirroring backend models
        │
        ├── components/
        │   ├── layout/
        │   │   ├── Header.tsx
        │   │   ├── Sidebar.tsx
        │   │   └── StepIndicator.tsx   # Workflow step progress bar
        │   │
        │   ├── common/
        │   │   ├── Card.tsx
        │   │   ├── Badge.tsx
        │   │   ├── StatusIndicator.tsx
        │   │   ├── TrendBadge.tsx
        │   │   ├── ProgressStep.tsx
        │   │   └── EditableTextArea.tsx
        │   │
        │   └── screens/
        │       ├── SourceFetch.tsx      # Screen 1 — Source & Review Fetch
        │       ├── AnalysisProgress.tsx # Screen 2 — Analysis Progress
        │       ├── InsightsDashboard.tsx # Screen 3 — Insights Dashboard
        │       ├── GeneratedOutputs.tsx  # Screen 4 — Generated Outputs
        │       └── ApprovalReview.tsx    # Screen 5 — Approval Review
        │
        └── styles/
            └── index.css               # Tailwind directives + custom design tokens
```

---

## 5. LangChain + LangGraph Agent Architecture

The AI layer is the core of the system. It uses **LangChain** for structured LLM interactions (prompt templates, output parsers, chains) and **LangGraph** for stateful, multi-step orchestration with conditional edges and progress reporting.

### 5.1 Why LangChain + LangGraph

| Concern | Solution |
|---|---|
| Structured LLM calls with output parsing | LangChain LCEL chains with `ChatGroq` |
| Multi-step analysis with branching logic | LangGraph `StateGraph` with conditional edges |
| Progress tracking across pipeline steps | LangGraph state updates streamed via SSE |
| Human-in-the-loop approval gate | LangGraph `interrupt()` mechanism |
| Tool integration (scraping, source retrieval) | LangChain `Tool` wrappers |
| Prompt management | LangChain `ChatPromptTemplate` |
| Reproducibility & debugging | LangSmith tracing (optional) |

### 5.2 Groq LLM Initialization

```python
# backend/agents/llm.py
from langchain_groq import ChatGroq
from core.config import settings

def get_llm(temperature: float | None = None) -> ChatGroq:
    """Create a ChatGroq instance with project defaults."""
    return ChatGroq(
        model=settings.groq_model_name,
        api_key=settings.groq_api_key,
        temperature=temperature or settings.groq_temperature,
        max_tokens=settings.groq_max_tokens,
        max_retries=2,
    )

# Shared instances for different tasks
analysis_llm = get_llm(temperature=0.0)       # Deterministic for classification
generation_llm = get_llm(temperature=0.3)     # Slightly creative for pulse/explainer
```

### 5.3 LangGraph State Schema

```python
# backend/agents/state.py
from typing import TypedDict, Literal
from models.review import ReviewRecord
from models.theme import Theme
from models.fee_issue import FeeIssue, OfficialSource
from models.outputs import ProductPulse, FeeExplainer, CustomerQuote

class PipelineState(TypedDict):
    """Central state object flowing through the LangGraph pipeline."""

    # --- Input ---
    raw_reviews: list[ReviewRecord]

    # --- Cleaning ---
    cleaned_reviews: list[ReviewRecord]
    cleaning_stats: dict  # { removed_empty, removed_duplicates, total_valid }

    # --- Classification ---
    classified_reviews: list[ReviewRecord]  # Reviews with theme/sentiment attached

    # --- Themes ---
    themes: list[Theme]
    top_themes: list[Theme]               # Top 3 ranked themes

    # --- Fee Detection ---
    fee_issue: FeeIssue | None
    fee_confidence: Literal["High", "Medium", "Low"] | None

    # --- Quotes ---
    customer_quotes: list[CustomerQuote]  # Exactly 3 verbatim quotes

    # --- Temporal ---
    trend_analysis: dict                  # Per-theme trend data

    # --- Source Verification ---
    official_sources: list[OfficialSource]

    # --- Generated Outputs ---
    product_pulse: ProductPulse | None
    fee_explainer: FeeExplainer | None

    # --- Progress ---
    current_step: str
    completed_steps: list[str]
    errors: list[str]
```

### 5.4 LangGraph Workflow Graph

```python
# backend/agents/graph.py
from langgraph.graph import StateGraph, START, END
from agents.state import PipelineState
from agents.nodes import (
    classify_reviews,
    cluster_themes,
    rank_themes,
    detect_fee,
    extract_quotes,
    analyze_trends,
    verify_sources,
    generate_pulse,
    generate_explainer,
)

def build_analysis_graph() -> StateGraph:
    """Build the LangGraph analysis pipeline."""

    builder = StateGraph(PipelineState)

    # --- Add nodes ---
    builder.add_node("classify_reviews", classify_reviews.run)
    builder.add_node("cluster_themes", cluster_themes.run)
    builder.add_node("rank_themes", rank_themes.run)
    builder.add_node("detect_fee_confusion", detect_fee.run)
    builder.add_node("extract_quotes", extract_quotes.run)
    builder.add_node("analyze_trends", analyze_trends.run)
    builder.add_node("verify_sources", verify_sources.run)
    builder.add_node("generate_pulse", generate_pulse.run)
    builder.add_node("generate_explainer", generate_explainer.run)

    # --- Define edges (sequential pipeline) ---
    builder.add_edge(START, "classify_reviews")
    builder.add_edge("classify_reviews", "cluster_themes")
    builder.add_edge("cluster_themes", "rank_themes")
    builder.add_edge("rank_themes", "detect_fee_confusion")
    builder.add_edge("detect_fee_confusion", "extract_quotes")
    builder.add_edge("extract_quotes", "analyze_trends")

    # --- Conditional edge: only verify sources if a fee issue was found ---
    builder.add_conditional_edges(
        "analyze_trends",
        lambda state: "verify_sources" if state.get("fee_issue") else "generate_pulse",
    )
    builder.add_edge("verify_sources", "generate_pulse")

    builder.add_edge("generate_pulse", "generate_explainer")

    # --- Conditional edge: skip explainer if no fee issue ---
    builder.add_conditional_edges(
        "generate_pulse",
        lambda state: "generate_explainer" if state.get("fee_issue") else END,
    )
    builder.add_edge("generate_explainer", END)

    return builder.compile()
```

### 5.5 LangGraph Pipeline Visualization

```text
                    START
                      │
                      ▼
            ┌───────────────────┐
            │ classify_reviews  │   LLM: Assign theme, sentiment, severity,
            │                   │         issue_type to each review
            └────────┬──────────┘
                     ▼
            ┌───────────────────┐
            │ cluster_themes    │   LLM: Group classified reviews into
            │                   │         ≤5 emergent themes
            └────────┬──────────┘
                     ▼
            ┌───────────────────┐
            │ rank_themes       │   LLM + Scoring: Rank themes, select top 3
            │                   │
            └────────┬──────────┘
                     ▼
            ┌───────────────────┐
            │ detect_fee_       │   LLM: Scan for recurring fee/charge
            │ confusion         │         confusion patterns
            └────────┬──────────┘
                     ▼
            ┌───────────────────┐
            │ extract_quotes    │   Rule-based + LLM: Pick 3 verbatim
            │                   │   quotes with provenance
            └────────┬──────────┘
                     ▼
            ┌───────────────────┐
            │ analyze_trends    │   Statistical: 7-day temporal patterns
            │                   │   per theme
            └────────┬──────────┘
                     │
             ┌───────┴────────┐
             │ fee_issue?     │
             ├── YES ─────────┤
             │                ▼
             │   ┌───────────────────┐
             │   │ verify_sources    │   Web scrape: Retrieve official
             │   │                   │   Groww documentation
             │   └────────┬──────────┘
             │            │
             └── NO ──┬───┘
                      ▼
            ┌───────────────────┐
            │ generate_pulse    │   LLM: ≤250-word Weekly Product Pulse
            │                   │
            └────────┬──────────┘
                     │
             ┌───────┴────────┐
             │ fee_issue?     │
             ├── YES ─────────┤
             │                ▼
             │   ┌───────────────────┐
             │   │ generate_         │   LLM: ≤6-bullet Fee Explainer
             │   │ explainer         │   grounded in official sources
             │   └────────┬──────────┘
             │            │
             └── NO ──┬───┘
                      ▼
                     END
```

### 5.6 Example Node Implementation (Theme Clustering)

```python
# backend/agents/nodes/cluster_themes.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from agents.llm import analysis_llm
from agents.state import PipelineState

CLUSTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert product analyst at a fintech company.
Given a batch of classified customer reviews, identify up to {max_themes} distinct themes.

Rules:
- Themes MUST emerge from the actual review content. Do NOT use pre-defined categories.
- Each theme needs: name, description, list of supporting review_ids.
- If fewer than {max_themes} meaningful themes exist, return fewer.
- Return valid JSON matching the schema.
"""),
    ("human", """Here are the classified reviews:

{reviews_json}

Identify the themes and return as JSON array:
[{{"name": "...", "description": "...", "review_ids": [...]}}]
"""),
])

async def run(state: PipelineState) -> dict:
    """Cluster classified reviews into emergent themes."""
    reviews = state["classified_reviews"]

    # Batch reviews for the LLM (handle large corpora by chunking)
    reviews_json = [
        {"review_id": r.review_id, "text": r.review_text, "rating": r.rating,
         "sentiment": r.sentiment, "issue_type": r.issue_type}
        for r in reviews
    ]

    chain = CLUSTER_PROMPT | analysis_llm | JsonOutputParser()

    result = await chain.ainvoke({
        "max_themes": 5,
        "reviews_json": reviews_json,
    })

    # Build Theme objects from LLM output
    themes = _build_themes(result, reviews)

    return {
        "themes": themes,
        "current_step": "cluster_themes",
        "completed_steps": state["completed_steps"] + ["cluster_themes"],
    }
```

---

## 6. Google Play Review Retrieval

### 6.1 Retrieval Strategy

Since we do not have Google Play Developer API access for the Groww application, the system uses the `google-play-scraper` Python package as the primary retrieval mechanism. The architecture is designed with a **common interface** so the underlying implementation can be swapped to the official API if access becomes available.

### 6.2 Common Interface

```python
# backend/services/review_scraper.py
from abc import ABC, abstractmethod
from datetime import date
from models.review import ReviewRecord

class ReviewProvider(ABC):
    """Abstract interface for review retrieval."""

    @abstractmethod
    async def get_reviews(
        self,
        app_id: str,
        start_date: date,
        end_date: date,
    ) -> list[ReviewRecord]:
        ...

class GooglePlayScraperProvider(ReviewProvider):
    """Retrieves reviews via google-play-scraper (public scraping)."""
    ...

class GooglePlayAPIProvider(ReviewProvider):
    """Retrieves reviews via Google Play Developer API (requires auth)."""
    ...
```

### 6.3 Scraper Implementation

```python
# backend/services/review_scraper.py (GooglePlayScraperProvider)
from google_play_scraper import reviews, Sort
from datetime import date, datetime
import asyncio

class GooglePlayScraperProvider(ReviewProvider):

    async def get_reviews(
        self,
        app_id: str,
        start_date: date,
        end_date: date,
    ) -> list[ReviewRecord]:
        """Fetch reviews with pagination using continuation_token."""

        all_reviews: list[ReviewRecord] = []
        continuation_token = None
        seen_ids: set[str] = set()

        while True:
            # Run sync scraper in thread pool
            result, continuation_token = await asyncio.to_thread(
                reviews,
                app_id,
                lang="en",
                country="in",
                sort=Sort.NEWEST,
                count=200,          # Max per page
                continuation_token=continuation_token,
            )

            if not result:
                break

            for r in result:
                review_date = r["at"].date() if isinstance(r["at"], datetime) else r["at"]

                # Stop if we've gone past the start_date boundary
                if review_date < start_date:
                    continuation_token = None
                    break

                # Deduplicate by review ID
                review_id = r.get("reviewId", str(hash(r["content"])))
                if review_id in seen_ids:
                    continue
                seen_ids.add(review_id)

                # Only include reviews within the window
                if start_date <= review_date <= end_date:
                    all_reviews.append(ReviewRecord(
                        review_id=review_id,
                        review_text=r.get("content", ""),
                        rating=r.get("score", 0),
                        review_date=r["at"].isoformat(),
                        app_version=r.get("reviewCreatedVersion", ""),
                        developer_reply=r.get("replyContent", ""),
                        source="Google Play",
                        source_url=f"https://play.google.com/store/apps/details?id={app_id}",
                    ))

            if not continuation_token:
                break

        return all_reviews
```

### 6.4 Review Data Flow

```text
google-play-scraper
  │
  │ Raw review dicts (200 per page, paginated via continuation_token)
  ▼
ReviewRecord normalization
  │
  │ Deduplicated, timestamped, within 7-day window
  ▼
Review Quality Checks (review_cleaner.py)
  │
  │ Remove empty, normalize whitespace, flag unreliable
  ▼
SQLite persistence (reviews table)
  │
  │ Clean ReviewRecord objects
  ▼
LangGraph Pipeline input (state.raw_reviews → state.cleaned_reviews)
```

---

## 7. Data Models

### 7.1 Database Schema (SQLite)

```sql
-- Reviews table
CREATE TABLE reviews (
    review_id       TEXT PRIMARY KEY,
    review_text     TEXT NOT NULL,
    rating          INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_date     TEXT NOT NULL,          -- ISO 8601
    app_version     TEXT DEFAULT '',
    developer_reply TEXT DEFAULT '',
    source          TEXT DEFAULT 'Google Play',
    source_url      TEXT DEFAULT '',
    -- Classification (populated after analysis)
    primary_theme   TEXT DEFAULT NULL,
    secondary_theme TEXT DEFAULT NULL,
    sentiment       TEXT DEFAULT NULL,      -- Positive / Neutral / Negative
    severity        TEXT DEFAULT NULL,
    issue_type      TEXT DEFAULT NULL,      -- Complaint / Question / Feature request / Praise / General
    -- Metadata
    batch_id        TEXT NOT NULL,          -- Links reviews to a specific fetch run
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Themes table
CREATE TABLE themes (
    id              SERIAL PRIMARY KEY,
    batch_id        TEXT NOT NULL,
    theme_name      TEXT NOT NULL,
    description     TEXT NOT NULL,
    review_count    INTEGER NOT NULL,
    percentage      REAL NOT NULL,
    negative_count  INTEGER NOT NULL,
    avg_rating      REAL NOT NULL,
    trend           TEXT DEFAULT 'Stable',  -- Increasing / Decreasing / Stable / Spiking
    rank_score      REAL NOT NULL,
    rank_position   INTEGER DEFAULT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fee issues table
CREATE TABLE fee_issues (
    id                  SERIAL PRIMARY KEY,
    batch_id            TEXT NOT NULL,
    fee_name            TEXT NOT NULL,
    related_review_count INTEGER NOT NULL,
    share_of_corpus     REAL NOT NULL,
    observed_misunderstanding TEXT NOT NULL,
    confidence          TEXT NOT NULL,       -- High / Medium / Low
    selection_reason    TEXT NOT NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Official sources table
CREATE TABLE official_sources (
    id              SERIAL PRIMARY KEY,
    fee_issue_id    INTEGER REFERENCES fee_issues(id),
    url             TEXT NOT NULL,
    title           TEXT NOT NULL,
    domain          TEXT NOT NULL,
    extracted_info  TEXT NOT NULL,
    date_checked    TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analysis runs table
CREATE TABLE analysis_runs (
    id              SERIAL PRIMARY KEY,
    batch_id        TEXT UNIQUE NOT NULL,
    status          TEXT DEFAULT 'pending',  -- pending / running / completed / failed
    review_count    INTEGER DEFAULT 0,
    review_period_start TEXT,
    review_period_end   TEXT,
    avg_rating      REAL DEFAULT 0,
    product_pulse   TEXT DEFAULT NULL,       -- Generated pulse text
    fee_explainer   TEXT DEFAULT NULL,       -- Generated explainer JSON
    approval_status TEXT DEFAULT 'pending',  -- pending / approved / rejected
    approved_at     TEXT DEFAULT NULL,
    mcp_document_status TEXT DEFAULT NULL,   -- success / failed / null
    mcp_gmail_status    TEXT DEFAULT NULL,   -- success / failed / null
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 7.2 Pydantic Models

```python
# backend/models/review.py
from pydantic import BaseModel
from typing import Optional

class ReviewRecord(BaseModel):
    review_id: str
    review_text: str
    rating: int                        # 1-5
    review_date: str                   # ISO 8601
    app_version: str = ""
    developer_reply: str = ""
    source: str = "Google Play"
    source_url: str = ""
    # Classification (populated after analysis)
    primary_theme: Optional[str] = None
    secondary_theme: Optional[str] = None
    sentiment: Optional[str] = None     # Positive / Neutral / Negative
    severity: Optional[str] = None
    issue_type: Optional[str] = None


# backend/models/theme.py
class Theme(BaseModel):
    theme_name: str
    description: str
    review_count: int
    percentage: float
    negative_count: int
    avg_rating: float
    representative_review_ids: list[str]
    trend: str = "Stable"               # Increasing / Decreasing / Stable / Spiking
    rank_score: float = 0.0


# backend/models/fee_issue.py
class FeeIssue(BaseModel):
    fee_name: str
    related_review_count: int
    share_of_corpus: float
    representative_complaints: list[str]
    observed_misunderstanding: str
    confidence: str                     # High / Medium / Low
    selection_reason: str

class OfficialSource(BaseModel):
    url: str
    title: str
    domain: str
    extracted_info: str
    date_checked: str


# backend/models/outputs.py
class CustomerQuote(BaseModel):
    review_id: str
    quote: str
    date: str
    rating: int
    theme: str
    source: str = "Google Play"

class ProductPulse(BaseModel):
    content: str
    word_count: int
    top_themes_summary: str
    user_voice_quotes: list[CustomerQuote]
    key_observation: str
    product_actions: list[str]          # Exactly 3

class FeeExplainer(BaseModel):
    fee_name: str
    customer_confusion_summary: str
    bullets: list[str]                  # Max 6
    sources: list[OfficialSource]
    last_checked: str


# backend/models/approval.py
from enum import Enum

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class MCPActionResult(BaseModel):
    action_name: str
    status: str                         # success / failed
    message: str
    timestamp: str
```

---

## 8. Backend API Design

### 8.1 API Endpoints

| Method | Endpoint | Purpose | Auth Required |
|---|---|---|---|
| `GET` | `/api/config` | Return app config (name, package, lookback) | No |
| `POST` | `/api/reviews/fetch` | Trigger review fetch from Google Play | No |
| `GET` | `/api/reviews/status/{batch_id}` | Poll fetch progress/status | No |
| `GET` | `/api/reviews/{batch_id}` | Get fetched reviews for a batch | No |
| `POST` | `/api/analysis/run/{batch_id}` | Trigger LangGraph analysis pipeline | No |
| `GET` | `/api/analysis/stream/{batch_id}` | SSE stream for real-time analysis progress | No |
| `GET` | `/api/analysis/results/{batch_id}` | Get complete analysis results | No |
| `PUT` | `/api/outputs/{batch_id}/pulse` | Update edited Product Pulse | No |
| `PUT` | `/api/outputs/{batch_id}/explainer` | Update edited Fee Explainer | No |
| `GET` | `/api/approval/{batch_id}/preview` | Get full approval preview (document + email) | No |
| `POST` | `/api/approval/{batch_id}/approve` | Execute approval → trigger MCP write actions | No |
| `GET` | `/api/approval/{batch_id}/status` | Get MCP action results | No |
| `GET` | `/api/auth/google/login` | Initiate Google OAuth flow (for Gmail/Docs) | No |
| `GET` | `/api/auth/google/callback` | OAuth callback handler | No |

### 8.2 SSE Progress Streaming

The analysis pipeline streams progress events to the frontend via Server-Sent Events:

```python
# backend/api/analysis.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/analysis")

@router.get("/stream/{batch_id}")
async def stream_analysis_progress(batch_id: str):
    """Stream analysis pipeline progress via SSE."""

    async def event_generator():
        async for step_update in run_analysis_pipeline(batch_id):
            yield f"data: {step_update.model_dump_json()}\n\n"
        yield "data: {\"type\": \"complete\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
```

### 8.3 Approval Gate Implementation

```python
# backend/services/approval_gate.py
from models.approval import ApprovalStatus

class ApprovalGate:
    """Application-level approval gate.

    This is NOT a prompt instruction to the LLM.
    This is a hard-coded application-level control that blocks
    all write MCP actions until explicit user approval.
    """

    def __init__(self):
        self._status: dict[str, ApprovalStatus] = {}

    def get_status(self, batch_id: str) -> ApprovalStatus:
        return self._status.get(batch_id, ApprovalStatus.PENDING)

    def approve(self, batch_id: str) -> None:
        self._status[batch_id] = ApprovalStatus.APPROVED

    def reject(self, batch_id: str) -> None:
        self._status[batch_id] = ApprovalStatus.REJECTED

    def is_write_allowed(self, batch_id: str) -> bool:
        return self._status.get(batch_id) == ApprovalStatus.APPROVED

    def guard(self, batch_id: str) -> None:
        """Raise if write actions are not approved."""
        if not self.is_write_allowed(batch_id):
            raise PermissionError(
                f"Write actions BLOCKED for batch {batch_id}. "
                f"Current status: {self.get_status(batch_id).value}. "
                "Explicit user approval is required."
            )

# Singleton instance
approval_gate = ApprovalGate()
```

---

## 9. MCP Write Actions

### 9.1 Action Architecture

```text
User clicks "Approve & Create Internal Updates"
        │
        ▼
POST /api/approval/{batch_id}/approve
        │
        ▼
ApprovalGate.approve(batch_id)
        │
        ▼
ApprovalGate.guard(batch_id)  ← Verified at application level
        │
        ├──► MCP Action #1: append_to_internal_document()
        │         │
        │         ├── Success → MCPActionResult(status="success")
        │         └── Failure → MCPActionResult(status="failed", message="...")
        │
        └──► MCP Action #2: create_gmail_draft()
                  │
                  ├── Success → MCPActionResult(status="success")
                  └── Failure → MCPActionResult(status="failed", message="...")
        │
        ▼
Return both MCPActionResult objects to frontend
```

### 9.2 Gmail Draft Creation

```python
# backend/services/gmail_service.py
import base64
from email.message import EmailMessage
from googleapiclient.discovery import build

class GmailService:
    """Creates Gmail drafts via the Gmail API. Never sends emails."""

    SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

    def __init__(self, credentials):
        self.service = build("gmail", "v1", credentials=credentials)

    async def create_draft(
        self,
        subject: str,
        body: str,
        to: str = "",
    ) -> dict:
        """Create a Gmail draft. Does NOT send the email."""

        message = EmailMessage()
        message.set_content(body)
        message["Subject"] = subject
        if to:
            message["To"] = to

        encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft = self.service.users().drafts().create(
            userId="me",
            body={"message": {"raw": encoded}},
        ).execute()

        return {
            "draft_id": draft["id"],
            "message": "Gmail draft created. No email has been sent.",
        }
```

### 9.3 Internal Document Append

```python
# backend/services/document_service.py
import json
from pathlib import Path
from datetime import datetime

class DocumentService:
    """Appends structured analysis entries to the internal knowledge repository.

    Supports:
    - Local JSON file (default, always available)
    - Google Docs API (when OAuth credentials are provided)
    """

    def __init__(self, storage_path: str = "data/knowledge_repository.json"):
        self.storage_path = Path(storage_path)

    async def append_entry(self, entry: dict) -> dict:
        """Append a new entry. Never overwrites existing data."""

        # Load existing entries
        entries = []
        if self.storage_path.exists():
            with open(self.storage_path, "r") as f:
                entries = json.load(f)

        # Add timestamp and append
        entry["appended_at"] = datetime.utcnow().isoformat()
        entries.append(entry)

        # Write back
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "message": f"Entry appended. Total entries: {len(entries)}",
            "entry_index": len(entries) - 1,
        }
```

---

## 10. Official Source Verification

### 10.1 Source Retrieval Flow

```text
Fee issue identified (e.g., "DP Charges")
        │
        ▼
Web search for: "Groww DP charges site:groww.in"
        │
        ▼
Filter: Only official Groww domains
        │
        ├── groww.in
        ├── support.groww.in
        └── help.groww.in
        │
        ▼
Retrieve page content via httpx
        │
        ▼
Extract relevant fee information via LLM
        │
        ▼
Store: URL, title, extracted info, date checked
        │
        ▼
Validate: Does extracted info support the Fee Explainer claims?
```

### 10.2 Implementation

```python
# backend/services/source_retriever.py
import httpx
from bs4 import BeautifulSoup
from datetime import date

ALLOWED_DOMAINS = [
    "groww.in",
    "support.groww.in",
    "help.groww.in",
]

class OfficialSourceRetriever:
    """Retrieves and verifies official Groww documentation."""

    async def search_fee_documentation(self, fee_name: str) -> list[dict]:
        """Search for official Groww documentation about a specific fee."""
        # 1. Search using web search or direct URL construction
        # 2. Filter to ALLOWED_DOMAINS only
        # 3. Fetch page content
        # 4. Extract relevant sections
        # 5. Return structured source data with date_checked
        ...

    async def fetch_page_content(self, url: str) -> str:
        """Retrieve and parse a page from an official Groww domain."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        # Extract main content, removing nav/footer/scripts
        main_content = soup.find("main") or soup.find("article") or soup.body
        return main_content.get_text(separator="\n", strip=True)
```

---

## 11. Frontend Architecture

### 11.1 Workflow State Machine

The frontend manages a 5-step workflow using Zustand:

```typescript
// frontend/src/store/workflowStore.ts
import { create } from 'zustand';

type WorkflowStep =
  | 'source_fetch'
  | 'analysis_progress'
  | 'insights_dashboard'
  | 'generated_outputs'
  | 'approval_review';

interface WorkflowState {
  currentStep: WorkflowStep;
  batchId: string | null;

  // Screen 1
  fetchStatus: 'idle' | 'fetching' | 'success' | 'error';
  reviewCount: number;
  reviewPeriod: { start: string; end: string } | null;
  avgRating: number;

  // Screen 2
  analysisSteps: AnalysisStep[];

  // Screen 3
  themes: Theme[];
  topThemes: Theme[];
  quotes: CustomerQuote[];
  feeIssue: FeeIssue | null;

  // Screen 4
  productPulse: ProductPulse | null;
  feeExplainer: FeeExplainer | null;
  isEditing: boolean;

  // Screen 5
  approvalStatus: 'pending' | 'approved' | 'rejected';
  mcpResults: MCPActionResult[];

  // Actions
  setStep: (step: WorkflowStep) => void;
  fetchReviews: () => Promise<void>;
  runAnalysis: () => Promise<void>;
  updatePulse: (content: string) => void;
  updateExplainer: (explainer: FeeExplainer) => void;
  submitApproval: () => Promise<void>;
}
```

### 11.2 Screen Flow

```text
┌───────────────────────────────────────────────────────────────┐
│                    Step Indicator Bar                          │
│  [1. Fetch] → [2. Analyze] → [3. Insights] → [4. Output] →  │
│  [5. Approve]                                                 │
└───────────────────────────────────────────────────────────────┘

Screen 1: SourceFetch
├── App info card (Groww, Google Play, com.nextbillion.groww)
├── "Fetch Latest Reviews" button
├── Retrieval statistics card (reviews, period, avg rating)
└── Status checklist (connected, retrieved, validated)

Screen 2: AnalysisProgress
├── Pipeline step checklist with animated checkmarks
├── Current step indicator
└── "Run Analysis" / auto-triggered after fetch

Screen 3: InsightsDashboard
├── Summary cards row (reviews analyzed, themes, top issue, confidence)
├── Theme table (sortable)
├── Top 3 theme cards with trend badges
├── Customer Voice section (3 verbatim quotes)
└── Fee Issue detail card

Screen 4: GeneratedOutputs
├── Product Pulse panel
│   ├── Full text (editable)
│   └── Word count: X / 250
└── Fee Explainer panel
    ├── Fee name + confusion summary
    ├── Bullet list (editable, max 6)
    ├── Sources list
    └── Last checked date

Screen 5: ApprovalReview
├── Review summary card
├── Document update preview (JSON)
├── Gmail draft preview (subject + body)
├── ⚠️ "No write action will occur until you approve."
├── [Approve & Create Internal Updates] button
└── MCP action result cards (success / failed per action)
```

---

## 12. Theme Ranking Algorithm

Themes are ranked using a composite score combining multiple signals:

```text
Theme Score = (0.30 × Frequency Score)
            + (0.25 × Negativity Score)
            + (0.20 × Severity Score)
            + (0.15 × Recency Score)
            + (0.10 × Persistence Score)
```

| Factor | Calculation | Rationale |
|---|---|---|
| **Frequency** | `theme_review_count / total_reviews` | More mentions = more impactful |
| **Negativity** | `negative_reviews_in_theme / theme_review_count` | Higher negative ratio = more critical |
| **Severity** | `1 - (avg_theme_rating - 1) / 4` | Lower average rating = more severe (normalized 0-1) |
| **Recency** | `reviews_in_last_3_weeks / theme_review_count` | Recent issues are more actionable |
| **Persistence** | `weeks_with_reviews / 12` | Issues spanning more weeks are systemic |

The top 3 themes by composite score are selected. If fewer than 3 themes exceed a minimum evidence threshold (≥3 reviews), fewer are returned with an explanation.

---

## 13. Error Handling Strategy

| Scenario | Behavior | User-Facing Message |
|---|---|---|
| Google Play scraper fails | Abort fetch, show error | "Unable to retrieve Google Play reviews. Check network connectivity or try again." |
| Zero reviews in 7-day window | Abort analysis | "No reviews found for the specified period." |
| Fewer than 10 reviews | Warn but proceed | "Only X reviews retrieved. Analysis reliability may be limited." |
| LLM call fails (Groq timeout) | Retry up to 2 times, then fail the step | "Analysis step failed: [step name]. Please retry." |
| No fee issue detected | Skip explainer generation | "No recurring fee/charge misunderstanding was identified with sufficient confidence." |
| Official source unavailable | Skip explainer, flag limitation | "Could not verify fee documentation from official Groww sources." |
| Gmail API auth missing | Block draft creation, show auth prompt | "Gmail authorization required. Please connect your Google account." |
| MCP action fails | Report per-action status | "Internal document update: Failed / Gmail draft: Successful" |

---

## 14. Security & Guardrails

### 14.1 Evidence Chain Enforcement

```text
Every claim in outputs → Must trace to:
├── Customer claim → ReviewRecord.review_id (real Google Play review)
├── Metric claim   → Computed from ReviewRecord[] (real data)
├── Fee claim      → OfficialSource.url (verified Groww documentation)
└── Trend claim    → Temporal analysis of real review dates
```

### 14.2 Hallucination Prevention

| Layer | Guardrail |
|---|---|
| **Quote extraction** | LLM selects review IDs; quotes are fetched from the original corpus, never generated |
| **Review counts** | Computed from database queries, never LLM-generated |
| **Fee identification** | LLM proposes candidates; evidence count is computed from actual matches |
| **Source URLs** | Only URLs actually fetched and verified are included; never invented |
| **Trends** | Computed statistically from review timestamps; LLM only narrates the finding |

### 14.3 Approval Gate Security

The approval gate is **application-level**, not a prompt instruction:

```text
┌──────────────────────────────────┐
│      approval_gate.guard()       │   ← Hard-coded Python check
│      Called before EVERY write   │
│      action. Cannot be bypassed  │
│      by LLM output or prompt     │
│      injection.                  │
└──────────────────────────────────┘
```

---

## 15. Dependency List

### 15.1 Backend (Python)

```text
# requirements.txt
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.9.0
pydantic-settings>=2.5.0

# LangChain + Groq
langchain>=0.3.0
langchain-core>=0.3.0
langchain-groq>=0.2.0
langgraph>=0.2.0

# Google Play Scraping
google-play-scraper>=1.2.0

# Web Scraping for Source Verification
httpx>=0.27.0
beautifulsoup4>=4.12.0

# Google APIs (Gmail + Docs)
google-api-python-client>=2.150.0
google-auth-httplib2>=0.2.0
google-auth-oauthlib>=1.2.0

# Database
aiosqlite>=0.20.0

# Utilities
python-dotenv>=1.0.0
python-multipart>=0.0.12
```

### 15.2 Frontend (Node.js)

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "zustand": "^4.5.0",
    "axios": "^1.7.0",
    "lucide-react": "^0.450.0",
    "clsx": "^2.1.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "vite": "^5.4.0",
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0"
  }
}
```

---

## 16. Development & Deployment

### 16.1 Local Development

```bash
# Terminal 1 — Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # Fill in GROQ_API_KEY + Google OAuth credentials
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev              # Vite dev server on port 5173
```

### 16.2 Environment Variables Required

| Variable | Required | Purpose |
|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | Groq API authentication |
| `PACKAGE_NAME` | ✅ Yes (default: `com.nextbillion.groww`) | Google Play app ID |
| `GOOGLE_CLIENT_ID` | ⚠️ For Gmail/Docs | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | ⚠️ For Gmail/Docs | Google OAuth client secret |
| `DATABASE_URL` | Optional (default provided) | SQLite database path |

### 16.3 Docker Compose (Optional)

```yaml
# docker-compose.yml
version: "3.9"
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
```

---

## 17. Key Design Decisions

| Decision | Rationale |
|---|---|
| **Groq over OpenAI** | User requirement. Groq provides ultra-fast inference via `ChatGroq` with Llama 3.3 70B, fully compatible with LangChain. |
| **LangGraph over plain chains** | The analysis pipeline has conditional branches (skip explainer if no fee issue), progress tracking needs, and potential for human-in-the-loop. LangGraph's `StateGraph` handles this natively. |
| **LangChain for prompts/parsing** | LangChain's `ChatPromptTemplate` and output parsers (JSON, structured) provide robust, reusable prompt engineering without custom boilerplate. |
| **`google-play-scraper` over official API** | We don't have Google Play Developer API access for Groww. The scraper provides a working fallback; the interface abstraction allows swapping later. |
| **SQLite over PostgreSQL** | Simplicity for an internal tool. Single-file database, zero config, sufficient for the expected data volume. |
| **SSE over WebSockets** | Analysis progress is unidirectional (server → client). SSE is simpler, HTTP-native, and sufficient for step-by-step progress updates. |
| **Application-level approval gate** | The problem statement explicitly requires the gate to be at the application level, not an LLM prompt instruction. A Python class with a `guard()` method enforces this. |
| **Zustand over Redux** | Lightweight, minimal boilerplate state management. The workflow state is straightforward enough to not need Redux's ceremony. |
| **Separate analysis/generation LLM temps** | Classification needs determinism (`temperature=0.0`); content generation benefits from slight creativity (`temperature=0.3`). |

---

## 18. Future Enhancements

| Enhancement | Description |
|---|---|
| **Google Play Developer API** | Swap to official API when Groww developer access is available |
| **LangSmith tracing** | Enable full pipeline observability and debugging in production |
| **Multi-app support** | Extend to analyze iOS App Store reviews or competitor apps |
| **Historical comparison** | Compare current week's pulse against previous weeks |
| **Slack integration** | Post Product Pulse to a Slack channel as an MCP action |
| **Scheduled runs** | Cron-triggered weekly analysis with auto-generated drafts |
| **PostgreSQL** | Switch to PostgreSQL for multi-user / production deployment |
