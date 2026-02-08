# RefactorBot Full Compliance Implementation Plan

**Date:** 2026-02-08
**Goal:** Full implementation to match Nanobot feature set with proper test coverage

---

## Phase 1: Critical Infrastructure Fixes

### 1.1 Fix slice_base.py Undefined Variables
- [x] Fix `self._version` undefined attribute in `slice_version` property
- [x] Added `__aenter__` and `__aexit__` for async context manager
- [x] Fixed `NotImplementedError` to have message
- [x] Updated `.md` status file

### 1.2 Fix meta_sdlc Wrong Attribute References
- [x] Fix `slice_instance.name` should be `slice_instance.slice_id`
- [x] Added hasattr check for config_path
- [x] Updated `.md` status file

### 1.3 Fix slice_memory Database Initialization
- [x] Initialize database in `MemoryStorageServices.__init__`
- [x] Added proper table creation with MemoryDatabase class
- [x] Updated `.md` status file

### 1.4 Fix slice_tools Handler Imports
- [x] Fix `_import_handler` to actually import modules
- [x] Added ToolsDatabase class for proper initialization
- [x] Added builtin handler support
- [x] Updated `.md` status file

---

## Phase 2: Tool Implementations (slice_tools)

### 2.1 File System Tools
- [x] Implement `ReadFileTool` - Read file contents
- [x] Implement `WriteFileTool` - Write content to files
- [x] Implement `EditFileTool` - Edit file contents
- [x] Implement `ListDirTool` - List directory contents
- [x] Add workspace restriction support
- [x] Update `.md` status file

### 2.2 Shell Execution Tool
- [x] Implement `ExecTool` with security guards
- [x] Add command validation (no rm -rf, fork bombs, etc.)
- [x] Add timeout support
- [x] Update `.md` status file

### 2.3 Web Tools
- [x] Implement `WebSearchTool` with Brave API
- [x] Implement `WebFetchTool` with HTML parsing
- [x] Add URL validation
- [x] Add blocked domain check
- [ ] Update `.md` status file

### 2.4 Message Tool
- [ ] Implement `MessageTool` for sending messages
- [ ] Add channel-specific formatting
- [ ] Update `.md` status file

### 2.5 Spawn Tool
- [ ] Implement `SpawnTool` for subagent spawning
- [ ] Add task management
- [ ] Update `.md` status file

### 2.6 Talk Tool
- [ ] Implement `TalkTool` for chat functionality
- [ ] Update `.md` status file

### 2.7 Cron Tool
- [ ] Implement `CronTool` for scheduling
- [ ] Integrate with scheduling service
- [ ] Update `.md` status file

### 2.8 Tool Registry
- [ ] Implement full `ToolRegistry` with registration
- [ ] Add validation support
- [ ] Update `.md` status file

### 2.9 Tests for slice_tools
- [ ] Write test for file tools
- [ ] Write test for shell tool security
- [ ] Write test for web tools
- [ ] Write test for registry
- [ ] Update `.md` status file

---

## Phase 3: Provider Implementation (slice_providers)

### 3.1 LiteLLM Wrapper
- [x] Create `LiteLLMGateway` class
- [x] Implement multi-provider support (50+ providers)
- [x] Add `MultiProviderGateway` for fallback
- [x] Update `.md` status file

### 3.2 Database Initialization
- [x] Add `ProvidersDatabase` class with schema
- [x] Initialize database in `SliceProviders.__init__`
- [x] Update `.md` status file

### 3.3 Service Database Operations
- [x] Add database access to all services
- [x] Implement `register_provider` with DB insert
- [x] Implement `list_providers` with DB query
- [x] Implement `get_provider` with DB fetch
- [x] Implement `update_provider` with DB update
- [x] Implement `delete_provider` with DB delete
- [x] Update `.md` status file

### 3.4 Provider Testing
- [x] Implement `_test_openrouter` with real connectivity test
- [x] Implement `_test_litellm` with real connectivity test
- [x] Update `.md` status file

### 3.5 Additional Provider Support
- [ ] Add OpenAI support (direct)
- [ ] Add Anthropic support (direct)
- [ ] Add Gemini support (direct)
- [ ] Add DeepSeek support
- [ ] Add Groq support
- [ ] Update `.md` status file

### 3.6 Transcription Support
- [ ] Implement transcription service (Whisper)
- [ ] Add audio processing
- [ ] Update `.md` status file

---

## Phase 4: Channel Implementation (slice_communication)

### 4.1 Telegram Channel
- [ ] Implement `TelegramChannel` class
- [ ] Add webhook handling
- [ ] Implement message sending
- [ ] Update `.md` status file

### 4.2 Discord Channel
- [ ] Implement `DiscordChannel` class
- [ ] Add gateway connection
- [ ] Implement message sending
- [ ] Update `.md` status file

### 4.3 WhatsApp Channel
- [ ] Implement `WhatsAppChannel` class
- [ ] Add Cloud API integration
- [ ] Implement message sending
- [ ] Update `.md` status file

### 4.4 Feishu Channel
- [ ] Implement `FeishuChannel` class
- [ ] Add webhook support
- [ ] Implement message sending
- [ ] Update `.md` status file

### 4.5 Channel Manager
- [ ] Implement `ChannelManager` for routing
- [ ] Add channel initialization
- [ ] Update `.md` status file

### 4.6 Tests for slice_communication
- [ ] Write test for Telegram
- [ ] Write test for Discord
- [ ] Write test for channel manager
- [ ] Update `.md` status file

---

## Phase 5: Subagent System

### 5.1 Subagent Manager
- [ ] Implement `SubagentManager` class
- [ ] Add mailbox system
- [ ] Implement task spawning
- [ ] Update `.md` status file

### 5.2 Tests for Subagent
- [ ] Write test for subagent spawning
- [ ] Write test for mailbox communication
- [ ] Update `.md` status file

---

## Phase 6: Scheduling & Heartbeat

### 6.1 Cron Service
- [ ] Implement `CronService` class
- [ ] Add job storage (JSON)
- [ ] Implement scheduling (at, every, cron)
- [ ] Update `.md` status file

### 6.2 Heartbeat Service
- [ ] Implement `HeartbeatService` class
- [ ] Add periodic wake-up
- [ ] Implement HEARTBEAT.md reading
- [ ] Update `.md` status file

### 6.3 Tests for Scheduling
- [ ] Write test for cron jobs
- [ ] Write test for heartbeat
- [ ] Update `.md` status file

---

## Phase 7: Memory & Session

### 7.1 Memory Enhancements
- [ ] Add vector storage support
- [ ] Implement semantic search
- [ ] Add memory consolidation
- [ ] Update `.md` status file

### 7.2 Session Enhancements
- [ ] Implement full JSONL persistence
- [ ] Add session keys (channel:chat_id)
- [ ] Add token tracking
- [ ] Update `.md` status file

### 7.3 Tests for Memory & Session
- [ ] Write test for memory storage
- [ ] Write test for session management
- [ ] Update `.md` status file

---

## Phase 8: Skills System

### 8.1 Skill Implementations
- [ ] Implement GitHub integration skill
- [ ] Implement Skill Creator
- [ ] Implement Summarize skill
- [ ] Implement Tmux control skill
- [ ] Implement Weather skill
- [ ] Update `.md` status file

### 8.2 Tests for Skills
- [ ] Write test for skill registry
- [ ] Write test for skill execution
- [ ] Update `.md` status file

---

## Phase 9: Infrastructure

### 9.1 Security Enhancements
- [ ] Add rate limiting
- [ ] Add command guards
- [ ] Add input validation
- [ ] Update `.md` status file

### 9.2 Message Bus
- [ ] Implement full `MessageBus` class
- [ ] Add queue-based messaging
- [ ] Update `.md` status file

### 9.3 Configuration
- [ ] Implement Pydantic schema
- [ ] Add environment variable loading
- [ ] Add CLI commands
- [ ] Update `.md` status file

---

## Phase 10: Final Testing & Integration

### 10.1 Integration Tests
- [ ] Write full integration test suite
- [ ] Test agent loop with all tools
- [ ] Test channel integrations
- [ ] Update `.md` status file

### 10.2 Performance Tests
- [ ] Write performance benchmarks
- [ ] Test concurrent operations
- [ ] Update `.md` status file

### 10.3 Final Audit
- [ ] Re-run Total Control audit
- [ ] Verify all commandments compliance
- [ ] Update `.md` status file

---

## Priority Order

1. **Week 1**: Phase 1 (Critical fixes)
2. **Week 2-3**: Phase 2 (Tools - core functionality)
3. **Week 4**: Phase 3 (Providers)
4. **Week 5**: Phase 4 (Channels)
5. **Week 6**: Phase 5-6 (Subagent, Scheduling)
6. **Week 7**: Phase 7-8 (Memory, Skills)
7. **Week 8**: Phase 9-10 (Infrastructure, Testing)

---

## Testing Requirements

Each file must have:
- [ ] Unit tests with >80% coverage
- [ ] Integration tests where applicable
- [ ] Test status updated in `.md` file
- [ ] All tests passing

## Compliance Requirements

Each file must:
- [ ] Pass Commandment 1 (No undefined vars)
- [ ] Pass Commandment 2 (No unreachable code)
- [ ] Pass Commandment 3 (Valid dependencies)
- [ ] Pass Commandment 4 (No stubs)
- [ ] Pass Commandment 5-10 (Protocol, Init, Context, Self-imp, Health, Docs)
- [ ] Status updated in `.md` file

---

## Status Summary

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 1: Critical Fixes | [ ] | 0% |
| Phase 2: Tools | [ ] | 0% |
| Phase 3: Providers | [ ] | 0% |
| Phase 4: Channels | [ ] | 0% |
| Phase 5: Subagent | [ ] | 0% |
| Phase 6: Scheduling | [ ] | 0% |
| Phase 7: Memory/Session | [ ] | 0% |
| Phase 8: Skills | [ ] | 0% |
| Phase 9: Infrastructure | [ ] | 0% |
| Phase 10: Testing | [ ] | 0% |

**Overall: 0% Complete**

---

## Commands

```bash
# Run all tests
python -m pytest tests/ -v --cov

# Run specific test file
python -m pytest tests/test_slices.py -v

# Run with coverage
python -m pytest tests/ --cov=refactorbot --cov-report=html

# Run linting
flake8 refactorbot/ --max-line-length=120

# Run type checking
mypy refactorbot/
```
