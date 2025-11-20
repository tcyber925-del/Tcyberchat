# Helper script to install optional integration deps, start the backend, and run integration tests on Windows (PowerShell)
# Usage: Open PowerShell in project root and run: .\backend\scripts\run_integration.ps1

param(
    [switch]$InstallDeps,
    [switch]$RunTests = $true
)

Set-Location -Path (Join-Path $PSScriptRoot "..")

if ($InstallDeps) {
    Write-Host "Installing optional integration dependencies (this may take a while)..."
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install chromadb langchain sentence-transformers transformers torch sse-starlette uvicorn
}

# Start the backend with uvicorn in the background
Write-Host "Starting backend (uvicorn) on 127.0.0.1:8000..."
Start-Process -NoNewWindow -FilePath "python" -ArgumentList '-m','uvicorn','main:app','--host','127.0.0.1','--port','8000'
Start-Sleep -Seconds 6

if ($RunTests) {
    Write-Host "Running integration tests..."
    # Set env var so tests that are gated by RUN_INTEGRATION_TESTS will run
    $env:RUN_INTEGRATION_TESTS = "1"
    uv run pytest tests/test_sse_client.py tests/unit/test_chat_rag_db_fallback.py -q
}

Write-Host "Done. If you started the server and want to stop it, find the uvicorn/python process and terminate it."