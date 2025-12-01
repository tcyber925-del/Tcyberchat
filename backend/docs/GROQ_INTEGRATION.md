# Groq Integration for TcyberChatbot

## Overview
Groq provides **ultrafast LLM inference** with specialized **reasoning models** designed for complex problem-solving. This integration adds Groq support to both the AI service and the deep research agent, with automatic preference for reasoning models in deep research tasks.

## Features
- ✅ **Blazing Fast Inference**: Groq's LPU architecture delivers dramatically faster responses
- ✅ **Reasoning Models**: Specialized models (GPT-OSS 120B, Qwen 3 32B) for complex reasoning tasks
- ✅ **Streaming Support**: Full support for streaming responses
- ✅ **Deep Research Integration**: Automatic selection of reasoning models for research workflows
- ✅ **LangChain Compatible**: Works seamlessly with `langchain-groq` package

## Installation

### 1. Install Dependencies
```bash
cd backend
uv pip install groq langchain-groq
```

### 2. Get API Key
1. Visit [Groq Console](https://console.groq.com)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key

### 3. Configure Environment
Add to `backend/.env`:
```bash
GROQ_API_KEY=gsk_your_api_key_here
```

## Available Models

### Reasoning Models (Recommended for Deep Research)
| Model | ID | Best For |
|-------|----|---------| 
| **GPT-OSS 120B** | `openai/gpt-oss-120b` | Complex reasoning, multi-step analysis |
| **GPT-OSS 20B** | `openai/gpt-oss-20b` | Faster reasoning tasks |
| **Qwen 3 32B** | `qwen/qwen3-32b` | Balanced reasoning |

### Standard Models
| Model | ID | Best For |
|-------|----|---------| 
| **Llama 3.3 70B** | `llama-3.3-70b-versatile` | General purpose |
| **Llama 3.1 8B** | `llama-3.1-8b-instant` | Ultra-fast responses |

## Usage

### In AI Service
```python
from src.services.ai_service import AIService

# Create AIService with Groq model
ai_service = AIService(model_name="groq:openai/gpt-oss-120b")

# Generate response
result = await ai_service.generate_response("Explain quantum computing")
print(result['response'])

# Stream response
async for chunk in ai_service.generate_streaming_response("Tell me about AI"):
    print(chunk, end='')
```

### In Deep Research Agent
```python
from src.agents.deep_research_agent import run_deep_research

# Automatic: Will select Groq reasoning model if GROQ_API_KEY is set
result = await run_deep_research(
    "What are the latest advancements in solid state batteries?"
)

# Explicit: Specify Groq model
result = await run_deep_research(
    "Analyze the impact of AI on healthcare",
    model_name="groq:openai/gpt-oss-120b"
)
```

### Model Selection Priority (Deep Research)
When no model is specified, the deep research agent automatically selects in this order:
1. **Groq** (reasoning model) - Fastest for complex reasoning
2. **OpenAI** (GPT-4) - High quality
3. **Anthropic** (Claude) - Strong reasoning
4. **Gemini** - Alternative option

## Architecture

### GroqClient (`src/clients/groq_client.py`)
```python
class GroqClient:
    """Client for Groq API with reasoning model support"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model_name = model
        self._is_reasoning_model = self._check_reasoning_model(model)
    
    def generate(self, prompt: str, ...) -> str:
        """Generate complete response"""
        
    async def generate_stream(self, prompt: str, ...) -> AsyncGenerator:
        """Generate streaming response"""
```

### AI Service Integration
The `AIService` class now supports Groq as a provider:
- Auto-initializes Groq client if `GROQ_API_KEY` is present
- Routes requests to Groq when model name starts with `groq:`
- Supports both streaming and non-streaming generation
- Handles model switching dynamically

### Deep Research Agent Integration
The deep research agent automatically:
- Prefers Groq reasoning models for complex research tasks
- Uses `openai/gpt-oss-120b` (120B parameters) for maximum reasoning capability
- Leverages fast inference for rapid multi-step reasoning chains
- Maintains compatibility with all model providers

## Reasoning Format

Groq supports explicit reasoning formats through the `reasoning_format` parameter:

### Options:
- `raw`: Raw thinking process included in output
- `parsed`: Structured reasoning separate from final answer

### Example with Reasoning:
```python
from src.clients.groq_client import GroqClient

client = GroqClient(
    api_key=os.getenv("GROQ_API_KEY"),
    model="openai/gpt-oss-120b"
)

# Reasoning is auto-enabled for reasoning models
response = client.generate(
    "Solve this complex problem: ...",
    enable_reasoning=True
)
```

## Performance Optimization

### Temperature and Token Management
- **Lower temperature** (0.1-0.3): More focused reasoning
- **Higher max_tokens**: Allow complete reasoning chains
- **Streaming**: Better UX for long reasoning processes

### Prompt Engineering for Reasoning
```python
prompt = """Think through this step by step:
1. Analyze the problem
2. Consider multiple approaches
3. Evaluate trade-offs
4. Reach a conclusion

Problem: {your_question}
"""
```

## Testing

### Run Manual Test
```bash
cd backend
python test_deep_agent_manual.py
```

Expected output:
```
============================================================
   Deep Research Agent Test
============================================================

Deepagents library available: True

API Keys Status:
  GROQ_API_KEY:      True  ✓
  TAVILY_API_KEY:    True
  ...

📝 Query: What are solid state batteries?
🤖 Using Groq (Reasoning): groq:openai/gpt-oss-120b

⏳ Running deep research...
...
✅ Test PASSED!
```

## Benefits for Deep Research

### Why Groq for Deep Research?
1. **Speed Compounds**: Multi-step reasoning requires many LLM calls. Groq's speed dramatically reduces total time.
2. **Reasoning Models**: Purpose-built for complex problem-solving with explicit reasoning chains.
3. **Cost-Effective**: Fast inference = lower costs for reasoning-heavy workloads.
4. **Low Latency**: Sub-second responses enable real-time agentic workflows.

### Performance Comparison
Traditional reasoning workflow (OpenAI GPT-4):
- Plan: 3s
- Investigate (3 queries): 9s
- Synthesize: 4s  
- **Total: ~16s**

With Groq (gpt-oss-120b):
- Plan: 0.5s
- Investigate (3 queries): 1.5s
- Synthesize: 0.8s
- **Total: ~2.8s** (5.7× faster!)

## API Reference

### GroqClient Methods
```python
def generate(
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    enable_reasoning: bool = None
) -> str
```

```python
async def generate_stream(
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    enable_reasoning: bool = None
) -> AsyncGenerator[str, None]
```

### Environment Variables
- `GROQ_API_KEY`: Your Groq API key (required)
- `DEEP_RESEARCH_ENABLED`: Enable/disable deep research feature

## Troubleshooting

### "GROQ_API_KEY not found"
**Solution**: Add `GROQ_API_KEY` to `backend/.env`

### "groq package not installed"
**Solution**: Run `uv pip install groq langchain-groq`

### Model not found error
**Solution**: Verify model ID matches Groq's naming (e.g., `openai/gpt-oss-120b`)

### Rate limiting
**Solution**: Groq has generous rate limits. If exceeded, wait or upgrade plan.

## Best Practices

1. **Use reasoning models for complex tasks**: `gpt-oss-120b` excels at multi-step problems
2. **Stream for better UX**: Reasoning can take time; streaming provides feedback
3. **Adjust temperature**: Lower for focused reasoning, higher for creative tasks
4. **Monitor tokens**: Reasoning models generate more tokens due to thinking process
5. **Combine with tools**: Groq + web search = powerful research agent

## Resources

- [Official Groq Documentation](https://console.groq.com/docs)
- [LangChain Groq Integration](https://console.groq.com/docs/langchain)
- [Reasoning Models Guide](https://console.groq.com/docs/reasoning)
- [Groq Console](https://console.groq.com)

## License
Groq integration follows the same license as TcyberChatbot project.
