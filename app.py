from fastapi import FastAPI, Query
from google_play_scraper import app as play_scraper
import httpx
import asyncio

app = FastAPI()

async def fetch_live_playstore_version() -> str:
    """Dynamically fetches the latest live version from the Play Store."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: play_scraper('com.dts.freefireth', lang='en', country='in')
        )
        return result.get("version", "1.123.1")  # Clean fallback only if scraper times out
    except Exception:
        return "1.123.1"

def parse_optional_files(version_string: str) -> dict:
    """Converts Garena's pipe-delimited string format into a clean JSON object."""
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
        "endpoint": "/update",
        "note": "Works automatically without parameters, or pass custom bases if needed."
    } 

@app.get("/update")
async def update(
    live_base: str = Query(None, description="Optional custom live version override"),
    advance_base: str = Query(None, description="Optional custom advance version override")
):
    try:
        # 1. Dynamically figure out the live version if not provided
        if not live_base:
            live_version_param = await fetch_live_playstore_version()
        else:
            live_version_param = live_base

        # 2. Dynamically calculate the advance version parameter if not provided
        if not advance_base:
            try:
                # Splitting "1.123.1" -> grabs "123" -> increments it to match Advance Server logic
                major_version = int(live_version_param.split('.')[1])
                advance_version_param = f"66.{major_version + 1}.0"
            except Exception:
                advance_version_param = "66.49.0"
        else:
            advance_version_param = advance_base

        # 3. Dynamic Live Server Link
        live_url = (
            f"https://version.ggwhitehawk.com/live/ver.php"
            f"?version={live_version_param}"
            f"&lang=en&device=android&channel=android&appstore=googleplay&region=IND"
            f"&whitelist_version=1.3.0&whitelist_sp_version=1.0.0"
        )
        
        # 4. Dynamic Advance Server Link
        advance_url = (
            f"https://version.advance.freefiremobile.com/trial/ver.php"
            f"?version={advance_version_param}"
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
            "version_details": {
                "client_version": live_data.get("remote_version", live_version_param),
                "patch_version": live_data.get("latest_release_version")
            },
            "resource_packages": {
                "standard": parse_optional_files(live_data.get("remote_option_version", "")),
                "astc": parse_optional_files(live_data.get("remote_option_version_astc", ""))
            }
        }
        
        # --- Structured Advance Server Output ---
        advance_output = {
            "version_details": {
                "client_version": advance_data.get("remote_version", advance_version_param),
                "patch_version": advance_data.get("latest_release_version")
            },
            "resource_packages": {
                "standard": parse_optional_files(advance_data.get("remote_option_version", "")),
                "astc": parse_optional_files(advance_data.get("remote_option_version_astc", ""))
            }
        }

        # --- Combined Clean Response ---
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
