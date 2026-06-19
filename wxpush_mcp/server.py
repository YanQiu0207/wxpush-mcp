import logging
import os
import re

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

WXPUSH_URL = os.environ.get("WXPUSH_URL", "").rstrip("/")
WXPUSH_TOKEN = os.environ.get("WXPUSH_TOKEN", "")

mcp = FastMCP("wxpush")

_LOCAL_PATH_RE = re.compile(r'!?\[.*?\]\((?!https?://)([^)]+)\)')
_logger = logging.getLogger(__name__)
_MAX_RETRIES = 3
_TIMEOUT = 15.0


async def _send_wxsend(
    url: str,
    token: str,
    title: str,
    content: str,
    shortid: str | None = None,
) -> dict:
    endpoint = url.rstrip("/") + "/wxsend"
    payload: dict = {"title": title, "content": content, "token": token}
    if shortid:
        payload["shortid"] = shortid

    last_exc: Exception | None = None
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                resp = await client.post(endpoint, json=payload)
                return resp.json()
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    _logger.warning("Attempt %d/%d failed (%s), retrying…", attempt, _MAX_RETRIES, exc)
                else:
                    _logger.error("All %d attempts failed. Last error: %s", _MAX_RETRIES, exc)

    raise last_exc  # type: ignore[misc]


@mcp.tool()
async def check_health() -> str:
    """Check whether the wxpush MCP server and its backend service are reachable."""
    if not WXPUSH_URL or not WXPUSH_TOKEN:
        missing = [v for v, val in [("WXPUSH_URL", WXPUSH_URL), ("WXPUSH_TOKEN", WXPUSH_TOKEN)] if not val]
        return f"Unhealthy: {', '.join(missing)} not configured"

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(WXPUSH_URL + "/")
        return f"OK: wxpush service reachable (HTTP {resp.status_code})"
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        return f"Unhealthy: cannot reach wxpush service — {exc}"


@mcp.tool()
async def send_wechat_message(title: str, content: str, shortid: str) -> str:
    """Send a WeChat message via the wxpush service.

    Args:
        title: Message title.
        content: Message body (Markdown supported). All images and links MUST use
                 publicly accessible URLs (http/https). Local file paths are not
                 supported — upload assets to a CDN or image host before calling.
        shortid: Recipient identifier defined in the server's config.toml [users] section.
    """
    if not WXPUSH_URL or not WXPUSH_TOKEN:
        return "Error: WXPUSH_URL and WXPUSH_TOKEN must be configured."

    if _LOCAL_PATH_RE.search(content):
        return "Error: content contains local file paths. Upload all images and documents to a publicly accessible URL before sending."

    try:
        data = await _send_wxsend(WXPUSH_URL, WXPUSH_TOKEN, title, content, shortid=shortid)
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        return f"Error: {exc}"
    return data.get("msg", "Unknown response")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
