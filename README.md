# Restaurant Inventory Operations Agentic System

## Project Description

This project implements a semi-autonomous multi-agent AI workflow designed to support restaurant inventory management, supplier planning, and food waste reduction.

The system receives natural language sales reports from restaurant staff, converts them into structured sales data, updates inventory records, assesses inventory health, and generates operational recommendations for restaurant managers. The workflow models a small Italian restaurant serving a limited menu of pizzas and pasta dishes.

The solution combines large language models, structured data validation, a custom workflow state machine, and human-in-the-loop approval to demonstrate core Agentic AI concepts including orchestration, reasoning, tool use, workflow routing, reflection, and state management.

The primary objective of the system is to assist restaurant managers in making informed operational decisions while maintaining human oversight of all inventory and menu changes.

---

# What Was Built

The project includes:

- A **Sales Intake Agent** that converts natural language manager reports into structured sales records.
- An **Inventory Operations Agent** that calculates ingredient consumption and updates inventory levels.
- A **Reorder Agent** that evaluates inventory shortages and recommends suppliers and replenishment quantities.
- A **Menu Strategy Agent** that recommends menu specials to reduce waste and improve inventory utilization.
- An **Operations Critic Agent** that reviews recommendations and provides approval decisions with confidence scores.
- An **Inventory Orchestrator Agent** that coordinates workflow execution and routing.
- A custom **State Machine** that manages workflow transitions and retry behavior.
- **Human-in-the-loop approval** prior to operational execution.
- A SQLite-backed business database.
- Structured communication using **Pydantic Models**.
- Agent reasoning and structured outputs using **PydanticAI** and **Gemini Flash**.
- Token tracking, cost estimation, workflow metrics, and centralized logging.
- Evaluation tests for individual agents, workflow execution, retry paths, and failure scenarios.

---

# Key Design Decisions

## Multi-Agent Architecture

The workflow was intentionally separated into specialized agents rather than a single monolithic agent.

Benefits include:

- Clear separation of responsibilities
- Improved maintainability
- Improved explainability
- Easier testing and debugging
- Better transparency of decision making

---

## Shared Workflow State

Agents communicate through a shared `WorkflowState` object.

This design allows agents to:

- Read only the information relevant to their task
- Update workflow state without directly calling other agents
- Be tested independently using mocked workflow state objects
- Remain loosely coupled

---

## Pydantic and Structured Outputs

Pydantic models are used throughout the project for:

- Agent outputs
- Workflow state
- Manager approvals
- Workflow responses
- Metrics collection
- Validation

This ensures predictable communication and data consistency across all workflow stages.

---

## PydanticAI and Gemini

PydanticAI is used to:

- Define agent behavior
- Enforce structured outputs
- Integrate Gemini Flash reasoning models
- Simplify prompt management

Gemini Flash performs the reasoning tasks used throughout the workflow while Pydantic validates generated outputs before they enter the workflow.

---

## SQLite for Persistent Data

The workflow operates almost entirely on structured business data including:

- Inventory levels
- Vendor pricing
- Recipes
- Menu items

A relational database was selected because it is lightweight, easy to distribute, and appropriate for the operational nature of the project.

---

## Custom State Machine

A custom state machine manages:

- Workflow transitions
- Conditional routing
- Retry behavior
- Workflow termination

This makes workflow execution explicit and significantly improves traceability, debugging, and evaluation.

---

## Human-in-the-Loop Design

Inventory replenishment and menu changes directly affect restaurant operations and profitability.

The workflow therefore requires explicit manager approval before recommendations are executed.

This design increases safety and operational oversight while still leveraging AI-generated recommendations.

---

## Memory and State Design

The system uses workflow state rather than conversational memory.

Because the project is implemented as a workflow system rather than a chatbot, persistent conversational memory is not required.

Workflow context is maintained through a shared `WorkflowState` object which stores:

- Sales reports
- Inventory assessments
- Reorder recommendations
- Menu recommendations
- Critic reviews
- Manager decisions
- Metrics and workflow outputs

Persistent business data is stored within SQLite.

---

# Project Structure

```text
agentic-workflows-project/

agentic_system.ipynb
data/
-- db_setup.py
-- data_seed.py
-- restaurant.db

libs/
-- agents.py
-- evaluation.py
-- llm.py
-- logging_config.py
-- manager_input.py
-- models.py
-- state.py
-- state_machine.py
-- token_tracker.py
-- tools.py

workflow_image/
-- multi_agent_system.png

requirements.txt
environment.yml
README.md
```

---

# Business Data

The SQLite database contains:

- Inventory records
- Recipes
- Vendor pricing
- Menu items

Database setup and seeding utilities are located in:

```python
data/db_setup.py
data/data_seed.py
```

---

# Notebook Configuration

This project uses PydanticAI with Google's Gemini models.

Near the beginning of the notebook, configure your Gemini API key:

```python
import os

os.environ["GOOGLE_API_KEY"] = ""

# Hide the PydanticAI startup banner

os.environ["PYDANTIC_AI_NO_BANNER"] = "1"

api_key = os.environ.get(
    "GOOGLE_API_KEY"
)
```

Replace the empty string with your own API key:

```python
os.environ["GOOGLE_API_KEY"] = "your_api_key_here"
```

### Important Security Notice

- Do not share your API key.
- Do not commit API keys to GitHub.
- Do not include API keys in reports, screenshots, notebooks, or source code submissions.
- Remove credentials before publishing the repository.

---

# How To Run The Project

## 1. Clone the Repository

```bash
git clone <repository-url>
cd agentic-workflows-project
```

---

## 2. Create a Virtual Environment

Using venv:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

Using Conda:

```bash
conda env create -f environment.yml
conda activate statistical_analysis
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Using Conda:

```bash
conda env create -f environment.yml
```

---

## 4. Launch Jupyter Notebook

```bash
jupyter notebook
```

Open:

```text
agentic_system.ipynb
```

---

## 5. Configure Your API Key

Locate the API configuration cell near the start of the notebook and enter your Gemini API key.

---

## 6. Run The Notebook

Run all notebook cells from top to bottom.

The notebook contains:

- Environment setup
- Agent demonstrations
- Evaluation tests
- Workflow executions
- Failure case demonstrations

---

# Evaluation and Testing

Evaluation functions are provided in:

```python
libs/evaluation.py
```

Implemented evaluations include:

- Sales Intake Agent Test
- Inventory Operations Agent Test
- Reorder Agent Test
- Menu Strategy Agent Test
- Critic Agent Test
- Full Workflow Test
- Workflow Retry Test
- Invalid Manager Input Test
- Empty Sales Report Workflow Test

These tests demonstrate both successful workflows and observed limitations.

# Future Improvements

## Workflow Improvements

- Validate sales reports before workflow execution
- Add workflow entry-point safeguards
- Request revised input when reports contain insufficient sales data
- Persist workflow execution history

## Agent Improvements

- Historical sales forecasting
- More advanced profitability analysis
- Seasonal inventory planning
- RAG based vendor knowledge base
- Parallel execution of agents if sequential not needed

## Reporting and Analytics

The database schema already contains a `workflow_runs` table for future enhancement.

Future versions could track:

- Workflow execution history
- Manager approval rates
- Workflow costs
- Token consumption trends
- Execution performance metrics

---

# Reproducibility

The repository contains:

- Source code
- Database schema
- Seeded business data
- Evaluation tests
- Notebook demonstrations
- Dependency requirements

No credentials or API keys are included.

To regenerate requirements:

```bash
pip freeze > requirements.txt
```

Using Conda

```bash
conda env export > environment.yml
```

This allows the project to be reproduced and evaluated on another machine.
