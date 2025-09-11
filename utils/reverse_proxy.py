import threading
import socket
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import httpx

TARGET_BASE = "https://www.openvlab.cn"
_server_thread: Optional[threading.Thread] = None
_app: Optional[FastAPI] = None


def _build_app() -> FastAPI:
    app = FastAPI(title="Reverse Proxy for Embedding", version="0.1.0")

    @app.api_route("/ovlab/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
    async def proxy(request: Request, path: str):
        # Build target URL
        url = f"{TARGET_BASE}/{path}" if path else f"{TARGET_BASE}/"
        method = request.method

        # Prepare request
        client = httpx.AsyncClient(follow_redirects=True, timeout=20.0)
        headers = dict(request.headers)
        # Set Host header to target
        headers["host"] = TARGET_BASE.replace("https://", "").replace("http://", "")

        # Body
        body = await request.body()

        try:
            resp = await client.request(method, url, content=body, headers=headers, params=dict(request.query_params))
        finally:
            await client.aclose()

        # Filter/override headers to allow iframe embedding
        excluded = {"content-encoding", "transfer-encoding", "connection"}
        out_headers = []
        for k, v in resp.headers.items():
            lk = k.lower()
            if lk in excluded:
                continue
            if lk in ("x-frame-options", "content-security-policy"):
                continue
            out_headers.append((k, v))

        # Set relaxed headers
        out_headers.append(("X-Frame-Options", "ALLOWALL"))
        # Keep CSP minimal; remove frame-ancestors limitation by not passing it

        return Response(content=resp.content, status_code=resp.status_code, headers=dict(out_headers))

    return app


def _is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def ensure_proxy_running(host: str = "127.0.0.1", port: int = 8900) -> str:
    global _server_thread, _app
    if _server_thread is not None and _server_thread.is_alive():
        return f"http://{host}:{port}"

    if _is_port_in_use(port):
        return f"http://{host}:{port}"

    _app = _build_app()

    def _run():
        import uvicorn
        uvicorn.run(_app, host=host, port=port, log_level="warning")

    _server_thread = threading.Thread(target=_run, daemon=True)
    _server_thread.start()
    return f"http://{host}:{port}"


