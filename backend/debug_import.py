try:
    import deepagents
    print(f"deepagents imported: {deepagents}")
    from deepagents import create_deep_agent
    print("create_deep_agent imported")
    from langchain_core.tools import tool
    print("langchain_core.tools imported")
    from langchain.chat_models import init_chat_model
    print("langchain.chat_models imported")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
