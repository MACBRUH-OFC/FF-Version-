from fastapi import FastAPI, Query
from google_play_scraper import app as play_scraper
import httpx
import asyncio

app = FastAPI()

async def get_playstore_version():
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: play_scraper('com.dts.freefireth', lang='en', country='in')
        )
        return result.get("version")
    except Exception:
        return None

def parse_optional_files(version_string: str) -> dict:
    if not version_string:
        return {}
    return {
        item.split(":")[0]: int(item.split(":")[1]) 
        for item in version_string.split("|") 
        if ":" in item
    }

async def fetch_server_data(client: httpx.AsyncClient, url: str):
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
        "dynamic_usage": "/update?advance_base=66.49.0"
    } 

@app.get("/update")
async def update(advance_base: str = Query(None, description="Pass dynamic advance version parameter on the fly")):
    try:
        # 1. Fetch live Play Store version dynamically
        play_version = await get_playstore_version()
        
        if not play_version:
            return {
                "success": False,
                "error": "Could not fetch dynamic play store version live. Ensure scraper is functioning."
            }

        # 2. Dynamically determine Advance Server query version parameter
        # If you don't pass one via URL query, it automatically guesses by incrementing the major engine version
        if not advance_base:
            try:
                major_version = int(play_version.split('.')[1])
                advance_version_param = f"66.{major_version + 1}.0"
            except Exception:
                advance_version_param = play_version  # absolute fallback loop
        else:
            advance_version_param = advance_base

        # 3. Dynamic Live Server Target Link (No hardcoded versions)
        live_url = (
            f"https://version.ggwhitehawk.com/live/ver.php"
            f"?version={play_version}"
            f"&lang=en"
            f"&device=android"
            f"&channel=android"
            f"&appstore=googleplay"
            f"&region=IND"
            f"&whitelist_version=1.3.0"
            f"&whitelist_sp_version=1.0.0"
        )
        
        # 4. Dynamic Advance Server Target Link (No hardcoded versions)
        advance_url = (
            f"https://version.advance.freefiremobile.com/trial/ver.php"
            f"?version={advance_version_param}"
            f"&lang=en"
            f"&device=android"
            f"&channel=android"
            f"&appstore=googleplay"
            f"&region=IND"
            f"&whitelist_version=1.3.0"
            f"&whitelist_sp_version=1.0.0"
        )

        async with httpx.AsyncClient(timeout=10) as client:
            live_task = fetch_server_data(client, live_url)
            advance_task = fetch_server_data(client, advance_url)
            live_data, advance_data = await asyncio.gather(live_task, advance_task)
            
        # --- Process Live Data ---
        live_output = {
            "live_version": live_data.get("remote_version", play_version),
            "ObVersion": live_data.get("latest_release_version"),
            "optional_files_version": parse_optional_files(live_data.get("remote_option_version", "")),
            "optional_files_version_astc": parse_optional_files(live_data.get("remote_option_version_astc", ""))
        }
        
        # --- Process Advance Data ---
        advance_output = {
            "advance_version": advance_data.get("remote_version", advance_version_param),
            "ObVersion": advance_data.get("latest_release_version"),
            "optional_files_version": parse_optional_files(advance_data.get("remote_option_version", "")),
            "optional_files_version_astc": parse_optional_files(advance_data.get("remote_option_version_astc", ""))
        }

        return {
            "success": True,
            "play_store_version": play_version,
            "live_server": live_output,
            "advance_server": advance_output
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
