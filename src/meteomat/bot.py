import asyncio
import logging
import os
import re
from io import BytesIO

import pandas as pd
import plotly.io as pio
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from meteomat.datasets.open_meteo import fetch_forecast
from meteomat.viz.charts import create_weather_dashboard

logger = logging.getLogger(__name__)

_started = False

_RANGES = {"24h": 24, "72h": 72, "7d": 168}
_RANGE_PATTERN = re.compile(r"\b(24h|72h|7d)\b", re.IGNORECASE)


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


def _forecast_png(location: dict, hours: int) -> BytesIO:
    data = fetch_forecast(location)
    dates = data["dates"]
    utc_offset = pd.Timedelta(seconds=data.get("utc_offset_seconds", 0))
    now = max(dates[0], min(pd.Timestamp.now("UTC").tz_localize(None) + utc_offset, dates[-1]))
    start = max(dates[0], now - pd.Timedelta(hours=4)) if hours == 24 else dates[0]
    end = min(now + pd.Timedelta(hours=hours), dates[-1])
    mask = (dates >= start) & (dates <= end)
    sliced = {k: v[mask] if hasattr(v, "__len__") and len(v) == len(dates) else v for k, v in data.items()}
    fig = create_weather_dashboard(sliced, location=location, now=now)
    fig.update_layout(paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e", font={"color": "#e0e0e0"})
    buf = BytesIO(pio.to_image(fig, format="png", width=1400, height=900))
    buf.seek(0)
    return buf


def _range_keyboard(location_key: str) -> InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton(r, callback_data=f"{r}|{location_key}") for r in _RANGES]
    return InlineKeyboardMarkup([buttons])


async def _send_forecast(update: Update, location: dict, hours: int, status_msg=None):
    try:
        image = _forecast_png(location, hours)
        range_label = next(k for k, v in _RANGES.items() if v == hours)
        caption = f"{range_label} forecast for {location['name']}"
        await update.effective_message.reply_photo(photo=image, caption=caption)
        if status_msg:
            await status_msg.delete()
    except Exception as e:
        logger.exception("forecast failed")
        text = f"Something went wrong: {e}"
        if status_msg:
            await status_msg.edit_text(text)
        else:
            await update.effective_message.reply_text(text)


async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a place name to get a forecast.\n"
        "You can also specify a range directly: Madrid 24h, Tokyo 7d, etc.\n"
        "Or drop a pin for your current location."
    )


async def _handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # Extract optional range suffix
    match = _RANGE_PATTERN.search(text)
    range_key = match.group(0).lower() if match else None
    name = _RANGE_PATTERN.sub("", text).strip()

    msg = await update.message.reply_text(f"Looking up {name}...")
    location = _geocode(name)
    if not location:
        await msg.edit_text(f"Could not find '{name}'. Try a different spelling.")
        return

    if range_key:
        await msg.edit_text(f"Fetching {range_key} forecast for {location['name']}...")
        await _send_forecast(update, location, _RANGES[range_key], status_msg=msg)
    else:
        # Store location in bot_data keyed by user+message so the callback can retrieve it
        location_key = f"{update.effective_user.id}:{update.message.message_id}"
        context.bot_data[location_key] = location
        await msg.edit_text(
            f"📍 {location['name']} — choose a forecast range:",
            reply_markup=_range_keyboard(location_key),
        )


async def _handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    range_key, location_key = query.data.split("|", 1)
    location = context.bot_data.get(location_key)
    if not location:
        await query.edit_message_text("Session expired — please send the location again.")
        return
    await query.edit_message_text(f"Fetching {range_key} forecast for {location['name']}...")
    await _send_forecast(update, location, _RANGES[range_key], status_msg=query.message)
    context.bot_data.pop(location_key, None)


async def _handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    location = {
        "lat": loc.latitude,
        "lon": loc.longitude,
        "name": f"{loc.latitude:.2f}°N, {loc.longitude:.2f}°E",
    }
    location_key = f"{update.effective_user.id}:{update.message.message_id}"
    context.bot_data[location_key] = location
    await update.message.reply_text(
        f"📍 {location['name']} — choose a forecast range:",
        reply_markup=_range_keyboard(location_key),
    )


async def _run():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", _cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_text))
    app.add_handler(MessageHandler(filters.LOCATION, _handle_location))
    app.add_handler(CallbackQueryHandler(_handle_callback))
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
    import time

    def _run_with_retry():
        while True:
            try:
                asyncio.run(_run())
            except Exception as e:
                logger.error(f"Bot crashed: {e}, retrying in 30s")
                time.sleep(30)

    threading.Thread(target=_run_with_retry, daemon=True).start()
    logger.info("Telegram bot started")
