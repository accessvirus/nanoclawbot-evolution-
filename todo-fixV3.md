# RefactorBot V2 - Fix Implementation Plan V3

**Date**: 2026-02-08
**Based on**: Audit V3
**Priority**: P1 (Tests & Type Hints)

---

## Overview

Audit V3 identified 3 remaining issues from the original todo-fix.md. All P0 and P1 issues from the previous audits have been resolved. The focus now is on test execution and type hints.

---

## Remaining Issues

### 1. Tests Not Verified (P1)

**Status**: 🔄 IN PROGRESS
**Priority**: P1
**Files**: `tests/test_slices.py`, `tests/test_orchestrator.py`, `tests/test_services.py`

**Problem**: Test files exist but have not been executed with pytest.

**Solution**:
```bash
cd refactorbot
pytest tests/ -v --cov --cov-report=html
```

**Target**: 80%+ code coverage

---

### 2. Missing Type Hints (P1)

**Status**: 🔄 PARTIAL
**Priority**: P1
**Files**: `master_core.py`, `core/services.py` files, test files

**Problem**: Some files have incomplete or missing type hints.

**Solution**:
- Run mypy for validation
- Add missing type hints to `master_core.py`
- Add missing type hints to remaining services files

---

### 3. Error Handling (P2)

**Status**: 🔄 PARTIAL
**Priority**: P2
**Files**: All slice.py files

**Problem**: Error handling uses generic `Exception` catching.

**Solution**: Consider specific exception types for better error handling.

---

## Action Plan

### Step 1: Run Tests

```bash
cd refactorbot
pytest tests/ -v --cov
```

**Expected Output**:
- Tests should pass
- Coverage report generated
- Any failures documented

**If Tests Fail**:
1. Document failures
2. Fix issues
3. Re-run tests
4. Update coverage

### Step 2: Type Hints Completion

Run mypy to identify missing type hints:

```bash
cd refactorbot
python -m mypy refactorbot/ --strict
```

**Fix Issues**:
1. Add return type hints
2. Add parameter type hints
3. Add exception type hints

### Step 3: Error Handling Improvement

Consider adding specific exception types:

```python
# Current
except Exception as e:
    ...

# Improved
except (DatabaseError, ValueError) as e:
    ...
```

---

## Test Files Overview

### tests/test_slices.py

Tests for slice functionality:

```python
def test_slice_agent():
    """Test Agent slice operations."""
    slice = SliceAgent()
    assert slice.slice_id == "slice_agent"
    assert slice.slice_name == "Agent Core Slice"

def test_slice_memory():
    """Test Memory slice operations."""
    slice = SliceMemory()
    assert slice.slice_id == "slice_memory"
    # ... more tests
```

### tests/test_orchestrator.py

Tests for Master Core orchestration:

```python
def test_orchestrator_initialization():
    """Test Master Core initialization."""
    orchestrator = MasterCore()
    assert orchestrator is not None

def test_slice_registration():
    """Test slice registration."""
    orchestrator = MasterCore()
    orchestrator.register_slice("slice_agent", SliceAgent())
    assert "slice_agent" in orchestrator.get_registered_slices()
```

### tests/test_services.py

Tests for service layer:

```python
def test_memory_storage():
    """Test memory storage service."""
    from slice_memory.core.services import MemoryStorageServices
    # ... tests
```

---

## Type Hints Checklist

### master_core.py

- [ ] `class MasterCore` - Add type hints
- [ ] `def __init__` - Add return type
- [ ] `async def execute_request` - Add parameter/return types
- [ ] `def register_slice` - Add parameter/return types

### core/services.py files

- [ ] `class *Services` - Add type hints
- [ ] `async def *` - Add return types
- [ ] `def _get_connection` - Add return type

### slice.py files

- [ ] `_execute_core` - Complete (✅ done)
- [ ] `_create_*` methods - Complete (✅ done)
- [ ] `_get_*` methods - Complete (✅ done)
- [ ] `_list_*` methods - Complete (✅ done)

---

## Error Handling Improvements

### Recommended Exception Types

| Operation | Exception Type |
|-----------|---------------|
| Database | `DatabaseError`, `IntegrityError` |
| Validation | `ValueError`, `TypeError` |
| Network | `ConnectionError`, `TimeoutError` |
| File I/O | `FileNotFoundError`, `PermissionError` |
| JSON | `JSONDecodeError` |
| Slice | `SliceNotFoundError`, `SliceExecutionError` |

---

## Progress Tracking

| Issue | Status | Assignee | Notes |
|-------|--------|----------|-------|
| Tests Not Verified | In Progress | - | Awaiting execution |
| Missing Type Hints | Partial | - | mypy not run |
| Error Handling | Partial | - | Not prioritized |

---

## Next Steps

1. **Run pytest** with coverage
2. **Document results** in auditV4.md
3. **Fix any failures** from tests
4. **Run mypy** for type checking
5. **Fix type hints** as needed
6. **Create auditV4.md** for final assessment

---

## References

- **Audit V1**: [`audit.md`](audit.md) - Original audit (Grade: C+)
- **Audit V2**: [`auditV2.md`](auditV2.md) - Second audit (Grade: B+)
- **Audit V3**: [`auditV3.md`](auditV3.md) - Third audit (Grade: A-)
- **Implementation**: [`IMPLEMENTATION.md`](IMPLEMENTATION.md) - Architecture docs
- **TODO**: [`TODO.md`](TODO.md) - Original TODO list
