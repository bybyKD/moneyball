# Moneyball AI Scouting Platform

## AI-Native Football Recruitment & Scouting Intelligence System

> **Mission:** Build a production-quality football scouting platform inspired by the Moneyball philosophy: identify players whose measurable performance, potential, and tactical suitability are greater than what their current market value suggests.
>
> This is **not** a simple football statistics dashboard. It is an AI-assisted scouting and recruitment intelligence platform where users can investigate players, discover undervalued talent, compare candidates, analyze tactical fit, and generate evidence-backed scouting reports.

---

## 1. Product Vision

Build a modern football scouting platform that answers questions such as:

* "Find undervalued U23 midfielders."
* "Find players similar to this player but cheaper."
* "Which players in smaller leagues could perform well in the Premier League?"
* "Find a replacement for this player."
* "Which players have unusually high output relative to their transfer value?"
* "Find 10 realistic targets for this club."
* "Why is this player potentially undervalued?"
* "Compare these three players."
* "Generate a complete scouting report for this player."

The system should combine:

1. Football statistics
2. Player profiles
3. Market/transfer information
4. Age and development potential
5. Positional analysis
6. League-strength adjustments
7. Tactical characteristics
8. Similar-player modelling
9. AI research
10. AI-generated scouting reports
11. Transparent evidence and explanations

---

## 2. Core Principle

Do NOT build the application around a single arbitrary "overall rating."

The platform must explain **why** a player appears valuable.

Every major conclusion should be traceable to:

* underlying statistics
* methodology
* comparison population
* data source
* model output
* confidence level

Avoid opaque statements such as:

> "Player X is 92/100."

Instead prefer:

> "Player X ranks in the 94th percentile for progressive carries among U23 wingers in comparable leagues while costing approximately €2.8M. His strongest relative advantages are ball progression and chance creation."

---

## 3. Target Users

Primary users:

### Scouts

Need to discover and evaluate players quickly.

### Recruitment Analysts

Need data-driven comparisons and candidate shortlists.

### Sporting Directors

Need recruitment intelligence and concise reports.

### Coaches

Need tactical-fit information.

### Football Enthusiasts

Need an accessible version of professional scouting analytics.

---

## 4. Application Structure

Create the following primary sections:

```text
Dashboard
Players
Discover
Compare
Scouting
Shortlists
Reports
Clubs
Leagues
Data Explorer
Settings
```

---

## 5. Dashboard

The dashboard should provide:

* Recently viewed players
* Saved players
* Active scouting missions
* Emerging talents
* Potentially undervalued players
* Market movers
* Recommended discoveries
* Recent reports
* Data updates
* Scouting alerts

Example:

```text
GOOD MORNING

Your Scouting Workspace

────────────────────────────────────

12  New Discoveries
8   Players Matching Watchlists
4   Market Changes
3   Reports Ready

────────────────────────────────────

UNDERVALUED PLAYERS

Player A
U23 • CM
€2.4M
Performance/value: High

Player B
U21 • RW
€1.8M
Performance/value: High

────────────────────────────────────

ACTIVE MISSIONS

"Find U23 Defensive Midfielder"
██████████████████░░ 87%

"Find Affordable RW"
████████████░░░░░░░░ 61%
```

---

## 6. Player Database

Every player should have a dedicated profile.

### Player Header

Display:

* Name
* Photo
* Age
* Date of birth
* Nationality
* Position
* Preferred foot
* Height
* Current club
* League
* Contract information when available
* Estimated market value
* Market-value trend

---

## 7. Player Profile

Organize the profile into:

```text
Overview
Performance
Possession
Passing
Chance Creation
Shooting
Defending
Physical
Goalkeeping
Tactical Profile
Similar Players
Market Value
Career
AI Analysis
Sources
```

Only show relevant categories for the player's position.

---

## 8. Statistical System

Use per-90 metrics wherever appropriate.

### Attacking

* Goals/90
* xG/90
* Non-penalty xG/90
* Assists/90
* xA/90
* Shots/90
* Shots on target/90
* Touches in penalty area
* Progressive carries
* Progressive passes
* Successful dribbles
* Shot-creating actions

### Passing

* Pass completion
* Progressive passes
* Key passes
* Final-third passes
* Passes into penalty area
* Through balls
* Long-pass completion
* Progressive passing distance

### Defending

* Tackles
* Interceptions
* Blocks
* Clearances
* Defensive duels
* Aerial duels
* Pressures
* Pressure success
* Recoveries

### Possession

* Carries
* Progressive carries
* Carry distance
* Miscontrols
* Dispossessions

---

## 9. Position-Specific Metrics

Never evaluate every position using the same metric weighting.

Create role profiles.

```text
ST
├── Non-penalty xG
├── xG + xA
├── Shots
├── Box touches
├── Pressing
└── Aerial ability

WINGER
├── Progressive carries
├── Successful dribbles
├── xA
├── Shot creation
├── Box entries
└── xG

CM
├── Progressive passing
├── Progressive carries
├── Ball retention
├── Chance creation
├── Defensive actions
└── Press resistance

CB
├── Defensive duels
├── Aerials
├── Interceptions
├── Progressive passing
├── Ball retention
└── Defensive errors

FB
├── Progressive carries
├── Progressive passing
├── Crosses
├── Defensive actions
├── Chance creation
└── Ball recoveries
```

Support custom tactical roles:

* Ball-winning midfielder
* Deep-lying playmaker
* Box-to-box midfielder
* Inverted fullback
* Attacking fullback
* Pressing forward
* Target forward
* Inside forward
* Ball-playing defender

---

## 10. League Adjustment

Raw statistics cannot be compared blindly across leagues.

Implement league-strength normalization.

```text
Raw Performance
        ↓
League Adjustment
        ↓
Position Adjustment
        ↓
Age Adjustment
        ↓
Minutes Reliability
        ↓
Normalized Performance
```

The system should explicitly identify when comparisons cross leagues.

Do NOT pretend that:

```text
0.70 xG/90 in League A
```

automatically equals:

```text
0.70 xG/90 in League B
```

---

## 11. Moneyball Model

Create a transparent "Value Discovery" model.

```text
Performance
+
Potential
+
Tactical Fit
+
Age
+
League Translation
+
Availability
-
Market Cost
-
Risk
=
Value Opportunity
```

Do not hardcode arbitrary weights permanently.

Create a configurable model.

```json
{
  "performance": 0.30,
  "potential": 0.20,
  "tactical_fit": 0.20,
  "age": 0.10,
  "league_translation": 0.10,
  "market_value": 0.10
}
```

Weights must be configurable by scouting mission.

---

## 12. Moneyball Score Explanation

Instead of only showing:

```text
Moneyball Score: 91
```

show:

```text
VALUE OPPORTUNITY

Strong

Why?

+ 94th percentile progressive carries
+ 91st percentile chance creation
+ U23 development profile
+ Low estimated market value
+ Strong performance relative to comparable players

Risks

- Limited top-level minutes
- Lower-strength league
- Small sample size

Confidence

Medium
```

---

## 13. Similar Player Engine

Implement player similarity.

A user should be able to select:

> "Find players similar to Bukayo Saka."

The system should consider:

* Position
* Role
* Statistical profile
* Age
* League
* Playing style
* Possession behaviour
* Passing
* Chance creation
* Defensive contribution

Return:

```text
SIMILARITY

Player A     91%
Player B     87%
Player C     84%
Player D     81%
```

Allow the user to modify the similarity criteria.

---

## 14. Replacement Finder

Create:

```text
Find Replacement
```

Workflow:

```text
Select Player
      ↓
Analyze Player Profile
      ↓
Identify Core Characteristics
      ↓
Search Global Player Database
      ↓
Apply User Constraints
      ↓
Rank Candidates
      ↓
Explain Differences
```

Example:

> Find a replacement for Player X under €10M, age <25.

The output should include:

* similarity
* estimated cost
* statistical differences
* tactical differences
* risks
* strengths
* development potential

---

## 15. Natural Language Scouting

The user should not have to manually configure every filter.

Provide:

```text
What are you looking for?
```

Example:

> "Find me a young left-footed centre-back under €5 million who is good at progressive passing and aerial duels."

The system converts this into structured constraints:

```json
{
  "position": ["CB"],
  "age_max": 23,
  "market_value_max": 5000000,
  "preferred_foot": "left",
  "metrics": [
    "progressive_passing",
    "aerial_duels"
  ]
}
```

The user must be able to inspect and modify these extracted constraints.

---

## 16. AI Agent Architecture

The application must use specialized AI agents rather than one giant prompt.

### Agent 1 — Scout Agent

Responsible for:

* understanding scouting requests
* converting natural language into constraints
* identifying relevant positions
* creating scouting missions

---

### Agent 2 — Data Analyst Agent

Responsible for:

* statistical analysis
* percentile calculations
* player comparisons
* identifying statistical anomalies
* calculating derived metrics

The agent must NOT invent statistics.

All numbers must originate from the database or verified tools.

---

### Agent 3 — Research Agent

Responsible for researching external information:

* player news
* injuries when publicly documented
* transfers
* contracts
* manager comments
* tactical roles
* career history

Every external factual claim must have a source.

---

### Agent 4 — Tactical Analyst Agent

Responsible for translating statistics into football concepts.

```text
Statistical observation:
High progressive carries + high final-third entries.

Possible interpretation:
Player frequently advances possession through ball carrying.

Confidence:
High
```

The agent must distinguish:

```text
FACT
INFERENCE
UNCERTAINTY
```

---

### Agent 5 — Market Analyst Agent

Responsible for:

* market-value analysis
* transfer activity
* estimated acquisition cost
* contract situations
* market trends

Never represent an estimate as an official transfer value.

---

### Agent 6 — Comparison Agent

Responsible for:

* player-v-player comparison
* similar player discovery
* strengths/weaknesses
* statistical differences

---

### Agent 7 — Verification Agent

This is mandatory.

Before generating a final report:

```text
Claims
   ↓
Verification Agent
   ↓
Check database
Check sources
Check calculations
Check contradictions
   ↓
Approved / Flagged
```

The Verification Agent must identify:

* unsupported claims
* stale data
* conflicting information
* insufficient sample size
* misleading comparisons
* hallucinated information

---

### Agent 8 — Scouting Report Agent

Produces the final human-readable report.

Report sections:

```text
Executive Summary
Player Profile
Statistical Profile
Tactical Profile
Strengths
Weaknesses
Development Potential
Market Context
Comparison Players
Risks
Data Confidence
Sources
```

---

## 17. Agent Orchestration

Do not allow agents to randomly call one another.

Create an explicit orchestration layer.

```text
User Request
     │
     ▼
Scout Agent
     │
     ▼
Mission Plan
     │
 ┌───┼─────────────┐
 ▼   ▼             ▼
Data Research    Market
Agent Agent      Agent
 └───┬─────────────┘
     ▼
Tactical Analyst
     │
     ▼
Comparison Engine
     │
     ▼
Verification Agent
     │
     ▼
Report Agent
```

The orchestrator should maintain:

* task state
* agent state
* tool calls
* intermediate results
* errors
* source references
* final output

---

## 18. Agent Activity UI

Users should be able to see what the system is doing.

```text
SCOUTING MISSION

"Find U23 midfielders under €5M"

✓ Scout Agent
  Parsed requirements

✓ Data Analyst
  Analyzed 18,421 players

◉ Research Agent
  Researching 37 candidates...

✓ Market Agent
  Market data collected

○ Tactical Analyst
  Waiting

○ Verification
  Waiting

○ Report
  Waiting
```

Allow users to expand each agent and inspect its reasoning summary, tool activity, sources, and outputs.

Do NOT expose private chain-of-thought.

Show concise:

* action
* tool used
* result
* evidence
* status

---

## 19. Scouting Missions

Users should be able to create persistent scouting missions.

```text
MISSION

Young Right Winger

Requirements:
Age: <23
Position: RW/RM
Market value: <€5M
League: Any
Preferred foot: Left

Priority:
Ball progression
Chance creation
Goal contribution

Status:
ACTIVE
```

The mission can be rerun whenever new data arrives.

---

## 20. Shortlists

Users can save players into:

```text
Shortlist
    ↓
Candidates
    ↓
Priority
    ↓
Scouting Status
```

Statuses:

```text
DISCOVERED
RESEARCHING
WATCHLIST
SHORTLISTED
SCOUTED
CONTACTED
REJECTED
SIGNED
```

Allow notes and custom tags.

---

## 21. Reports

Reports should be generated as structured documents.

```text
SCOUTING REPORT

Player:
Position:
Age:
Club:

────────────────────────

EXECUTIVE SUMMARY

...

STATISTICAL PROFILE

...

TACTICAL PROFILE

...

MARKET ANALYSIS

...

RISKS

...

SIMILAR PLAYERS

...

DATA CONFIDENCE

...

SOURCES
```

Allow:

* HTML
* PDF
* Markdown export

---

## 22. Data Sources

Design the system so data providers are abstracted behind interfaces.

Do NOT hard-code the entire application around one provider.

Create:

```text
FootballDataProvider
MarketDataProvider
PlayerDataProvider
NewsDataProvider
CompetitionDataProvider
```

Possible data sources may include:

* licensed football APIs
* public football datasets
* provider APIs
* manually imported datasets

Respect each provider's:

* terms of service
* licensing
* rate limits
* attribution requirements

Do not scrape websites in violation of their terms.

---

## 23. Database

Use PostgreSQL.

Core entities:

```text
users
players
clubs
leagues
competitions
seasons
player_season_stats
player_match_stats
player_positions
player_roles
transfers
market_values
contracts
injuries
sources
scouting_missions
mission_candidates
shortlists
shortlist_players
player_comparisons
scouting_reports
agent_runs
agent_tasks
agent_events
```

---

## 24. Vector Search

Use vector embeddings for:

* player descriptions
* tactical profiles
* scouting reports
* news
* research documents

Potential architecture:

```text
PostgreSQL
+
pgvector
```

Use structured SQL for numerical statistics.

Use vector search for semantic retrieval.

Do NOT use embeddings to replace structured statistical queries.

---

## 25. AI / RAG Architecture

AI should receive structured context.

```text
PLAYER DATA
      +
STATISTICS
      +
MARKET DATA
      +
TACTICAL DATA
      +
RESEARCH SOURCES
      +
USER REQUIREMENTS
      ↓
      LLM
      ↓
SCOUTING ANALYSIS
```

Never ask an LLM to calculate statistics that SQL/Python can calculate reliably.

---

## 26. Backend

Recommended:

```text
Python
FastAPI
PostgreSQL
Redis
Celery / background workers
```

The backend should expose APIs such as:

```text
GET /players
GET /players/:id
GET /players/:id/stats
GET /players/:id/similar
GET /players/:id/market

POST /scouting/missions
GET /scouting/missions/:id
POST /scouting/missions/:id/run

POST /compare
POST /discover
POST /reports
```

---

## 27. Frontend

Use:

```text
Next.js
TypeScript
React
Tailwind CSS
```

The UI should feel like a **professional football analytics terminal**, not a generic SaaS dashboard.

Design principles:

* information-dense
* fast
* minimal
* professional
* dark/light mode
* excellent typography
* strong data visualization
* keyboard friendly
* responsive

Avoid:

* excessive gradients
* generic AI purple styling
* unnecessary glassmorphism
* giant cards
* excessive animations
* "AI-generated" visual clichés

---

## 28. Data Visualization

Use charts where they genuinely improve understanding.

### Radar chart

For player role comparison.

### Percentile chart

```text
Progressive Passing       ██████████████████ 92
Chance Creation           ████████████████   84
Ball Retention            █████████████████  88
Defensive Actions         ███████████        61
```

### Scatter plot

Extremely important for Moneyball.

```text
Performance
    ↑
    │        ●
    │    ●
    │             ●
    │
    │ ●
    │       ●
    └────────────────────→
             Market Value
```

Highlight players with:

```text
High performance
+
Low market value
```

These become potential value opportunities.

---

## 29. Player Comparison

Comparison page:

```text
              PLAYER A       PLAYER B

Age              21              24
Value           €3.2M           €7.5M

xG/90           0.31            0.28
xA/90           0.24            0.19
Prog Carries    5.8             4.2
Prog Passes     6.4             8.1

League Adj.     82              91
Potential       High            Medium
```

Allow:

* 2–5 players
* same position
* different positions
* different leagues
* custom metric weighting

---

## 30. AI Chat Interface

Include an AI scouting assistant.

```text
┌───────────────────────────────────────┐
│ Scout AI                              │
├───────────────────────────────────────┤
│                                       │
│ You:                                  │
│ Find me 5 U21 midfielders under €3M   │
│                                       │
│ AI:                                   │
│ I'll search across 47 competitions.   │
│                                       │
│ [Analyzing 21,384 players...]         │
│                                       │
│ Found 127 candidates.                 │
│                                       │
│ After applying your tactical profile │
│ and market constraints, 12 candidates │
│ remain.                               │
│                                       │
│ [View 12 Candidates]                  │
└───────────────────────────────────────┘
```

The AI must be capable of calling application tools.

---

## 31. AI Tool System

Agents should have explicit tools.

```text
search_players()
get_player_stats()
get_player_profile()
compare_players()
find_similar_players()
search_market_data()
search_news()
search_sources()
calculate_percentile()
calculate_value_metrics()
create_shortlist()
generate_report()
verify_claim()
```

Every tool should have:

* typed input
* typed output
* validation
* logging
* error handling

---

## 32. Reliability Requirements

The application must prioritize correctness over impressive AI output.

### Rule 1

Never invent statistics.

### Rule 2

Never invent transfer values.

### Rule 3

Never invent sources.

### Rule 4

Clearly label estimates.

### Rule 5

Display sample size.

```text
xG/90: 0.72

Sample:
612 minutes

Confidence:
Low
```

rather than pretending the number is equally reliable as one based on 3,000 minutes.

---

## 33. Explainability

Every AI conclusion should have an explanation.

```text
WHY THIS PLAYER?

1. Performance
   91st percentile in chance creation.

2. Value
   Strong output relative to estimated market value.

3. Age
   U21 profile provides development potential.

4. Tactical Fit
   Statistical profile matches your requested role.

5. Risk
   Only 900 minutes in the current season.
```

---

## 34. Confidence System

Every analysis should have:

```text
Confidence:
HIGH
MEDIUM
LOW
```

Confidence should depend on factors such as:

* sample size
* data completeness
* source reliability
* league comparability
* statistical consistency
* conflicting sources

---

## 35. Data Freshness

Every data point should have:

```text
last_updated
source
season
competition
```

Display:

> Data updated 2 days ago.

Avoid silently mixing different seasons.

---

## 36. Security

Implement:

* authentication
* authorization
* rate limiting
* API key protection
* server-side secrets
* input validation
* audit logs
* secure database access

Never expose:

```text
OPENAI_API_KEY
DATABASE_URL
API provider secrets
```

to the browser.

---

## 37. Observability

Every agent execution should produce structured logs.

```json
{
  "mission_id": "...",
  "agent": "data_analyst",
  "action": "calculate_percentiles",
  "status": "completed",
  "duration_ms": 1832,
  "records_processed": 18234
}
```

Track:

* latency
* token usage
* API cost
* failures
* tool calls
* agent execution time

---

## 38. Cost Control

AI agents should NOT use LLM calls for everything.

Use:

```text
SQL
Python
Statistical models
Rules
Vector search
```

before invoking an LLM.

For example:

```text
LLM → analyze 50,000 players
```

should instead be:

```text
SQL → filter 50,000 → 500
Python → calculate metrics → 50
ML → rank → 10
LLM → explain final 10
```

This dramatically reduces cost.

---

## 39. AI Model Strategy

Use different models for different tasks.

```text
Cheap/Fast model
    ↓
classification
query parsing
simple extraction

Stronger model
    ↓
tactical analysis
research synthesis
report generation

Embedding model
    ↓
semantic search
player similarity
document retrieval
```

Do not use the most expensive model for trivial operations.

---

## 40. Machine Learning

Do not force AI/ML into the application unnecessarily.

Use classical ML where appropriate:

```text
Player Similarity
    ↓
Cosine similarity
    +
standardized statistical vectors
```

Potential future models:

* player value prediction
* transfer success prediction
* development projection
* league translation
* injury risk modelling
* career trajectory

These should be separate modules.

---

## 41. Development Phases

The AI coding agent must build the project incrementally.

### Phase 1 — Foundation

Build:

* repository
* frontend
* backend
* PostgreSQL
* authentication
* basic navigation
* design system

Do NOT build every feature immediately.

---

### Phase 2 — Football Data

Implement:

* players
* clubs
* competitions
* seasons
* player statistics
* market values

Create seed/demo data so the UI works before production data integration.

---

### Phase 3 — Analytics Engine

Implement:

* percentiles
* per-90 normalization
* position normalization
* league adjustment
* player similarity
* value analysis

These should be deterministic and testable.

---

### Phase 4 — Discovery

Build:

* player search
* advanced filters
* Moneyball discovery
* scatter plots
* similar players
* replacement finder

---

### Phase 5 — AI Agents

Implement:

1. Scout Agent
2. Data Analyst Agent
3. Research Agent
4. Tactical Analyst
5. Market Analyst
6. Comparison Agent
7. Verification Agent
8. Report Agent

---

### Phase 6 — Agent Orchestration

Implement:

* mission planning
* background execution
* task state
* streaming agent activity
* retries
* failure recovery
* observability

---

### Phase 7 — Scouting Workspace

Build:

* missions
* shortlists
* notes
* saved searches
* reports
* player watchlists

---

### Phase 8 — Production Polish

Implement:

* responsive UI
* accessibility
* performance optimization
* error handling
* caching
* security
* monitoring
* deployment

---

## 42. Testing

The AI coding agent MUST write tests.

Minimum:

```text
Unit tests
Integration tests
API tests
Database tests
Analytics tests
Agent tool tests
End-to-end tests
```

Especially test:

```text
percentile calculations
league normalization
player similarity
Moneyball calculations
filter parsing
agent tool calls
source verification
```

---

## 43. Seed Dataset

Before connecting expensive external APIs, create a realistic development dataset.

```text
10,000 players
500 clubs
50 competitions
5 seasons
```

The exact number can be reduced if necessary for local development.

The seed data must clearly be labeled as:

```text
DEMO DATA
```

Never present synthetic data as real-world information.

---

## 44. UX Requirement

The application should make complex analytics understandable.

A normal user should be able to go from:

```text
"I need a striker"
```

to:

```text
Requirements
      ↓
Candidate discovery
      ↓
Candidate comparison
      ↓
AI analysis
      ↓
Verification
      ↓
Scouting report
```

without needing to understand SQL, statistics, or data science.

---

## 45. Agent Development Rules

The AI coding agent building this project MUST follow these rules.

### Rule A — Inspect before changing

Before modifying an existing component:

1. inspect the repository
2. understand dependencies
3. identify existing architecture
4. reuse existing components when appropriate

Do not blindly overwrite files.

### Rule B — Small iterations

Implement one vertical slice at a time.

```text
Player database
      ↓
Player page
      ↓
Player statistics
      ↓
Similarity
      ↓
AI analysis
```

Do not create hundreds of placeholder files.

### Rule C — Working software

After every significant phase:

```text
Build
Run tests
Fix errors
Verify UI
Continue
```

### Rule D — No fake functionality

Do not create buttons that claim to work but only display:

```text
Coming soon
```

unless the feature is explicitly marked as planned.

### Rule E — No hallucinated data

If production data is unavailable:

```text
Use demo data
```

and clearly label it.

### Rule F — Type everything

Use strict TypeScript and typed Python models.

### Rule G — Document decisions

Maintain:

```text
/docs
```

with:

```text
architecture.md
data-model.md
agents.md
analytics.md
data-sources.md
development.md
```

---

## 46. Suggested Repository

```text
moneyball/
│
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── lib/
│   │   └── hooks/
│   │
│   └── api/
│       ├── app/
│       │   ├── api/
│       │   ├── agents/
│       │   ├── analytics/
│       │   ├── models/
│       │   ├── services/
│       │   └── tools/
│       │
│       └── tests/
│
├── packages/
│   ├── types/
│   ├── ui/
│   └── config/
│
├── data/
│   ├── seed/
│   └── migrations/
│
├── docs/
│   ├── architecture.md
│   ├── agents.md
│   ├── analytics.md
│   ├── data-model.md
│   └── data-sources.md
│
├── docker/
│
├── docker-compose.yml
├── README.md
└── .env.example
```

---

## 47. Definition of Done

The application is NOT considered complete merely because the pages exist.

A feature is complete only when:

```text
UI
 +
Backend
 +
Database
 +
Real logic
 +
Error handling
 +
Loading state
 +
Empty state
 +
Tests
```

are implemented.

For AI features:

```text
Agent
 +
Tools
 +
Structured output
 +
Validation
 +
Sources
 +
Error handling
 +
Observability
```

must exist.

---

## 48. Final Product Experience

The finished application should allow a user to do this:

```text
USER

"I need a U23 attacking midfielder.
Maximum €5M.
Prefer left-footed.
Strong chance creation.
Must be capable of playing in a possession-based system."

                 ↓

SCOUT AGENT

Understands requirements.

                 ↓

DATA AGENT

Searches global database.

                 ↓

ANALYTICS ENGINE

Normalizes statistics.

                 ↓

MARKET AGENT

Evaluates market context.

                 ↓

TACTICAL AGENT

Evaluates stylistic fit.

                 ↓

RESEARCH AGENT

Collects contextual information.

                 ↓

VERIFICATION AGENT

Checks claims and evidence.

                 ↓

REPORT AGENT

Creates scouting report.

                 ↓

USER

Receives:

10 candidates
+
statistics
+
comparisons
+
market context
+
tactical analysis
+
risk assessment
+
sources
+
confidence
```

The user should be able to continue asking:

> "Why did you choose Player 3?"

> "Find someone cheaper."

> "Only players from South America."

> "Compare Player 3 with my current midfielder."

> "Create a scouting report."

> "Add the top 3 to my shortlist."

The application should maintain the context of the scouting mission throughout the workflow.

---

## 49. Most Important Product Principle

Build **an AI scouting system**, not an AI chatbot attached to a football database.

The intelligence should be embedded throughout the product:

```text
SEARCH
   ↓
DISCOVERY
   ↓
ANALYSIS
   ↓
RESEARCH
   ↓
COMPARISON
   ↓
VERIFICATION
   ↓
REPORTING
   ↓
MONITORING
```

The AI should perform useful work.

The interface should make that work understandable.

The underlying analytics should remain deterministic, explainable, and testable.

---

## 50. Initial Implementation Instruction

Start by inspecting the existing repository.

Do NOT immediately generate the entire application.

First:

1. inspect the repository
2. identify existing technologies
3. create an architecture plan
4. identify missing dependencies
5. create the database schema
6. create the development environment
7. implement the application shell
8. implement the player data layer
9. implement analytics
10. implement discovery
11. implement AI agents
12. implement orchestration
13. implement scouting workflows
14. implement reports
15. test everything
16. polish the UX
17. prepare production deployment

At the end of each phase, verify that the application actually works before continuing.

**Prioritize a working vertical slice over generating large amounts of incomplete code.**