import os
import random
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("8912701722:AAGQ56NXNLhhRtZ4JOvxrl3qWEbrF7SzElg")
CHAT_ID = os.getenv("-1004400411528")

API_URL = (
    "https://draw.ar-lottery01.com/"
    "WinGo/WinGo_1M/GetHistoryIssuePage.json"
)

POLL_SECONDS = 1

# =========================================================
# SIMPLE HTTP SERVER
# Render Web Service-এর জন্য PORT open রাখে
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Telegram Signal Bot is running.")

    def log_message(self, format, *args):
        return


def start_health_server():
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


# =========================================================
# API
# =========================================================

def get_latest_result():
    try:
        response = requests.get(
            API_URL,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        data = response.json()
        result_list = data.get("data", {}).get("list", [])

        if not result_list:
            return None

        return result_list[0]

    except Exception as e:
        print("API ERROR:", e)
        return None


# =========================================================
# SAME PREDICTION LOGIC
# =========================================================

def make_prediction():

    # একই logic:
    # Math.random() > 0.5 ? BIG : SMALL

    prediction = "BIG" if random.random() > 0.5 else "SMALL"

    if prediction == "BIG":

        # 5 - 9
        main_number = random.randint(5, 9)

    else:

        # 0 - 4
        main_number = random.randint(0, 4)

    # একই backup logic:
    # (main + 5) % 10

    backup_number = (main_number + 5) % 10

    return prediction, main_number, backup_number


# =========================================================
# RESULT LOGIC
# =========================================================

def get_actual_type(number):

    number = int(number)

    if number >= 5:
        return "BIG"

    return "SMALL"


# =========================================================
# TELEGRAM HELPERS
# =========================================================

async def send_message(application, text):

    if not CHAT_ID:
        print("CHAT_ID is not configured.")
        return

    try:
        await application.bot.send_message(
            chat_id=CHAT_ID,
            text=text
        )

    except Exception as e:
        print("TELEGRAM ERROR:", e)


# =========================================================
# COMMAND
# =========================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = (
        "🤖 EMON-VHAI SIGNAL BOT\n\n"
        "✅ Bot is online.\n"
        "⏱️ WinGo 1 Minute\n\n"
        "Signal system is running."
    )

    await update.message.reply_text(message)


async def id_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    await update.message.reply_text(
        f"Your Chat ID:\n\n{chat_id}"
    )


# =========================================================
# MAIN SIGNAL ENGINE
# =========================================================

async def signal_engine(application):

    last_period = None
    active_prediction = None
    active_number = None
    active_backup = None
    active_period = None

    print("Signal engine started.")

    while True:

        try:

            latest = get_latest_result()

            if latest is None:
                await asyncio_sleep(POLL_SECONDS)
                continue

            current_period = str(
                latest.get("issueNumber", "")
            )

            current_result = latest.get("number")

            if not current_period:
                await asyncio_sleep(POLL_SECONDS)
                continue

            # =================================================
            # FIRST RUN
            # =================================================

            if last_period is None:

                last_period = current_period

                next_period = str(
                    int(current_period) + 1
                )

                (
                    active_prediction,
                    active_number,
                    active_backup
                ) = make_prediction()

                active_period = next_period

                text = (
                    "━━━━━━━━━━━━━━━━━━\n"
                    "🔥 NEW SIGNAL\n"
                    "━━━━━━━━━━━━━━━━━━\n\n"

                    f"🎯 Period: {active_period}\n\n"

                    f"📊 Prediction: "
                    f"{active_prediction}\n"

                    f"🔢 Number: "
                    f"{active_number}\n"

                    f"🔄 Backup: "
                    f"{active_backup}\n\n"

                    "⏱️ WinGo 1 Minute\n"
                    "━━━━━━━━━━━━━━━━━━"
                )

                await send_message(
                    application,
                    text
                )

            # =================================================
            # NEW PERIOD
            # =================================================

            elif current_period != last_period:

                # -------------------------------------------------
                # Previous signal-এর result
                # -------------------------------------------------

                if (
                    active_period is not None
                    and current_result is not None
                ):

                    actual_number = int(
                        current_result
                    )

                    actual_result = get_actual_type(
                        actual_number
                    )

                    status = (
                        "WIN"
                        if active_prediction == actual_result
                        else "LOSS"
                    )

                    if status == "WIN":

                        result_icon = "✅"
                        result_text = "WIN"

                    else:

                        result_icon = "❌"
                        result_text = "LOSS"

                    result_message = (
                        "━━━━━━━━━━━━━━━━━━\n"
                        "📊 RESULT\n"
                        "━━━━━━━━━━━━━━━━━━\n\n"

                        f"🎯 Period: {active_period}\n\n"

                        f"📌 Signal: "
                        f"{active_prediction}\n"

                        f"🔢 Result: "
                        f"{actual_number}\n"

                        f"📊 Actual: "
                        f"{actual_result}\n\n"

                        f"{result_icon} Status: "
                        f"{result_text}\n"

                        "━━━━━━━━━━━━━━━━━━"
                    )

                    await send_message(
                        application,
                        result_message
                    )

                # -------------------------------------------------
                # New period
                # -------------------------------------------------

                last_period = current_period

                next_period = str(
                    int(current_period) + 1
                )

                (
                    active_prediction,
                    active_number,
                    active_backup
                ) = make_prediction()

                active_period = next_period

                signal_message = (
                    "━━━━━━━━━━━━━━━━━━\n"
                    "🔥 NEW SIGNAL\n"
                    "━━━━━━━━━━━━━━━━━━\n\n"

                    f"🎯 Period: {active_period}\n\n"

                    f"📊 Prediction: "
                    f"{active_prediction}\n"

                    f"🔢 Number: "
                    f"{active_number}\n"

                    f"🔄 Backup: "
                    f"{active_backup}\n\n"

                    "⏱️ WinGo 1 Minute\n"
                    "━━━━━━━━━━━━━━━━━━"
                )

                await send_message(
                    application,
                    signal_message
                )

        except Exception as e:

            print("ENGINE ERROR:", e)

        await asyncio_sleep(POLL_SECONDS)


# =========================================================
# ASYNC SLEEP
# =========================================================

async def asyncio_sleep(seconds):

    import asyncio

    await asyncio.sleep(seconds)


# =========================================================
# START
# =========================================================

async def main():

    if not BOT_TOKEN:8912701722:AAGQ56NXNLhhRtZ4JOvxrl3qWEbrF7SzElg

        print(
            "ERROR: BOT_TOKEN is not configured."
        )

        return

    # Start Render health server
    threading.Thread(
        target=start_health_server,
        daemon=True
    ).start()

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    application.add_handler(
        CommandHandler(
            "id",
            id_command
        )
    )

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    print("Telegram bot started.")

    await signal_engine(application)


if __name__ == "__main__":

    import asyncio

    asyncio.run(main())
