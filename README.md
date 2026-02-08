# 🔮 RefactorBot - Self-Aware Atomic Vertical Slice Architecture

[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org)
[![Tests](https://img.shields.io/badge/Tests-50%20passed-green)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-60%25-yellow)]()

## Overview

RefactorBot is a **Self-Aware Atomic Vertical Slice Architecture** where each slice is a meta-agent with its own LLM capabilities, SQLite database, and dedicated UI. A Master Dashboard built with Streamlit orchestrates and monitors all slices.

## ✨ Features

- **8 Vertical Slices** - Each with its own SQLite database, services, and UI
- **Master Core Orchestrator** - Hierarchical AI orchestration of all slices
- **Self-Aware Slices** - Each slice has SelfImprovementServices for meta-reasoning
- **Meta SDLC CI/CD** - Each slice can self-improve and deploy itself
- **OpenRouter Integration** - Unified multi-model access layer
- **Plugin System** - Discord, Telegram, Feishu, WhatsApp integrations
- **Production Ready** - Full test suite, observability, deployment automation

## 📁 Project Structure

```
refactorbot/
├── master_core/                    # Master Core AI Orchestrator
│   ├── master_core.py              # Core orchestrator (79% coverage)
│   ├── dashboard_connector.py      # Dashboard integration (62%)
│   ├── global_state.py            # Global state (67%)
│   └── resource_allocator.py      # Resource allocation (59%)
├── master_dashboard/               # Streamlit Master Dashboard
│   └── app.py
├── slices/                        # 8 Vertical Slices
│   ├── slice_base.py              # Base classes & protocols (71%)
│   ├── slice_agent/               # Agent Core Slice (41%)
│   ├── slice_tools/               # Tool System Slice (40%)
│   ├── slice_memory/              # Memory System Slice (51%)
│   ├── slice_communication/       # Communication Slice (42%)
│   ├── slice_session/             # Session Slice (42%)
│   ├── slice_providers/          # Providers Slice (38%)
│   ├── slice_skills/             # Skills Slice (38%)
│   ├── slice_eventbus/            # Event Bus Slice (38%)
│   └── meta_sdlc/               # Meta SDLC module
├── providers/                      # LLM Providers
│   └── openrouter_gateway.py      # OpenRouter integration
├── plugins/                       # Plugin System
│   ├── discord/adapter.py
│   ├── telegram/adapter.py
│   ├── feishu/adapter.py
│   └── whatsapp/adapter.py
├── infrastructure/                # Infrastructure
│   ├── observability.py
│   └── security.py
├── deployment/                    # Deployment configs
│   ├── docker/
│   └── kubernetes/
├── tests/                        # Test suite (60% coverage)
│   ├── test_slices.py
│   ├── test_master_core.py
│   ├── test_integration.py
│   └── conftest.py
├── data/                         # SQLite databases
├── pyproject.toml
├── requirements.txt
└── main.py
```

## 🎯 Vertical Slices

| Slice | ID | Coverage | Description |
|-------|-----|----------|-------------|
| **Agent Core** | `slice_agent` | 41% | Core agent logic and chat handling |
| **Tools** | `slice_tools` | 40% | Tool registry and execution |
| **Memory** | `slice_memory` | 51% | Persistent memory storage |
| **Communication** | `slice_communication` | 42% | Channel management |
| **Session** | `slice_session` | 42% | Session handling |
| **Providers** | `slice_providers` | 38% | LLM provider management |
| **Skills** | `slice_skills` | 38% | Skill registry |
| **Event Bus** | `slice_eventbus` | 38% | Event publishing |

Each slice contains:
- `slice.py` - Main slice implementation
- `core/services.py` - Business logic services
- `database/schema.sql` - SQLite schema
- `ui/pages/` - Streamlit UI pages

## 🏗️ Architecture

### Master Core Responsibilities

1. **Slice Lifecycle Management** - Register/unregister, initialize/start/stop slices
2. **Request Routing** - Route operations to appropriate slices
3. **Resource Allocation** - Manage slice quotas and resource usage
4. **Dashboard Integration** - Publish events, track metrics, manage alerts

### Self-Aware Slices

Each slice implements the `AtomicSlice` protocol and includes `SelfImprovementServices`:

```python
from refactorbot.slices import AtomicSlice, SelfImprovementServices

class MySlice(AtomicSlice):
    def __init__(self):
        self.self_improve = SelfImprovementServices(self)
    
    async def self_improve(self, feedback: Dict[str, Any]) -> ImprovementPlan:
        return await self.self_improve.analyze_and_improve(feedback)
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/accessvirus/nanoclawbot-evolution-
cd refactorbot

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v --cov
```

### Running the Application

```bash
# Run Master Dashboard
streamlit run master_dashboard/app.py

# Run a single slice
streamlit run slices/slice_agent/ui/pages/dashboard.py
```

### Programmatic Usage

```python
import asyncio
from refactorbot.master_core import MasterCore
from refactorbot.slices.slice_agent import SliceAgent

async def main():
    core = MasterCore()
    core.register_slice("slice_agent", SliceAgent)
    
    response = await core.execute(
        operation="agent_chat",
        payload={"message": "Hello!"},
        context={}
    )
    print(f"Success: {response.success}")

asyncio.run(main())
```

## 🔌 Plugin System

Available adapters:

| Plugin | Location |
|--------|----------|
| Discord | `plugins/discord/adapter.py` |
| Telegram | `plugins/telegram/adapter.py` |
| Feishu | `plugins/feishu/adapter.py` |
| WhatsApp | `plugins/whatsapp/adapter.py` |

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=refactorbot --cov-report=html

# Run specific test file
python -m pytest tests/test_master_core.py -v
```

### Test Results

| Category | Tests | Coverage |
|----------|-------|----------|
| Unit Tests | 30 | 53% |
| Integration Tests | 20 | 99% |
| **Total** | **50** | **60%** |

## 📊 Coverage by Module

| Module | Coverage |
|--------|----------|
| master_core/master_core.py | 79% |
| master_core/dashboard_connector.py | 62% |
| master_core/global_state.py | 67% |
| master_core/resource_allocator.py | 59% |
| slices/slice_base.py | 71% |
| slices/slice_agent/ | 41% |
| slices/slice_tools/ | 40% |
| slices/slice_memory/ | 51% |
| slices/slice_communication/ | 42% |
| slices/slice_session/ | 42% |
| slices/slice_providers/ | 38% |
| slices/slice_skills/ | 38% |
| slices/slice_eventbus/ | 38% |
| **Overall** | **60%** |

## ⚙️ Configuration

### Environment Variables

```env
# Master Core
OPENROUTER_API_KEY=your_api_key
DATA_DIR=data

# Slice Databases
SLICE_AGENT_DB=data/slice_agent.db
SLICE_TOOLS_DB=data/slice_tools.db
SLICE_MEMORY_DB=data/slice_memory.db
...
```

### Slice Configuration

```python
from refactorbot.slices import SliceConfig

config = SliceConfig(
    slice_id="slice_agent",
    slice_name="Agent Core",
    slice_version="1.0.0",
    database_path="data/slice_agent.db",
    debug=True
)
```

## 🚢 Deployment

### Docker

```bash
cd deployment/docker
docker-compose up -d
```

### Kubernetes

```bash
cd deployment/kubernetes
kubectl apply -f deployment.yaml
```

## 📝 Documentation

- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Full architecture design
- [TODO.md](TODO.md) - Execution plan
- [todo-fixV4.md](todo-fixV4.md) - Phase 4 completion
- [auditV4.md](auditV4.md) - Final audit report

## 🏆 Status

| Metric | Value |
|--------|-------|
| **Grade** | A |
| **Tests** | 50/50 passing |
| **Coverage** | 60% |
| **Slices** | 8/8 implemented |
| **Plugins** | 4/4 available |

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure all tests pass
5. Submit a pull request

---

**Repository:** https://github.com/accessvirus/nanoclawbot-evolution-
