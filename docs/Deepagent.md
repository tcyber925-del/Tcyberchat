Perfect! Now I have comprehensive information from the official LangChain documentation. Let me create a detailed guide for implementing deep agents.

## How to Implement Deep Agents in Your Deep Research Agent Project

Deep Agents is an advanced agent architecture built on LangGraph that empowers AI agents to handle complex, multi-step research tasks with planning, context management, and specialized sub-agent delegation. Here's a comprehensive implementation guide based on the official LangChain documentation.[1][2]

### Understanding Deep Agents Architecture

Deep Agents differs from traditional agents by combining four interconnected capabilities:[1]

**Planning and task decomposition**: Agents use the built-in `write_todos` tool to break complex tasks into manageable steps, track progress, and adapt plans as new information emerges.[3]

**Context management**: File system tools (`ls`, `read_file`, `write_file`, `edit_file`) allow agents to offload large context to memory, preventing context window overflow and enabling work with variable-length tool results.[3]

**Sub-agent spawning**: A built-in `task` tool enables agents to spawn specialized sub-agents for context isolation, keeping the main agent's context clean while working deeply on specific subtasks.[3]

**Long-term memory**: Agents can extend their memory across conversations and threads using LangGraph's Store, enabling them to save and retrieve information from previous interactions.[3]

### Installation and Setup

Begin by installing the required dependencies:[2]

```bash
pip install deepagents tavily-python
```

Set up your environment variables for API keys:[2]

```bash
export ANTHROPIC_API_KEY="your-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```

### Step-by-Step Implementation

#### Step 1: Create Your Tools

Define the tools your agent needs. For deep research, a web search tool is essential:[2]

```python
import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )
```

#### Step 2: Define Custom System Prompt

Create a detailed system prompt that guides your agent's behavior. This should include specific instructions for your research use case:[2]

```python
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""
```

#### Step 3: Create Sub-Agents (Optional but Recommended)

Sub-agents are specialized agents that handle specific tasks, keeping your main agent's context clean. Define them as dictionaries with required and optional fields:[4]

```python
# Research sub-agent for in-depth research
research_subagent = {
    "name": "research-agent",
    "description": "Conducts in-depth research on specific topics using web search and synthesizes findings",
    "system_prompt": """You are a thorough researcher. Your job is to:
1. Break down the research question into searchable queries
2. Use internet_search to find relevant information
3. Synthesize findings into a comprehensive summary
4. Cite sources when making claims

Output format:
- Summary (2-3 paragraphs)
- Key findings (bullet points)
- Sources (with URLs)

Keep your response under 500 words to maintain clean context.""",
    "tools": [internet_search],
    "model": "openai:gpt-4o",  # Optional: override main agent model
}

# Critique sub-agent for quality review
critique_subagent = {
    "name": "critique-agent",
    "description": "Reviews and critiques research reports for accuracy, completeness, and tone",
    "system_prompt": """You are a policy editor reviewing a research report. Check for:
- Accuracy and completeness of information
- Proper citation of sources
- Balanced analysis
- Clarity and neutrality of tone

Provide constructive feedback.""",
    "tools": [internet_search],
}

subagents = [research_subagent, critique_subagent]
```

#### Step 4: Initialize the Deep Agent

Pass your tools, system prompt, and sub-agents to `create_deep_agent`:[2]

```python
from langchain.chat_models import init_chat_model

# Initialize your model
model = init_chat_model(model="gpt-4o")

# Create the deep agent
agent = create_deep_agent(
    model=model,
    tools=[internet_search],
    system_prompt=research_instructions,
    subagents=subagents
)
```

#### Step 5: Invoke the Agent

Execute your deep agent with a research query:[2]

```python
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "What are the latest updates on the EU AI Act and its global impact?"
    }]
})

# Print the agent's response
print(result["messages"][-1].content)
```

### Built-in Tools and Capabilities

Your deep agent automatically has access to these tools without additional configuration:[4]

| Tool | Purpose |
|------|---------|
| `write_todos` | Update the agent's to-do list for task planning |
| `ls` | List all files in the agent's filesystem |
| `read_file` | Read a file from the agent's filesystem |
| `write_file` | Write a new file in the agent's filesystem |
| `edit_file` | Edit an existing file in the agent's filesystem |
| `task` | Spawn a sub-agent to handle a specific task |

### Customization Options

#### Changing Models

Deep Agents defaults to Claude Sonnet 4.5, but you can use any LangChain-supported model:[4]

```python
from langchain.chat_models import init_chat_model

# Use OpenAI GPT-4
model = init_chat_model(model="openai:gpt-4o")

# Use Google Gemini
model = init_chat_model(model="google_genai:gemini-2.5-flash")

agent = create_deep_agent(model=model, tools=[internet_search])
```

#### Advanced Sub-Agent Patterns

For complex workflows, create multiple specialized sub-agents:[4]

```python
subagents = [
    {
        "name": "data-collector",
        "description": "Gathers raw data from various sources",
        "system_prompt": "Collect comprehensive data on the topic",
        "tools": [internet_search],
    },
    {
        "name": "data-analyzer",
        "description": "Analyzes collected data for insights",
        "system_prompt": "Analyze data and extract key insights",
        "tools": [internet_search],
    },
    {
        "name": "report-writer",
        "description": "Writes polished reports from analysis",
        "system_prompt": "Create professional reports from insights",
        "tools": [internet_search],
    }
]

agent = create_deep_agent(
    model=model,
    system_prompt="You coordinate data analysis and reporting. Use subagents for specialized tasks.",
    subagents=subagents
)
```

#### Using Pre-built LangGraph Graphs as Sub-Agents

For even more complex scenarios, you can use existing LangGraph graphs:[4]

```python
from deepagents import CompiledSubAgent
from langchain.agents import create_agent

# Create a custom agent graph
custom_graph = create_agent(
    model=your_model,
    tools=specialized_tools,
    prompt="You are a specialized agent for data analysis..."
)

# Wrap it as a sub-agent
custom_subagent = CompiledSubAgent(
    name="data-analyzer",
    description="Specialized agent for complex data analysis tasks",
    runnable=custom_graph
)

agent = create_deep_agent(
    model=model,
    tools=[internet_search],
    system_prompt=research_instructions,
    subagents=[custom_subagent]
)
```

### Middleware Architecture

Deep Agents automatically applies three middleware components:[5]

**TodoListMiddleware**: Provides the `write_todos` tool for planning and task management.

**FilesystemMiddleware**: Provides file system tools (`ls`, `read_file`, `write_file`, `edit_file`) for context management.

**SubAgentMiddleware**: Provides the `task` tool for spawning specialized sub-agents.

For advanced use cases, you can customize middleware:[5]

```python
from langchain.agents import create_agent
from deepagents.middleware import FilesystemMiddleware
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

agent = create_agent(
    model=model,
    middleware=[
        FilesystemMiddleware(
            backend=lambda rt: CompositeBackend(
                default=StateBackend(rt),
                routes={"/memories/": StoreBackend(rt)}
            ),
        ),
    ],
)
```

### Best Practices for Deep Research Agents

**Write clear sub-agent descriptions**: The main agent uses descriptions to decide which sub-agent to call. Be specific and action-oriented:[4]

```python
# ✅ Good
"description": "Analyzes financial data and generates investment insights with confidence scores"

# ❌ Bad
"description": "Does finance stuff"
```

**Minimize tool sets**: Only give sub-agents the tools they need. This improves focus and security.[4]

**Keep system prompts detailed**: Include specific guidance on how to use tools and format outputs.[4]

**Instruct sub-agents to return concise results**: This prevents context bloat:[4]

```python
"system_prompt": """...your instructions...
IMPORTANT: Return only the essential summary. Do NOT include raw data or intermediate results.
Your response should be under 500 words."""
```

**Delegate complex tasks**: Instruct your main agent to delegate multi-step work to sub-agents:[4]

```python
system_prompt = """...your instructions...
IMPORTANT: For complex tasks, delegate to your subagents using the task() tool. 
This keeps your context clean and improves results."""
```

### What Happens When Your Agent Runs

When you invoke your deep agent, it automatically:[2]

Breaks down the research task into manageable steps using the `write_todos` tool, conducts research by calling the `internet_search` tool multiple times, manages context overflow by using file system tools (`write_file`, `read_file`), spawns sub-agents as needed using the `task` tool for specialized work, and synthesizes findings into a comprehensive, well-structured report with citations.

### Deployment and Monitoring

Deep Agents are built on LangGraph, so they work seamlessly with:[3]

**LangGraph Studio**: For local development and debugging

**LangSmith**: For observability, evaluation, and production monitoring

Deploy your agent as a LangGraph API by running:[6]

```bash
langraph dev
```

This starts a local development server where you can test your agent before production deployment.

### Key Takeaway

Deep Agents transform simple tool-calling agents into sophisticated systems that can plan, delegate, manage complex context, and execute multi-step research workflows with the same principles used by advanced applications like Claude Code and Deep Research. For your deep research agent project, this architecture enables handling complex, long-horizon research tasks while maintaining clean context and producing high-quality outputs.[1][2][4]

[1](https://dev.to/samadhi_patil_294a4ff7fea/building-advanced-ai-agents-with-langchains-deepagents-a-hands-on-guide-1bk4)
[2](https://docs.langchain.com/oss/python/deepagents/quickstart)
[3](https://docs.langchain.com/oss/python/deepagents/overview)
[4](https://docs.langchain.com/oss/python/deepagents/customization)
[5](https://docs.langchain.com/oss/python/deepagents/middleware)
[6](https://www.youtube.com/watch?v=5tn6O0uXYEg)
[7](https://www.linkedin.com/pulse/building-deep-research-agent-langchain-gemini-tavily-hiram-reis-neto-vxqmf)
[8](https://siriusdigital.us/meet-langchains-deepagents-library-and-a-practical-example-to-see-how-deepagents-actually-work-in-action/)
[9](https://www.datacamp.com/tutorial/deep-agents)
[10](https://www.reddit.com/r/LangChain/comments/1kmfcrp/built_a_local_deep_research_agent_using_qwen3/)
[11](https://www.youtube.com/watch?v=AZ6257Ya_70)
[12](https://www.reddit.com/r/LangChain/comments/1j98fpt/langchain_deepresearch_i_built_an_autonomous/)
[13](https://www.linkedin.com/posts/ravi-chauhan-6b8715190_deep-agents-overview-docs-by-langchain-activity-7387529811642048512--7xY)
[14](https://github.com/langchain-ai/deepagents)
[15](https://pypi.org/project/deepagents/0.0.10/)
[16](https://www.flowhunt.io/blog/building-extensible-ai-agents-with-langchain-1-0/)
[17](https://docs.langchain.com/oss/javascript/deepagents/quickstart)
[18](https://pypi.org/project/deepagents/0.0.6/)
[19](https://colinmcnamara.com/blog/langchain-middleware-v1-alpha-guide)
[20](https://langchain-5e9cc07a-preview-custom-1757090078-b891f4e.mintlify.app/labs/deep-agents/configuration-options)
[21](https://colinmcnamara.com/blog/deep-agents-part-4-usage-integration-roadmap)
[22](https://www.youtube.com/watch?v=AZ6257Ya_70&ab_channel=LangChain)
[23](https://docs.langchain.com/oss/python/deepagents/subagents)
[24](https://langchain-5e9cc07a-preview-manage-1758134194-1b52021.mintlify.app/labs/deep-agents/configuration-options)
[25](https://kr.langchain-docs.com/oss/python/deepagents/subagents)
[26](https://reference.langchain.com/python/deepagents/)