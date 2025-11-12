"""
Web-enabled agent setup with search and fetch tools

This module provides optional agent configurations that can use web search
and web fetch capabilities. The agent can be configured to use either:
1. Local llama.cpp backend (via existing llama_cpp_client)
2. OpenAI-compatible API endpoint
3. Any LangChain-compatible LLM

This is completely optional and doesn't affect the main chat API.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Check if LangChain is available
try:
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain.prompts import PromptTemplate
    from langchain.tools import BaseTool

    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning(
        "LangChain not available. Web agent functionality will not be available."
    )
    LANGCHAIN_AVAILABLE = False


def get_llm_for_agent(model_endpoint: str | None = None, model_name: str | None = None):
    """
    Get an LLM instance for the agent

    Args:
        model_endpoint: Optional OpenAI-compatible API endpoint (e.g., http://localhost:8080/v1)
        model_name: Optional model name

    Returns:
        LLM instance compatible with LangChain

    Raises:
        ImportError: If required LangChain packages not available
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain is required. Install with: pip install langchain")

    try:
        from langchain_community.llms import OpenAI
    except ImportError:
        raise ImportError(
            "langchain-community required. Install with: pip install langchain-community"
        )

    # Default to environment variable or localhost
    endpoint = model_endpoint or os.getenv(
        "AGENT_LLM_ENDPOINT", "http://localhost:8080/v1"
    )
    model = model_name or os.getenv("AGENT_LLM_MODEL", "local-llama")

    logger.info(f"Creating LLM for agent: endpoint={endpoint}, model={model}")

    # Create OpenAI-compatible LLM pointing to local llama.cpp or other server
    llm = OpenAI(
        openai_api_base=endpoint,
        openai_api_key="none",  # Not needed for local
        model_name=model,
        temperature=0.7,
        max_tokens=1024,
    )

    return llm


def create_web_agent(
    llm: Any | None = None,
    model_endpoint: str | None = None,
    model_name: str | None = None,
    verbose: bool = True,
) -> AgentExecutor | None:
    """
    Create a web-enabled agent with search and fetch tools

    Args:
        llm: Optional LLM instance (if not provided, will create one)
        model_endpoint: Optional OpenAI-compatible API endpoint
        model_name: Optional model name
        verbose: Enable verbose logging

    Returns:
        AgentExecutor instance or None if dependencies not available

    Example:
        >>> agent = create_web_agent()
        >>> response = agent.run("Find the latest llama.cpp benchmarks")
        >>> print(response)
    """
    if not LANGCHAIN_AVAILABLE:
        logger.error("LangChain not available. Cannot create web agent.")
        return None

    try:
        from ..tools.web_fetch_tool import get_web_fetch_tool
        from ..tools.web_search_tool import get_web_search_tool
    except ImportError as e:
        logger.error(f"Failed to import web tools: {e}")
        return None

    # Get or create LLM
    if llm is None:
        try:
            llm = get_llm_for_agent(model_endpoint, model_name)
        except Exception as e:
            logger.error(f"Failed to create LLM for agent: {e}")
            return None

    # Create tools
    tools: list[BaseTool] = []

    try:
        web_search_tool = get_web_search_tool()
        tools.append(web_search_tool)
        logger.info("Added web_search tool to agent")
    except Exception as e:
        logger.warning(f"Failed to create web_search_tool: {e}")

    try:
        web_fetch_tool = get_web_fetch_tool()
        tools.append(web_fetch_tool)
        logger.info("Added web_fetch tool to agent")
    except Exception as e:
        logger.warning(f"Failed to create web_fetch_tool: {e}")

    if not tools:
        logger.error("No tools available for agent")
        return None

    # Create ReAct agent with custom prompt
    react_prompt = PromptTemplate.from_template(
        """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT: Always provide a Final Answer, even if you couldn't find complete information.

Begin!

Question: {input}
Thought: {agent_scratchpad}"""
    )

    try:
        # Create agent
        agent = create_react_agent(llm, tools, react_prompt)

        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=verbose,
            max_iterations=5,  # Limit iterations to prevent infinite loops
            max_execution_time=60,  # 60 second timeout
            handle_parsing_errors=True,
            return_intermediate_steps=False,
        )

        logger.info(f"Created web agent with {len(tools)} tools")

        return agent_executor

    except Exception as e:
        logger.error(f"Failed to create agent: {e}", exc_info=True)
        return None


def get_web_agent(
    model_endpoint: str | None = None,
    model_name: str | None = None,
    verbose: bool = False,
) -> AgentExecutor | None:
    """
    Convenience function to get a configured web agent

    Args:
        model_endpoint: Optional OpenAI-compatible API endpoint
        model_name: Optional model name
        verbose: Enable verbose logging

    Returns:
        AgentExecutor instance or None if not available

    Example:
        >>> from backend.src.agents.web_agent import get_web_agent
        >>> agent = get_web_agent()
        >>> if agent:
        ...     result = agent.run("What are the newest AI models from Meta?")
        ...     print(result)
    """
    return create_web_agent(
        model_endpoint=model_endpoint, model_name=model_name, verbose=verbose
    )


# Example usage for testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Web Agent Test")
    print("=" * 60)

    # Try to create agent
    agent = get_web_agent(verbose=True)

    if agent:
        print("\n✓ Agent created successfully")
        print(f"  Tools: {[tool.name for tool in agent.tools]}")

        # Test query
        test_query = "Search for the latest llama.cpp performance benchmarks"
        print(f"\nTest Query: {test_query}")
        print("-" * 60)

        try:
            result = agent.run(test_query)
            print("\nResult:")
            print(result)
        except Exception as e:
            print(f"\n✗ Error running agent: {e}")
    else:
        print("\n✗ Failed to create agent")
        print("  Make sure:")
        print("  1. LangChain is installed: pip install langchain langchain-community")
        print("  2. llama.cpp server is running on http://localhost:8080/v1")
        print("     OR set AGENT_LLM_ENDPOINT environment variable")
