from fastapi import FastAPI
import httpx
from google_play_scraper import app as play_scraper
import asyncio
import json
import os

app = FastAPI()

def load_client_urls():
    file_path = 'clients_url.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {"error": "clients_url.json not found"}

async def get_api_update():
    try:
        loop = asyncio.get_event_loop()
        # Scrapes version from Play Store for the specific package
        result = await loop.run_in_executor(None, lambda: play_scraper('com.dts.freefireth', lang="bn", country='bd'))
        play_version = result['version']
        
        api_url = f'https://version.ggwhitehawk.com/live/ver.php?version={play_version}&lang=bn&device=android&channel=android&appstore=googleplay&region=BD&whitelist_version=1.3.0&whitelist_sp_version=1.0.0'
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(api_url)
            data = response.json()

        return {
            "remote_version": data.get('remote_version'),
            "server_url": data.get('server_url'),
            "latest_release_version": data.get('latest_release_version'),
            "play_store_version": play_version
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/update")
async def get_combined_update():
    # [span_0](start_span)Load region URLs from your local JSON[span_0](end_span)
    region_urls = load_client_urls()

    # [span_1](start_span)Get the official source update info[span_1](end_span)
    api_info = await get_api_update()

    return {
        "status": "success",
        "SourceUpdate_info": api_info,
        "Region_URLs": region_urls
    }
