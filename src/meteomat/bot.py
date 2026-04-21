import asyncio
import logging
import os
from io import BytesIO

import plotly.io as pio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from meteomat.datasets.open_meteo import fetch_ensemble_forecast
from meteomat.viz.charts import create_weather_dashboard

logger = logging.getLogger(__name__)

_started = False


def _geocode(name: str) -> dict | None:
    r = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": name, "count": 1, "language": "en", "format": "json"},
    )
    results = r.json().get("results")
    if not results:
        return None
    hit = results[0]
    return {"lat": hit["latitude"], "lon": hit["longitude"], "name": hit["name"]}


def _forecast_png(location: dict) -> BytesIO:
    data = fetch_ensemble_forecast(location)
    fig = create_weather_dashboard(data, location=location)
    fig.update_layout(paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e", font={"color": "#e0e0e0"})
    buf = BytesIO(pio.to_image(fig, format="png", width=1400, height=900))
    buf.seek(0)
    return buf


async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a place name or drop a pin to get a 7-day ensemble forecast."
    )


async def _handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    msg = await update.message.reply_text(f"Looking up {name}...")
    location = _geocode(name)
    if not location:
        await msg.edit_text(f"Could not find '{name}'. Try a different spelling.")
        return
    await msg.edit_text(f"Fetching forecast for {location['name']}...")
    try:
        image = _forecast_png(location)
        await update.message.reply_photo(
            photo=image, caption=f"7-day forecast for {location['name']}"
        )
        await msg.delete()
    except Exception as e:
        logger.exception("forecast failed")
        await msg.edit_text(f"Something went wrong: {e}")


async def _handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    location = {
        "lat": loc.latitude,
        "lon": loc.longitude,
        "name": f"{loc.latitude:.2f}°N, {loc.longitude:.2f}°E",
    }
    msg = await update.message.reply_text("Fetching forecast...")
    try:
        image = _forecast_png(location)
        await update.message.reply_photo(
            photo=image, caption=f"7-day forecast for {location['name']}"
        )
        await msg.delete()
    except Exception as e:
        logger.exception("forecast failed")
        await msg.edit_text(f"Something went wrong: {e}")


async def _run():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", _cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_text))
    app.add_handler(MessageHandler(filters.LOCATION, _handle_location))
    async with app:
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()
        await app.updater.stop()
        await app.stop()


def start_bot_thread():
    global _started
    if _started:
        return
    _started = True
    import threading
    threading.Thread(target=lambda: asyncio.run(_run()), daemon=True).start()
    logger.info("Telegram bot started")
