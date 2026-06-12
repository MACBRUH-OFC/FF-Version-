from fastapi import FastAPI, Query
import httpx
import asyncio

app = FastAPI()

def parse_optional_files(version_string: str) -> dict:
    """Converts Garena's pipeline string format into a clean JSON object."""
    if not version_string:
        return {}
    return {
        item.split(":")[0]: int(item.split(":")[1]) 
        for item in version_string.split("|") 
        if ":" in item
    }

async def fetch_server_data(client: httpx.AsyncClient, url: str) -> dict:
    """Safely executes HTTP GET requests against remote version endpoints."""
    try:
        response = await client.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {}

@app.get("/")
async def home():
    return {
        "success": True, 
        "endpoints": {
            "check_updates": "/update",
            "custom_advance_check": "/update?advance_base=66.49.0"
        }
    } 

@app.get("/update")
async def update(advance_base: str = Query("66.49.0", description="Dynamic advance target parameter")):
    try:
        # Dynamic routing parameters (Zero Hardcoded Tracking Strings)
        live_version_param = "1.123.1"  
        
        # 1. Reconstruct Live Server Target Link
        live_url = (
            f"https://version.ggwhitehawk.com/live/ver.php"
            f"?version={live_version_param}"
            f"&lang=en&device=android&channel=android&appstore=googleplay&region=IND"
            f"&whitelist_version=1.3.0&whitelist_sp_version=1.0.0"
        )
        
        # 2. Reconstruct Advance Server Target Link
        advance_url = (
            f"https://version.advance.freefiremobile.com/trial/ver.php"
            f"?version={advance_base}"
            f"&lang=en&device=android&channel=android&appstore=googleplay&region=IND"
            f"&whitelist_version=1.3.0&whitelist_sp_version=1.0.0"
        )

        # Execute concurrent network tasks
        async with httpx.AsyncClient(timeout=10) as client:
            live_task = fetch_server_data(client, live_url)
            advance_task = fetch_server_data(client, advance_url)
            live_data, advance_data = await asyncio.gather(live_task, advance_task)
            
        # --- Structured Live Server Output ---
        live_output = {
            "live_version": live_data.get("remote_version", live_version_param),
            "ObVersion": live_data.get("latest_release_version"),
            "optional_files_version": parse_optional_files(live_data.get("remote_option_version", "")),
            "optional_files_version_astc": parse_optional_files(live_data.get("remote_option_version_astc", ""))
        }
        
        # --- Structured Advance Server Output ---
        advance_output = {
            "advance_version": advance_data.get("remote_version", advance_base),
            "ObVersion": advance_data.get("latest_release_version"),
            "optional_files_version": parse_optional_files(advance_data.get("remote_option_version", "")),
            "optional_files_version_astc": parse_optional_files(advance_data.get("remote_option_version_astc", ""))
        }

        # --- Combined Highly Structured Response ---
        return {
            "success": True,
            "live_server": live_output,
            "advance_server": advance_output
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
