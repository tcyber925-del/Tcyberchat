# COMPREHENSIVE FIX PLAN: Force LangGraph Deep Research Agent

## Problem Statement

The Deep Research feature is **falling back to the custom WebResearchOrchestrator** instead of using the LangGraph-based deep research agent. Additionally, the Groq API is returning a **404 error** with a doubled URL path.

---

## Root Causes Identified

### 1. **Groq API 404 Error** (CRITICAL BLOCKER)
**Error**: `POST /openai/v1/chat/completions/openai/v1/chat/completions`

**Diagnosis**: The URL path is doubled, indicating:
- Either `GROQ_BASE_URL` is incorrectly set to include `/openai/v1/chat/completions`
- OR the Groq client is somehow duplicating the path

**Impact**: The LangGraph agent **cannot run** because the `plan_node` immediately fails when calling Groq

### 2. **Fallback Logic in deep_research_agent.py**
**File**: `backend/src/agents/deep_research_agent.py` (lines 40-44, 51-63)

**Problem**: There are TWO fallback mechanisms:
1. If `GROQ_API_KEY` is missing → falls back to `WebResearchOrchestrator`
2. If ANY exception occurs → falls back to `WebResearchOrchestrator`

**Impact**: Even when  the user explicitly chooses Deep Research, errors cause silent fallback to simple search

### 3. **Unclear Error Messages**
**Problem**: When fallback occurs, the user sees generic results without knowing the LangGraph agent failed

**Impact**: User cannot diagnose why Deep Research isn't working

---

## Comprehensive Fix Plan

### Phase 1: Fix Groq URL Issue (URGENT - BLOCKING)

#### Step 1.1: Check and Remove GROQ_BASE_URL
**File**: `backend/.env`

**Actions**:
```bash
# Check if GROQ_BASE_URL exists
grep "GROQ_BASE_URL" .env

# If it exists and is NOT commented out, comment it
# GROQ_BASE_URL should NOT be set - let Groq SDK use default
```

**Expected**: `GROQ_BASE_URL` should either:
- Not exist in `.env`
- Be commented out: `# GROQ_BASE_URL=...`

#### Step 1.2: Remove Base URL Logging from GroqClient
**File**: `backend/src/clients/groq_client.py` (line 50)

**Current**:
```python
self._client = Groq(api_key=self.api_key)
logger.info(f"Groq client base_url: {self._client.base_url}")
```

**Problem**: Accessing `base_url` might trigger initialization issues

**Fix**: Remove the logging line
```python
self._client = Groq(api_key=self.api_key)
# Removed base_url logging to avoid initialization issues
```

#### Step 1.3: Explicitly Set Base URL to Default
**File**: `backend/src/clients/groq_client.py` (line 49)

**Enhanced**:
```python
from groq import Groq
# Explicitly  use default base_url to avoid environment variable pollution
self._client = Groq(
    api_key=self.api_key,
    base_url="https://api.groq.com/openai/v1"  # Explicit default
)
```

---

### Phase 2: Remove ALL Fallback Logic

#### Step 2.1: Remove GROQ_API_KEY Check Fallback
**File**: `backend/src/agents/deep_research_agent.py` (lines 40-44)

**Current**:
```python
if not os.getenv("GROQ_API_KEY"):
    logger.warning("GROQ_API_KEY not found. Falling back to simple search.")
    from src.services.web_research_orchestrator import WebResearchOrchestrator
    orchestrator = WebResearchOrchestrator()
    return await orchestrator.run(query)
```

**Fix**: Replace with hard error
```python
if not os.getenv("GROQ_API_KEY"):
    raise ValueError(
        "GROQ_API_KEY is required for Deep Research. "
        "Please set it in your .env file or use regular chat mode."
    )
```

**Justification**: Better to fail fast and clearly inform user than silently degrade

#### Step 2.2: Remove Exception Handler Fallback
**File**: `backend/src/agents/deep_research_agent.py` (lines 51-63)

**Current**:
```python
except Exception as e:
    logger.error(f"Deep research failed: {e}")
    # Fallback to simple search on error
    try:
        from src.services.web_research_orchestrator import WebResearchOrchestrator
        orchestrator = WebResearchOrchestrator()
        return await orchestrator.run(query)
    except Exception as fallback_error:
        return {
            "answer": f"An error occurred...",
            "citations": [],
            "metadata": {"error": str(e)}
        }
```

**Fix**: Let exceptions propagate with better error handling
```python
except Exception as e:
    logger.error(f"Deep Research LangGraph execution failed: {e}", exc_info=True)
    # Re-raise with context instead of falling back
    raise RuntimeError(
        f"Deep Research failed to execute. This could indicate:\n"
        f"1. Groq API configuration issue\n"
        f"2. Web search provider failure\n"
        f"3. LangGraph execution error\n"
        f"Original error: {str(e)}"
    ) from e
```

**Justification**: 
- Fails loudly so user knows something is wrong
- Provides diagnostic information
- Forces fixing the root cause instead of masking it

---

### Phase 3: Add Validation and Better Error Messages

#### Step 3.1: Add Pre-Flight Checks
**File**: `backend/src/agents/deep_research_agent.py`

**Add Function**:
```python
async def validate_deep_research_requirements():
    """Validate all requirements before running deep research"""
    errors = []
    
    # Check GROQ_API_KEY
    if not os.getenv("GROQ_API_KEY"):
        errors.append("GROQ_API_KEY is not set")
    
    # Check web search provider
    from src.services.web_search_service import get_web_search_service
    try:
        svc = get_web_search_service()
        if not svc.primary_provider or not svc.primary_provider.is_available():
            errors.append(f"Web search provider '{svc.provider_name}' is not available")
    except Exception as e:
        errors.append(f"Web search service initialization failed: {e}")
    
    # Check Groq client
    try:
        from src.clients.groq_client import GroqClient
        client = GroqClient(model="llama-3.3-70b-versatile")
        # Test generation with simple prompt
        response = await asyncio.to_thread(
            client.generate,
            prompt="Say 'OK'",
            max_tokens=10
        )
        if not response or len(response.strip()) == 0:
            errors.append("Groq client returned empty response")
    except Exception as e:
        errors.append(f"Groq client test failed: {e}")
    
    if errors:
        raise ValueError(
            "Deep Research requirements not met:\n" + 
            "\n".join(f"  - {err}" for err in errors)
        )
    
    logger.info("Deep Research requirements validated successfully")
```

#### Step 3.2: Call Validation Before Execution
**File**: `backend/src/agents/deep_research_agent.py`

**Updated `run_deep_research`**:
```python
async def run_deep_research(query: str, model_name: str = None, max_iterations: int = 3):
    """Executes the deep research agent using LangGraph"""
    try:
        logger.info(f"Starting deep research for query: {query}")
        
        # Validate requirements first
        await validate_deep_research_requirements()
        
        # Run the LangGraph agent
        result = await run_deep_research_graph(query, max_iterations=max_iterations)
        
        return result
        
    except ValueError as e:
        # Configuration/validation errors
        logger.error(f"Deep Research validation failed: {e}")
        raise
        
    except Exception as e:
        # Execution errors
        logger.error(f"Deep Research execution failed: {e}", exc_info=True)
        raise RuntimeError(f"Deep Research failed: {str(e)}") from e
```

---

### Phase 4: Improve LangGraph Error Handling

#### Step 4.1: Add Try-Catch in Each Node
**File**: `backend/src/agents/deep_research_graph.py`

**Enhanced `plan_node`**:
```python
async def plan_node(state: ResearchState):
    """Generates a research plan"""
    print(f"--- Planning: {state['query']} ---")
    
    try:
        client = get_groq_client(model="openai/gpt-oss-120b")
        
        prompt = f"""You are a senior research planner.
User Query: "{state['query']}"

Break this query down into 3-5 distinct, specific web search queries...
Return ONLY a JSON array of strings. Example: ["query 1", "query 2"]
Do not include any other text."""

        response = await asyncio.to_thread(
            client.generate,
            prompt=prompt,
            temperature=0.3
        )
        
        # Parse response...
        
    except Exception as e:
        logger.error(f"Planning node failed: {e}", exc_info=True)
        # Return fallback plan instead of crashing
        return {"plan": [state['query']], "iteration": 0}
```

**Justification**: Individual node failures should be handled gracefully while still completing the workflow

---

### Phase 5: Add Debug Logging

#### Step 5.1: Add Verbose Logging
**File**: `backend/src/agents/deep_research_graph.py`

**Add at top**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)  # For deep research only
logger = logging.getLogger(__name__)
```

**Enhanced logging in nodes**:
```python
async def plan_node(state: ResearchState):
    logger.debug(f"[PLAN] Starting with query: {state['query']}")
    # ... execution ...
    logger.debug(f"[PLAN] Generated {len(plan)} search queries")
    logger.debug(f"[PLAN] Queries: {plan}")
    return {"plan": plan, "iteration": 0}
```

---

## Implementation Checklist

### Immediate Actions (Phase 1)

- [ ] **1a**: Check `.env` for `GROQ_BASE_URL` and comment it out if exists
- [ ] **1b**: Modify `groq_client.py` to explicitly set `base_url="https://api.groq.com/openai/v1"`
- [ ] **1c**: Remove `base_url` logging line
- [ ] **Test**: Run `test_graph_direct.py` - should NOT get 404 error

### Core Fixes (Phase 2)

- [ ] **2a**: Replace GROQ_API_KEY fallback with hard error in `deep_research_agent.py`
- [ ] **2b**: Remove exception handler fallback, let errors propagate
- [ ] **Test**: Deep Research should fail with clear error if requirements not met

### Validation (Phase 3)

- [ ] **3a**: Add `validate_deep_research_requirements()` function
- [ ] **3b**: Call validation before running graph
- [ ] **Test**: Missing GROQ_API_KEY should give clear error message

### Resilience (Phase 4)

- [ ] **4a**: Add try-catch in `plan_node`, `investigate_node`, `synthesize_node`
- [ ] **Test**: Individual node failures shouldn't crash entire workflow

### Debugging (Phase 5)

- [ ] **5a**: Add DEBUG-level logging to all nodes
- [ ] **5b**: Log Groq client initialization
- [ ] **Test**: Run with DEBUG logging, verify each step executes

---

## Testing Protocol

### Test 1: Groq Client Direct
```bash
cd backend
uv run python -c "
from src.clients.groq_client import GroqClient
client = GroqClient(model='llama-3.3-70b-versatile')
print(client.client.base_url)
response = client.generate('Say hello')
print(response)
"
```
**Expected**: `https://api.groq.com/openai/v1` and "Hello" response

### Test 2: LangGraph Execution
```bash
uv run python test_graph_direct.py
```
**Expected**: Graph executes without 404 error, returns structured answer

### Test 3: Deep Research Agent
```bash
uv run python test_deep_agent_manual.py
```
**Expected**: Uses LangGraph (not WebResearchOrchestrator), returns citations

### Test 4: UI Integration
1. Open `http://localhost:3000`
2. Click `+` → `Deep Research`
3. Ask: "What is quantum computing?"
4. **Expected**: 
   - If requirements met: Shows structured answer
   - If requirements NOT met: Shows clear error message (not generic results)

---

## Success Criteria

✅ **No Groq 404 Errors**: All API calls succeed  
✅ **No Silent Fallbacks**: Errors are visible to user
✅ **LangGraph Always Runs**: When Deep Research is selected, LangGraph executes
✅ **Clear Error Messages**: User knows exactly what's wrong when it fails
✅ **Structured Output**: Results have Summary, Analysis, Insights, Sources sections

---

## Next Steps

I'm ready to implement this plan. Shall I proceed with:

1. **Phase 1 (URGENT)**: Fix Groq URL issue
2. **Phase 2**: Remove fallback logic
3. **Phases 3-5**: Add validation, resilience, logging

Or would you like me to implement all phases at once?
