# 📋 REFACTORBOT V2 REFACTORING - EXECUTION PLAN

## Phase 1: Foundation Setup

### 1.1 Project Structure Creation
- [ ] Create `refactorbot/master_core/` directory with master core modules
- [ ] Create `refactorbot/master_dashboard/` directory for Streamlit dashboard
- [ ] Create `refactorbot/slices/` directory structure
- [ ] Create `refactorbot/slices/slice_base.py` - AtomicSlice abstract base class
- [ ] Create `refactorbot/providers/` directory for OpenRouter integration
- [ ] Create `refactorbot/plugins/` directory structure
- [ ] Create `refactorbot/infrastructure/` for observability and caching
- [ ] Create `refactorbot/data/` directory for SQLite databases
- [ ] Create `refactorbot/tests/` directory structure

### 1.2 Base Classes and Protocols
- [ ] Implement `AtomicSlice` protocol in `slice_base.py`
- [ ] Implement `SliceDatabase` class for SQLite management
- [ ] Implement `SliceContext` class for slice initialization
- [ ] Implement `SliceRequest` and `SliceResponse` classes
- [ ] Implement `SliceCapabilities` class
- [ ] Implement `ImprovementFeedback` and `ImprovementPlan` classes

### 1.3 Configuration System
- [ ] Create `refactorbot/config/config.py` - Main configuration loader
- [ ] Create environment variable support for all slice databases
- [ ] Implement YAML/JSON config parsing with validation

---

## Phase 2: Master Core AI Orchestrator

### 2.1 Global State Management
- [ ] Implement `refactorbot/master_core/global_state.py` - GlobalStateManager
- [ ] Create `refactorbot/data/master.db` - Master SQLite database
- [ ] Implement state persistence to master database
- [ ] Implement state synchronization across slices

### 2.2 Resource Allocator
- [ ] Implement `refactorbot/master_core/resource_allocator.py` - ResourceAllocator
- [ ] Implement memory allocation limits per slice
- [ ] Implement CPU quota management

### 2.3 Slice Orchestrator
- [ ] Implement `refactorbot/master_core/master_core.py` - MasterCoreAI
- [ ] Implement `refactorbot/master_core/dashboard_connector.py` - Dashboard integration
- [ ] Implement request routing to appropriate slices
- [ ] Implement cross-slice communication protocol

### 2.4 Meta Scheduler
- [ ] Implement `refactorbot/master_core/meta_scheduler.py` - MetaScheduler
- [ ] Implement slice lifecycle management
- [ ] Implement self-improvement scheduling

---

## Phase 3: Master Dashboard (Streamlit)

### 3.1 Dashboard Infrastructure
- [ ] Create `refactorbot/master_dashboard/app.py` - Main Streamlit entry
- [ ] Implement dashboard theme configuration
- [ ] Create sidebar navigation component
- [ ] Create metrics grid component

### 3.2 Dashboard Pages
- [ ] Implement `01_overview.py` - All slices status overview
- [ ] Implement `02_analytics.py` - Cross-slice analytics
- [ ] Implement `03_control.py` - Slice management control panel
- [ ] Implement `04_logs.py` - Unified logging view
- [ ] Implement `05_settings.py` - Global settings

### 3.3 Dashboard Integration
- [ ] Implement slice connector for dashboard
- [ ] Implement real-time metrics updates
- [ ] Implement cross-slice data aggregation

---

## Phase 4: OpenRouter Integration Layer

### 4.1 OpenRouter Gateway
- [ ] Implement `refactorbot/providers/openrouter_gateway.py`
- [ ] Implement API client with proper authentication
- [ ] Implement request/response handling
- [ ] Implement streaming support

### 4.2 Model Router
- [ ] Implement `refactorbot/providers/model_router.py`
- [ ] Implement task complexity assessment
- [ ] Implement model capability matching
- [ ] Implement cost-based routing

### 4.3 Cost Tracker
- [ ] Implement `refactorbot/providers/cost_tracker.py`
- [ ] Implement token usage tracking
- [ ] Implement budget management per slice
- [ ] Implement cost reporting for dashboard

---

## Phase 5: Vertical Slice Implementation

### 5.1 Slice 1: Agent Core Slice
**Database**: `data/slice_agent_core.db`

- [ ] Create `refactorbot/slices/slice_agent_core/pyproject.toml`
- [ ] Create `slice.yaml` configuration
- [ ] Implement `core/models.py` - Domain models
- [ ] Implement `core/services.py` - Business services
- [ ] Implement `database/db_manager.py` - SQLite manager
- [ ] Implement `database/schema.sql` - Database schema
- [ ] Implement `database/repositories/` - Data access layer
- [ ] Implement `llm/provider.py` - LLM provider
- [ ] Implement `llm/meta_reasoning.py` - Meta-cognition
- [ ] Implement `ui/pages/dashboard.py` - Main dashboard
- [ ] Implement `ui/pages/analytics.py` - Analytics
- [ ] Implement `ui/pages/config.py` - Configuration
- [ ] Write unit tests

### 5.2 Slice 2: Tool System Slice
**Database**: `data/slice_tools.db`

- [ ] Create slice structure
- [ ] Implement tool registry SQLite schema
- [ ] Implement tool execution logging
- [ ] Implement UI for tool management
- [ ] Write tests

### 5.3 Slice 3: Memory System Slice
**Database**: `data/slice_memory.db`

- [ ] Create slice structure
- [ ] Implement memory storage SQLite schema
- [ ] Implement memory retrieval and consolidation
- [ ] Implement UI for memory browser
- [ ] Write tests

### 5.4 Slice 4: Communication Slice
**Database**: `data/slice_communication.db`

- [ ] Create slice structure
- [ ] Implement channel management SQLite schema
- [ ] Implement message logging
- [ ] Implement UI for channel management
- [ ] Write tests

### 5.5 Slice 5: Session Management Slice
**Database**: `data/slice_session.db`

- [ ] Create slice structure
- [ ] Implement session SQLite schema
- [ ] Implement conversation history
- [ ] Implement UI for session management
- [ ] Write tests

### 5.6 Slice 6: Providers Slice
**Database**: `data/slice_providers.db`

- [ ] Create slice structure
- [ ] Implement provider SQLite schema
- [ ] Implement cost tracking tables
- [ ] Implement UI for provider management
- [ ] Write tests

### 5.7 Slice 7: Skills Engine Slice
**Database**: `data/slice_skills.db`

- [ ] Create slice structure
- [ ] Implement skill SQLite schema
- [ ] Fix YAML parsing vulnerability (CRITICAL)
- [ ] Fix path traversal vulnerability (CRITICAL)
- [ ] Implement UI for skill management
- [ ] Write tests

### 5.8 Slice 8: Event Bus Slice
**Database**: `data/slice_event_bus.db`

- [ ] Create slice structure
- [ ] Implement event SQLite schema
- [ ] Implement bounded queues (CRITICAL FIX)
- [ ] Implement UI for event monitoring
- [ ] Write tests

---

## Phase 6: Plugin System

### 6.1 Plugin Framework
- [ ] Implement `refactorbot/plugins/plugin_base.py`
- [ ] Implement `refactorbot/plugins/hook_system.py`
- [ ] Implement plugin discovery service
- [ ] Implement UI integration for plugins

### 6.2 Channel Plugins
- [ ] Implement Discord adapter plugin with UI
- [ ] Implement Telegram adapter plugin with UI
- [ ] Implement WhatsApp adapter plugin with UI
- [ ] Implement Feishu adapter plugin with UI

---

## Phase 7: Meta SDLC CI/CD for Slices

### 7.1 Self-Improvement Framework
- [ ] Implement slice analysis module
- [ ] Implement improvement plan generation
- [ ] Implement code patch generation
- [ ] Implement UI for self-improvement monitoring

### 7.2 Slice CI/CD Pipelines
- [ ] Create CI/CD for Agent Core Slice
- [ ] Create CI/CD for Tool System Slice
- [ ] Create CI/CD for Memory Slice
- [ ] Create CI/CD for all remaining slices

---

## Phase 8: Test Suite Implementation

### 8.1 Shared Test Infrastructure
- [ ] Create `refactorbot/tests/conftest.py`
- [ ] Implement mock LLM provider
- [ ] Implement mock SQLite database fixtures
- [ ] Implement Streamlit UI testing fixtures

### 8.2 Unit Tests (Target: 80% coverage per slice)
- [ ] Write unit tests for Master Core
- [ ] Write unit tests for Agent Core Slice
- [ ] Write unit tests for Tool System Slice
- [ ] Write unit tests for Memory Slice
- [ ] Write unit tests for Communication Slice
- [ ] Write unit tests for Session Slice
- [ ] Write unit tests for Providers Slice
- [ ] Write unit tests for Skills Slice
- [ ] Write unit tests for Event Bus Slice

### 8.3 Integration Tests
- [ ] Write cross-slice integration tests
- [ ] Write dashboard integration tests
- [ ] Write database integration tests

### 8.4 E2E Tests
- [ ] Write full workflow tests
- [ ] Write UI automation tests with Playwright
- [ ] Write performance tests

---

## Phase 9: Observability

### 9.1 Metrics Collection
- [ ] Implement `refactorbot/infrastructure/observability.py`
- [ ] Implement slice execution metrics
- [ ] Implement latency histograms
- [ ] Implement dashboard metrics display

### 9.2 Structured Logging
- [ ] Implement JSON logging format
- [ ] Implement dashboard log viewer

### 9.3 Alerting
- [ ] Implement performance alerts with dashboard display
- [ ] Implement error alerts with dashboard display

---

## Phase 10: Security Hardening

### 10.1 Input Validation
- [ ] Implement comprehensive input validation
- [ ] Implement parameter schema validation (HIGH PRIORITY)
- [ ] Implement file size limits
- [ ] Implement path traversal prevention (HIGH PRIORITY)

### 10.2 Rate Limiting
- [ ] Implement per-slice rate limiting
- [ ] Implement dashboard rate limit display

---

## Phase 11: Production Deployment

### 11.1 Docker Configuration
- [ ] Create `deployment/docker/Dockerfile`
- [ ] Create `deployment/docker/docker-compose.yml`
- [ ] Optimize image size
- [ ] Implement multi-stage builds

### 11.2 Kubernetes Configuration
- [ ] Create `deployment/kubernetes/deployment.yaml`
- [ ] Create `deployment/kubernetes/service.yaml`
- [ ] Implement HPA (Horizontal Pod Autoscaler)

---

## 📊 Execution Order (Critical Path)

```
Phase 1 (Foundation) → Phase 2 (Master Core) → Phase 3 (Master Dashboard)
                                      ↓
Phase 4 (OpenRouter) → Phase 5 (Vertical Slices)
        ↓
Phase 6 (Plugins) → Phase 7 (Meta SDLC)
        ↓
Phase 8 (Tests) → Phase 9 (Observability)
        ↓
Phase 10 (Security) → Phase 11 (Deployment)
```

---

## 🎯 Milestones

| Milestone | Description | Deliverable |
|-----------|-------------|-------------|
| M1 | Foundation Complete | Base classes, config, project structure |
| M2 | Master Core Running | Core orchestrator with global state |
| M3 | Dashboard Ready | Streamlit dashboard with overview |
| M4 | OpenRouter Ready | Model routing and cost tracking |
| M5 | First Slice | Agent Core Slice with UI and DB |
| M6 | All Slices | All 8 slices with UIs and databases |
| M7 | Plugin System | Channel plugins with UIs |
| M8 | Test Coverage | 80%+ coverage achieved |
| M9 | Production Ready | Full deployment stack |
| M10 | Launch | System in production |

---

## ⚠️ Critical Issues (From Audit - Must Fix First)

| Issue | File | Priority | Action |
|-------|------|----------|--------|
| YAML Parsing | slice_skills | CRITICAL | Fix in Skills Slice implementation |
| Path Traversal | slice_skills | CRITICAL | Implement path validation |
| Unbounded Queues | slice_event_bus | HIGH | Implement bounded queues |
| No Tool Validation | slice_tools | HIGH | Implement param validation |

---

## 📦 Dependencies

```txt
# requirements.txt
streamlit>=1.28
pydantic>=2.0
pyyaml>=6.0
httpx>=0.25
aiofiles>=23.0
tiktoken>=0.5
tenacity>=8.0
structlog>=23.0
pytest>=7.0
pytest-asyncio>=0.21
pytest-cov>=4.0
playwright>=1.40
```

---

## 🚦 Quality Gates

Before advancing to each phase:

1. **Code Quality**: All new code must pass linting and type checking
2. **Test Coverage**: Must maintain 80%+ coverage per slice
3. **Security**: Must pass security scan
4. **Performance**: Must pass performance benchmarks
5. **UI**: Dashboard must render correctly
6. **Database**: All migrations must pass
7. **Review**: Must have peer code review approval
