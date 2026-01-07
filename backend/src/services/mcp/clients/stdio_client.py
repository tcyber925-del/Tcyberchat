"""
Stdio MCP connection using the official MCP SDK.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import traceback
import logging
import asyncio
import os
import time
import subprocess
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


class _StdioMonkeyPatch:
    def __init__(self):
        self.logs_dir = os.path.join(os.getcwd(), 'logs')
        try:
            os.makedirs(self.logs_dir, exist_ok=True)
        except Exception:
            pass
        ts = int(time.time())
        self.diag_log = os.path.join(self.logs_dir, f"mcp_stdio_diag_{ts}.log")
        self.child_log = os.path.join(self.logs_dir, f"mcp_stdio_child_{ts}.log")
        
        self.orig_create = asyncio.create_subprocess_exec
        self.orig_subproc_create = getattr(asyncio.subprocess, 'create_subprocess_exec', None)
        self.orig_popen = subprocess.Popen

    def __enter__(self):
        asyncio.create_subprocess_exec = self._wrapped_create_subprocess_exec
        if self.orig_subproc_create:
            asyncio.subprocess.create_subprocess_exec = self._wrapped_create_subprocess_exec
        subprocess.Popen = self._wrapped_popen
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.create_subprocess_exec = self.orig_create
        if self.orig_subproc_create:
            asyncio.subprocess.create_subprocess_exec = self.orig_subproc_create
        subprocess.Popen = self.orig_popen

    async def _wrapped_create_subprocess_exec(self, *p, **kw):
        kw['stdout'] = asyncio.subprocess.PIPE
        kw['stderr'] = asyncio.subprocess.PIPE
        try:
            with open(self.diag_log, 'a', encoding='utf-8') as f:
                try:
                    f.write(f"PROC_ATTEMPT args={p} kw={{{', '.join([f'{k}={v}' for k,v in kw.items()])}}}\n")
                except Exception:
                    f.write("PROC_ATTEMPT args=...\n")
                f.flush()
        except Exception:
            pass

        try:
            proc = await self.orig_create(*p, **kw)
        except Exception as e:
            try:
                with open(self.diag_log, 'a', encoding='utf-8') as f:
                    f.write(f"PROC_CREATE_FAILED: {repr(e)}\n")
                    f.flush()
            except Exception:
                pass
            raise
            
        try:
            with open(self.diag_log, 'a', encoding='utf-8') as f:
                f.write(f"PROC_START pid={getattr(proc, 'pid', None)} args={p} kw={{{', '.join([f'{k}={v}' for k,v in kw.items()])}}}\n")
                f.flush()
        except Exception:
            pass

        async def _wait_and_log(pobj, path):
            try:
                code = await pobj.wait()
                with open(path, 'a', encoding='utf-8') as f:
                    f.write(f"PROC_EXIT pid={getattr(pobj, 'pid', None)} code={code}\n")
            except Exception:
                pass

        try:
            asyncio.create_task(_wait_and_log(proc, self.diag_log))
        except Exception:
            pass

        return proc

    def _wrapped_popen(self, *popen_args, **popen_kwargs):
        popen_kwargs.setdefault('stdout', subprocess.PIPE)
        popen_kwargs.setdefault('stderr', subprocess.PIPE)
        proc = self.orig_popen(*popen_args, **popen_kwargs)

        def _drain_stream(stream, path):
            try:
                with open(path, 'ab') as f:
                    while True:
                        data = stream.read(1024)
                        if not data:
                            break
                        f.write(data)
                        f.flush()
            except Exception:
                pass

        try:
            if proc.stdout is not None:
                t = threading.Thread(target=_drain_stream, args=(proc.stdout, self.child_log), daemon=True)
                t.start()
            if proc.stderr is not None:
                t2 = threading.Thread(target=_drain_stream, args=(proc.stderr, self.child_log), daemon=True)
                t2.start()
        except Exception:
            pass
        return proc


class StdioMcpConnection:
    """Stdio-based MCP client connection."""

    def __init__(self, command: str, args: Optional[list[str]] = None, env: Optional[Dict[str, str]] = None) -> None:
        self._command = command
        self._args = args or []
        self._env = env or {}
        self._session = None
        self._client = None
        self._context = None

    async def start(self) -> None:
        """Spawn the MCP server process and connect via stdio."""
        try:
            # Fast dev path: if set, delegate startup to the external runner
            # process which isolates the MCP anyio-based stdio client from
            # the webserver asyncio event loop. This avoids cancel-scope and
            # read() concurrency issues during local development.
            if os.environ.get('MCP_STDIO_RUNNER_ONLY') == '1':
                import json
                import sys

                # Resolve relative to this file
                backend_dir = Path(__file__).resolve().parents[4]
                runner_script = backend_dir / 'scripts' / 'mcp_stdio_runner.py'

                payload = {
                    'command': self._command,
                    'args': self._args or [],
                    'env': self._env or {},
                    'cwd': str(backend_dir),
                    'timeout': int(os.environ.get('MCP_STDIO_START_TIMEOUT', '60')),
                    'attempts': int(os.environ.get('MCP_STDIO_RUNNER_ATTEMPTS', '3')),
                }

                def _run_runner():
                    try:
                        p = subprocess.run([sys.executable, str(runner_script)], input=json.dumps(payload), text=True, capture_output=True)
                        out = p.stdout.strip()
                        if not out:
                            raise RuntimeError(f"Runner produced no output, rc={p.returncode}, err={p.stderr}")
                        try:
                            return json.loads(out)
                        except Exception:
                            raise RuntimeError(f"Runner returned non-json output: {out}\nerr={p.stderr}")
                    except Exception as e:
                        raise

                # Run the blocking runner in a thread to avoid blocking the
                # asyncio loop. The runner itself will perform the MCP SDK
                # startup and return a structured JSON result.
                result = await asyncio.to_thread(_run_runner)
                if not isinstance(result, dict) or not result.get('ok'):
                    raise RuntimeError(f"External runner failed: {result}")
                # Runner succeeded; we treat the external process as the
                # MCP provider for dev purposes (no ClientSession created
                # in-process).
                return
            # Log details about the command we will spawn for easier debugging
            try:
                logger.info("Starting stdio MCP with command=%s args=%s env_keys=%s cwd=%s PATH=%s",
                            self._command, self._args, list((self._env or {}).keys()),
                            __import__('os').getcwd(), __import__('os').environ.get('PATH')[:200])
            except Exception:
                pass
            from mcp.client.session import ClientSession
            from mcp.client.stdio import stdio_client, StdioServerParameters

            # To aid debugging when the SDK spawns the child process via
            # asyncio.create_subprocess_exec, temporarily monkey-patch that
            # function so we can capture the child's stdout/stderr to a file.
            with _StdioMonkeyPatch() as patcher:
                # Normalize args to avoid duplicated `backend/backend` paths.
                # Many test helpers pass paths like `backend/scripts/...` which
                # when combined with an explicit `backend` cwd can produce
                # incorrect duplicated segments. Strip any leading `backend/`
                # or `backend\` prefix from args unconditionally.
                normalized_args: list[str] = []
                for a in (self._args or []):
                    if isinstance(a, str) and (a.startswith('backend/') or a.startswith('backend\\')):
                        # remove both possible separators
                        if a.startswith('backend/'):
                            normalized_args.append(a[len('backend/'):])
                        else:
                            normalized_args.append(a[len('backend\\'):])
                    else:
                        normalized_args.append(a)

                # Start stdio server process - pass a typed StdioServerParameters instance
                server_params = StdioServerParameters(command=self._command, args=normalized_args, env=self._env or None)

                # Feature-flagged proxy flow: when MCP_STDIO_USE_PROXY=1 the
                # backend starts a local TCP listener and asks the SDK to spawn
                # a tiny wrapper script that connects back to that listener.
                # The backend then spawns the real child process and bridges
                # the wrapper socket to the child's stdio. This avoids some
                # platform-specific stdio spawn/pipe quirks.
                use_proxy = os.environ.get('MCP_STDIO_USE_PROXY') == '1'

                orig_cwd = os.getcwd()
                changed_cwd = False
                try:
                    if os.path.basename(orig_cwd) == 'backend' and any(isinstance(a, str) and a.startswith('backend/') for a in normalized_args):
                        os.chdir(os.path.dirname(orig_cwd))
                        changed_cwd = True

                    if use_proxy:
                        import socket
                        import sys

                        # Start a listening socket on localhost, ephemeral port
                        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        listener.bind(('127.0.0.1', 0))
                        listener.listen(1)
                        proxy_port = listener.getsockname()[1]

                        # Compute the absolute `backend` directory based on this
                        # module's file location.
                        backend_dir_path = Path(__file__).resolve().parents[4]
                        backend_dir = str(backend_dir_path)

                        # Build wrapper server params (SDK will spawn this wrapper)
                        wrapper_script = str(backend_dir_path / 'scripts' / 'mcp_stdio_wrapper.py')
                        try:
                            logger.info("Computed backend_dir=%s wrapper_script=%s orig_cwd=%s", backend_dir, wrapper_script, orig_cwd)
                        except Exception:
                            pass
                        wrapper_cmd = sys.executable
                        wrapper_args = ['-u', wrapper_script]
                        wrapper_env = dict(os.environ)
                        wrapper_env['MCP_PROXY_PORT'] = str(proxy_port)

                        wrapper_params = StdioServerParameters(command=wrapper_cmd, args=wrapper_args, env=wrapper_env)

                        # Start SDK context which spawns the wrapper and returns
                        # anyio-compatible `read, write` streams. We capture those
                        # streams and use them for the MCP ClientSession. The
                        # wrapper will connect back to our listener; accept that
                        # connection in a blocking thread so we don't mix
                        # asyncio and anyio accept calls in the same event loop.
                        # Write a guaranteed pre-spawn diag entry for the wrapper
                        try:
                            with open(patcher.diag_log, 'a', encoding='utf-8') as f:
                                f.write("PRE_SPAWN wrapper command=%s args=%s cwd=%s env_keys=%s backend_dir=%s proxy_port=%s\n" % (
                                    wrapper_cmd, wrapper_args, orig_cwd, list(wrapper_env.keys()), backend_dir, proxy_port
                                ))
                                f.flush()
                        except Exception:
                            pass
                        self._context = stdio_client(wrapper_params)

                        # Accept the incoming wrapper connection in a helper
                        # thread to avoid any event-loop compatibility issues.
                        accept_result: dict = {}

                        def _accept_block(sock, out_dict):
                            try:
                                cli, addr = sock.accept()
                                out_dict['sock'] = cli
                            except Exception:
                                out_dict['sock'] = None

                        accept_thread = threading.Thread(target=_accept_block, args=(listener, accept_result), daemon=True)
                        accept_thread.start()

                        # Enter SDK context (this spawns the wrapper which will
                        # connect back to our listener). Capture the anyio
                        # read/write streams that the SDK exposes.
                        logger.info("Entering SDK context and awaiting read/write streams")
                        read, write = await self._context.__aenter__()
                        # Small pause to allow child process to flush any early output
                        try:
                            await asyncio.sleep(0.05)
                        except Exception:
                            pass
                        logger.info("Obtained read/write streams from SDK context")

                        # Wait for the accept thread to finish (timeout guarded)
                        accept_thread.join(timeout=10)
                        client_sock = accept_result.get('sock')
                        try:
                            listener.close()
                        except Exception:
                            pass

                        # If wrapper didn't connect for some reason, raise
                        if client_sock is None:
                            raise RuntimeError('Wrapper client did not connect back to proxy listener')

                        # Resolve argument paths so we don't pass a leading
                        # `backend/...` relative path when `cwd=backend_dir` is
                        # also used (this produced `backend/backend/...`). For
                        # any relative path that exists under `backend_dir`, use
                        # the absolute path instead.
                        final_args: list[str] = []
                        for a in normalized_args:
                            if not isinstance(a, str):
                                final_args.append(a)
                                continue
                            # If absolute, keep as-is
                            if os.path.isabs(a):
                                final_args.append(a)
                                continue
                            # Candidate under backend_dir
                            cand = os.path.join(backend_dir, a.replace('/', os.path.sep).replace('\\', os.path.sep))
                            if os.path.exists(cand):
                                final_args.append(cand)
                            else:
                                final_args.append(a)

                        # Spawn the real child process whose stdio we will bridge
                        # Log child pre-spawn details so we have exact args/cwd/env
                        try:
                            with open(patcher.diag_log, 'a', encoding='utf-8') as f:
                                f.write("PRE_SPAWN child command=%s args=%s cwd=%s backend_dir=%s\n" % (
                                    self._command, final_args, orig_cwd, backend_dir
                                ))
                                f.flush()
                        except Exception:
                            pass
                        
                        # Use ORIG POPEN to avoid double-draining by the patcher
                        try:
                            child_proc = patcher.orig_popen([self._command] + final_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=backend_dir)
                        except Exception:
                            # fallback
                            try:
                                with open(patcher.diag_log, 'a', encoding='utf-8') as f:
                                    f.write("PRE_SPAWN child FALLBACK command=%s args=%s cwd=%s\n" % (
                                        self._command, normalized_args, orig_cwd
                                    ))
                                    f.flush()
                            except Exception:
                                pass
                            child_proc = patcher.orig_popen([self._command] + normalized_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=backend_dir)

                        # Start threads to forward between child pipes and the accepted socket
                        def _pipe_to_sock(src, sock):
                            try:
                                while True:
                                    chunk = src.read(4096)
                                    if not chunk:
                                        try:
                                            sock.shutdown(1)
                                        except Exception:
                                            pass
                                        break
                                    sock.sendall(chunk)
                            except Exception:
                                pass

                        def _sock_to_pipe(sock, dst):
                            try:
                                while True:
                                    data = sock.recv(4096)
                                    if not data:
                                        try:
                                            dst.close()
                                        except Exception:
                                            pass
                                        break
                                    try:
                                        dst.write(data)
                                        dst.flush()
                                    except Exception:
                                        break
                            except Exception:
                                pass

                        # stderr captured to diag_log file in background thread
                        def _drain_stderr(stream, path):
                            try:
                                with open(path, 'ab') as f:
                                    while True:
                                        d = stream.read(1024)
                                        if not d:
                                            break
                                        f.write(d)
                                        f.flush()
                            except Exception:
                                pass

                        try:
                            t_out = threading.Thread(target=_pipe_to_sock, args=(child_proc.stdout, client_sock), daemon=True)
                            t_in = threading.Thread(target=_sock_to_pipe, args=(client_sock, child_proc.stdin), daemon=True)
                            t_err = threading.Thread(target=_drain_stderr, args=(child_proc.stderr, patcher.diag_log), daemon=True)
                            t_out.start()
                            t_in.start()
                            t_err.start()
                        except Exception:
                            pass
                    else:
                        # Default flow: let SDK spawn the child on stdio
                        # Write a pre-spawn diag entry for the SDK spawn attempt
                        try:
                            with open(patcher.diag_log, 'a', encoding='utf-8') as f:
                                f.write("PRE_SPAWN sdk_spawn command=%s args=%s cwd=%s env_keys=%s\n" % (
                                    self._command, normalized_args, orig_cwd, list((self._env or {}).keys())
                                ))
                                f.flush()
                        except Exception:
                            pass
                        self._context = stdio_client(server_params)
                        read, write = await self._context.__aenter__()
                finally:
                    if changed_cwd:
                        try:
                            os.chdir(orig_cwd)
                        except Exception:
                            pass
                
                # Optionally wrap read/write streams to log wire traffic for
                # debugging. Enable by setting environment variable
                # `MCP_STDIO_WIRE_LOG=1` when running tests.
                try:
                    if os.environ.get('MCP_STDIO_WIRE_LOG') == '1':
                        wire_log = os.path.join(os.getcwd(), 'logs', f"mcp_session_wire_{int(time.time())}.log")

                        class _LoggingSendStream:
                            def __init__(self, orig, path):
                                self._orig = orig
                                self._path = path

                            async def send(self, item):
                                try:
                                    with open(self._path, 'a', encoding='utf-8') as f:
                                        f.write(f"OUT: {time.time()} {repr(item)}\n")
                                except Exception:
                                    pass
                                return await self._orig.send(item)

                            def __getattr__(self, name):
                                return getattr(self._orig, name)

                        class _LoggingReceiveStream:
                            def __init__(self, orig, path):
                                self._orig = orig
                                self._path = path

                            async def receive(self):
                                item = await self._orig.receive()
                                try:
                                    with open(self._path, 'a', encoding='utf-8') as f:
                                        f.write(f"IN: {time.time()} {repr(item)}\n")
                                except Exception:
                                    pass
                                return item

                            def __getattr__(self, name):
                                return getattr(self._orig, name)

                        try:
                            write = _LoggingSendStream(write, wire_log)
                            read = _LoggingReceiveStream(read, wire_log)
                            logger.info("MCP stdio wire logging enabled -> %s", wire_log)
                        except Exception:
                            pass
                except Exception:
                    pass

                self._session = ClientSession(read, write)
            logger.info("ClientSession created, starting initialize()")
            try:
                await self._session.initialize()
            except Exception as _e:
                logger.exception("Exception during ClientSession.initialize()")
                raise
            logger.info("ClientSession.initialize() completed")
            self._client = self._session
        except Exception as e:
            self._session = None
            self._client = None
            # Include repr(e) and full traceback to aid debugging when the
            # parent code logs or returns the error message.
            tb = traceback.format_exc()
            # Log the exception explicitly so application logs contain the
            # underlying error even if higher layers produce a terse message.
            try:
                logger.exception("Failed to start stdio MCP connection: %s", repr(e))
                logger.error("Full traceback:\n%s", tb)
            except Exception:
                # Swallow logging errors to avoid masking the original exception
                pass
            # Also print to stdout/stderr to ensure the traceback is visible
            # in environments where the file logger may not capture child
            # process spawn errors immediately (useful for local debugging).
            try:
                print("STDIO_START_EXCEPTION:", tb, flush=True)
            except Exception:
                pass
            raise RuntimeError(f"Failed to start stdio MCP connection: {repr(e)}\n{tb}") from e

    async def stop(self) -> None:
        """Stop the MCP server process."""
        if self._context is not None:
            try:
                await self._context.__aexit__(None, None, None)
            except Exception:
                pass
            finally:
                self._session = None
                self._client = None
                self._context = None

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        if self._client is None:
            return []
        try:
            result = await self._client.list_tools()
            out: List[Dict[str, Any]] = []
            for tool in result.tools:
                out.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema if hasattr(tool, "inputSchema") else None,
                })
            return out
        except Exception:
            return []

    async def call_tool(self, name: str, params: Dict[str, Any], stream: bool = False) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        if self._client is None:
            return {"error": "stdio mcp client not available"}
        try:
            result = await self._client.call_tool(name, params)
            # MCP SDK returns CallToolResult with content list
            out: Dict[str, Any] = {}
            if hasattr(result, "content"):
                content_text = ""
                for block in result.content:
                    if hasattr(block, "text"):
                        content_text += block.text
                out["content"] = content_text
            if hasattr(result, "structuredContent") and getattr(result, "structuredContent") is not None:
                out["structuredContent"] = getattr(result, "structuredContent")
            out["isError"] = getattr(result, "isError", False)
            if out:
                return out
            return {"result": str(result)}
        except Exception as e:
            return {"error": str(e)}
