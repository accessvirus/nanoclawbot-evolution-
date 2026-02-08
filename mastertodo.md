# RefactorBot V2 - MASTER TODO

**Date:** 2026-02-08  
**Objective:** Fix all stub/demo implementations for 100% real code

---

## 🔴 CRITICAL - MUST FIX

### 1. Fix Agent Execution Stub

**File:** `slices/slice_agent/core/services.py`  
**Lines:** 202-203  
**Status:** ❌ NOT FIXED

#### Current Code (STUB)
```python
async def run_agent(self, agent_id: str, input_text: str) -> Dict[str, Any]:
    """Execute an agent with input and persistence."""
    execution_id = f"exec_{uuid.uuid4().hex[:8]}"
    start_time = datetime.utcnow()
    
    agent = await AgentLifecycleServices(self.slice).get_agent_status(agent_id)
    if not agent:
        return {"success": False, "error": f"Agent {agent_id} not found"}
    
    try:
        # ❌ STUB - Simulated execution
        result_text = f"Agent '{agent['name']}' processed: {input_text}"
        
        # ... persistence code ...
```

#### Required Code (REAL)
```python
async def run_agent(self, agent_id: str, input_text: str) -> Dict[str, Any]:
    """Execute an agent with real LLM call."""
    execution_id = f"exec_{uuid.uuid4().hex[:8]}"
    start_time = datetime.utcnow()
    
    agent = await AgentLifecycleServices(self.slice).get_agent_status(agent_id)
    if not agent:
        return {"success": False, "error": f"Agent {agent_id} not found"}
    
    try:
        # ✅ REAL LLM CALL
        from providers.openrouter_gateway import create_gateway
        
        gateway = await create_gateway(self.slice.config.openrouter_api_key)
        llm_response = await gateway.complete(
            prompt=f"Agent System: {agent.get('system_prompt', '')}\n\nUser: {input_text}",
            model=agent.get('model', 'openai/gpt-4-turbo'),
            temperature=agent.get('temperature', 0.7),
            max_tokens=agent.get('max_tokens', 4000)
        )
        result_text = llm_response["content"]
        await gateway.close()
        
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        execution_data = {
            "id": execution_id,
            "agent_id": agent_id,
            "input_text": input_text,
            "result": result_text,
            "status": "completed",
            "error_message": None,
            "duration_ms": duration_ms,
            "executed_at": start_time.isoformat(),
            "model_used": agent.get('model', 'openai/gpt-4-turbo'),
            "prompt_tokens": llm_response.get("prompt_tokens", 0),
            "completion_tokens": llm_response.get("completion_tokens", 0),
        }
        
        # Persist to database
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                INSERT INTO agent_executions 
                (id, agent_id, input_text, result, status, error_message, 
                 duration_ms, executed_at, model_used, prompt_tokens, completion_tokens)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution_id, agent_id, input_text, result_text, "completed",
                None, duration_ms, start_time.isoformat(),
                agent.get('model', 'openai/gpt-4-turbo'),
                llm_response.get("prompt_tokens", 0),
                llm_response.get("completion_tokens", 0)
            ))
            await db.commit()
        
        return {"success": True, **execution_data}
        
    except Exception as e:
        return {"success": False, "error": str(e), "execution_id": execution_id}
```

#### Verification
```bash
python -c "
import asyncio
from slices.slice_agent.core.services import AgentExecutionServices
from slices.slice_agent import AgentSlice

async def test():
    slice = AgentSlice()
    await slice.initialize()
    svc = AgentExecutionServices(slice)
    result = await svc.run_agent('test_agent', 'Hello, world!')
    print('Result:', result)
    if 'Agent' in str(result.get('result', '')) and 'processed' in str(result):
        print('❌ STUB DETECTED!')
    else:
        print('✅ REAL LLM CALL!')
        print('Tokens:', result.get('prompt_tokens'), result.get('completion_tokens'))

asyncio.run(test())
```

---

### 2. Fix Dashboard Demo Buttons

**File:** `master_dashboard/app.py`  
**Lines:** 243-276  
**Status:** ❌ NOT FIXED

#### Current Code (DEMO)
```python
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("▶️ Start All Slices"):
        st.success("Starting all slices... (Demo)")

with col2:
    if st.button("⏹️ Stop All Slices"):
        st.warning("Stopping all slices... (Demo)")

with col3:
    if st.button("🔄 Restart All Slices"):
        st.info("Restarting all slices... (Demo)")
```

#### Required Code (REAL)
```python
# Add at top of render_control_panel_page()
if "master_core" not in st.session_state:
    from master_core.master_core import MasterCore
    import asyncio
    st.session_state.master_core = MasterCore(
        openrouter_api_key=st.session_state.get("openrouter_api_key")
    )
    asyncio.run(st.session_state.master_core.initialize())

master_core = st.session_state.master_core

ALL_SLICES = [
    "slice_agent", "slice_tools", "slice_memory", 
    "slice_communication", "slice_session", "slice_providers",
    "slice_skills", "slice_eventbus"
]

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("▶️ Start All Slices"):
        for slice_id in ALL_SLICES:
            await master_core.initialize_slice(slice_id)
            await master_core.start_slice(slice_id)
        st.success("✅ All slices started!")
        st.rerun()

with col2:
    if st.button("⏹️ Stop All Slices"):
        for slice_id in ALL_SLICES:
            await master_core.stop_slice(slice_id)
        st.warning("All slices stopped.")
        st.rerun()

with col3:
    if st.button("🔄 Restart All Slices"):
        for slice_id in ALL_SLICES:
            await master_core.stop_slice(slice_id)
            await master_core.initialize_slice(slice_id)
            await master_core.start_slice(slice_id)
        st.info("All slices restarted!")
        st.rerun()
```

#### Individual Slice Controls (REAL)
```python
for name, slice_id, emoji in slices:
    state = states.get(slice_id, {})
    status = state.get("status", "unknown")
    
    with st.expander(f"{emoji} {name} ({status})"):
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button(f"Start {name}", key=f"start_{slice_id}"):
                await master_core.initialize_slice(slice_id)
                await master_core.start_slice(slice_id)
                st.success(f"✅ {name} started!")
                st.rerun()
        
        with col_b:
            if st.button(f"Stop {name}", key=f"stop_{slice_id}"):
                await master_core.stop_slice(slice_id)
                st.warning(f"⏹️ {name} stopped!")
                st.rerun()
        
        with col_c:
            if st.button(f"Restart {name}", key=f"restart_{slice_id}"):
                await master_core.stop_slice(slice_id)
                await master_core.initialize_slice(slice_id)
                await master_core.start_slice(slice_id)
                st.info(f"🔄 {name} restarted!")
                st.rerun()
        
        st.markdown("**Metrics:**")
        st.json(state.get("metrics", {}))
```

#### Verification
```bash
# 1. Open dashboard
# 2. Click "Start All Slices"
# 3. Verify slices show "running" status
# 4. Check no "(Demo)" messages appear
# 5. Verify master_core._slices contains all slices
```

---

## 🟡 HIGH PRIORITY

### 3. Add OpenRouter API Key Configuration

**File:** `master_dashboard/app.py`  
**Status:** ❌ NOT IMPLEMENTED

```python
# Add in sidebar
with st.sidebar:
    st.title("🔑 Configuration")
    api_key = st.text_input("OpenRouter API Key", type="password")
    if api_key:
        st.session_state["openrouter_api_key"] = api_key
        st.success("API key set!")
```

---

### 4. Add Real Health Checks

**File:** `master_dashboard/app.py`  
**Status:** ❌ NOT IMPLEMENTED

```python
# Add to individual slice controls
try:
    health = asyncio.run(
        master_core._slices[slice_id].health_check()
    ) if slice_id in master_core._slices else "unknown"
except:
    health = "unknown"

st.markdown(f"**Health:** {health}")
```

---

## 🟢 MEDIUM PRIORITY

### 5. Add Stub Detection to Tests

**File:** `tests/conftest.py`  
**Status:** ❌ NOT IMPLEMENTED

```python
import pytest

@pytest.fixture
def no_stubs_allowed():
    """Ensure no stub implementations are used in tests."""
    yield
    # After test runs, check that real implementations were used
```

---

## 📋 COMPLETION CHECKLIST

| Task | Status | Owner | Notes |
|------|--------|-------|-------|
| Fix agent execution stub | ☐ | | Must use real LLM call |
| Fix dashboard demo buttons | ☐ | | Must call MasterCore methods |
| Add API key configuration | ☐ | | For OpenRouter access |
| Add real health checks | ☐ | | Display actual slice health |
| Verify no stubs remain | ☐ | | Search for "simulate", "demo" |

---

## 🚀 QUICK START

```bash
# 1. Run agent test
python -c "
import asyncio
from slices.slice_agent.core.services import AgentExecutionServices
from slices.slice_agent import AgentSlice

async def test():
    slice = AgentSlice()
    await slice.initialize()
    svc = AgentExecutionServices(slice)
    result = await svc.run_agent('test_agent', 'Hello, world!')
    print('SUCCESS!' if result.get('success') else 'FAILED!')
    print('Tokens:', result.get('prompt_tokens'), result.get('completion_tokens'))

asyncio.run(test())
"

# 2. Verify dashboard control
# Open http://localhost:8501
# Click Start/Stop buttons
# Verify slices status changes

# 3. Check for stubs
grep -r "Simulate\|Demo" refactorbot/ --include="*.py"
```

---

## 📞 SUPPORT

For issues, check:
- `master-audit.md` - Full audit report
- `mastertodo.md` - This file
- `totalcontrol.md` - Original requirements

---

*End of Master Todo*
