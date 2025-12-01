"""
Unit tests for deep research agent structure validation.
Tests the implementation without requiring external API calls.
"""
import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_deepagents_import():
    """Test that deepagents library is available."""
    from src.agents.deep_research_agent import DEEPAGENTS_AVAILABLE
    assert DEEPAGENTS_AVAILABLE, "deepagents library should be installed"

def test_internet_search_tool_exists():
    """Test that internet_search tool is properly defined."""
    from src.agents.deep_research_agent import internet_search
    
    assert hasattr(internet_search, 'name'), "Tool should have a name attribute"
    assert hasattr(internet_search, 'description'), "Tool should have a description"
    assert callable(internet_search), "Tool should be callable"

def test_subagent_structure():
    """Test that subagents are properly structured."""
    from src.agents.deep_research_agent import research_subagent, critique_subagent, subagents
    
    # Check research_subagent structure
    assert isinstance(research_subagent, dict), "research_subagent should be a dict"
    assert "name" in research_subagent, "research_subagent should have a name"
    assert "description" in research_subagent, "research_subagent should have a description"
    assert "prompt" in research_subagent, "research_subagent should have a prompt field"
    assert "tools" in research_subagent, "research_subagent should have tools"
    assert isinstance(research_subagent["tools"], list), "tools should be a list"
    assert "internet_search" in research_subagent["tools"], "should reference internet_search by name"
    
    # Check critique_subagent structure 
    assert isinstance(critique_subagent, dict), "critique_subagent should be a dict"
    assert "name" in critique_subagent, "critique_subagent should have a name"
    assert "description" in critique_subagent, "critique_subagent should have a description"
    assert "prompt" in critique_subagent, "critique_subagent should have a prompt field"
    
    # Check subagents list
    assert isinstance(subagents, list), "subagents should be a list"
    assert len(subagents) == 2, "should have exactly 2 subagents"
    assert research_subagent in subagents, "research_subagent should be in list"
    assert critique_subagent in subagents, "critique_subagent should be in list"

def test_research_instructions_exists():
    """Test that main agent instructions are defined."""
    from src.agents.deep_research_agent import research_instructions
    
    assert isinstance(research_instructions, str), "research_instructions should be a string"
    assert len(research_instructions) > 0, "research_instructions should not be empty"
    assert "researcher" in research_instructions.lower(), "should mention researcher role"

def test_run_deep_research_signature():
    """Test that run_deep_research has the expected signature."""
    from src.agents.deep_research_agent import run_deep_research
    import inspect
    
    sig = inspect.signature(run_deep_research)
    params = list(sig.parameters.keys())
    
    assert "query" in params, "should have query parameter"
    assert "model_name" in params, "should have model_name parameter"
    assert "max_iterations" in params, "should have max_iterations parameter"

@pytest.mark.asyncio
async def test_fallback_mode_works():
    """Test that fallback mode works when deepagents is disabled."""
    import os
    from src.agents.deep_research_agent import run_deep_research
    
    # Temporarily disable deepagents
    original_flag = os.getenv("DEEP_RESEARCH_ENABLED")
    os.environ["DEEP_RESEARCH_ENABLED"] = "false"
    
    try:
        result = await run_deep_research("test query", max_iterations=1)
        
        assert isinstance(result, dict), "result should be a dict"
        assert "answer" in result, "result should have an answer"
        assert "citations" in result, "result should have citations"
        assert "metadata" in result, "result should have metadata"
        assert result["metadata"].get("error") == "Feature disabled", "should indicate feature is disabled"
    finally:
        # Restore original flag
        if original_flag:
            os.environ["DEEP_RESEARCH_ENABLED"] = original_flag
        else:
            os.environ.pop("DEEP_RESEARCH_ENABLED", None)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
