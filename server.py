from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn
import threading
from fastmcp import FastMCP
import httpx
import os
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("TradeTally")

BASE_URL = "https://tradetally.io/api/v1"
JWT_SECRET = os.environ.get("JWT_SECRET", "")


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {JWT_SECRET}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


@mcp.tool()
async def import_trades(
    file_path: str,
    broker: str,
    account_id: Optional[str] = None,
) -> dict:
    """Import trades from a CSV file exported by a supported broker (Lightspeed, Charles Schwab, ThinkorSwim, IBKR, E*TRADE, ProjectX). Use this when the user wants to upload trade history from their brokerage account."""
    try:
        resolved_path = os.path.expanduser(file_path)
        if not os.path.exists(resolved_path):
            return {"error": f"File not found: {resolved_path}"}

        with open(resolved_path, "rb") as f:
            file_content = f.read()

        file_name = os.path.basename(resolved_path)

        data = {"broker": broker}
        if account_id:
            data["account_id"] = account_id

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/trades/import",
                headers={
                    "Authorization": f"Bearer {JWT_SECRET}",
                    "Accept": "application/json",
                },
                data=data,
                files={"file": (file_name, file_content, "text/csv")},
            )
            if response.status_code >= 400:
                return {
                    "error": f"API request failed with status {response.status_code}",
                    "detail": response.text,
                }
            return response.json()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_trade_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account_id: Optional[str] = None,
    group_by: Optional[str] = "day",
) -> dict:
    """Retrieve performance analytics and statistics for trades over a given date range. Use this when the user wants to understand their trading performance, win rate, P&L breakdown, or behavioral patterns like revenge trading."""
    try:
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if account_id:
            params["account_id"] = account_id
        if group_by:
            params["group_by"] = group_by

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/analytics",
                headers=get_headers(),
                params=params,
            )
            if response.status_code >= 400:
                return {
                    "error": f"API request failed with status {response.status_code}",
                    "detail": response.text,
                }
            return response.json()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_ai_insights(
    analysis_type: Optional[str] = "general",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    prompt: Optional[str] = None,
) -> dict:
    """Get AI-powered personalized trading recommendations and behavioral analysis powered by Google Gemini. Use this when the user wants actionable suggestions to improve their trading strategy or understand their patterns."""
    try:
        payload = {}
        if analysis_type:
            payload["analysis_type"] = analysis_type
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
                return {
                    "error": f"API request failed with status {response.status_code}",
                    "detail": response.text,
                }
            return response.json()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def manage_api_key(
    action: str,
    key_id: Optional[str] = None,
    label: Optional[str] = None,
    scopes: Optional[List[str]] = None,
) -> dict:
    """Create, list, revoke, or rotate API keys for programmatic access to TradeTally. Use this when the user wants to integrate with external tools, set up automation, or manage their API credentials."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if action == "list":
                response = await client.get(
                    f"{BASE_URL}/api-keys",
                    headers=get_headers(),
                )
            elif action == "create":
                payload = {}
                if label:
                    payload["name"] = label
                if scopes:
                    payload["scopes"] = scopes
                response = await client.post(
                    f"{BASE_URL}/api-keys",
                    headers=get_headers(),
                    json=payload,
                )
            elif action == "revoke":
                if not key_id:
                    return {"error": "key_id is required for revoke action"}
                response = await client.delete(
                    f"{BASE_URL}/api-keys/{key_id}",
                    headers=get_headers(),
                )
            elif action == "rotate":
                if not key_id:
                    return {"error": "key_id is required for rotate action"}
                response = await client.post(
                    f"{BASE_URL}/api-keys/{key_id}/rotate",
                    headers=get_headers(),
                )
            else:
                return {"error": f"Unknown action: {action}. Valid options: create, list, revoke, rotate"}

            if response.status_code >= 400:
                return {
                    "error": f"API request failed with status {response.status_code}",
                    "detail": response.text,
                }
            if response.status_code == 204 or not response.content:
                return {"success": True, "action": action}
            return response.json()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_year_wrapped(
    year: Optional[int] = None,
    account_id: Optional[str] = None,
) -> dict:
    """Retrieve the annual 'Year Wrapped' summary — a highlights reel of the user's trading year including best/worst trades, most traded symbols, P&L milestones, and key stats. Use this when the user wants a yearly recap of their trading activity."""
    try:
        params = {}
        if year:
            params["year"] = year
        if account_id:
            params["account_id"] = account_id

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/analytics/year-wrapped",
                headers=get_headers(),
                params=params,
            )
            if response.status_code >= 400:
                return {
                    "error": f"API request failed with status {response.status_code}",
                    "detail": response.text,
                }
            return response.json()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def manage_csv_mapping(
    action: str,
    mapping_id: Optional[str] = None,
    broker_name: Optional[str] = None,
    column_map: Optional[List[dict]] = None,
) -> dict:
    """Create, update, list, or delete custom CSV column mappings for brokers not natively supported. Use this when the user wants to import trades from an unsupported broker or has a custom CSV format."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if action == "list":
                response = await client.get(
                    f"{BASE_URL}/csv-mappings",
                    headers=get_headers(),
                )
            elif action == "create":
                if not broker_name:
                    return {"error": "broker_name is required for create action"}
                payload = {"broker_name": broker_name}
                if column_map:
                    payload["column_map"] = column_map
                response = await client.post(
                    f"{BASE_URL}/csv-mappings",
                    headers=get_headers(),
                    json=payload,
                )
            elif action == "update":
                if not mapping_id:
                    return {"error": "mapping_id is required for update action"}
                payload = {}
                if broker_name:
                    payload["broker_name"] = broker_name
                if column_map:
                    payload["column_map"] = column_map
                response = await client.put(
                    f"{BASE_URL}/csv-mappings/{mapping_id}",
                    headers=get_headers(),
                    json=payload,
                )
            elif action == "delete":
                if not mapping_id:
                    return {"error": "mapping_id is required for delete action"}
                response = await client.delete(
                    f"{BASE_URL}/csv-mappings/{mapping_id}",
                    headers=get_headers(),
                )
            else:
                return {"error": f"Unknown action: {action}. Valid options: create, list, update, delete"}

            if response.status_code >= 400:
                return {
                    "error": f"API request failed with status {response.status_code}",
                    "detail": response.text,
                }
            if response.status_code == 204 or not response.content:
                return {"success": True, "action": action}
            return response.json()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def lookup_cusip(
    cusip: Optional[str] = None,
    symbol: Optional[str] = None,
    action: Optional[str] = "lookup",
) -> dict:
    """Look up or resolve CUSIP-to-symbol mappings used for translating broker trade exports that reference securities by CUSIP instead of ticker symbol. Use this when imported trades show CUSIP codes instead of recognizable ticker symbols."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if action == "list":
                response = await client.get(
                    f"{BASE_URL}/cusip-mappings",
                    headers=get_headers(),
                )
            elif action == "lookup":
                params = {}
                if cusip:
                    params["cusip"] = cusip
                if symbol:
                    params["symbol"] = symbol
                if not params:
                    return {"error": "Either cusip or symbol must be provided for lookup action"}
                response = await client.get(
                    f"{BASE_URL}/cusip-mappings/lookup",
                    headers=get_headers(),
                    params=params,
                )
            elif action == "add":
                if not cusip or not symbol:
                    return {"error": "Both cusip and symbol are required for add action"}
                payload = {"cusip": cusip, "symbol": symbol}
                response = await client.post(
                    f"{BASE_URL}/cusip-mappings",
                    headers=get_headers(),
                    json=payload,
                )
            else:
                return {"error": f"Unknown action: {action}. Valid options: lookup, add, list"}

            if response.status_code >= 400:
                return {
                    "error": f"API request failed with status {response.status_code}",
                    "detail": response.text,
                }
            if response.status_code == 204 or not response.content:
                return {"success": True, "action": action}
            return response.json()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def admin_manage_users(
    action: str,
    user_id: Optional[str] = None,
    filter: Optional[str] = "all",
    page: Optional[int] = 1,
) -> dict:
    """Admin-only tool to manage user accounts: list users, approve pending registrations, disable/enable accounts, or view platform-wide usage stats. Use this when an admin needs to manage the TradeTally instance's user base."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if action == "list":
                params = {"filter": filter or "all", "page": page or 1}
                response = await client.get(
                    f"{BASE_URL}/admin/users",
                    headers=get_headers(),
                    params=params,
                )
            elif action == "stats":
                response = await client.get(
                    f"{BASE_URL}/admin/stats",
                    headers=get_headers(),
                )
            elif action == "approve":
                if not user_id:
                    return {"error": "user_id is required for approve action"}
                response = await client.post(
                    f"{BASE_URL}/admin/users/{user_id}/approve",
                    headers=get_headers(),
                )
            elif action == "disable":
                if not user_id:
                    return {"error": "user_id is required for disable action"}
                response = await client.post(
                    f"{BASE_URL}/admin/users/{user_id}/disable",
                    headers=get_headers(),
                )
            elif action == "enable":
                if not user_id:
                    return {"error": "user_id is required for enable action"}
                response = await client.post(
                    f"{BASE_URL}/admin/users/{user_id}/enable",
                    headers=get_headers(),
                )
            elif action == "delete":
                if not user_id:
                    return {"error": "user_id is required for delete action"}
                response = await client.delete(
                    f"{BASE_URL}/admin/users/{user_id}",
                    headers=get_headers(),
                )
            else:
                return {"error": f"Unknown action: {action}. Valid options: list, approve, disable, enable, delete, stats"}

            if response.status_code >= 400:
                return {
                    "error": f"API request failed with status {response.status_code}",
                    "detail": response.text,
                }
            if response.status_code == 204 or not response.content:
                return {"success": True, "action": action}
            return response.json()
    except Exception as e:
        return {"error": str(e)}




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
