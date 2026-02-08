# 🔮 REFACTORBOT V2 - VERTICAL SLICE ARCHITECTURE IMPLEMENTATION

## 📋 Executive Summary

RefactorBot is a **Self-Aware Atomic Vertical Slice Architecture** where each slice is a meta-agent with its own LLM capabilities, SQLite database, and dedicated UI. A Master Dashboard built with Streamlit orchestrates and monitors all slices.

### Key Objectives

- **Atomic Responsibility**: Each slice owns a single domain concern completely
- **Full-Stack Slices**: Each slice has its own SQLite database and UI
- **Self-Awareness**: Each slice has SelfImprovementServices for meta-reasoning
- **Hierarchical Orchestration**: Master Core AI controls and coordinates all slices
- **Meta SDLC**: Each slice can self-improve, test, and deploy itself
- **Master Dashboard**: Streamlit-based unified UI for all slices
- **Production Ready**: Full test suite (50 tests, 60% coverage), observability
- **Dual LLM Gateways**: OpenRouter + LiteLLM (50+ providers)
- **Tool Handlers**: File system, shell execution, web search/fetch
- **Scheduling System**: Cron-based scheduling with heartbeat monitoring

---

## 🏗️ Architecture Overview

### High-Level System Architecture

```
                          ┌─────────────────────────────────────┐
                          │     Master Dashboard (Streamlit)     │
                          │   ┌─────────┬─────────┬─────────┐   │
                          │   │ Overview│ Analytics│ Control │   │
                          │   └─────────┴─────────┴─────────┘   │
                          └──────────────┬──────────────────────┘
                                         │
                          ┌──────────────▼──────────────────────┐
                          │        Master Core Orchestrator      │
                          │  ┌──────────┬──────────┬────────┐  │
                          │  │ Global   │ Resource │DashBoard│  │
                          │  │ State    │ Allocator│Connector│  │
                          │  │ Master   │         │        │  │
                          │  │ Chat     │         │        │  │
                          │  └──────────┴──────────┴────────┘  │
                          └──────────────┬──────────────────────┘
                                         │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
         ▼                          ▼                          ▼
 ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
 │ slice_agent   │      │ slice_tools   │      │ slice_memory  │
 │  - core/      │      │  - core/      │      │  - core/     │
 │  - ui/pages/  │      │  - handlers/  │      │  - ui/pages/  │
 │               │      │    - file     │      │               │
 │               │      │    - exec    │      │               │
 │               │      │    - web     │      │               │
 └───────────────┘      └───────────────┘      └───────────────┘
         │                          │                          │
         ▼                          ▼                          ▼
 ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
 │slice_commun.. │      │slice_session  │      │slice_providers│
 │  - core/      │      │  - core/     │      │  - core/     │
 │  - ui/pages/  │      │  - ui/pages/  │      │- litellm GW  │
 └───────────────┘      └───────────────┘      └───────────────┘
         │                          │                          │
         ▼                          ▼                          ▼
 ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
 │slice_skills   │      │slice_eventbus │      │slice_scheduling│
 │  - core/      │      │  - core/      │      │  - core/     │
 │  - ui/pages/  │      └───────────────┘      │- cron sched  │
 └───────────────┘                             │- heartbeat  │
                                               └───────────────┘
```

### Hierarchical Orchestration

```
Level 0: Master Dashboard (Streamlit)
    │
    ├── Admin Controls
    ├── Metrics View
    └── Logs View
            │
            ▼
Level 0: Master Core AI
    │
    ├── Global State Manager
    ├── Resource Allocator
    ├── Dashboard Connector
    └── Master Chat Orchestrator
            │
    ┌───────┴───────┬───────┬───────┬───────┬───────┬───────┬───────┬───────┐
    ▼               ▼       ▼       ▼       ▼       ▼       ▼       ▼       ▼
Level 1: Domain Slices (9 total)
│
├── slice_agent     → SQLite: data/slice_agent.db
├── slice_tools    → SQLite: data/slice_tools.db
│   └── handlers/  → file_handlers.py, exec_handler.py, web_handlers.py
├── slice_memory   → SQLite: data/slice_memory.db
├── slice_communication → SQLite: data/slice_communication.db
├── slice_session  → SQLite: data/slice_session.db
├── slice_providers → SQLite: data/slice_providers.db
│   └── litellm_gateway.py (50+ providers)
├── slice_skills   → SQLite: data/slice_skills.db
├── slice_eventbus  → In-memory event bus
└── slice_scheduling → SQLite: data/slice_scheduling.db
    └── core/services.py (cron, heartbeat)
```

---

## 🎯 Vertical Slice Definition

### Slice Contract Interface

Every vertical slice MUST implement the `AtomicSlice` protocol:

```python
class AtomicSlice(Protocol):
    """Protocol that all atomic slices must implement."""
    
    @property
    def slice_id(self) -> str: ...
    @property
    def slice_name(self) -> str: ...
    @property
    def slice_version(self) -> str: ...
    @property
    def config(self) -> SliceConfig: ...
    
    async def initialize(self) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def shutdown(self) -> None: ...
    async def health_check(self) -> HealthStatus: ...
    async def execute(self, operation: str, payload: Dict, context: Dict) -> SliceResponse: ...
    async def get_capabilities(self) -> SliceCapabilities: ...
    async def self_improve(self, feedback: ImprovementFeedback) -> ImprovementPlan: ...
    async def run_self_diagnostics(self) -> Dict[str, Any]: ...
```

### Base Classes

#### SliceConfig
```python
class SliceConfig(BaseSettings):
    slice_id: str = "base_slice"
    slice_name: str = "Base Slice"
    slice_version: str = "1.0.0"
    database_path: str = "data/base_slice.db"
    debug: bool = False
```

#### SliceRequest
```python
class SliceRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slice_id: str = ""
    operation: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

#### SliceResponse
```python
class SliceResponse(BaseModel):
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    success: bool
    payload: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### SliceDatabase
```python
class SliceDatabase:
    def __init__(self, db_path: str): ...
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def initialize(self) -> None: ...
    async def execute(self, query: str, params: tuple = ()) -> Any: ...
    async def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict]: ...
    async def fetchall(self, query: str, params: tuple = ()) -> List[Dict]: ...
```

### SelfImprovementServices

Each slice includes self-improvement capabilities:

```python
class SelfImprovementServices:
    """Common self-improvement services for all slices."""
    
    def __init__(self, slice: "AtomicSlice"): ...
    
    async def analyze_and_improve(self, feedback: Dict[str, Any]) -> List[Dict[str, Any]]: ...
    async def run_diagnostics(self) -> Dict[str, Any]: ...
```

---

## 🔷 Full-Stack Slice Specifications

### Slice 1: Agent Core Slice (`slice_agent`)

**Location**: `refactorbot/slices/slice_agent/`

**Database**: `data/slice_agent.db` (created on first run)

**Responsibilities**:
- Core agent logic and chat handling
- Request/response processing
- Context management

**Structure**:
```
slice_agent/
├── slice.py              # Main slice implementation
├── core/
│   └── services.py      # Agent services
└── __init__.py
```

**Coverage**: 41%

---

### Slice 2: Tools Slice (`slice_tools`)

**Location**: `refactorbot/slices/slice_tools/`

**Database**: `data/slice_tools.db`

**Responsibilities**:
- Tool registry
- Tool execution
- Tool metadata management
- **File Handlers** - File read/write/list/search
- **Exec Handler** - Shell execution with security
- **Web Handlers** - Web search and fetch

**Structure**:
```
slice_tools/
├── slice.py              # Main slice
├── core/
│   ├── services.py      # Tool services
│   └── handlers/
│       ├── __init__.py
│       ├── file_handlers.py    # read_file, write_to_file, search_and_replace, list_files
│       ├── exec_handler.py     # execute_command with security guards
│       └── web_handlers.py     # web_search, web_fetch
├── database/
│   ├── schema.sql       # SQLite schema
│   └── db_manager.py    # Database manager
└── ui/pages/
    ├── dashboard.py
    ├── analytics.py
    └── config.py
```

**Coverage**: 40%

**Tool Handlers Implemented**:

| Handler | File | Tools |
|---------|------|-------|
| File Handlers | `file_handlers.py` | read_file, write_to_file, search_and_replace, list_files, delete_file |
| Exec Handler | `exec_handler.py` | execute_command, list_files, delete_file |
| Web Handlers | `web_handlers.py` | web_search, web_fetch |

---

### Slice 3: Memory Slice (`slice_memory`)

**Location**: `refactorbot/slices/slice_memory/`

**Database**: `data/slice_memory.db`

**Responsibilities**:
- Persistent memory storage
- Memory retrieval
- Memory consolidation

**Structure**:
```
slice_memory/
├── slice.py              # Main slice
├── core/
│   └── services.py      # Memory services
├── database/
│   ├── schema.sql       # SQLite schema
│   └── db_manager.py    # Database manager
└── ui/pages/
    ├── dashboard.py
    ├── analytics.py
    └── config.py
```

**Coverage**: 51%

---

### Slice 4: Communication Slice (`slice_communication`)

**Location**: `refactorbot/slices/slice_communication/`

**Database**: `data/slice_communication.db`

**Responsibilities**:
- Channel management
- Message routing
- Communication templates

**Structure**:
```
slice_communication/
├── slice.py              # Main slice
├── core/
│   └── services.py      # Communication services
├── database/
│   └── schema.sql       # SQLite schema
└── ui/pages/
    ├── dashboard.py
    ├── analytics.py
    └── config.py
```

**Coverage**: 42%

---

### Slice 5: Session Slice (`slice_session`)

**Location**: `refactorbot/slices/slice_session/`

**Database**: `data/slice_session.db`

**Responsibilities**:
- Session management
- Session state tracking
- Session metadata

**Structure**:
```
slice_session/
├── slice.py              # Main slice
├── core/
│   └── services.py      # Session services
├── database/
│   └── schema.sql       # SQLite schema
└── ui/pages/
    ├── dashboard.py
    ├── analytics.py
    └── config.py
```

**Coverage**: 42%

---

### Slice 6: Providers Slice (`slice_providers`)

**Location**: `refactorbot/slices/slice_providers/`

**Database**: `data/slice_providers.db`

**Responsibilities**:
- LLM provider management
- Model configuration
- Cost tracking
- **LiteLLM Gateway** - 50+ providers

**Structure**:
```
slice_providers/
├── slice.py              # Main slice
├── core/
│   └── services.py      # Provider services
├── database/
│   └── schema.sql       # SQLite schema
└── ui/pages/
    ├── dashboard.py
    ├── analytics.py
    └── config.py
```

**Coverage**: 38%

**LiteLLM Gateway** (`providers/litellm_gateway.py`):

Supports 50+ providers:
- OpenAI, Anthropic, Google, Mistral
- Azure, AWS Bedrock, VertexAI
- HuggingFace, Cohere, AI21
- DeepInfra, Perplexity, Together AI
- And many more...

---

### Slice 7: Skills Slice (`slice_skills`)

**Location**: `refactorbot/slices/slice_skills/`

**Database**: `data/slice_skills.db`

**Responsibilities**:
- Skill registry
- Skill execution
- Skill metadata

**Structure**:
```
slice_skills/
├── slice.py              # Main slice
├── core/
│   └── services.py      # Skill services
├── database/
│   └── schema.sql       # SQLite schema
└── ui/pages/
    ├── dashboard.py
    ├── analytics.py
    └── config.py
```

**Coverage**: 38%

---

### Slice 8: Event Bus Slice (`slice_eventbus`)

**Location**: `refactorbot/slices/slice_eventbus/`

**Database**: In-memory event bus

**Responsibilities**:
- Event publishing
- Event subscription
- Event routing

**Structure**:
```
slice_eventbus/
├── slice.py              # Main slice
├── core/
│   └── services.py      # Event services
└── __init__.py
```

**Coverage**: 38%

---

### Slice 9: Scheduling Slice (`slice_scheduling`) - NEW

**Location**: `refactorbot/slices/slice_scheduling/`

**Database**: `data/slice_scheduling.db`

**Responsibilities**:
- Cron-based task scheduling
- Heartbeat monitoring
- Workflow support
- Execution history
- Alerting

**Structure**:
```
slice_scheduling/
├── slice.py              # Main slice
├── core/
│   ├── __init__.py
│   └── services.py      # Scheduling services (cron, heartbeat)
└── __init__.py
```

**Features**:
- **Cron Scheduling**: Cron expression-based task scheduling
- **Heartbeat Monitoring**: Task health and liveness checks
- **Workflow Support**: Multi-step task workflows
- **Execution History**: Track task execution results
- **Alerting**: Notification on failures

---

## 🏗️ Master Core Implementation

### MasterCore Class

**Location**: `refactorbot/master_core/master_core.py` (177 lines, 79% coverage)

```python
class MasterCore:
    """Master Core AI Orchestrator."""
    
    @property
    def orchestrator_id(self) -> str: ...
    @property
    def orchestrator_name(self) -> str: ...
    @property
    def orchestrator_version(self) -> str: ...
    
    def __init__(
        self,
        data_dir: str = "data",
        global_state_db: str = "data/master.db",
        openrouter_api_key: Optional[str] = None
    ): ...
    
    async def health_check(self) -> Dict[str, Any]: ...
    
    # Slice Management
    def register_slice(self, slice_id: str, slice_class: Type, quota: ResourceQuota = None): ...
    def unregister_slice(self, slice_id: str) -> bool: ...
    async def initialize_slice(self, slice_id: str) -> bool: ...
    async def start_slice(self, slice_id: str) -> bool: ...
    async def stop_slice(self, slice_id: str) -> bool: ...
    async def shutdown(self) -> None: ...
    
    # Orchestration
    async def orchestrate(self, request: OrchestrationRequest) -> OrchestrationResponse: ...
```

### MasterChat Class - NEW

**Location**: `refactorbot/master_core/master_chat.py`

```python
class MasterChat:
    """Chat orchestration across multiple slices."""
    
    def __init__(self, master_core: MasterCore): ...
    
    async def process_message(
        self,
        message: str,
        context: Dict[str, Any] = None
    ) -> ChatResponse: ...
    
    async def route_to_slice(
        self,
        slice_id: str,
        operation: str,
        payload: Dict
    ) -> SliceResponse: ...
```

### Global State Manager

**Location**: `refactorbot/master_core/global_state.py` (67% coverage)

### Resource Allocator

**Location**: `refactorbot/master_core/resource_allocator.py` (59% coverage)

### Dashboard Connector

**Location**: `refactorbot/master_core/dashboard_connector.py` (62% coverage)

---

## 🔌 Plugin System

### Plugin Base Classes

**Location**: `refactorbot/plugins/plugin_base.py`

```python
class PluginAdapter(Protocol):
    """Base protocol for all plugins."""
    
    @property
    def plugin_id(self) -> str: ...
    @property
    def plugin_name(self) -> str: ...
    @property
    def plugin_version(self) -> str: ...
    
    async def initialize(self, config: Dict[str, Any]) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def health_check(self) -> HealthStatus: ...

class MessageAdapter(PluginAdapter):
    """Protocol for messaging capabilities."""
    
    async def send_message(self, channel: str, message: str) -> MessageResult: ...
    async def receive_message(self, channel: str) -> Optional[Message]: ...
    async def handle_callback(self, callback_data: Dict) -> Response: ...

class ChannelAdapter(MessageAdapter):
    """Channel-specific adapter implementation."""
    
    def __init__(self, channel_config: Dict[str, Any]): ...
    
    # Lifecycle
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    
    # Message handling
    async def send(self, message: OutgoingMessage) -> MessageResult: ...
    async def receive(self) -> List[IncomingMessage]: ...
```

### Implemented Adapters

| Adapter | Location | Status |
|---------|----------|--------|
| Discord | `plugins/discord/adapter.py` | ✅ Implemented |
| Telegram | `plugins/telegram/adapter.py` | ✅ Implemented |
| Feishu | `plugins/feishu/adapter.py` | ✅ Implemented |
| WhatsApp | `plugins/whatsapp/adapter.py` | ✅ Implemented |

---

## 🤖 LLM Gateways

### OpenRouter Gateway

**Location**: `refactorbot/providers/openrouter_gateway.py`

Unified access to 100+ models through OpenRouter.

### LiteLLM Gateway - NEW

**Location**: `refactorbot/providers/litellm_gateway.py`

```python
class LiteLLMGateway:
    """Unified gateway for 50+ LLM providers."""
    
    SUPPORTED_PROVIDERS = [
        "openai", "anthropic", "google", "mistral",
        "azure", "bedrock", "vertexai", "huggingface",
        "cohere", "ai21", "deepinfra", "perplexity",
        "togetherai", "groq", "cloudflare", "deepseek",
        "xai", "nvidia", "cerebras", "fireworks",
        "openrouter", "palmer", "custom", "local",
        # ... and 30+ more
    ]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_provider: str = "openai"
    ): ...
    
    async def complete(
        self,
        model: str,
        messages: List[Dict],
        provider: Optional[str] = None,
        **kwargs
    ) -> LLMResponse: ...
    
    async def stream_complete(
        self,
        model: str,
        messages: List[Dict],
        provider: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]: ...
```

---

## ⏰ Tool Handlers Implementation

### File Handlers

**Location**: `refactorbot/slices/slice_tools/core/handlers/file_handlers.py`

```python
class FileHandlers:
    """File system operations handlers."""
    
    async def read_file(
        self,
        path: str,
        line_ranges: Optional[List[Tuple[int, int]]] = None
    ) -> FileResult: ...
    
    async def write_to_file(
        self,
        path: str,
        content: str,
        overwrite: bool = False
    ) -> FileResult: ...
    
    async def search_and_replace(
        self,
        path: str,
        operations: List[SearchReplaceOperation]
    ) -> FileResult: ...
    
    async def list_files(
        self,
        path: str,
        recursive: bool = False
    ) -> ListResult: ...
    
    async def delete_file(self, path: str) -> DeleteResult: ...
```

### Exec Handler

**Location**: `refactorbot/slices/slice_tools/core/handlers/exec_handler.py`

```python
class ExecHandler:
    """Shell execution handler with security guards."""
    
    async def execute_command(
        self,
        command: str,
        timeout: int = 30,
        environment: Optional[Dict] = None,
        working_directory: Optional[str] = None
    ) -> ExecResult: ...
    
    # Security features:
    # - Command whitelisting
    # - Dangerous command blocking
    # - Output sanitization
    # - Environment sandboxing
```

### Web Handlers

**Location**: `refactorbot/slices/slice_tools/core/handlers/web_handlers.py`

```python
class WebHandlers:
    """Web search and fetch handlers."""
    
    async def web_search(
        self,
        query: str,
        num_results: int = 10,
        timeout: int = 10
    ) -> SearchResult: ...
    
    async def web_fetch(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict] = None,
        timeout: int = 10
    ) -> FetchResult: ...
```

---

## ⏰ Scheduling System

### Scheduling Slice

**Location**: `refactorbot/slices/slice_scheduling/core/services.py`

```python
class SchedulingServices:
    """Cron-based task scheduling and heartbeat monitoring."""
    
    async def schedule_task(
        self,
        task_id: str,
        cron_expression: str,
        task_func: Callable,
        **kwargs
    ) -> SchedulingResult: ...
    
    async def heartbeat_check(
        self,
        task_id: str,
        interval: int = 30
    ) -> HeartbeatStatus: ...
    
    async def cancel_task(self, task_id: str) -> bool: ...
    
    async def get_task_history(
        self,
        task_id: str,
        limit: int = 100
    ) -> List[ExecutionRecord]: ...
```

---

## 📋 Audit Documentation

### Master Audit Report

**Location**: `refactorbot/masteraudit.md`

Comprehensive audit of the entire codebase with:
- Architecture analysis
- Code quality assessment
- Security review
- Performance analysis
- Recommendations

### Module Audit Files

Every Python module has a corresponding `.md` audit file:

| Module | Audit File |
|--------|------------|
| `main.py` | `main.py.md` |
| `master_core/` | `master_core/__init__.py.md`, `master_core/master_core.py.md`, etc. |
| `slices/` | `slices/__init__.py.md`, `slices/slice_*.py.md`, etc. |
| `providers/` | `providers/__init__.py.md`, `providers/openrouter_gateway.py.md`, etc. |
| `plugins/` | `plugins/__init__.py.md`, `plugins/plugin_base.py.md`, etc. |
| `infrastructure/` | `infrastructure/__init__.py.md`, etc. |

Each audit file includes:
- File overview
- Code analysis
- Quality assessment
- Security review
- Performance analysis
- Compliance checklist
- **Critical Improvements** section

---

## 📊 Status Summary

| Metric | Value |
|--------|-------|
| **Grade** | A- |
| **Total Slices** | 9 |
| **Implemented Slices** | 9/9 |
| **Test Coverage** | 60% |
| **Tests Passing** | 50/50 |
| **LLM Gateways** | 2 (OpenRouter, LiteLLM) |
| **Plugin Adapters** | 4 (Discord, Telegram, Feishu, WhatsApp) |
| **Tool Handlers** | 3 (File, Exec, Web) |
| **Audit Files** | 80+ |

---

## 🔄 Implementation Roadmap

### Completed (v2.0)
- ✅ Vertical Slice Architecture (9 slices)
- ✅ Master Core Orchestrator
- ✅ Master Dashboard (Streamlit)
- ✅ Dual LLM Gateways
- ✅ Plugin System (4 adapters)
- ✅ Tool Handlers (File, Exec, Web)
- ✅ Scheduling System
- ✅ Comprehensive Audit Documentation

### Future Enhancements
- [] Increase test coverage to 80%
- [] Add distributed slicing
- [] Implement workflow engine
- [] Add more LLM providers
- [] Improve security audit
- [] Add performance benchmarking

---

**Last Updated**: 2026-02-08
**Version**: 2.0
**Grade**: A-
