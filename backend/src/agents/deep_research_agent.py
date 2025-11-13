"""
Deep Research Agent using LangGraph for multi-step research workflows.

Flow:
1. Plan: Break query into sub-questions
2. Investigate: Parallel search + fetch for each sub-question
3. Synthesize: Merge findings into draft answer
4. Critique: Evaluate quality, identify gaps
5. Refine: Loop back if needed (max iterations)
6. Report: Final answer with citations
"""
from __future__ import annotations

import os
import asyncio
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime
import operator
import logging

logger = logging.getLogger(__name__)

# Optional LangGraph imports; graceful degradation if not installed
try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph not available; deep research will use fallback mode")


# --- State Definition ---
class ResearchState(TypedDict):
    """State tracked across the research graph."""
    query: str
    plan: Optional[Dict[str, Any]]  # {sub_questions: [...], angles: [...]}
    investigations: Annotated[List[Dict[str, Any]], operator.add]  # Each: {question, sources, findings}
    draft_answer: Optional[str]
    critique: Optional[Dict[str, Any]]  # {score, gaps, needs_refinement}
    final_answer: Optional[str]
    citations: Annotated[List[Dict[str, Any]], operator.add]
    metadata: Dict[str, Any]  # {iterations, timings, tokens}
    iteration: int
    max_iterations: int


# --- Node Functions ---
async def plan_research(state: ResearchState) -> Dict[str, Any]:
    """
    Generate a research plan: break query into sub-questions and angles.
    """
    query = state["query"]
    logger.info(f"Planning research for: {query}")
    
    # Use AI service to generate sub-questions
    from ..services.ai_service import get_ai_service
    ai_service = await get_ai_service(None)
    
    planning_prompt = f"""You are a research planner. Break down this question into 3-5 focused sub-questions that need to be answered to provide a comprehensive response.

Query: {query}

Output a JSON object with:
- sub_questions: array of strings (each a specific question to investigate)
- angles: array of strings (different perspectives to explore)

Example:
{{
  "sub_questions": [
    "What are the recent developments in X?",
    "How does X compare to Y?",
    "What are the challenges with X?"
  ],
  "angles": ["technical", "business", "ethical"]
}}

Output ONLY valid JSON, no markdown fences."""
    
    result = await ai_service.generate_response(planning_prompt, context=None)
    response_text = result.get("response", "{}") if isinstance(result, dict) else str(result)
    
    # Parse plan (basic fallback if parsing fails)
    try:
        import json
        plan = json.loads(response_text.strip())
        if not isinstance(plan, dict) or "sub_questions" not in plan:
            raise ValueError("Invalid plan structure")
    except Exception as e:
        logger.warning(f"Failed to parse plan, using fallback: {e}")
        plan = {
            "sub_questions": [query],  # Fallback to original query
            "angles": ["general"]
        }
    
    return {"plan": plan, "metadata": {**state["metadata"], "plan_generated_at": datetime.now().isoformat()}}


async def investigate_parallel(state: ResearchState) -> Dict[str, Any]:
    """
    Investigate each sub-question in parallel using web search + fetch.
    """
    plan = state["plan"]
    if not plan or "sub_questions" not in plan:
        return {"investigations": []}
    
    sub_questions = plan["sub_questions"]
    logger.info(f"Investigating {len(sub_questions)} sub-questions in parallel")
    
    from ..services.web_search_service import get_web_search_service
    from ..services.web_fetch_service import get_web_fetch_service
    
    search_service = get_web_search_service()
    fetch_service = get_web_fetch_service()
    
    async def investigate_one(question: str) -> Dict[str, Any]:
        """Investigate a single sub-question."""
        try:
            # Search
            results = await search_service.search(question, max_results=3, use_cache=True)
            if not results:
                return {"question": question, "sources": [], "findings": "No results found."}
            
            # Fetch top URLs
            urls = [r.url for r in results[:2] if r.url]
            fetched = await fetch_service.fetch_multiple(urls) if urls else []
            
            # Build findings summary
            findings_parts = []
            sources = []
            for idx, r in enumerate(results[:2], 1):
                fr = next((f for f in fetched if f.url == r.url or f.canonical_url == r.url), None)
                content = (fr.content or r.snippet or "")[:500]
                findings_parts.append(f"[{idx}] {r.title}\n{content}")
                sources.append({
                    "id": idx,
                    "title": r.title,
                    "url": fr.canonical_url if fr and fr.canonical_url else r.url,
                    "snippet": r.snippet,
                    "tokens": fr.tokens_estimate if fr else 0,
                })
            
            return {
                "question": question,
                "sources": sources,
                "findings": "\n\n".join(findings_parts)
            }
        except Exception as e:
            logger.error(f"Investigation failed for '{question}': {e}")
            return {"question": question, "sources": [], "findings": f"Error: {e}"}
    
    # Parallel investigation
    tasks = [investigate_one(q) for q in sub_questions]
    investigations = await asyncio.gather(*tasks)
    
    # Flatten citations
    all_citations = []
    for inv in investigations:
        all_citations.extend(inv.get("sources", []))
    
    return {
        "investigations": investigations,
        "citations": all_citations,
        "metadata": {**state["metadata"], "investigation_completed_at": datetime.now().isoformat()}
    }


async def synthesize_findings(state: ResearchState) -> Dict[str, Any]:
    """
    Synthesize all investigation findings into a draft answer.
    """
    query = state["query"]
    investigations = state["investigations"]
    
    if not investigations:
        return {"draft_answer": "No findings to synthesize."}
    
    logger.info(f"Synthesizing {len(investigations)} investigation results")
    
    # Build synthesis prompt
    findings_text = "\n\n".join([
        f"Sub-question: {inv['question']}\nFindings:\n{inv['findings']}"
        for inv in investigations
    ])
    
    synthesis_prompt = f"""You are a research synthesizer. Using ONLY the findings below, write a comprehensive answer to the original query.

Original Query: {query}

Findings:
{findings_text}

Instructions:
- Write a clear, structured answer with sections
- Use inline citations [1], [2], etc.
- Be factual and precise
- Highlight key insights and any conflicting information
- Output markdown format

Answer:"""
    
    from ..services.ai_service import get_ai_service
    ai_service = await get_ai_service(None)
    
    result = await ai_service.generate_response(synthesis_prompt, context=None)
    draft = result.get("response", "") if isinstance(result, dict) else str(result)
    
    return {
        "draft_answer": draft,
        "metadata": {**state["metadata"], "synthesis_completed_at": datetime.now().isoformat()}
    }


async def critique_answer(state: ResearchState) -> Dict[str, Any]:
    """
    Critique the draft answer: check quality, identify gaps, decide if refinement needed.
    """
    draft = state["draft_answer"]
    query = state["query"]
    iteration = state["iteration"]
    max_iterations = state["max_iterations"]
    
    if not draft or iteration >= max_iterations:
        return {"critique": {"score": 1.0, "gaps": [], "needs_refinement": False}}
    
    logger.info(f"Critiquing draft answer (iteration {iteration}/{max_iterations})")
    
    # Simple heuristic critique (can be enhanced with LLM-as-judge)
    word_count = len(draft.split())
    has_citations = "[1]" in draft or "[2]" in draft
    
    # Basic quality checks
    score = 0.7
    gaps = []
    
    if word_count < 100:
        gaps.append("Answer is too short")
        score -= 0.2
    if not has_citations:
        gaps.append("Missing citations")
        score -= 0.3
    
    # Decide if refinement needed
    needs_refinement = score < 0.6 and iteration < max_iterations - 1
    
    critique = {
        "score": max(0.0, score),
        "gaps": gaps,
        "needs_refinement": needs_refinement,
    }
    
    return {"critique": critique}


async def refine_research(state: ResearchState) -> Dict[str, Any]:
    """
    Refine research by investigating gaps identified by critic.
    """
    critique = state["critique"]
    gaps = critique.get("gaps", [])
    
    if not gaps:
        return {"iteration": state["iteration"] + 1}
    
    logger.info(f"Refining research to address gaps: {gaps}")
    
    # For simplicity, generate one additional sub-question per gap
    new_sub_questions = [f"Provide more details about: {gap}" for gap in gaps[:2]]
    
    # Re-use investigate logic
    temp_state = {**state, "plan": {"sub_questions": new_sub_questions}}
    refinement_result = await investigate_parallel(temp_state)
    
    return {
        "investigations": refinement_result.get("investigations", []),
        "citations": refinement_result.get("citations", []),
        "iteration": state["iteration"] + 1,
    }


async def finalize_report(state: ResearchState) -> Dict[str, Any]:
    """
    Finalize the research report with metadata and formatting.
    """
    draft = state["draft_answer"]
    citations = state["citations"]
    
    # Deduplicate citations by URL
    seen_urls = set()
    unique_citations = []
    for c in citations:
        if c["url"] not in seen_urls:
            seen_urls.add(c["url"])
            unique_citations.append(c)
    
    # Append sources section
    sources_section = "\n\n## Sources\n" + "\n".join([
        f"[{idx+1}] [{c['title']}]({c['url']})"
        for idx, c in enumerate(unique_citations)
    ])
    
    final_answer = (draft or "No answer generated.") + sources_section
    
    return {
        "final_answer": final_answer,
        "citations": unique_citations,
        "metadata": {
            **state["metadata"],
            "finalized_at": datetime.now().isoformat(),
            "total_citations": len(unique_citations),
        }
    }


# --- Conditional Routing ---
def should_refine(state: ResearchState) -> str:
    """Decide if we should refine or finalize."""
    critique = state.get("critique")
    if critique and critique.get("needs_refinement"):
        return "refine"
    return "finalize"


# --- Graph Builder ---
def build_research_graph() -> StateGraph:
    """Build the LangGraph research workflow."""
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("LangGraph is required for deep research feature")
    
    workflow = StateGraph(ResearchState)
    
    # Add nodes
    workflow.add_node("plan", plan_research)
    workflow.add_node("investigate", investigate_parallel)
    workflow.add_node("synthesize", synthesize_findings)
    workflow.add_node("critique", critique_answer)
    workflow.add_node("refine", refine_research)
    workflow.add_node("finalize", finalize_report)
    
    # Define edges
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "investigate")
    workflow.add_edge("investigate", "synthesize")
    workflow.add_edge("synthesize", "critique")
    workflow.add_conditional_edges(
        "critique",
        should_refine,
        {
            "refine": "investigate",  # Loop back to investigate gaps
            "finalize": "finalize"
        }
    )
    workflow.add_edge("finalize", END)
    
    return workflow.compile()


# --- Public API ---
async def run_deep_research(
    query: str,
    model_name: Optional[str] = None,
    max_iterations: int = 2,
) -> Dict[str, Any]:
    """
    Run deep research workflow on a query.
    
    Args:
        query: User's research question
        model_name: AI model to use (defaults to service default)
        max_iterations: Max refinement loops
    
    Returns:
        {
            "answer": str,
            "citations": List[Dict],
            "metadata": Dict (timings, iterations, etc.)
        }
    """
    if not LANGGRAPH_AVAILABLE:
        logger.error("LangGraph not available; cannot run deep research")
        return {
            "answer": "Deep research feature requires LangGraph. Please install: pip install langgraph",
            "citations": [],
            "metadata": {"error": "LangGraph not installed"}
        }
    
    enabled = os.getenv("DEEP_RESEARCH_ENABLED", "false").lower() == "true"
    if not enabled:
        logger.warning("Deep research disabled via DEEP_RESEARCH_ENABLED flag")
        return {
            "answer": "Deep research feature is disabled. Set DEEP_RESEARCH_ENABLED=true to enable.",
            "citations": [],
            "metadata": {"error": "Feature disabled"}
        }
    
    logger.info(f"Starting deep research for query: {query}")
    start_time = datetime.now()
    
    # Initialize state
    initial_state: ResearchState = {
        "query": query,
        "plan": None,
        "investigations": [],
        "draft_answer": None,
        "critique": None,
        "final_answer": None,
        "citations": [],
        "metadata": {
            "started_at": start_time.isoformat(),
            "model": model_name or "default",
        },
        "iteration": 0,
        "max_iterations": max_iterations,
    }
    
    # Build and run graph
    try:
        graph = build_research_graph()
        result = await graph.ainvoke(initial_state)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            "answer": result.get("final_answer", "No answer generated."),
            "citations": result.get("citations", []),
            "metadata": {
                **result.get("metadata", {}),
                "duration_seconds": duration,
                "iterations": result.get("iteration", 0),
            }
        }
    except Exception as e:
        logger.error(f"Deep research failed: {e}", exc_info=True)
        return {
            "answer": f"Deep research encountered an error: {e}",
            "citations": [],
            "metadata": {"error": str(e)}
        }


# Fallback for when LangGraph is not available
async def run_deep_research_fallback(query: str, model_name: Optional[str] = None) -> Dict[str, Any]:
    """Simplified fallback when LangGraph not installed."""
    from ..services.web_research_orchestrator import WebResearchOrchestrator
    orchestrator = WebResearchOrchestrator()
    result = await orchestrator.run(query, model_name=model_name, max_results=5)
    return {
        "answer": result.get("response", ""),
        "citations": result.get("citations", []),
        "metadata": {
            "fallback": True,
            "web_provider": result.get("web_provider"),
        }
    }
