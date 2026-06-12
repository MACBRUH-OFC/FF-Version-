from fastapi import FastAPI, Query
from google_play_scraper import app as play_scraper
import httpx
import asyncio

app = FastAPI()

async def get_playstore_version():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, 
        lambda: play_scraper('com.dts.freefireth', lang='bn', country='bd')
    )
    return result.get("version") 

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
            # Advance Server URL configuration
            api_url = (
                f"https://version.advance.freefiremobile.com/trial/ver.php"
                f"?version={play_version}"
                f"&lang=bn"
                f"&device=android"
                f"&channel=android_max"
                f"&appstore=trial"
                f"&region=DEFAULT"
                f"&release_version="       # Left dynamic/empty as requested to avoid hardcoding static OB versions
                f"&whitelist_version="
                f"&whitelist_sp_version="
            )
        else:
            # Live Server URL configuration (Kept exactly as your original structure)
            api_url = (
                f"https://version.ggwhitehawk.com/live/ver.php"
                f"?version={play_version}"
                f"&lang=bn"
                f"&device=android"
                f"&channel=android"
                f"&appstore=googleplay"
                f"&region=BD"
                f"&whitelist_version=1.3.0"
                f"&whitelist_sp_version=1.0.0"
            )

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(api_url)
            # Using response.text if the response structure changes, but safely loading json
            data = response.json() if response.status_code == 200 else {}
            
        return {
            "success": True,
            "server_targeted": server,
            "remote_version": data.get("remote_version"),
            "latest_release_version": data.get("latest_release_version"),
            "play_store_version": play_version
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
