import sys

sys.path.insert(0, "backend")
import asyncio
import datetime
import os

from src.services.rag_service import RAGService


async def run():
    r = RAGService()
    text = "Paris is the capital of France. It is a major European city."
    out_lines = []

    def log(s):
        print(s)
        out_lines.append(str(s))

    log("RUN START " + datetime.datetime.utcnow().isoformat())
    log("vectorstore type " + str(type(r.vectorstore)))
    try:
        before_get = r.vectorstore.get()
        log("vectorstore get before " + str(before_get))
    except Exception as e:
        log("vectorstore.get() before raised: " + str(e))
    # call the async method
    ok = await r.add_document_with_chunking("d_test", text, metadata={"source": "test"})
    log("add_document_with_chunking ok " + str(ok))
    try:
        afterA = r.vectorstore.get()
        log("vectorstore get after A " + str(afterA))
    except Exception as e:
        log("vectorstore.get() after A raised: " + str(e))
    # now do manual steps
    chunks = r.text_splitter.split_text(text)
    print("chunks", chunks)
    docs = []
    for i, chunk in enumerate(chunks):
        meta = {
            "document_id": "d_test",
            "chunk_index": i,
            "chunk_length": len(chunk),
            "total_chunks": len(chunks),
        }
        docs.append({"page_content": chunk, "metadata": meta})
    log("prepared docs " + str(docs))
    try:
        r.vectorstore.add_documents(docs)
        log("manual add_documents succeeded")
    except Exception as e:
        log("manual add_documents failed " + str(e))
    try:
        after_manual = r.vectorstore.get()
        log("vectorstore get after manual add " + str(after_manual))
    except Exception as e:
        log("vectorstore.get() after manual add raised: " + str(e))

    # Run retrieval and generation to finish the RAG flow
    try:
        hits = await r.search_relevant_chunks("What is the capital of France?", limit=5)
        log("search_relevant_chunks -> " + str(hits))
    except Exception as e:
        log("search_relevant_chunks failed: " + str(e))

    try:
        resp = await r.generate_rag_response(
            "What is the capital of France?", document_id="d_test"
        )
        log("generate_rag_response -> " + str(resp))
    except Exception as e:
        log("generate_rag_response failed: " + str(e))

    # write log to file for reliable retrieval
    try:
        os.makedirs(os.path.join("backend", "logs"), exist_ok=True)
        with open(
            os.path.join("backend", "logs", "debug_rag.log"), "a", encoding="utf-8"
        ) as f:
            f.write(
                "\n--- DEBUG RUN " + datetime.datetime.utcnow().isoformat() + " ---\n"
            )
            for l in out_lines:
                f.write(l + "\n")
            f.write("--- END RUN ---\n")
    except Exception as e:
        print("failed to write log file", e)


asyncio.get_event_loop().run_until_complete(run())
