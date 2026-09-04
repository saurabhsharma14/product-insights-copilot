
> [!IMPORTANT]
> **AUTONOMOUS ARCHITECTURE UPDATE**
> This project has been updated to run autonomously. 
> - The 5-step interactive frontend wizard has been replaced by a **React Dashboard**.
> - The backend uses **APScheduler** to automatically trigger the review fetch and LangGraph analysis pipeline every day at 11:00 AM UTC.
> - The MCP Approval Gate remains the only manual step, which is actioned from the new Frontend Dashboard.
>
> *(Note: The original documentation below describes the manual 5-step UI, which is now superseded by the autonomous dashboard model.)*

# Groww AI Product Feedback Intelligence — Evaluation Rubric

This document defines a structured evaluation framework for the Groww AI Product Feedback Intelligence application. Every criterion maps back to the `implementation_plan.md`, `architecture.md`, `problemStatement.md`, and `edge-cases.md`.

---

## Scoring Guide

| Score | Label | Meaning |
|---|---|---|
| **0** | Not Implemented | Feature is absent or non-functional |
| **1** | Partially Implemented | Core path works but significant gaps remain |
| **2** | Fully Implemented | Feature works correctly with edge cases handled |
| **3** | Exceeds Expectations | Feature is robust, polished, and handles corner cases gracefully |

---

## E1 — Project Scaffolding & Core Infrastructure

| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E1.1 | **Backend starts without errors** — `uvicorn main:app --reload` boots on `:8000` | 2 | Run the command; confirm no tracebacks |
| E1.2 | **Frontend starts without errors** — `npm run dev` boots Vite on `:5173` and renders a shell | 2 | Run the command; confirm browser shows the app |
| E1.3 | **PostgreSQL auto-creates with correct schema** — tables `reviews`, `themes`, `fee_issues`, `official_sources`, `analysis_runs` exist on first boot | 2 | Connect to Postgres and inspect tables |
| E1.4 | **Environment config loads** — `GET /api/config` returns app name, package ID, lookback weeks | 2 | `curl http://localhost:8000/api/config` |
| E1.5 | **CORS configured** — Frontend on `:5173` can reach backend on `:8000` without CORS errors | 2 | Open browser console; confirm no CORS errors |
| E1.6 | **Pydantic models defined** — `ReviewRecord`, `Theme`, `FeeIssue`, `OfficialSource`, `ProductPulse`, `FeeExplainer`, `ApprovalStatus`, `MCPActionResult` | 2 | Grep for model classes |
| E1.7 | **`.env.example` documented** — All required variables listed with descriptions | 2 | Review file |

**Phase 1 Total: /14**

---

## E2 — Review Ingestion Pipeline

| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E2.1 | **Real Google Play reviews fetched** — `POST /api/reviews/fetch` retrieves actual reviews for `com.nextbillion.groww`, not sample data | 3 | Trigger fetch; confirm reviews contain real user text, dates, ratings |
| E2.2 | **7-day rolling window** — Only reviews within the configured lookback window are retained | 2 | Check review dates |
| E2.3 | **Deduplication** — Duplicate `review_id`s across pagination pages are removed | 2 | Check `cleaning_stats.removed_duplicates` |
| E2.4 | **Empty/whitespace-only reviews filtered** — Reviews with `null`/empty text are excluded | 2 | Check `cleaning_stats.removed_empty` |
| E2.5 | **Pagination works** — `continuation_token` is followed until exhausted or hard cap hit | 2 | Fetch on a date range with many reviews |
| E2.6 | **Cleaning stats returned** — Response includes `removed_empty`, `removed_duplicates`, `total_valid` | 2 | Inspect API response JSON |
| E2.7 | **Persistence** — Cleaned reviews are saved to the `reviews` table with `batch_id` | 2 | Query `SELECT COUNT(*) FROM reviews WHERE batch_id = ?` |
| E2.8 | **Screen 1 UI** — App info card, "Fetch Latest Reviews" CTA, post-fetch statistics card, animated status checklist | 3 | Visual inspection |
| E2.9 | **Zero-review abort** — If scraper returns 0 reviews, pipeline aborts with an explanatory message (not silent fallback) | 2 | Test with an invalid package name |
| E2.10 | **Fewer-than-10 warning** — If < 10 reviews, a warning is displayed but analysis proceeds | 2 | Simulate a narrow window |

**Phase 2 Total: /22**

---

## E3 — LangGraph Analysis Pipeline (Nodes 1–6)

### 3A — LLM & Agent Foundation
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E3.1 | **LLM factory** — `get_llm()` returns configured `ChatGroq` instances | 2 | Code review |
| E3.2 | **PipelineState** — TypedDict contains all required fields | 2 | Code review |

### 3B — Classification Node
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E3.3 | **Per-review classification** — Each review receives `primary_theme`, `secondary_theme`, `sentiment`, `severity`, `issue_type` | 3 | Run pipeline; spot-check 10 reviews |
| E3.4 | **Batching** — Reviews are chunked if > 50 per LLM call | 2 | Add > 50 reviews; confirm batch splitting |
| E3.5 | **Structured JSON parsing** — LLM output is parsed reliably; markdown fence stripping works | 2 | Check for JSON error handling |

### 3C — Theme Clustering & Ranking
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E3.6 | **Emergent themes ≤ 5** — Themes are NOT hard-coded; they emerge from the data | 3 | Run on different datasets |
| E3.7 | **Theme objects complete** — Each theme has `review_count`, `percentage`, `negative_count`, `avg_rating`, `representative_review_ids` | 2 | Inspect theme output objects |
| E3.8 | **Composite scoring formula** — Uses Frequency, Negativity, Severity, Recency, Persistence | 2 | Code review |
| E3.9 | **Top 3 selection** — Top 3 themes (or fewer if insufficient evidence) are selected | 2 | Verify with < 3 themes |

### 3D — Fee Detection
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E3.10 | **Fee confusion detection** — Scans for recurring fee/charge confusion patterns | 3 | Run pipeline |
| E3.11 | **No fee → graceful skip** — If no fee confusion found, `fee_issue = None`; downstream nodes skip cleanly | 2 | Test with reviews that don't mention fees |
| E3.12 | **Single strongest candidate** — When multiple fee candidates exist, selects the strongest | 2 | Inspect selection logic |

### 3E — Quote Extraction
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E3.13 | **Exactly 3 verbatim quotes** — Quotes are real text from the corpus, never LLM-generated | 3 | Match each returned quote against the `reviews` table |
| E3.14 | **Provenance maintained** — Each quote has `review_id`, `date`, `rating`, `theme`, `source` | 2 | Inspect quote objects |
| E3.15 | **Post-validation** — LLM selects review IDs → quotes fetched from DB, not from LLM output | 3 | Code review |

### 3F — Trend Analysis
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E3.16 | **Statistical temporal analysis** — Trends computed from real timestamps, not LLM-generated | 3 | Code review |
| E3.17 | **Trend labels** — Each theme gets `Increasing / Decreasing / Stable / Spiking` (or `Insufficient data`) | 2 | Run pipeline |

### 3G — SSE Progress & Graph Assembly
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E3.18 | **SSE stream emits step events** — `{ step, status, message }` per pipeline node | 2 | Connect via EventSource |
| E3.19 | **Screen 2 UI** — Animated pipeline checklist with spinner on current step; auto-advances on completion | 3 | Visual inspection |
| E3.20 | **Graph assembly** — LangGraph `StateGraph` connects all 6 nodes in correct order with conditional edges | 2 | Code review of `graph.py` |

**Phase 3 Total: /47**

---

## E4 — Source Verification & Output Generation (Nodes 7–9)

### 4A — Source Verification
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E4.1 | **Official source retrieval** — Fetches pages from `groww.in`, `support.groww.in`, `help.groww.in` via `httpx` | 3 | Run pipeline |
| E4.2 | **No fabricated URLs** — Every URL cited was actually fetched with an HTTP 200 response | 3 | Cross-reference `official_sources` URLs against HTTP logs |
| E4.3 | **Conditional execution** — Only runs if `fee_issue` exists in state | 2 | Test with no-fee scenario |
| E4.4 | **Domain restriction** — Redirects to non-allowed domains are discarded | 2 | Code review |

### 4B — Product Pulse Generation
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E4.5 | **≤ 250 words** — Generated pulse respects the hard word-count constraint | 3 | Count words in output |
| E4.6 | **Required sections present** — Top Themes, User Voice, Key Observation, Product Actions (exactly 3) | 3 | Parse output |
| E4.7 | **Re-prompt on violation** — If > 250 words or missing sections, the system re-prompts (up to 2 retries) | 2 | Code review |

### 4C — Fee Explainer Generation
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E4.8 | **≤ 6 bullets** — Fee Explainer has at most 6 explanation bullets | 2 | Count bullets in output |
| E4.9 | **Grounded in official sources** — Bullets reference verified Groww documentation | 3 | Cross-check each bullet against `official_sources.extracted_info` |
| E4.10 | **Neutral, customer-friendly tone** — No blame language | 2 | Read the output |
| E4.11 | **Conditional generation** — Only generated if `fee_issue` exists; shows informational state otherwise | 2 | Test with no-fee scenario |

### 4D — Insights Dashboard (Screen 3)
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E4.12 | **Summary cards** — Reviews analyzed, Themes found, Top issue, Fee issue confidence | 2 | Visual inspection |
| E4.13 | **Theme table** — Sortable table with Theme, Reviews, Share, Avg Rating, Trend | 2 | Click column headers |
| E4.14 | **Top 3 theme cards** — Prominent cards with name, count, share, trend badge, description | 2 | Visual inspection |
| E4.15 | **Customer Voice** — 3 verbatim quotes with metadata (review_id, date, rating, theme, source) | 2 | Verify data matches actual reviews |
| E4.16 | **Fee Issue detail card** — Detected fee, related reviews, confusion description, confidence level | 2 | Visual inspection |

### 4E — Generated Outputs (Screen 4)
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E4.17 | **Product Pulse panel** — Full text in editable textarea with live word count `X / 250` | 2 | Type in the textarea |
| E4.18 | **Fee Explainer panel** — Editable bullets with count `X / 6 bullets`, official sources list, last checked date | 2 | Edit a bullet |
| E4.19 | **Edit mode toggle** — Both panels support toggling between view and edit modes | 2 | Click edit |
| E4.20 | **Save edits** — API endpoints persist changes | 2 | Edit and save |

**Phase 4 Total: /43**

---

## E5 — Approval Gate & MCP Write Actions

### 5A — Approval Gate
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E5.1 | **Application-level gate** — `approval_gate.guard()` is a hard-coded Python check | 3 | Code review |
| E5.2 | **Cannot be bypassed by LLM** — No prompt injection or LLM output can skip the gate | 3 | Code review |
| E5.3 | **Blocks when pending** — Write actions fail with clear error when approval status = pending | 2 | Attempt writes without approving |
| E5.4 | **Idempotent approval** — Calling `approve()` twice on the same `batch_id` is safe | 2 | Double-click approve |

### 5B — MCP Write Actions
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E5.5 | **Internal document append** — New entry appended to `data/knowledge_repository.json` without overwriting | 3 | Run twice; confirm both entries exist |
| E5.6 | **Gmail draft created** — Draft appears in Gmail (not sent) with correct subject and body | 3 | Verify in Gmail Drafts folder |
| E5.7 | **Email NEVER auto-sent** — System only creates drafts; sending is impossible | 3 | Code review |
| E5.8 | **Per-action result reporting** — Each action's success/failure is reported independently | 2 | Simulate one action failing |
| E5.9 | **Partial success handling** — Document append succeeding while Gmail fails (or vice versa) is handled without rollback | 2 | Test each failure scenario |

### 5C — Approval Review Screen (Screen 5)
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E5.10 | **Review summary card** — Reviews analyzed, period, top themes, fee issue, confidence displayed | 2 | Visual inspection |
| E5.11 | **Document update preview** — Structured JSON entry shown before approval | 2 | Compare preview with actual appended entry |
| E5.12 | **Gmail draft preview** — Subject line + full email body shown before approval | 2 | Compare preview with actual Gmail draft |
| E5.13 | **Warning banner** — ⚠️ "No write action will occur until you approve." is visible | 2 | Visual inspection |
| E5.14 | **Post-approval status** — MCP action result cards show per-action success/failed status | 2 | Approve and check status display |
| E5.15 | **Post-approval message** — "Gmail draft created. No email has been sent." is displayed | 2 | Visual inspection after approval |

### 5D — Google OAuth
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E5.16 | **OAuth flow** — `GET /api/auth/google/login` initiates flow; `GET /api/auth/google/callback` stores credentials | 2 | Walk through OAuth |
| E5.17 | **Missing OAuth graceful fallback** — If no OAuth credentials configured, Gmail draft is unavailable with clear messaging; document append still works | 2 | Remove OAuth vars |

**Phase 5 Total: /37**

---

## E6 — Error Handling, Guardrails & Polish

### 6A — Error Handling
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E6.1 | **Google Play scraper failure** — Aborts fetch, shows error toast (no silent fallback to sample data) | 2 | Simulate network failure |
| E6.2 | **Zero reviews** — Aborts analysis with explanatory message | 2 | Test with impossible date range |
| E6.3 | **LLM call failure** — Retries up to 2 times, then fails the step with SSE error event | 2 | Simulate Groq timeout |
| E6.4 | **No fee issue** — Skips explainer, shows informational message | 2 | Test with non-fee reviews |
| E6.5 | **Official source unavailable** — Skips explainer, flags limitation | 2 | Block `groww.in` |
| E6.6 | **Gmail auth missing** — Blocks draft creation, prompts OAuth | 2 | Remove OAuth config |
| E6.7 | **MCP action failure** — Reports per-action status clearly; never falsely reports success | 2 | Simulate file permission error |

### 6B — Hallucination Prevention Guardrails
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E6.8 | **Quotes from corpus, not LLM** — LLM selects review IDs → quotes fetched from DB | 3 | Diff LLM-returned text vs DB text |
| E6.9 | **Review counts from DB** — All numeric claims computed from `SELECT COUNT(*)`, not LLM-generated | 3 | Trace every number in the Product Pulse |
| E6.10 | **Fee identification evidence-based** — LLM proposes candidates → evidence count computed from actual matches | 3 | Confirm count matches actual review matches |
| E6.11 | **Source URLs verified** — Only URLs that returned HTTP 200 are cited; none are invented | 3 | Cross-check `official_sources` |
| E6.12 | **Trends computed statistically** — Temporal analysis uses actual review dates; LLM only narrates | 3 | Code review |

### 6C — UI Polish
| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E6.13 | **Loading skeletons** — Shown during data fetches (not blank screens) | 2 | Throttle network |
| E6.14 | **Error boundaries** — Friendly error messages; React app doesn't crash on render errors | 2 | Trigger a render error |
| E6.15 | **Smooth step transitions** — Animated transitions between workflow screens | 2 | Navigate between screens |
| E6.16 | **Professional color palette** — Groww-inspired dark green primary, professional design | 2 | Visual inspection |
| E6.17 | **Responsive layout** — Content remains readable on narrow viewports (single-column stacking) | 2 | Resize browser to < 768px |
| E6.18 | **Empty state handling** — All screens handle no-data scenarios gracefully (not blank cards) | 2 | Navigate to screens before data is loaded |
| E6.19 | **Hover effects** — Interactive elements have hover states | 1 | Hover over buttons |

**Phase 6 Total: /40**

---

## E7 — End-to-End Acceptance Test (21-Step Success Criteria)

Each step is **pass/fail**. The application must complete all 21 steps in a single uninterrupted session without the user manually preparing a review dataset.

| Step | Criterion | Pass/Fail |
|---|---|---|
| 1 | Open the application | ☐ |
| 2 | Confirm Groww Android app (source/package displayed) | ☐ |
| 3 | Fetch the latest 7 days of Google Play reviews | ☐ |
| 4 | See actual retrieval statistics (count, period, avg rating) | ☐ |
| 5 | Analyze the retrieved reviews (pipeline runs) | ☐ |
| 6 | Cluster reviews into ≤ 5 themes | ☐ |
| 7 | Identify the top 3 themes (or fewer if insufficient evidence) | ☐ |
| 8 | Extract 3 real customer quotes (verbatim, not paraphrased) | ☐ |
| 9 | Identify one recurring fee/charge confusion (data-driven, not pre-assumed) | ☐ |
| 10 | Support the fee finding with review evidence (review IDs, counts) | ☐ |
| 11 | Verify the fee using official Groww sources (real URLs, HTTP 200) | ☐ |
| 12 | Generate a ≤ 250-word Weekly Product Pulse with all 4 sections | ☐ |
| 13 | Generate a ≤ 6-bullet Fee Explainer grounded in official sources | ☐ |
| 14 | Review/edit both outputs (edit mode, live counters) | ☐ |
| 15 | Preview the document update (structured JSON entry) | ☐ |
| 16 | Preview the Gmail draft (subject + body) | ☐ |
| 17 | Explicitly approve (via UI button, not auto-triggered) | ☐ |
| 18 | Append the result to an internal document | ☐ |
| 19 | Create a Gmail draft (appears in Drafts folder) | ☐ |
| 20 | Do not send the email (no `send()` call; draft only) | ☐ |
| 21 | Show final success/failure status for each MCP action | ☐ |

**E2E Total: /21 (all must pass)**

---

## E8 — Edge Case Coverage

> Based on `edge-cases.md` — 62 documented edge cases

### 8A — Critical Edge Cases (Must Handle)

| ID | Edge Case | Handled? |
|---|---|---|
| EC-1.1 | Scraper returns zero reviews → abort with message, no fake data | ☐ |
| EC-1.3 | Scraper rate-limited (429/403) → exponential backoff, 3 retries | ☐ |
| EC-1.5 | Continuation token loops infinitely → hard cap at 20 pages | ☐ |
| EC-1.6 | Null/empty review text → filtered by cleaner | ☐ |
| EC-1.8 | Non-English reviews → passed to LLM, never fabricated translations | ☐ |
| EC-3.1 | Invalid Groq API key → fail fast with clear message | ☐ |
| EC-3.3 | Groq returns malformed JSON → markdown fence stripping + retry | ☐ |
| EC-4.4 | Zero fee-related reviews → skip explainer, conditional edge | ☐ |
| EC-4.6 | Fabricated fee name → source verification fails → no explainer | ☐ |
| EC-4.8 | LLM paraphrases quote → post-validation fetches real text from DB | ☐ |
| EC-5.1 | Groww website down → retry once, then skip verification | ☐ |
| EC-6.1 | Product Pulse > 250 words → re-prompt up to 2 times | ☐ |
| EC-7.1 | Double-click approve → idempotent, no duplicate actions | ☐ |
| EC-7.5 | Document succeeds, Gmail fails → independent per-action reporting | ☐ |
| EC-7.9 | `knowledge_repository.json` corrupted → backup + fresh array | ☐ |
| EC-9.1 | Client disconnects mid-SSE → pipeline continues in background | ☐ |
| EC-11.1 | LLM invents review ID → validate against DB, discard invalid | ☐ |
| EC-11.4 | Prompt injection via review text → reviews as data, not instructions | ☐ |

**Edge Case Score: X / 62 handled**

---

## E9 — Architecture & Code Quality

| ID | Criterion | Max Score | How to Verify |
|---|---|---|---|
| E9.1 | **LangGraph StateGraph** — Nodes connected in correct order with conditional edges | 3 | Code review of `graph.py` |
| E9.2 | **Separation of concerns** — Services, agents, API, models in distinct directories | 2 | Directory structure review |
| E9.3 | **Abstract `ReviewProvider` interface** — Allows swapping scraper for official API later | 2 | Code review |
| E9.4 | **Async architecture** — FastAPI endpoints use `async/await`; scraper runs in `asyncio.to_thread()` | 2 | Code review |
| E9.5 | **SSE over WebSocket** — Unidirectional progress uses SSE | 2 | Code review |
| E9.6 | **Zustand state management** — Workflow state is clean | 2 | Code review |
| E9.7 | **Type safety** — TypeScript interfaces mirror backend Pydantic models | 2 | Code review |
| E9.8 | **Two LLM temperature configs** — Analysis at `0.0`, generation at `0.3` | 2 | Code review |
| E9.9 | **Evidence chain traceability** — Every output claim traces back to a `review_id` or `official_source.url` | 3 | End-to-end trace |

**Architecture Total: /20**

---

## E10 — Core Product Principles

These are **binary pass/fail** — the system either upholds the principle or it doesn't.

| ID | Principle | Pass/Fail |
|---|---|---|
| P1 | **Fee issue emerges from real customer feedback** — not pre-assumed or hard-coded | ☐ |
| P2 | **Fee Explainer is grounded in official Groww documentation** — not LLM-generated policy | ☐ |
| P3 | **MCP actions require explicit user approval** — application-level gate, not prompt-level | ☐ |
| P4 | **Email is only drafted, never sent automatically** — no `send()` call anywhere in codebase | ☐ |
| P5 | **No synthetic evidence** — never invents reviews, quotes, counts, ratings, trends, fees, URLs, or policies | ☐ |
| P6 | **Feels like a realistic internal Groww Product + Support Intelligence tool** — not a generic CSV summarizer or chatbot | ☐ |

**Principles Total: /6 (all must pass)**

---

## Scoring Summary

| Section | Max Score | Actual Score |
|---|---|---|
| E1 — Scaffolding & Infrastructure | 14 | |
| E2 — Review Ingestion | 22 | |
| E3 — Analysis Pipeline | 47 | |
| E4 — Source Verification & Outputs | 43 | |
| E5 — Approval Gate & MCP Actions | 37 | |
| E6 — Error Handling & Polish | 40 | |
| E7 — End-to-End Acceptance (21 steps) | 21 | |
| E8 — Edge Case Coverage | 62 | |
| E9 — Architecture & Code Quality | 20 | |
| E10 — Core Product Principles | 6 | |
| **Grand Total** | **312** | |

### Grade Thresholds

| Grade | Score Range | Interpretation |
|---|---|---|
| **A+** | 280–312 (90%+) | Production-ready; all core principles upheld; comprehensive edge case coverage |
| **A** | 250–279 (80%+) | Fully functional; minor edge case gaps; polish items remain |
| **B** | 200–249 (64%+) | Core workflow works end-to-end; significant edge case gaps |
| **C** | 150–199 (48%+) | Partial functionality; critical flows broken or unimplemented |
| **F** | < 150 (< 48%) | Fundamental issues; cannot complete the 21-step acceptance test |

> **Hard Requirement**: The application **cannot** receive an A grade unless all 6 Core Product Principles (E10: P1–P6) pass AND all 21 E2E acceptance steps (E7) pass — regardless of the numeric score.
