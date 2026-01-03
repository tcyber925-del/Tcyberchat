import os
import asyncio
import json
import logging
from typing import TypedDict, List, Annotated, Dict, Any, Optional, Literal
from pathlib import Path
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
import operator

# Import our services
from src.services.web_search_service import get_web_search_service
from src.services.web_fetch_service import get_web_fetch_service
from src.clients.groq_client import GroqClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define the state
class ResearchState(TypedDict):
    query: str
    plan: List[str]
    findings: Annotated[List[str], operator.add]
    draft: str
    critique_feedback: Optional[str]
    iteration: int
    max_iterations: int
    satisfied: bool

def get_groq_client(model: str = "llama-3.3-70b-versatile"):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found")
    return GroqClient(api_key=api_key, model=model)

# --- Helper Functions ---

def load_prompt_template(name: str) -> Optional[str]:
    """Load prompt template from file"""
    try:
        template_path = Path(__file__).parent.parent / "services" / "prompts" / f"{name}.txt"
        if template_path.exists():
            return template_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.warning(f"Could not load template {name}: {e}")
    return None

def classify_query(query: str) -> dict:
    """Classify query characteristics for dynamic prompt sections"""
    query_lower = query.lower()
    return {
        'is_temporal': any(kw in query_lower for kw in [
            'latest', 'recent', 'new', 'current', 'today', 
            '2024', '2025', 'this year', 'this month'
        ]),
        'is_complex': len(query.split()) > 8 or any(kw in query_lower for kw in [
            'how', 'why', 'explain', 'compare', 'difference', 'relationship'
        ]),
    }

def format_findings_for_synthesis(findings: List[str]) -> str:
    """Format findings with clear numbering for citation"""
    formatted_parts = []
    
    for finding in findings:
        formatted_parts.append(finding)
    
    return '\n\n'.join(formatted_parts)

def parse_citations_from_draft(draft: str) -> List[dict]:
    """Extract citations from the Sources section of the generated draft"""
    citations = []
    
    try:
        if "## Sources" in draft:
            sources_section = draft.split("## Sources")[1]
            if "\n##" in sources_section:
                sources_section = sources_section.split("\n##")[0]
            
            lines = sources_section.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if line and line[0].isdigit():
                    parts = None
                    if " — " in line:
                        parts = line.split(" — ", 1)
                    elif " - " in line:
                        parts = line.split(" - ", 1)
                    
                    if parts and len(parts) == 2:
                        title_part = parts[0]
                        if ". " in title_part:
                            title = title_part.split(". ", 1)[1].strip()
                        else:
                            title = title_part.strip()
                        
                        url = parts[1].strip()
                        
                        citations.append({
                            "title": title,
                            "url": url,
                            "source": "web_search"
                        })
    except Exception as e:
        logger.warning(f"Could not parse citations: {e}")
    
    return citations

# --- Nodes ---

async def plan_node(state: ResearchState):
    """Generates a research plan (list of search queries)."""
    logger.info(f"--- Planning (Iteration {state.get('iteration', 0)}) ---")
    
    try:
        if state.get("iteration", 0) > 0 and state.get("plan"):
            logger.info(f"Using follow-up queries from critique: {state['plan']}")
            return {"plan": state['plan']}

        client = get_groq_client(model="openai/gpt-oss-120b")
        
        prompt = f"""You are a senior research planner.
User Query: "{state['query']}"

Break this query down into 2-3 distinct, specific web search queries that will gather comprehensive information to answer the user.
Return ONLY a JSON array of strings. Example: ["query 1", "query 2"]
Do not include any other text."""

        response = await asyncio.to_thread(
            client.generate,
            prompt=prompt,
            temperature=0.3
        )
        
        content = response.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        plan = json.loads(content.strip())
        if not isinstance(plan, list):
            plan = [state['query']]
            
        logger.info(f"Generated initial plan with {len(plan)} queries")
        return {"plan": plan[:3], "iteration": 0}
        
    except Exception as e:
        logger.error(f"Planning error: {e}", exc_info=True)
        return {"plan": [state['query']], "iteration": 0}

async def investigate_node(state: ResearchState):
    """Executes search queries and fetches limited content to stay within token limits."""
    queries = state['plan']
    logger.info(f"--- Investigating: {len(queries)} queries ---")
    
    web_search = get_web_search_service()
    web_fetch = get_web_fetch_service()
    
    async def process_single_query(query):
        try:
            # 1. Search (Reduced to top 2 for context)
            search_results = await web_search.search(query, max_results=2)
            if not search_results:
                return f"No results found for query: {query}"
                
            # 2. Fetch Content (Deep Fetching)
            urls = [r.url for r in search_results if r.url][:2]
            fetched_pages = await web_fetch.fetch_multiple(urls)
            
            # 3. Format
            formatted_results = []
            formatted_results.append(f"### Search Query: {query}")
            
            for i, (search_res, page) in enumerate(zip(search_results, fetched_pages)):
                title = page.title or search_res.title or "Untitled"
                url = page.url or search_res.url
                content = page.content or search_res.snippet or ""
                
                # Heavily truncate to stay within Groq's 8k TPM limit
                # 3000 chars is roughly 750 tokens. With 4-6 sources, we reach 3000-4500 tokens.
                content = content[:3000]
                if len(content) >= 3000:
                    content += "...(truncated)"
                
                formatted_results.append(
                    f"#### Source: {title}\n"
                    f"URL: {url}\n"
                    f"Content:\n{content}\n"
                )
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"Error investigating '{query}': {e}")
            return f"Error investigating '{query}': {e}\n"

    tasks = [process_single_query(q) for q in queries]
    results = await asyncio.gather(*tasks)
    
    return {"findings": results}

async def synthesize_node(state: ResearchState):
    """Synthesizes findings into a final answer using enhanced template."""
    logger.info("--- Synthesizing ---")
    
    try:
        # Use standard model if reasoning model limits are too tight, 
        # but let's try to stick with the planner's model first with reduced context.
        client = get_groq_client(model="openai/gpt-oss-120b")
        
        template = load_prompt_template("deep_research_synthesis")
        findings_formatted = format_findings_for_synthesis(state['findings'])
        
        if template:
            query_type = classify_query(state['query'])
            temporal_section = ""
            if query_type['is_temporal']:
                temporal_section = "## Recent Developments\n- Recent breakthroughs with citations [n]\n"
            
            complex_section = ""
            if query_type['is_complex']:
                complex_section = "## Technical Considerations\n- Challenges and limitations with citations [n]\n"
            
            template = template.replace("{TEMPORAL_SECTION}", temporal_section)
            template = template.replace("{COMPLEX_SECTION}", complex_section)
            prompt = template.replace("{query}", state['query']).replace("{findings}", findings_formatted)
        else:
            prompt = f"Query: {state['query']}\n\nFindings:\n{findings_formatted}\n\nWrite a detailed research report with inline citations."
        
        response = await asyncio.to_thread(
            client.generate,
            prompt=prompt,
            temperature=0.5,
            max_tokens=2048
        )
        
        return {"draft": response}
        
    except Exception as e:
        logger.error(f"Synthesis error: {e}", exc_info=True)
        # Try one last time with a model that might have higher limits if reasoning fails
        try:
            logger.info("Retrying synthesis with llama-3.3-70b-versatile...")
            client_fallback = get_groq_client(model="llama-3.3-70b-versatile")
            response = await asyncio.to_thread(client_fallback.generate, prompt=prompt, temperature=0.5)
            return {"draft": response}
        except Exception as e2:
            return {"draft": f"I encountered an error while synthesizing: {str(e2)}"}

async def critique_node(state: ResearchState):
    """Reviews the draft and decides if more research is needed."""
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", 3)
    
    logger.info(f"--- Critique (Iteration {iteration}/{max_iter}) ---")
    if iteration >= max_iter:
        return {"satisfied": True}

    try:
        client = get_groq_client(model="llama-3.3-70b-versatile")
        prompt = f"""Evaluate if this research report covers "{state['query']}" comprehensively.
Report:
{state['draft'][:2000]}...\n
If not satisfied, provide 1-2 specific follow-up search queries.
Return JSON: {{'satisfied': bool, 'feedback': '...', 'follow_up_queries': []}}"""

        response = await asyncio.to_thread(client.generate, prompt=prompt, temperature=0.1)
        content = response.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        result = json.loads(content.strip())
        satisfied = result.get("satisfied", False)
        
        if not satisfied and result.get("follow_up_queries"):
            return {
                "satisfied": False,
                "plan": result["follow_up_queries"][:2],
                "iteration": iteration + 1
            }
        return {"satisfied": True}
    except Exception as e:
        logger.error(f"Critique error: {e}")
        return {"satisfied": True}

def route_critique(state: ResearchState) -> Literal["plan", "end"]:
    if state.get("satisfied", True):
        return "end"
    return "plan"

def create_research_graph():
    workflow = StateGraph(ResearchState)
    workflow.add_node("plan", plan_node)
    workflow.add_node("investigate", investigate_node)
    workflow.add_node("synthesize", synthesize_node)
    workflow.add_node("critique", critique_node)
    
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "investigate")
    workflow.add_edge("investigate", "synthesize")
    workflow.add_edge("synthesize", "critique")
    workflow.add_conditional_edges("critique", route_critique, {"plan": "plan", "end": END})
    
    return workflow.compile()

async def run_deep_research_graph(query: str, max_iterations: int = 3):
    try:
        graph = create_research_graph()
        initial_state = {
            "query": query,
            "plan": [],
            "findings": [],
            "draft": "",
            "iteration": 0,
            "max_iterations": max_iterations,
            "satisfied": False
        }
        final_state = await graph.ainvoke(initial_state)
        citations = parse_citations_from_draft(final_state["draft"])
        return {
            "answer": final_state["draft"],
            "citations": citations,
            "metadata": {
                "iterations": final_state["iteration"],
                "model": "groq:mixed",
                "satisfied": final_state.get("satisfied", True)
            }
        }
    except Exception as e:
        logger.error(f"Graph error: {e}", exc_info=True)
        raise
