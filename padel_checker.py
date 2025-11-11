import logging
import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
API_BASE_URL = "https://activezone.fun/api/v1/settings/tickets/user"
LOCATION_ID = os.environ.get("LOCATION_ID", "224")
DAYS_TO_CHECK = int(
    os.environ.get("DAYS_TO_CHECK", "7")
)  # Check next 7 days by default
DAY_DELAY = int(os.environ.get("DAY_DELAY", "1"))  # Check next 7 days by default
TICKET_FROM = os.environ.get("TICKET_FROM", "00:00")
TICKET_TO = os.environ.get("TICKET_TO", "23:59")


def send_telegram_message(message):
    """Send a message via Telegram bot"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials not set!")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Telegram message sent successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


def fetch_available_slots(date):
    """Fetch available slots for a specific date"""
    date_str = date.strftime("%Y-%m-%d")
    params = {
        "page": 0,
        "size": 2000,
        "ticketFrom": f"{date_str} {TICKET_FROM}:00",
        "ticketTo": f"{date_str} {TICKET_TO}:00",
        "locationIds": LOCATION_ID,
        "sportTypes": "padel",
        "isAuthorized": "true",
        "isAllCity": "false",
        "showSingle": "false",
        "status": "free",
        "cityId": 1,
        "isTrainer": "false",
    }

    try:
        response = requests.get(API_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        content = response.json()["content"]
        filtered_content = [
            item for item in content if item.get("court", {}).get("id") != 828
        ]

        return filtered_content
    except Exception as e:
        logger.error(f"Failed to fetch slots for {date_str}: {e}")
        return None


def parse_time(time_str):
    """Parse time string to datetime.time object"""
    try:
        # Handle different time formats
        if "T" in time_str:
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        else:
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        return dt.time()
    except Exception as e:
        logger.error(f"Failed to parse time {time_str}: {e}")
        return None


def find_consecutive_slots(data, date):
    """Find 3 consecutive 30-minute time slots (any court)"""
    if not data:
        return []

    # Extract all time slots
    slots = []
    for item in data:
        ticket_date_time_str = item.get("ticketDateTime", "")

        if ticket_date_time_str:
            try:
                # Parse the datetime string
                ticket_date_time = datetime.strptime(
                    ticket_date_time_str, "%Y-%m-%d %H:%M:%S"
                )

                slots.append(
                    {
                        "datetime": ticket_date_time,
                        "court": item.get("court", {}).get("name", "Unknown"),
                        "price": item.get("price", 0),
                    }
                )
            except ValueError:
                continue

    # Get unique time slots (there might be multiple courts at same time)
    unique_times = sorted(set(slot["datetime"] for slot in slots))

    # Find consecutive 30-minute slots
    consecutive_groups = []

    for i in range(len(unique_times) - 2):
        if unique_times[i + 1] == unique_times[i] + timedelta(
            minutes=30
        ) and unique_times[i + 2] == unique_times[i + 1] + timedelta(minutes=30):

            # Get all slots for these three times (all court options)
            time1 = unique_times[i]
            time2 = unique_times[i + 1]
            time3 = unique_times[i + 2]

            group = {
                "times": [time1, time2, time3],
                "slot1": [s for s in slots if s["datetime"] == time1],
                "slot2": [s for s in slots if s["datetime"] == time2],
                "slot3": [s for s in slots if s["datetime"] == time3],
            }
            consecutive_groups.append(group)

    return consecutive_groups


def format_message(date, consecutive_groups):
    """Format the Telegram message"""
    date_str = date.strftime("%Y-%m-%d (%A)")
    message = f"🎾 <b>Padel Court Available!</b>\n\n"
    message += f"📅 Date: {date_str}\n\n"

    for idx, group in enumerate(consecutive_groups, 1):
        start_time = group["times"][0].strftime("%H:%M")
        minutes_to_add = timedelta(minutes=30)
        end_time = (group["times"][2] + minutes_to_add).strftime("%H:%M")
        total_price = sum(
            slot["price"]
            for slot in [group["slot1"][0], group["slot2"][0], group["slot3"][0]]
        )

        message += f"<b>Option {idx}:</b>\n"
        message += f"⏰ Time: {start_time} - {end_time}\n"
        message += f"💰 Total Price: {total_price/100}\n\n"

    return message


def check_availability():
    """Main function to check availability for upcoming days"""
    logger.info("Starting availability check...")

    found_any = False

    for day_offset in range(DAY_DELAY, DAYS_TO_CHECK + DAY_DELAY):
        check_date = datetime.now() + timedelta(days=day_offset)
        logger.info(f"Checking {check_date.strftime('%Y-%m-%d')}...")

        data = fetch_available_slots(check_date)
        if not data:
            continue

        consecutive_groups = find_consecutive_slots(data, check_date)

        if consecutive_groups:
            logger.info(
                f"Found {len(consecutive_groups)} consecutive slot group(s) on {check_date.strftime('%Y-%m-%d')}"
            )
            message = format_message(check_date, consecutive_groups)
            send_telegram_message(message)
            found_any = True

    if not found_any:
        logger.info("No consecutive slots found in any of the checked days")


if __name__ == "__main__":
    logger.info("Padel Court Checker Started")
    check_availability()
    logger.info("Check completed")
