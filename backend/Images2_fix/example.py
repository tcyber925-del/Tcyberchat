import subprocess
import requests
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain.schema import Document

# -------------------------------
# 1️⃣ WSL2 port forwarding helper
# -------------------------------
def get_wsl_ip():
    try:
        ip = subprocess.check_output(
            "wsl hostname -I", shell=True, text=True
        ).strip().split()[0]
        return ip
    except Exception as e:
        raise RuntimeError(f"Failed to get WSL2 IP: {e}")

def setup_port_forward(wsl_ip, port=11434):
    try:
        subprocess.run(
            f'netsh interface portproxy add v4tov4 listenport={port} listenaddress=0.0.0.0 '
            f'connectport={port} connectaddress={wsl_ip}',
            shell=True,
            check=False
        )
        subprocess.run(
            f'netsh advfirewall firewall add rule name="Ollama WSL2" dir=in action=allow protocol=TCP localport={port}',
            shell=True,
            check=False
        )
        print(f"Port {port} forwarded from WSL2 ({wsl_ip}) to Windows localhost.")
    except Exception as e:
        print(f"Port forwarding failed: {e}")

# -------------------------------
# 2️⃣ Chroma setup with Hugging Face embeddings
# -------------------------------
docs = [
    Document(page_content="Ollama models can run inside WSL2.", metadata={"source": "guide"}),
    Document(page_content="WSL2 uses a separate IP, so port forwarding is needed to access from Windows.", metadata={"source": "guide"}),
    Document(page_content="Retrieval-Augmented Generation allows combining external knowledge with local LLMs.", metadata={"source": "guide"}),
]

# Use Hugging Face all-MiniLM-L6-v2 embeddings
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectordb = Chroma.from_documents(docs, embedding_model)

# -------------------------------
# 3️⃣ Ollama API configuration
# -------------------------------
PORT = 11434
wsl_ip = get_wsl_ip()
setup_port_forward(wsl_ip, PORT)

OLLAMA_API_URL = f"http://localhost:{PORT}"

def list_models():
    response = requests.get(f"{OLLAMA_API_URL}/models")
    response.raise_for_status()
    return response.json()

# -------------------------------
# 4️⃣ Streaming query to Ollama
# -------------------------------
def query_ollama_stream(model: str, prompt: str):
    payload = {"model": model, "prompt": prompt, "stream": True}
    with requests.post(f"{OLLAMA_API_URL}/completion", json=payload, stream=True) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if line:
                try:
                    chunk = line.decode("utf-8")
                    yield chunk
                except Exception:
                    continue

# -------------------------------
# 5️⃣ RAG chat with streaming
# -------------------------------
def rag_chat_stream(query: str, model: str = "llama2", k: int = 2):
    results = vectordb.similarity_search(query, k=k)
    context_text = "\n".join([doc.page_content for doc in results])
    prompt = f"Context:\n{context_text}\n\nQuestion:\n{query}\nAnswer:"
    for chunk in query_ollama_stream(model, prompt):
        print(chunk, end="", flush=True)
    print()

# -------------------------------
# 6️⃣ Run example
# -------------------------------
if __name__ == "__main__":
    print("Available Ollama models:", list_models())
    user_query = "How do I connect my Windows chatbot to Ollama in WSL2?"
    print("\nChatbot response:\n")
    rag_chat_stream(user_query)
