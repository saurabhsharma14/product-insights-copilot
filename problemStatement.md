# Groww AI Product Feedback Intelligence & Support Workflow

---

## 1. Project Overview

Build a polished internal web application for **Groww** that automatically retrieves recent customer reviews of the **Groww Android app from the Google Play Store**, analyzes those reviews to identify recurring product issues, detects a frequently misunderstood fee or charge, and generates two actionable outputs:

1. A **Weekly Product Pulse** for Groww's Product team.
2. A **Customer Fee Explainer** that Support teams can reuse when responding to recurring fee-related confusion.

Once both outputs are generated, the application must use **approval-gated MCP actions** to:

* Append the insights to an internal document/knowledge repository.
* Create a Gmail draft containing the Product Pulse and Fee Explainer.
* Never automatically send the email.

### Core Workflow

```text
Google Play Store Reviews
        ↓
Review Ingestion
        ↓
Review Cleaning & Normalization
        ↓
Theme Clustering
        ↓
Top 3 Themes
        ↓
Fee / Charge Confusion Detection
        ↓
Official Groww Source Verification
        ↓
Weekly Product Pulse
        +
Fee Explainer
        ↓
User Review
        ↓
Explicit Approval
        ↓
MCP Write Actions
        ↓
Internal Document + Gmail Draft
```

---

## 2. Primary Goal

The application should simulate a realistic **Product + Support feedback loop**.

### Product Perspective

The system should answer:

* What are Groww users complaining about most?
* What are the top recurring product issues?
* Which issues are increasing, decreasing, or persistent?
* What should the Product team investigate or act on?

### Support Perspective

The system should answer:

* Is there a recurring misunderstanding related to a fee or charge?
* What exactly are customers misunderstanding?
* How can Support explain that fee clearly and consistently?

### Operational Perspective

The system should:

* Turn raw customer feedback into a structured internal update.
* Create a reusable customer-support explanation.
* Save the output internally.
* Prepare an email draft.
* Require explicit human approval before any write action.

---

## 3. Critical Requirement — Automatically Retrieve Google Play Reviews

The user must **not manually upload a CSV**.

The application must retrieve reviews automatically from the **Google Play Store**.

The source should be:

> **Google Play Store reviews for the Groww Android application**

The default analysis period is:

> **Most recent 7 days**

---

## 4. Google Play Review Retrieval

### Preferred Implementation

Use the appropriate **Google Play Developer API / Reviews API** where authentication and application access permit.

The implementation should support, where available:

* Review ID
* Review text
* Star rating
* Review timestamp
* App version
* Developer reply
* Source metadata

It must support pagination and retrieve enough reviews to cover the entire 7-day analysis window, subject to API limitations.

### Important Access Consideration

Google Play review APIs are subject to application/developer access permissions.

If the authenticated credentials do not have access to the Groww application, the system must not pretend that the API can retrieve those reviews.

In that scenario, implement a reasonable **public Google Play review retrieval/scraping fallback**, subject to applicable technical and legal constraints.

The rest of the system must be independent of the retrieval mechanism.

Use a common interface such as:

```python
get_reviews(
    app_id,
    start_date,
    end_date
)
```

The implementation behind this interface may use:

```text
Google Play Developer API
OR
Public Google Play review retrieval/scraping
```

---

## 5. Groww App Configuration

Keep the app configuration separate from business logic.

Example:

```text
APP_NAME = Groww
PLATFORM = Google Play
PACKAGE_NAME = <Groww Android package ID>
REVIEW_LOOKBACK_DAYS = 7
```

The package ID should be configurable via environment variables or application settings.

The UI should display:

```text
Source:
Google Play Store — Groww Android App

Review period:
Last 7 days
```

---

## 6. Frontend Requirement

This must be a **full working web application with a frontend**.

Do not build only:

* A CLI
* A Python notebook
* A backend API
* A terminal workflow

The user should be able to complete the entire workflow through a browser-based UI.

### Recommended Technology Stack

A practical implementation could use:

```text
Frontend:
React + TypeScript

Styling:
Tailwind CSS

Backend:
FastAPI (Python) or Node.js

LLM:
OpenAI API

Integrations:
Google Play review retrieval + MCP-connected tools
```

Use whatever equivalent stack produces the most reliable end-to-end implementation.

---

## 7. Frontend Design

The UI should look like a polished **internal Product Intelligence dashboard**.

Design principles:

* Clean
* Minimal
* Professional
* Modern
* Data-driven
* Easy to scan
* Responsive
* Clear workflow states

Use:

* Cards
* Tables
* Status badges
* Trend indicators
* Progress states
* Expandable evidence
* Clear primary actions

Avoid excessive decorative animations.

The evidence and workflow should remain the visual priority.

---

## 8. End-to-End User Journey

The user should be able to do this:

```text
1. Open Groww Product Feedback Intelligence
2. Confirm Groww Android app
3. Fetch latest 7 days of reviews
4. See retrieval statistics
5. Run analysis
6. See top themes and evidence
7. See recurring fee confusion
8. See official fee documentation
9. Review generated Product Pulse
10. Review Fee Explainer
11. Review proposed document update
12. Review proposed Gmail draft
13. Click Approve
14. Append to internal document
15. Create Gmail draft
16. See completion status
```

No manual review CSV preparation should be required.

---

## 9. Screen 1 — Source & Review Fetch

Header:

> **Groww Product Feedback Intelligence**

Show:

```text
Source
Google Play Store

Application
Groww Android App

Review Window
Last 7 Days
```

Primary CTA:

> **Fetch Latest Reviews**

After retrieval, show:

```text
Reviews retrieved: X
Review period: DD MMM YYYY – DD MMM YYYY
Average rating: X.X / 5
```

Also show retrieval status:

```text
✓ Source connected
✓ Reviews retrieved
✓ Review period validated
```

---

## 10. Review Ingestion Layer

The ingestion system should:

* Determine today's date automatically.
* Calculate the previous 7 days.
* Retrieve reviews until the period boundary is reached.
* Handle API pagination.
* Deduplicate reviews.
* Normalize timestamps.
* Preserve original review text.
* Preserve review IDs.
* Preserve ratings.
* Preserve app version where available.
* Preserve developer replies where available.

Recommended internal format:

```json
{
  "review_id": "...",
  "review_text": "...",
  "rating": 1,
  "review_date": "2026-08-29T10:30:00Z",
  "app_version": "...",
  "source": "Google Play",
  "source_url": "..."
}
```

---

## 11. Review Quality Checks

Before analysis:

* Remove empty reviews.
* Remove exact duplicates.
* Handle duplicate review IDs.
* Normalize whitespace.
* Exclude reviews outside the 7-day window.
* Preserve original wording.
* Handle multilingual/poorly structured reviews gracefully.
* Flag reviews that cannot be reliably interpreted rather than fabricating meaning.

The original review text must always remain available for evidence and quote extraction.

---

## 12. Screen 2 — Analysis Progress

After fetching reviews, show a visible analysis workflow.

Example:

```text
✓ Reviews loaded
✓ Reviews cleaned
✓ Reviews deduplicated
✓ Themes identified
✓ Themes ranked
✓ Fee confusion detected
✓ Official sources verified
✓ Product Pulse generated
✓ Fee Explainer generated
```

The user should be able to see that the system is actually processing the source data rather than displaying static results.

---

## 13. Review Intelligence Layer

Cluster reviews into **a maximum of 5 themes**.

Themes must be derived from the actual review corpus.

Do not hard-code categories.

Possible themes could include:

* Fees / pricing
* Trading / order execution
* App performance
* Payments / withdrawals
* Customer support
* KYC / account issues
* Portfolio / investment experience

These are examples only.

The actual themes must come from the retrieved reviews.

---

## 14. Per-Review Classification

Where practical, assign:

```text
Primary theme
Secondary theme
Sentiment
Severity
Issue type
```

Issue type:

```text
Complaint
Question / confusion
Feature request
Praise
General feedback
```

Sentiment:

```text
Positive
Neutral
Negative
```

This classification should support theme ranking and fee-confusion detection.

---

## 15. Theme Aggregation

For each theme calculate:

* Theme name
* Description
* Number of reviews
* Percentage of review corpus
* Negative review count
* Average rating
* Representative reviews
* Trend over the 7-day period

All metrics must be based on real retrieved data.

---

## 16. Identify the Top 3 Themes

Rank themes using a transparent combination of:

* Frequency
* Negative sentiment
* Rating severity
* Recency
* Persistence

The exact scoring formula is implementation-specific, but it must be explainable.

Do not rank themes solely by keyword frequency.

Return the top 3 themes when sufficient data exists.

If fewer than 3 meaningful themes exist, return fewer and explain why.

---

## 17. Temporal Analysis

Because reviews cover 7 days, analyze temporal patterns.

Where sufficient data exists, identify whether key issues are:

* Increasing
* Decreasing
* Stable
* Recently spiking

Example:

> Fee-related complaints increased during the most recent three weeks.

Only state this when supported by the actual data.

Do not manufacture a trend from small or inconclusive samples.

---

## 18. Extract 3 Real User Quotes

Extract exactly **3 real, verbatim customer quotes**.

Requirements:

* Must exist in the retrieved Google Play review corpus.
* Must not be generated by the LLM.
* Must not be paraphrased.
* Prefer quotes strongly supporting the top themes.
* Preferably include a fee-related quote when a fee issue is identified.

Maintain provenance:

```text
Review ID
Quote
Date
Rating
Theme
Source
```

The UI should make it clear that these are real customer reviews.

---

## 19. Detect Recurring Fee / Charge Confusion

This is the critical insight-generation requirement.

Inspect the actual review corpus for recurring confusion involving:

* Fees
* Charges
* Deductions
* Brokerage
* Taxes
* Transaction charges
* Investment-related charges
* Account charges
* Other customer-paid costs

The system must identify **one recurring fee/charge misunderstanding**, when sufficient evidence exists.

### Do Not Assume the Fee Upfront

The system must not be preconfigured to detect a specific fee such as:

* DP charges
* Exit load
* Brokerage
* AMC

Those are only examples.

The fee issue must emerge from actual customer feedback.

---

## 20. Fee Confusion Detection Logic

Look for reviews containing patterns such as:

```text
"Why was I charged?"
"Why was money deducted?"
"What is this fee?"
"I did not know this charge applied."
"Why is there an extra deduction?"
"How was this amount calculated?"
"When does this fee apply?"
```

Group such reviews into candidate fee issues.

Choose the strongest recurring issue based on:

* Number of reviews
* Consistency
* Recency
* Severity
* Clarity of the underlying fee
* Ability to verify the fee through official Groww documentation

---

## 21. Distinguish Customer Confusion From Billing Error

This must be enforced.

Customer reviews can establish:

> Users are confused, surprised, or unhappy about a charge.

They cannot by themselves establish:

> Groww charged the customer incorrectly.

Example:

Customer review:

> "Why was ₹20 deducted?"

Valid finding:

> Users appear confused about a ₹20 deduction.

Invalid finding without authoritative support:

> Groww incorrectly charged ₹20.

The system must remain neutral about billing correctness unless verified evidence supports the claim.

---

## 22. Fee Issue Output

Display:

```text
Fee / Charge
Related review count
Share of corpus
Representative complaints
Observed misunderstanding
Confidence
Why this issue was selected
```

Example:

```text
Fee:
DP Charges

Related reviews:
21

Observed misunderstanding:
Customers appear unclear about when the charge applies and why it is deducted.

Confidence:
High
```

---

## 23. Confidence

For major insights use:

```text
High
Medium
Low
```

Confidence should account for:

* Number of supporting reviews
* Consistency
* Review quality
* Temporal persistence
* Clustering quality
* Availability of official documentation

Do not present weak evidence as a strong conclusion.

---

## 24. Official Groww Source Verification

After identifying the fee issue, retrieve the relevant **official Groww documentation**.

Prefer:

* Groww Help Center
* Groww official website
* Groww charges/pricing documentation
* Other first-party Groww documentation

Do not use:

* Reddit
* Random blogs
* Third-party financial websites
* Search snippets as authoritative evidence

The system must verify that the sources support the factual claims in the Fee Explainer.

The model should not rely on generic financial knowledge for Groww's current fee policy.

---

## 25. Source Retrieval Requirements

The source retrieval layer should:

* Search for the exact fee identified.
* Prefer official Groww domains.
* Retrieve the relevant page content.
* Extract supporting factual information.
* Store the source URL.
* Record the date checked.

Never invent a URL.

Never claim a source was checked if it was not actually retrieved.

---

## 26. Step 3 — Weekly Product Pulse

Generate an internal Product update of **≤250 words**.

### Required Structure

#### Top Themes

Summarize the top 3 themes, with supporting metrics.

#### User Voice

Include the 3 real customer quotes.

#### Key Observation

Explain:

* What customers are struggling with.
* What appears to be causing friction/confusion.
* Whether the issue is recurring.
* Whether there is a meaningful trend.

#### Product Actions

Provide exactly **3 actionable ideas**.

These should be framed as product hypotheses/recommendations.

Do not claim they are already validated.

---

## 27. Product Pulse Constraints

The Product Pulse must be:

* ≤250 words
* Internal-facing
* Concise
* Evidence-backed
* Neutral
* Action-oriented

Avoid:

* Marketing language
* Unsupported speculation
* Blaming users
* Blaming internal teams
* Unnecessary jargon

Show a live word count in the frontend:

```text
Word count: 187 / 250
```

---

## 28. Step 4 — Fee Explainer

Generate a Support-facing explanation for the **exact fee identified from customer reviews**.

The chain must always be:

```text
Real reviews
→ Recurring confusion
→ Identified fee
→ Official Groww documentation
→ Verified explanation
```

Never generate a generic fee explanation unrelated to the review findings.

---

## 29. Fee Explainer Requirements

Maximum **6 bullet points**.

Where supported, explain:

1. What the fee is.
2. When it applies.
3. Why it is charged.
4. How the amount is determined.
5. Relevant conditions/exceptions.
6. What the customer should expect.

Only include claims supported by official Groww sources.

Show a bullet count:

```text
5 / 6 bullets
```

---

## 30. Fee Explainer Tone

The explanation must be:

* Neutral
* Factual
* Clear
* Customer-friendly
* Non-defensive
* Reusable by Support

Avoid language that blames or dismisses customers.

Prefer:

> "This charge applies when..."

over:

> "Customers should have known..."

---

## 31. Sources

Include **2 official source links** whenever two relevant first-party sources genuinely exist.

Display:

```text
Sources

1. Official Groww source
2. Official Groww source
```

If two relevant official sources do not exist, do not invent a second source. Flag the limitation in the UI.

---

## 32. Last Checked

Include:

```text
Last checked: DD Month YYYY
```

This must represent the actual date the official sources were verified.

---

## 33. Screen 3 — Insights Dashboard

After analysis, show a dashboard with:

### Summary Cards

```text
Reviews analyzed
X

Themes found
X

Top issue
[Theme]

Fee issue confidence
[High / Medium / Low]
```

### Theme Table

Columns:

```text
Theme
Reviews
Share
Avg Rating
Trend
```

### Top 3 Themes

Use prominent cards showing:

* Theme
* Review count
* Share
* Trend
* Description

### Customer Voice

Show the 3 verbatim quotes.

### Fee Issue

Show:

```text
Detected fee:
[Fee]

Related reviews:
[X]

Observed confusion:
[...]

Confidence:
[High/Medium/Low]
```

---

## 34. Screen 4 — Generated Outputs

Use two main panels.

### Weekly Product Pulse

Show:

* Complete pulse
* Word count
* Edit control

### Customer Fee Explainer

Show:

* Fee name
* Why customers are confused
* Up to 6 bullets
* Official sources
* Last checked date
* Edit control

The user must be able to inspect the output before approval.

---

## 35. Screen 5 — Approval Review

This is the most important safety/controls screen.

Show the exact content that will be written externally/internally.

### Review Summary

```text
Reviews analyzed
Review period
Top themes
Fee issue
Confidence
```

### Document Update Preview

Show the structured record that will be appended.

### Gmail Draft Preview

Show:

```text
Subject:
Weekly Product Pulse + Customer Clarification — [Fee Name]

Body:
...
```

Then show an explicit approval control:

> **Approve & Create Internal Updates**

Also display:

> No write action will occur until you approve.

---

## 36. Approval Gate

No write-capable MCP action can execute before explicit user approval.

### Before Approval

Allowed:

* Fetch reviews
* Analyze reviews
* Retrieve official sources
* Generate outputs
* Display results
* Edit/regenerate outputs

Not allowed:

* Append to internal document
* Create Gmail draft
* Send email
* Any other write action

### After Approval

The application may invoke approved write actions.

The approval gate must exist at the **application level**, not merely as a prompt instruction to the LLM.

---

## 37. Optional Pre-Approval Editing

Allow the user to edit:

* Weekly Product Pulse
* Product action ideas
* Fee Explainer
* Email subject
* Email body

However:

* Original review quotes must remain linked to source reviews.
* Edited content must not be falsely presented as untouched model-generated evidence.
* The approval action should operate on the exact content visible in the preview.

---

## 38. Required MCP Action #1 — Append to Internal Document

After approval, append a new entry to an internal document/knowledge repository.

Preferred:

* Google Docs
* Notion
* Equivalent connected internal system

Do not overwrite previous entries.

Append data equivalent to:

```json
{
  "date": "YYYY-MM-DD",
  "review_period": {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD"
  },
  "source": "Google Play Store",
  "review_count": 0,
  "top_themes": [
    {
      "theme": "Theme 1",
      "review_count": 0,
      "percentage": 0
    },
    {
      "theme": "Theme 2",
      "review_count": 0,
      "percentage": 0
    },
    {
      "theme": "Theme 3",
      "review_count": 0,
      "percentage": 0
    }
  ],
  "weekly_pulse": "Generated weekly pulse",
  "identified_fee_issue": {
    "fee": "Fee name",
    "description": "Recurring customer confusion",
    "evidence_count": 0,
    "confidence": "High"
  },
  "explanation_bullets": [
    "Bullet 1",
    "Bullet 2"
  ],
  "source_links": [
    "https://official-source-1",
    "https://official-source-2"
  ]
}
```

Each successful run should append a new entry.

---

## 39. Required MCP Action #2 — Create Gmail Draft

After approval, create a **Gmail draft only**.

Do not send it.

### Subject

```text
Weekly Product Pulse + Customer Clarification — [Fee Name]
```

Example:

```text
Weekly Product Pulse + Customer Clarification — DP Charges
```

### Body

```text
Weekly Product Pulse

[Generated Product Pulse]


Customer Fee Clarification

[Generated Fee Explainer]


Sources

1. ...
2. ...

Last checked: ...
```

The Fee Explainer should be formatted so Support can reuse it.

---

## 40. No Auto-Send

The application must never send the email.

After the action succeeds, clearly display:

> **Gmail draft created. No email has been sent.**

---

## 41. MCP Architecture

Separate read-only and write-capable functionality.

### Read

```text
fetch_google_play_reviews()
fetch_official_groww_fee_sources()
```

### Analysis

```text
cluster_reviews()
rank_themes()
detect_fee_confusion()
extract_quotes()
analyze_trends()
```

### Generation

```text
generate_product_pulse()
generate_fee_explainer()
```

### Write

```text
append_to_internal_document()
create_gmail_draft()
```

Only the final two are approval-gated.

---

## 42. Approval State

Implement explicit approval state.

Example:

```python
approval_status = "pending"
```

Before approval:

```text
append_to_internal_document() → BLOCKED
create_gmail_draft()          → BLOCKED
```

After explicit approval:

```python
approval_status = "approved"
```

then invoke the write operations.

The LLM must not be able to bypass this application-level control.

---

## 43. Error Handling

### Google Play Retrieval Failure

Show:

> Unable to retrieve Google Play reviews. Check the app package ID, API credentials/access, or review retrieval availability.

Do not silently switch to fake/sample data.

### Insufficient Reviews

Explain that the dataset does not contain enough evidence for reliable analysis.

### No Meaningful Themes

Explain why meaningful clustering could not be established.

### No Recurring Fee Issue

Do not invent one.

Show:

> No recurring fee or charge misunderstanding was identified with sufficient confidence in the available reviews.

Do not generate a fabricated Fee Explainer in this scenario.

### Official Source Unavailable

Do not generate an unverified fee explanation.

Flag the issue.

### MCP Failure

Show the exact result of each action.

Example:

```text
Internal document update: Failed
Gmail draft: Successful
```

Never falsely report an action as successful.

---

## 44. Evidence & Hallucination Guardrails

Every customer-related claim must be grounded in the retrieved Google Play reviews.

Every Groww fee-policy claim must be grounded in official Groww documentation.

Maintain internal provenance:

```text
Insight
  ↓
Supporting review IDs
  ↓
Real customer quotes
  ↓
Official source(s)
```

The system must never invent:

* Customer reviews
* Customer quotes
* Review counts
* Ratings
* Trends
* Fee names
* Fee policies
* Official URLs
* Evidence

When evidence is insufficient, state that explicitly.

---

## 45. No Synthetic Evidence

This requirement is strict.

Never create a quote that did not appear in the source data.

Never state a review count that was not calculated.

Never infer a fee policy from a customer complaint alone.

Never state that a charge was incorrect unless authoritative evidence establishes it.

Never generate a fake official Groww source.

---

## 46. Suggested Technical Architecture

A reasonable architecture:

```text
                 FRONTEND
                     │
                     ▼
              Backend / API
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
Google Play Connector      Official Source Retriever
        │                         │
        ▼                         ▼
   Review Store             Groww Documentation
        │                         │
        └────────────┬────────────┘
                     ▼
              AI Analysis Layer
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
 Theme Detection  Fee Detection  Trend Analysis
       │             │             │
       └─────────────┼─────────────┘
                     ▼
              Output Generation
               │              │
               ▼              ▼
        Product Pulse    Fee Explainer
               │              │
               └──────┬───────┘
                      ▼
                 Approval Gate
                      │
                      ▼
                 MCP Layer
                 │         │
                 ▼         ▼
              Document    Gmail Draft
```

---

## 47. Suggested Backend Data Model

Maintain structured internal objects such as:

```text
Review
Theme
ThemeEvidence
FeeIssue
Source
ProductPulse
FeeExplainer
ApprovalRequest
MCPActionResult
```

This makes it possible to trace every generated output back to evidence.

---

## 48. Review Data Model

Example:

```json
{
  "review_id": "...",
  "text": "...",
  "rating": 1,
  "date": "...",
  "app_version": "...",
  "theme": "...",
  "sentiment": "negative",
  "issue_type": "complaint"
}
```

---

## 49. Final Success Criteria

The project is successful when a user can open the web application and complete this entire workflow without manually preparing a review dataset:

```text
1. Open the application
2. Confirm Groww Android app
3. Fetch the latest 7 days of Google Play reviews
4. See actual retrieval statistics
5. Analyze the retrieved reviews
6. Cluster reviews into no more than 5 themes
7. Identify the top 3 themes
8. Extract 3 real customer quotes
9. Identify one recurring fee/charge confusion
10. Support the fee finding with review evidence
11. Verify the fee using official Groww sources
12. Generate a ≤250-word Weekly Product Pulse
13. Generate a ≤6-bullet Fee Explainer
14. Review/edit both outputs
15. Preview the document update
16. Preview the Gmail draft
17. Explicitly approve
18. Append the result to an internal document
19. Create a Gmail draft
20. Do not send the email
21. Show final success/failure status
```

---

## 50. Core Product Principle

The system must preserve a strict evidence chain:

```text
REAL GOOGLE PLAY REVIEWS
        ↓
CUSTOMER THEMES
        ↓
TOP PRODUCT ISSUES
        ↓
RECURRING FEE CONFUSION
        ↓
OFFICIAL GROWW DOCUMENTATION
        ↓
WEEKLY PRODUCT PULSE
+
FEE EXPLAINER
        ↓
USER APPROVAL
        ↓
MCP WRITE ACTIONS
```

The **fee issue must emerge from real customer feedback**.

The **Fee Explainer must be grounded in official Groww documentation**.

The **MCP actions must require explicit user approval**.

The **email must only be drafted, never sent automatically**.

The final product should feel like a realistic internal **Groww Product + Support Intelligence tool**, not a generic CSV summarizer or chatbot.
