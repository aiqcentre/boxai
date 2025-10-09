# 🎬 BoxAI: Film Performance Simulation & AI Query Agent

**Film Viet Australia – 2025 Data Science & AI Internship**

## Background

Film Viet Australia (FVA) is exploring tools to forecast a film’s performance in the Australian market and simulate alternative release strategies. Distributors often rely on instinct or global box office as a guide, but there is no public model that predicts screen count, run duration, or first-week sales, or explains how timing and competition affect performance.

This project uses FVA’s internal database of all 2023–2024 Australian releases. You will not source data. Your task is to build predictive modelling and a natural language agent on top of it.

## Project Goal

Build a machine learning simulation tool to predict screen count, run length, and first-week box office for Australian releases, wrapped in an LLM agent for “what-if” analysis, competitive windows, and hypothetical plans.

## Tech Stack

* **DuckDB** for embedded analytics storage
* **PydanticAI** for the LLM agent runtime
* **FastAPI** for serving prediction and simulation endpoints
* **SQLAlchemy** for data access and modelling

*(You may also use pandas, scikit-learn, XGBoost, and optional Streamlit for demos.)*

## Business Questions

* If Movie X launched one week later, would first-week revenue improve?
* If we released Movie Y on a given date, how would it perform?
* How do big-budget releases affect similar films in the same week?
* What are the most crowded release windows in 2023–2024?
* Which attributes most influence AU performance: global box office, distributor, cast, or others?

## Deliverables

* **Predictive Model**: forecasts for screens, run duration, first-week box office
* **Competitive Context Engine**: overlapping releases and timing features
* **FastAPI Backend**: simulation and prediction endpoints
* **LLM Agent**: natural language interface for hypotheticals and SQL-style queries
* **User Demo**: Streamlit or notebook showcasing agent responses and insights
* **Executive Summary**: README or PDF with examples and findings

## Project Roles (Dual Track)

### Machine Learning Engineer (MLE)

**Focus**: predictive modelling and API deployment
**Responsibilities**

* Train models for screens, run length, and first-week box office
* Engineer features from global performance and local competition
* Simulate counterfactual launch dates
* Deploy as REST endpoints via FastAPI

**Skills**

* Python (pandas, scikit-learn, XGBoost, FastAPI)
* Feature engineering, evaluation, interpretation
* ML in production

### AI Agent Developer (LLM)

**Focus**: natural language interface and business querying
**Responsibilities**

* Build an agent with **PydanticAI** (or similar)
* Orchestrate simulations via the FastAPI model
* Support SQL-style trend and seasonality queries
* Provide a simple Streamlit or notebook UI

**Skills**

* PydanticAI (or LangChain), prompt design, agent workflows
* SQL and NL querying over structured data
* UX for data tools

## Timeline & Milestones

| Week | Milestone                                                         |
| ---- | ----------------------------------------------------------------- |
| 1    | Kickoff, tech setup, database orientation, plan model + agent     |
| 2    | EDA: distributions, correlations, baseline heuristics             |
| 3    | Baseline models: screens, run length, first-week box office       |
| 4    | Feature enhancement: competitive films (week-before/week-of)      |
| 5    | API development: FastAPI endpoints; request/response schema       |
| 6    | LLM agent prototype with PydanticAI                               |
| 7    | Agent refinement: simulations, SQL-style insights, error handling |
| 8    | Front-end integration: Streamlit or notebook UI                   |
| 9    | Testing and edge cases; real business questions                   |
| 10   | Final polish: executive summary, demo, clean code and docs        |

## Requirements

* 6 weeks, about 8–10 hours per week
* Flexible hours with weekly check-ins
* Work spans technical delivery and storytelling

## What You’ll Gain

* A polished data product simulating real business decisions
* End-to-end experience: modelling, deployment, and LLM integration
* Portfolio-ready case study for full-stack ML + agent workflows
* Insight into how predictive tools shape release and marketing strategy
