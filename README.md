# 🔮 RefactorBot - Self-Aware Atomic Vertical Slice Architecture

[![Tests](https://img.shields.io/badge/tests-50%20passed-green)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-60%25-yellow)]()
[![Grade](https://img.shields.io/badge/Grade-A-green)]()

## Overview

RefactorBot is a **Self-Aware Atomic Vertical Slice Architecture** where each slice is a meta-agent with its own LLM capabilities, SQLite database, and dedicated UI. A Master Dashboard built with Streamlit orchestrates and monitors all slices.

### Key Features

- **8 Vertical Slices** - Each with its own SQLite database, services, and UI
- **Master Core Orchestrator** - Hierarchical AI orchestration of all slices
- **Self-Aware Slices** - Each slice has SelfImprovementServices for meta-reasoning
- **Meta SDLC CI/CD** - Each slice can self-improve and deploy itself
- **OpenRouter Integration** - Unified multi-model access layer
- **Plugin System** - Discord, Telegram, Feishu, WhatsApp integrations
- **Production Ready** - Full test suite, observability, deployment automation

---

## 📁 Project Structure

```
refactorbot/
├── master_core/                    # Master Core AI Orchestrator
│   ├── master_core.py              # Core orchestrator (79% coverage)
│   ├── dashboard_connector.py      # Dashboard integration (62% coverage)
│   ├── global_state.py             # Global state management (67% coverage)
│   └── resource_allocator.py       # Resource allocation (59% coverage)
│
├── master_dashboard/               # Streamlit Master Dashboard
│   └── app.py                     # Main dashboard app
│
├── slices/                        # 8 Vertical Slices
│   ├── slice_base.py              # Base classes & protocols (71% coverage)
│   ├── slice_agent/               # Agent Core Slice
│   │   ├── slice.py               # Core slice implementation
│   │   └── __init__.py
│   ├── slice_tools/               # Tool System Slice
│   │   ├── slice.py
│   │   ├── core/services.py
│   │   ├── database/schema.sql
│   │   └── ui/pages/
│   ├── slice_memory/              # Memory System Slice
│   │   ├── slice.py
│   │   ├── core/services.py
│   │   ├── database/schema.sql
│   │   └── ui/pages/
│   ├── slice_communication/       # Communication Slice
│   │   ├── slice.py
│   │   ├── core/services.py
│   │   ├── database/schema.sql
│   │   └── ui/pages/
│   ├── slice_session/             # Session Slice
│   │   ├── slice.py
│   │   ├── core/services.py
│   │   ├── database/schema.sql
│   │   └── ui/pages/
│   ├── slice_providers/           # Providers Slice
│   │   ├── slice.py
│   │   ├── core/services.py
│   │   ├── database/schema.sql
│   │   └── ui/pages/
│   ├── slice_skills/              # Skills Slice
│   │   ├── slice.py
│   │   ├── core/services.py
│   │   ├── database/schema.sql
│   │   └── ui/pages/
│   ├── slice_eventbus/            # Event Bus Slice
│   │   ├── slice.py
│   │   ├── core/services.py
│   │   └── __init__.py
│   └── meta_sdlc/                 # Meta SDLC module
│
├── providers/                      # LLM Providers
│   └── openrouter_gateway.py       # OpenRouter integration
│
├── plugins/                       # Plugin System
│   ├── discord/adapter.py
│   ├── telegram/adapter.py
│   ├── feishu/adapter.py
│   └── whatsapp/adapter.py
│
├── infrastructure/                # Infrastructure
│   ├── observability.py
│   └── security.py
│
├── deployment/                    # Deployment configs
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   └── kubernetes/
│       └── deployment.yaml
│
├── data/                         # SQLite databases
├── tests/                        # Test suite (60% coverage)
│   ├── test_slices.py           # Unit tests (99% coverage)
│   ├── test_master_core.py      # Core tests (100% coverage)
│   ├── test_integration.py      # Integration tests (99% coverage)
│   └── conftest.py
│
├── pyproject.toml
├── requirements.txt
└── main.py
```

---

## 🎯 Vertical Slices

### Slice Overview

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

### Each Slice Contains

```
slice_name/
├── slice.py              # Main slice implementation
├── core/
│   └── services.py       # Business logic services
├── database/
│   ├── schema.sql        # SQLite schema
│   └── db_manager.py     # Database manager (if needed)
└── ui/pages/
    ├── dashboard.py      # Main dashboard
    ├── analytics.py      # Analytics page
    └── config.py        # Configuration page
```

---

## 🏗️ Master Core Architecture

### MasterCore Responsibilities

1. **Slice Lifecycle Management**
   - Register/unregister slices
   - Initialize/start/stop slices
   - Health monitoring

2. **Request Routing**
   - Route operations to appropriate slices
   - Handle cross-slice communication
   - Error handling and recovery

3. **Resource Allocation**
   - Manage slice quotas
   - Track resource usage
   - Load balancing

4. **Dashboard Integration**
   - Publish events to dashboard
   - Track execution metrics
   - Alert management

### Orchestration Flow

```python
from refactorbot.master_core import MasterCore, OrchestrationRequest

# Create orchestrator
core = MasterCore()

# Register a slice
core.register_slice("slice_agent", SliceAgent)

# Execute an operation
response = await core.execute(
    operation="agent_chat",
    payload={"message": "Hello"},
    context={}
)
```

---

## 🔧 Self-Aware Slices

Each slice implements the `AtomicSlice` protocol and includes `SelfImprovementServices`:

```python
from refactorbot.slices import AtomicSlice, SelfImprovementServices

class MySlice(AtomicSlice):
    def __init__(self):
        self.self_improve = SelfImprovementServices(self)
    
    async def self_improve(self, feedback: Dict[str, Any]) -> ImprovementPlan:
        """Analyze feedback and create improvement plan."""
        return await self.self_improve.analyze_and_improve(feedback)
```

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/accessvirus/nanoclawbot-evolution-
cd refactorbot

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v --cov

# Run Master Dashboard
streamlit run master_dashboard/app.py
```

---

## 🚀 Usage

### Running a Single Slice UI

```bash
# Run Agent Core Slice Dashboard
streamlit run slices/slice_agent/ui/pages/dashboard.py

# Run Memory Slice Dashboard
streamlit run slices/slice_memory/ui/pages/dashboard.py
```

### Running the Master Dashboard

```bash
# Run Master Dashboard (controls all slices)
streamlit run master_dashboard/app.py
```

### Programmatic Usage

```python
import asyncio
from refactorbot.master_core import MasterCore
from refactorbot.slices.slice_agent import SliceAgent

async def main():
    # Create orchestrator
    core = MasterCore()
    
    # Register slice
    core.register_slice("slice_agent", SliceAgent)
    
    # Execute operation
    response = await core.execute(
        operation="agent_chat",
        payload={"message": "Hello, World!"},
        context={}
    )
    
    print(f"Success: {response.success}")
    print(f"Response: {response.payload}")

asyncio.run(main())
```

---

## 🔌 Plugin System

### Available Adapters

- **Discord** - `plugins/discord/adapter.py`
- **Telegram** - `plugins/telegram/adapter.py`
- **Feishu** - `plugins/feishu/adapter.py`
- **WhatsApp** - `plugins/whatsapp/adapter.py`

### Using Plugins

```python
from plugins.discord import DiscordAdapter

adapter = DiscordAdapter(token="your_token")
await adapter.connect()
await adapter.send_message("channel_id", "Hello from RefactorBot!")
```

---

## 🧪 Testing

### Test Suite

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

---

## 📊 Coverage by Module

| Module | Coverage | Status |
|--------|----------|--------|
| master_core/master_core.py | 79% | ✅ |
| master_core/dashboard_connector.py | 62% | ✅ |
| master_core/global_state.py | 67% | ✅ |
| master_core/resource_allocator.py | 59% | ✅ |
| slices/slice_base.py | 71% | ✅ |
| slices/slice_memory/core/services.py | 21% | ⚠️ |
| Overall | 60% | ✅ |

---

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

Each slice can be configured via `SliceConfig`:

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

---

## 📁 Data Directory

The `data/` directory contains:

- `master.db` - Master Core global state
- `slice_*.db` - Individual slice databases
- `dashboard_*.jsonl` - Dashboard events, alerts, metrics
- `dashboard_state.json` - Dashboard state

---

## 🚢 Deployment

### Docker

```bash
# Build and run with Docker Compose
cd deployment/docker
docker-compose up -d
```

### Kubernetes

```bash
# Deploy to Kubernetes
cd deployment/kubernetes
kubectl apply -f deployment.yaml
```

---

## 📝 Documentation

- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Full architecture design
- [TODO.md](TODO.md) - Execution plan
- [todo-fixV4.md](todo-fixV4.md) - Phase 4 completion
- [auditV4.md](auditV4.md) - Final audit report

---

## 🏆 Status

| Metric | Value |
|--------|-------|
| **Grade** | A |
| **Tests** | 50/50 passing |
| **Coverage** | 60% |
| **Slices** | 8/8 implemented |
| **Plugins** | 4/4 available |

---

## 📄 License

MIT License - See LICENSE file for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure all tests pass
5. Submit a pull request

---

**Repository:** https://github.com/accessvirus/nanoclawbot-evolution-
