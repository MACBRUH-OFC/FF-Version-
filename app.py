from fastapi import FastAPI, Query
from google_play_scraper import app as play_scraper
import httpx
import asyncio

app = FastAPI()

async def get_playstore_version():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, 
        lambda: play_scraper('com.dts.freefireth', lang='en', country='in')
    )
    return result.get("version") 

def parse_optional_files(version_string: str) -> dict:
    """Helper to convert pipeline string formats like 'res:49|avatar:757' into an object."""
    if not version_string:
        return {}
    return {
        item.split(":")[0]: int(item.split(":")[1]) 
        for item in version_string.split("|") 
        if ":" in item
    }

@app.get("/")
async def home():
    return {
        "success": True, 
        "endpoint": "/update",
        "usage": "/update?server=live or /update?server=advance"
    } 

@app.get("/update")
async def update(server: str = Query("live", regex="^(live|advance)$")):
    try:
        play_version = await get_playstore_version()
        
        if server == "advance":
            # Updated Advance Server Configuration matching IND regional patterns 
            # Force target version if Play Store scraper gets out-of-sync for the Trial Server
            version_param = "66.49.0" if not play_version else play_version
            api_url = (
                f"https://version.advance.freefiremobile.com/trial/ver.php"
                f"?version={version_param}"
                f"&lang=en"
                f"&device=android"
                f"&channel=android"
                f"&appstore=googleplay"
                f"&region=IND"
                f"&whitelist_version=1.3.0"
                f"&whitelist_sp_version=1.0.0"
            )
        else:
            # Updated Live Server Configuration 
            version_param = "1.123.1" if not play_version else play_version
            api_url = (
                f"https://version.ggwhitehawk.com/live/ver.php"
                f"?version={version_param}"
                f"&lang=en"
                f"&device=android"
                f"&channel=android"
                f"&appstore=googleplay"
                f"&region=IND"
                f"&whitelist_version=1.3.0"
                f"&whitelist_sp_version=1.0.0"
            )

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(api_url)
            data = response.json() if response.status_code == 200 else {}
            
        # Extract response payload parameters 
        remote_version = data.get("remote_version")
        ob_version = data.get("latest_release_version")
        
        # Parse out both raw and ASTC specialized optional content packages
        optional_packs = parse_optional_files(data.get("remote_option_version", ""))
        optional_packs_astc = parse_optional_files(data.get("remote_option_version_astc", ""))

        # Dynamically structure output fields based on targeted selection
        output = {
            "success": True,
            "server_targeted": server,
            f"{server}_version": remote_version,
            "ObVersion": ob_version,
            "optional_files_version": optional_packs,
            "optional_files_version_astc": optional_packs_astc
        }
        
        return output
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
