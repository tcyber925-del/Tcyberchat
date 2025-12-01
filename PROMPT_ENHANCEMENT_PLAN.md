# Deep Research Prompt Enhancement - Implementation Plan

## Analysis Date: 2025-11-28

---

## Current State Analysis

### Current Synthesis Prompt (lines 104-115 in deep_research_graph.py)

```python
prompt = """You are a deep research assistant.
User Query: "{query}"

Here are the search results gathered:
{findings_text}

Write a comprehensive, detailed answer to the user's query based on these findings.
- Use markdown formatting.
- Cite sources using [Title](URL) format inline.
- Be objective and thorough.
- If the findings are insufficient, state what is missing.
"""
```

**Characteristics:**
- Generic instructions
- Basic markdown requirement
- Inline citation format: `[Title](URL)`
- Flexible structure
- No specific sections required

### Template Prompt (web_synthesis_prompt.txt)

```
You are a web research assistant. Use ONLY the sources in the Evidence Pack below.

Output rules:
- Be concise and factual. Avoid generic disclaimers.
- Use inline citations [1], [2], ... immediately after claims.
- Include a Sources section with numbered entries: "<Title> — <URL>".
- If no relevant sources exist, say "No recent results found." and stop.

Required Markdown Format:
## Summary
- 3–5 bullets with the most important updates [n]

## Key Developments
- Bullet points with short explanations and inline citations [n]

## What's New vs Previous Week/Month
- A couple of bullets highlighting deltas [n]

## Risks & Uncertainties
- Bullets (policy/technical/market) [n]

## Sources
1. <Title> — <URL>
2. <Title> — <URL>
```

**Characteristics:**
- Strict structure enforcement
- Numbered citations `[1]`, `[2]`
- Separate Sources section
- Focus on recency ("What's New")
- Includes risks/uncertainties
- More concise output

---

## Comparison Matrix

| Aspect | Current Prompt | Template Prompt | Winner |
|--------|---------------|-----------------|--------|
| **Structure** | Flexible | Strict sections | Template (better organization) |
| **Citations** | Inline `[Title](URL)` | Numbered `[1]` + Sources section | Template (easier to parse) |
| **Conciseness** | Verbose allowed | Enforced brevity | Template (better UX) |
| **Relevance Check** | Weak | Strong ("No recent results") | Template (clearer) |
| **Temporal Focus** | Generic | "What's New" section | Template (for research) |
| **Risk Analysis** | Not required | Required section | Template (more complete) |
| **Parsing Ease** | Hard (mixed citations) | Easy (numbered) | Template (better for code) |

---

## Recommendation: **HYBRID APPROACH** ✅

**Why not use template as-is?**
1. Template assumes "Evidence Pack" format we don't use
2. "What's New vs Previous Week/Month" doesn't fit all queries
3. Template is too rigid for varied research topics

**Why not keep current?**
1. Current lacks structure → hard to parse citations
2. No quality checks ("No recent results")
3. Too verbose for quick answers

**Best Solution: Enhanced Prompt**
Combine the strengths of both:
- Template's structure and citation system
- Current's flexibility and comprehensiveness
- Adapt sections dynamically based on query type

---

## Implementation Plan

### Phase 1: Create Enhanced Prompt Template

**File**: `src/services/prompts/deep_research_synthesis.txt`

```
You are an expert deep research analyst. Synthesize the search findings below into a clear, well-cited answer.

STRICT RULES:
- Use ONLY information from the findings below
- Cite sources using [1], [2], etc. immediately after each claim
- Be concise and factual - avoid generic disclaimers
- If findings are insufficient or irrelevant, say "No relevant sources found for this query." and explain what's missing

REQUIRED OUTPUT FORMAT:

## Summary
{2-4 concise bullet points covering the main findings with citations [n]}

## Detailed Analysis
{Comprehensive explanation organized by topic/theme with inline citations [n]}

## Key Insights
{2-3 bullets highlighting the most important or surprising findings [n]}

{IF_TEMPORAL_QUERY}
## Recent Developments
{Bullets focused on what's new/changed recently with citations [n]}
{/IF_TEMPORAL_QUERY}

{IF_COMPLEX_TOPIC}
## Considerations & Limitations
{Technical challenges, risks, or uncertainties mentioned in sources [n]}
{/IF_COMPLEX_TOPIC}

## Sources
{Numbered list matching citation numbers:}
1. <Title> — <URL>
2. <Title> — <URL>

---

USER QUERY:
{query}

SEARCH FINDINGS:
{findings}
```

### Phase 2: Update deep_research_graph.py

**Location**: `synthesize_node` function (lines 96-124)

**Changes**:
1. Load prompt template from file
2. Add query classification (temporal? complex?)
3. Format findings properly
4. Parse structured output

**New Code**:

```python
import os
from pathlib import Path

def load_prompt_template(name: str) -> str:
    """Load prompt template from file"""
    template_path = Path(__file__).parent.parent / "services" / "prompts" / f"{name}.txt"
    if template_path.exists():
        return template_path.read_text(encoding='utf-8')
    return None

def classify_query(query: str) -> dict:
    """Classify query characteristics"""
    query_lower = query.lower()
    return {
        'is_temporal': any(kw in query_lower for kw in ['latest', 'recent', 'new', 'current', '2024', '2025']),
        'is_complex': len(query.split()) > 8 or any(kw in query_lower for kw in ['how', 'why', 'explain']),
    }

async def synthesize_node(state: ResearchState):
    """Synthesizes findings into a final answer using enhanced template."""
    print("--- Synthesizing ---")
    client = get_groq_client(model="openai/gpt-oss-120b")
    
    # Load template
    template = load_prompt_template("deep_research_synthesis")
    if not template:
        # Fallback to inline prompt
        template = """..."""  # Use enhanced prompt as fallback
    
    # Classify query
    query_type = classify_query(state['query'])
    
    # Process template conditionals
    if not query_type['is_temporal']:
        template = template.replace("{IF_TEMPORAL_QUERY}", "").replace("{/IF_TEMPORAL_QUERY}", "")
    else:
        template = template.replace("{IF_TEMPORAL_QUERY}", "").replace("{/IF_TEMPORAL_QUERY}", "")
    
    if not query_type['is_complex']:
        template = template.replace("{IF_COMPLEX_TOPIC}", "").replace("{/IF_COMPLEX_TOPIC}", "")
    else:
        template = template.replace("{IF_COMPLEX_TOPIC}", "").replace("{/IF_COMPLEX_TOPIC}", "")
    
    # Format findings for better readability
    findings_formatted = format_findings_for_synthesis(state['findings'])
    
    # Fill template
    prompt = template.replace("{query}", state['query']).replace("{findings}", findings_formatted)
    
    # Generate response
    response = await asyncio.to_thread(
        client.generate,
        prompt=prompt,
        temperature=0.5,
        max_tokens=2048  # Increased for structured output
    )
    
    return {"draft": response}

def format_findings_for_synthesis(findings: List[str]) -> str:
    """Format findings with numbering for easy citation"""
    formatted = []
    citation_num = 1
    
    for finding in findings:
        # Add source numbering
        lines = finding.split('\n')
        for line in lines:
            if line.strip().startswith('- Title:'):
                formatted.append(f"\n[{citation_num}] " + line)
                citation_num += 1
            else:
                formatted.append(line)
    
    return '\n'.join(formatted)
```

### Phase 3: Citation Parsing (NEW)

Add citation extraction to return structured citations:

```python
def parse_citations_from_draft(draft: str, findings: List[str]) -> List[dict]:
    """Extract citations from the Sources section"""
    citations = []
    
    # Find Sources section
    if "## Sources" in draft:
        sources_section = draft.split("## Sources")[1].split("\n##")[0]
        lines = sources_section.strip().split('\n')
        
        for line in lines:
            if line.strip() and line[0].isdigit():
                # Parse: "1. Title — URL"
                parts = line.split(" — ", 1)
                if len(parts) == 2:
                    title = parts[0].split(". ", 1)[1].strip()
                    url = parts[1].strip()
                    citations.append({
                        "title": title,
                        "url": url,
                        "source": "web_search"
                    })
    
    return citations

# Update return in run_deep_research_graph:
return {
    "answer": final_state["draft"],
    "citations": parse_citations_from_draft(final_state["draft"], final_state["findings"]),
    "metadata": {
        "iterations": final_state["iteration"],
        "model": "groq:openai/gpt-oss-120b"
    }
}
```

---

## Implementation Timeline

### Step 1: Create Enhanced Template (15 min)
- Write `deep_research_synthesis.txt`
- Test placeholders

### Step 2: Update synthesize_node (30 min)
- Add template loading
- Add query classification
- Update findings formatting
- Test with various queries

### Step 3: Add Citation Parsing (20 min)
- Implement `parse_citations_from_draft`
- Update return format
- Test citation extraction

### Step 4: Testing (30 min)
- Test with temporal queries ("latest X")
- Test with complex queries ("how does X work")
- Test with simple queries ("what is X")
- Verify citation accuracy

**Total Estimated Time**: ~2 hours

---

## Benefits of Enhanced Approach

### 1. **Better Structure** ✅
- Consistent output format
- Easy to parse for UI
- Professional presentation

### 2. **Accurate Citations** ✅
- Numbered system easier to track
- Sources section separate
- Can extract programmatically

### 3. **Quality Control** ✅
- Detects insufficient results
- Requires evidence-based claims
- No hallucinations allowed

### 4. **Flexibility** ✅
- Adapts to query type
- Optional sections
- Not overly rigid

### 5. **User Experience** ✅
- Concise summaries
- Detailed analysis
- Clear source attribution

---

## Alternative: Simple Template Replacement

If you want the quickest implementation:

**Just replace synthesis prompt with template as-is**:

```python
# Load template
template_path = Path(__file__).parent.parent / "services" / "prompts" / "web_synthesis_prompt.txt"
template = template_path.read_text(encoding='utf-8')

prompt = template + f"\n\n{findings_text}"
```

**Pros**: 5 minutes to implement
**Cons**: May not fit all query types, rigid structure

---

## Final Recommendation

**Use the Hybrid Approach (Enhanced Template)**

**Reasoning**:
1. Better than current (structured, parseable)
2. Better than template alone (flexible, adaptable)
3. Small effort (2 hours) for significant quality gain
4. Future-proof (easy to extend sections)

**Start with**: Template replacement for quick win
**Then enhance**: Add query classification and dynamic sections

---

## Next Steps

Would you like me to:
1. ✅ **Implement the enhanced template** (recommended)
2. ✅ **Just use existing template** (quick)
3. ✅ **Create hybrid with query classification** (best)

Let me know your preference and I'll proceed with implementation!
