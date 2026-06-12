from fastapi import FastAPI
from google_play_scraper import app as play_scraper
import httpx
import asyncio

app = FastAPI()


async def get_playstore_version():

    loop = asyncio.get_event_loop()

    result = await loop.run_in_executor(
        None,
        lambda: play_scraper(
            "com.dts.freefireth",
            lang="bn",
            country="bd"
        )
    )

    return result.get("version")


@app.get("/")
async def home():

    return {
        "success": True,
        "endpoint": "/update"
    }


@app.get("/update")
async def update():

    try:

        play_version = await get_playstore_version()

        live_url = (
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

        advance_url = (
            f"https://version.advance.freefiremobile.com/trial/ver.php"
            f"?version=68.54.0"
            f"&lang=en"
            f"&device=android"
            f"&channel=android_max"
            f"&appstore=trial"
            f"&region=DEFAULT"
            f"&release_version=OB54"
            f"&whitelist_version="
            f"&whitelist_sp_version="
            f"&device_name=samsung%20SM-X910N"
            f"&device_CPU=x86-64%20SSE3%20SSE4.1%20SSE4.2%20AVX"
            f"&device_GPU=Adreno%20%28TM%29%20640"
            f"&device_mem=3946"
        )

        async with httpx.AsyncClient(timeout=15) as client:

            live_response, advance_response = await asyncio.gather(
                client.get(live_url),
                client.get(advance_url)
            )

            live_data = live_response.json()
            advance_data = advance_response.json()

        return {
            "success": True,

            "live": {
                "version": live_data.get("remote_version"),
                "release": live_data.get("latest_release_version"),
                "optional_files": live_data.get("remote_option_version")
            },

            "advance": {
                "version": advance_data.get("remote_version"),
                "release": advance_data.get("latest_release_version"),
                "optional_files": advance_data.get("remote_option_version")
            }
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }