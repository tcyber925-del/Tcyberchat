import os
import asyncio
import json
import logging
from typing import TypedDict, List, Annotated, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
import operator

# Import our services
from src.services.web_search_service import get_web_search_service
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
    critique: Optional[str]
    iteration: int
    max_iterations: int

# Initialize services
web_search = get_web_search_service()

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
    citation_num = 1
    
    for finding_idx, finding in enumerate(findings):
        # Add separator between different search queries
        formatted_parts.append(f"\n--- Search Result Set {finding_idx + 1} ---\n")
        
        lines = finding.split('\n')
        current_source = {}
        
        for line in lines:
            line_stripped = line.strip()
            
            if line_stripped.startswith('### Search Query:'):
                formatted_parts.append(line)
            elif line_stripped.startswith('- Title:'):
                # Start new source
                current_source = {'num': citation_num, 'title': line_stripped[8:].strip()}
                citation_num += 1
            elif line_stripped.startswith('URL:'):
                current_source['url'] = line_stripped[4:].strip()
            elif line_stripped.startswith('Snippet:'):
                current_source['snippet'] = line_stripped[8:].strip()
                # Complete source entry
                formatted_parts.append(
                    f"\n[{current_source['num']}] {current_source['title']}\n"
                    f"    URL: {current_source['url']}\n"
                    f"    {current_source['snippet']}\n"
                )
                current_source = {}
    
    return '\n'.join(formatted_parts)

def parse_citations_from_draft(draft: str) -> List[dict]:
    """Extract citations from the Sources section of the generated draft"""
    citations = []
    
    try:
        if "## Sources" in draft:
            sources_section = draft.split("## Sources")[1]
            # Stop at next ## or end of text
            if "\n##" in sources_section:
                sources_section = sources_section.split("\n##")[0]
            
            lines = sources_section.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                # Match format: "1. Title — URL" or "1. Title - URL"
                if line and line[0].isdigit():
                    # Try both em dash and hyphen
                    parts = None
                    if " — " in line:
                        parts = line.split(" — ", 1)
                    elif " - " in line:
                        parts = line.split(" - ", 1)
                    
                    if parts and len(parts) == 2:
                        # Remove number and dot from title
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
    logger.info(f"--- Planning: {state['query']} ---")
    
    try:
        # Use reasoning model for planning
        client = get_groq_client(model="openai/gpt-oss-120b")
        
        prompt = f"""You are a senior research planner.
User Query: "{state['query']}"

Break this query down into 3-5 distinct, specific web search queries that will gather comprehensive information to answer the user.
Return ONLY a JSON array of strings. Example: ["query 1", "query 2"]
Do not include any other text."""

        # Run sync generation in thread
        response = await asyncio.to_thread(
            client.generate,
            prompt=prompt,
            temperature=0.3
        )
        
        # Clean up potential markdown code blocks
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
            
        logger.info(f"Generated plan with {len(plan)} queries")
        return {"plan": plan, "iteration": 0}
        
    except Exception as e:
        logger.error(f"Planning error: {e}", exc_info=True)
        # Fallback to single query on error
        return {"plan": [state['query']], "iteration": 0}

async def investigate_node(state: ResearchState):
    """Executes search queries in parallel."""
    logger.info(f"--- Investigating: {len(state['plan'])} queries ---")
    
    async def search_single(query):
        try:
            results = await web_search.search(query, max_results=3)
            # Format results
            formatted = f"### Search Query: {query}\n"
            for r in results:
                formatted += f"- Title: {r.title}\n  URL: {r.url}\n  Snippet: {r.snippet}\n\n"
            return formatted
        except Exception as e:
            logger.error(f"Error searching for '{query}': {e}")
            return f"Error searching for '{query}': {e}\n"

    # Run searches in parallel
    tasks = [search_single(q) for q in state['plan']]
    results = await asyncio.gather(*tasks)
    
    return {"findings": results}

async def synthesize_node(state: ResearchState):
    """Synthesizes findings into a final answer using enhanced template."""
    logger.info("--- Synthesizing ---")
    
    try:
        client = get_groq_client(model="openai/gpt-oss-120b")
        
        # Load enhanced template
        template = load_prompt_template("deep_research_synthesis")
        
        if template:
            # Classify query to determine which sections to include
            query_type = classify_query(state['query'])
            
            # Add temporal section if needed
            temporal_section = ""
            if query_type['is_temporal']:
                temporal_section = """## Recent Developments
- Bullets focused on what's new/changed recently with citations [n]
"""
            
            # Add complex topic section if needed
            complex_section = ""
            if query_type['is_complex']:
                complex_section = """## Considerations & Limitations
- Technical challenges, risks, or uncertainties mentioned in sources [n]
"""
            
            # Replace placeholders
            template = template.replace("{TEMPORAL_SECTION}", temporal_section)
            template = template.replace("{COMPLEX_SECTION}", complex_section)
            
            # Format findings for better citation
            findings_formatted = format_findings_for_synthesis(state['findings'])
            
            # Fill in query and findings
            prompt = template.replace("{query}", state['query']).replace("{findings}", findings_formatted)
        else:
            # Fallback to inline prompt if template not found
            findings_text = "\n".join(state['findings'])
            prompt = f"""You are a deep research assistant.
User Query: "{state['query']}"

Here are the search results gathered:
{findings_text}

Write a comprehensive, detailed answer to the user's query based on these findings.
- Use markdown formatting.
- Cite sources using [1], [2], etc. format inline.
- Include a Sources section at the end.
- Be objective and thorough.
- If the findings are insufficient, state what is missing."""
        
        # Run sync generation in thread
        response = await asyncio.to_thread(
            client.generate,
            prompt=prompt,
            temperature=0.5,
            max_tokens=2048
        )
        
        return {"draft": response}
        
    except Exception as e:
        logger.error(f"Synthesis error: {e}", exc_info=True)
        return {"draft": f"I encountered an error while synthesizing the research results: {str(e)}. Please try again."}

async def critique_node(state: ResearchState):
    """Reviews the draft and decides if more research is needed."""
    # For now, we'll keep it simple and just stop after one pass unless explicitly requested
    # This node can be expanded for iterative refinement
    return {"critique": "looks good"}

# --- Graph Construction ---

def create_research_graph():
    workflow = StateGraph(ResearchState)
    
    # Add nodes
    workflow.add_node("plan", plan_node)
    workflow.add_node("investigate", investigate_node)
    workflow.add_node("synthesize", synthesize_node)
    
    # Define edges
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "investigate")
    workflow.add_edge("investigate", "synthesize")
    workflow.add_edge("synthesize", END)
    
    return workflow.compile()

# --- Main Entry Point ---

async def run_deep_research_graph(query: str, max_iterations: int = 1):
    """Runs the deep research graph with enhanced synthesis."""
    try:
        graph = create_research_graph()
        
        initial_state = {
            "query": query,
            "plan": [],
            "findings": [],
            "draft": "",
            "critique": None,
            "iteration": 0,
            "max_iterations": max_iterations
        }
        
        final_state = await graph.ainvoke(initial_state)
        
        # Parse citations from the structured output
        citations = parse_citations_from_draft(final_state["draft"])
        
        return {
            "answer": final_state["draft"],
            "citations": citations,
            "metadata": {
                "iterations": final_state["iteration"],
                "model": "groq:openai/gpt-oss-120b",
                "citations_found": len(citations)
            }
        }
    except Exception as e:
        logger.error(f"Graph execution error: {e}", exc_info=True)
        raise
