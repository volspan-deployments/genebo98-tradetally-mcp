from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn
import threading
from fastmcp import FastMCP
import httpx
import os
from typing import Optional

mcp = FastMCP("TradeTally")

BASE_URL = "https://tradetally.io/api/v1"

def get_headers() -> dict:
    token = os.environ.get("JWT_SECRET", "")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


@mcp.tool()
async def get_trades(
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    broker: Optional[str] = None,
    trade_type: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> dict:
    """Retrieve a list of trades from the trading journal. Supports filtering by date range, symbol, broker, trade type (options/futures/stocks), and status."""
    params: dict = {"page": page, "limit": limit}
    if symbol:
        params["symbol"] = symbol
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if broker:
        params["broker"] = broker
    if trade_type:
        params["trade_type"] = trade_type

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/trades",
            headers=get_headers(),
            params=params,
        )
        if response.status_code >= 400:
            return {"error": f"HTTP {response.status_code}", "detail": response.text}
        return response.json()


@mcp.tool()
async def import_trades(
    broker: str,
    file_path: str,
    account_id: Optional[str] = None,
) -> dict:
    """Import trades from a broker CSV file into the trading journal. Handles CSV mapping and CUSIP resolution automatically."""
    headers = get_headers()
    # Remove Content-Type for multipart upload
    headers.pop("Content-Type", None)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Determine if file_path is a URL or a local path
        if file_path.startswith("http://") or file_path.startswith("https://"):
            # Download the file first
            file_response = await client.get(file_path)
            if file_response.status_code >= 400:
                return {"error": f"Failed to download file: HTTP {file_response.status_code}"}
            file_content = file_response.content
            filename = file_path.split("/")[-1] or "trades.csv"
        else:
            try:
                with open(file_path, "rb") as f:
                    file_content = f.read()
                filename = os.path.basename(file_path)
            except FileNotFoundError:
                return {"error": f"File not found: {file_path}"}
            except Exception as e:
                return {"error": f"Failed to read file: {str(e)}"}

        data = {"broker": broker}
        if account_id:
            data["account_id"] = account_id

        files = {"file": (filename, file_content, "text/csv")}

        response = await client.post(
            f"{BASE_URL}/trades/import",
            headers=headers,
            data=data,
            files=files,
        )
        if response.status_code >= 400:
            return {"error": f"HTTP {response.status_code}", "detail": response.text}
        return response.json()


@mcp.tool()
async def get_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: str = "day",
    trade_type: Optional[str] = None,
    symbol: Optional[str] = None,
) -> dict:
    """Retrieve performance analytics and statistics for trades. Provides aggregated metrics including P&L, win rate, average hold time, and performance by day of week, sector, or time period."""
    params: dict = {"group_by": group_by}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if trade_type:
        params["trade_type"] = trade_type
    if symbol:
        params["symbol"] = symbol

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/analytics",
            headers=get_headers(),
            params=params,
        )
        if response.status_code >= 400:
            return {"error": f"HTTP {response.status_code}", "detail": response.text}
        return response.json()


@mcp.tool()
async def get_ai_insights(
    analysis_type: str = "general",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    prompt: Optional[str] = None,
) -> dict:
    """Get AI-powered trading recommendations and behavioral analysis powered by Google Gemini. Includes revenge trading detection, overtrading analysis, and actionable suggestions."""
    payload: dict = {"analysis_type": analysis_type}
    if start_date:
        payload["start_date"] = start_date
    if end_date:
        payload["end_date"] = end_date
    if prompt:
        payload["prompt"] = prompt

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/ai/insights",
            headers=get_headers(),
            json=payload,
        )
        if response.status_code >= 400:
            # Try GET as fallback
            params: dict = {"analysis_type": analysis_type}
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date
            if prompt:
                params["prompt"] = prompt
            response = await client.get(
                f"{BASE_URL}/ai/insights",
                headers=get_headers(),
                params=params,
            )
            if response.status_code >= 400:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
        return response.json()


@mcp.tool()
async def get_year_wrapped(year: int) -> dict:
    """Retrieve the annual Year Wrapped summary report for a given year, similar to Spotify Wrapped but for trading. Includes top symbols, best days, biggest wins/losses, and key stats."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/analytics/year-wrapped/{year}",
            headers=get_headers(),
        )
        if response.status_code >= 400:
            # Try alternative endpoint
            response = await client.get(
                f"{BASE_URL}/year-wrapped/{year}",
                headers=get_headers(),
            )
            if response.status_code >= 400:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
        return response.json()


@mcp.tool()
async def manage_api_keys(
    action: str,
    key_name: Optional[str] = None,
    key_id: Optional[str] = None,
) -> dict:
    """Create, list, or revoke API keys for programmatic access to TradeTally. Actions: create, list, revoke."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        if action == "list":
            response = await client.get(
                f"{BASE_URL}/api-keys",
                headers=get_headers(),
            )
            if response.status_code >= 400:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
            return response.json()

        elif action == "create":
            if not key_name:
                return {"error": "key_name is required when action is 'create'"}
            payload = {"name": key_name}
            response = await client.post(
                f"{BASE_URL}/api-keys",
                headers=get_headers(),
                json=payload,
            )
            if response.status_code >= 400:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
            return response.json()

        elif action == "revoke":
            if not key_id:
                return {"error": "key_id is required when action is 'revoke'"}
            response = await client.delete(
                f"{BASE_URL}/api-keys/{key_id}",
                headers=get_headers(),
            )
            if response.status_code >= 400:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
            if response.status_code == 204:
                return {"message": f"API key {key_id} revoked successfully"}
            return response.json()

        else:
            return {"error": f"Unknown action '{action}'. Valid actions: create, list, revoke"}


@mcp.tool()
async def manage_account(
    action: str,
    display_name: Optional[str] = None,
    email: Optional[str] = None,
    timezone: Optional[str] = None,
    current_password: Optional[str] = None,
    new_password: Optional[str] = None,
) -> dict:
    """View or update the authenticated user's account settings including profile information, timezone, broker connections, and notification preferences."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        if action == "get":
            response = await client.get(
                f"{BASE_URL}/users/profile",
                headers=get_headers(),
            )
            if response.status_code >= 400:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
            return response.json()

        elif action == "update":
            payload: dict = {}
            if display_name is not None:
                payload["display_name"] = display_name
            if email is not None:
                payload["email"] = email
            if timezone is not None:
                payload["timezone"] = timezone

            results = {}

            # Update profile if there are profile fields
            if payload:
                response = await client.put(
                    f"{BASE_URL}/users/profile",
                    headers=get_headers(),
                    json=payload,
                )
                if response.status_code >= 400:
                    return {"error": f"HTTP {response.status_code}", "detail": response.text}
                results["profile"] = response.json()

            # Update password separately if requested
            if current_password and new_password:
                password_payload = {
                    "current_password": current_password,
                    "new_password": new_password,
                }
                pwd_response = await client.put(
                    f"{BASE_URL}/users/password",
                    headers=get_headers(),
                    json=password_payload,
                )
                if pwd_response.status_code >= 400:
                    results["password_error"] = {
                        "error": f"HTTP {pwd_response.status_code}",
                        "detail": pwd_response.text,
                    }
                else:
                    results["password"] = pwd_response.json() if pwd_response.text else {"message": "Password updated successfully"}

            if not results:
                return {"message": "No fields provided to update"}
            return results

        else:
            return {"error": f"Unknown action '{action}'. Valid actions: get, update"}


@mcp.tool()
async def admin_manage_users(
    action: str,
    user_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    page: int = 1,
) -> dict:
    """Admin-only tool to manage user accounts on the TradeTally instance. Actions: list_users, approve_user, suspend_user, get_stats. Requires admin privileges."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        if action == "list_users":
            params: dict = {"page": page}
            if status_filter:
                params["status"] = status_filter
            response = await client.get(
                f"{BASE_URL}/admin/users",
                headers=get_headers(),
                params=params,
            )
            if response.status_code >= 400:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
            return response.json()

        elif action == "approve_user":
            if not user_id:
                return {"error": "user_id is required for approve_user action"}
            response = await client.post(
                f"{BASE_URL}/admin/users/{user_id}/approve",
                headers=get_headers(),
            )
            if response.status_code >= 400:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
            return response.json() if response.text else {"message": f"User {user_id} approved successfully"}

        elif action == "suspend_user":
            if not user_id:
                return {"error": "user_id is required for suspend_user action"}
            response = await client.post(
                f"{BASE_URL}/admin/users/{user_id}/suspend",
                headers=get_headers(),
            )
            if response.status_code >= 400:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
            return response.json() if response.text else {"message": f"User {user_id} suspended successfully"}

        elif action == "get_stats":
            response = await client.get(
                f"{BASE_URL}/admin/stats",
                headers=get_headers(),
            )
            if response.status_code >= 400:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
            return response.json()

        else:
            return {"error": f"Unknown action '{action}'. Valid actions: list_users, approve_user, suspend_user, get_stats"}




_SERVER_SLUG = "genebo98-tradetally"

def _track(tool_name: str, ua: str = ""):
    try:
        import urllib.request, json as _json
        data = _json.dumps({"slug": _SERVER_SLUG, "event": "tool_call", "tool": tool_name, "user_agent": ua}).encode()
        req = urllib.request.Request("https://www.volspan.dev/api/analytics/event", data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=1)
    except Exception:
        pass

async def health(request):
    return JSONResponse({"status": "ok", "server": mcp.name})

async def tools(request):
    registered = await mcp.list_tools()
    tool_list = [{"name": t.name, "description": t.description or ""} for t in registered]
    return JSONResponse({"tools": tool_list, "count": len(tool_list)})

sse_app = mcp.http_app(transport="sse")

app = Starlette(
    routes=[
        Route("/health", health),
        Route("/tools", tools),
        Mount("/", sse_app),
    ],
    lifespan=sse_app.lifespan,
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
