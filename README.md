# nanoclawbot-evolution Architecture Refactor Bot V-Mk2 - Self-Aware Atomic Vertical Slice Architecture

## Overview

RefactorBot is a full-stack AI agent framework with:
- **8 Vertical Slices** - Each with its own SQLite database and Streamlit UI
- **Master Dashboard** - Streamlit-based unified control panel
- **Self-Aware Slices** - Each slice has its own LLM for meta-reasoning
- **Meta SDLC** - Each slice can self-improve and deploy itself

## Installation

```bash
# Clone the repository
git clone <repo>
cd refactorbot

# Install dependencies
pip install -r requirements.txt

# Run the Master Dashboard
streamlit run master_dashboard/app.py
```

## Project Structure

```
refactorbot/
├── master_core/           # Master Core AI Orchestrator
├── master_dashboard/      # Streamlit Master Dashboard
├── slices/                # 8 Vertical Slices
│   ├── slice_agent_core/
│   ├── slice_tools/
│   ├── slice_memory/
│   ├── slice_communication/
│   ├── slice_session/
│   ├── slice_providers/
│   ├── slice_skills/
│   └── slice_event_bus/
├── providers/             # LLM Providers (OpenRouter)
├── plugins/               # Plugin System
├── infrastructure/        # Observability, Caching
└── data/                  # SQLite Databases
```

## Slices

Each slice is a full-stack module with:
- **Core** - Business logic and services
- **Database** - SQLite with migrations
- **LLM** - Slice's own LLM brain
- **UI** - Streamlit pages
- **API** - REST endpoints
- **Tests** - Comprehensive test suite

## Usage

### Running a Single Slice UI

```bash
# Run Agent Core Slice Dashboard
streamlit run slices/slice_agent_core/ui/pages/dashboard.py
```

### Running the Master Dashboard

```bash
# Run Master Dashboard (controls all slices)
streamlit run master_dashboard/app.py
```

## Configuration

All configuration is managed via environment variables:

```env
OPENROUTER_API_KEY=your_api_key
SLICE_AGENT_CORE_DB=data/slice_agent_core.db
SLICE_TOOLS_DB=data/slice_tools.db
...
```

## License

MIT
