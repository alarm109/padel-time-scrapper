import hashlib
import json
import logging
import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "6772347030")
API_BASE_URL = "https://activezone.fun/api/v1/settings/tickets/user"
LOCATION_ID = os.environ.get("LOCATION_ID", "224")
DAYS_TO_CHECK = int(
    os.environ.get("DAYS_TO_CHECK", "7")
)  # Check next 7 days by default
DAY_DELAY = int(os.environ.get("DAY_DELAY", "1"))  # Check next 7 days by default
TICKET_FROM = os.environ.get("TICKET_FROM", "00:00")
TICKET_TO = os.environ.get("TICKET_TO", "23:59")
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")  # e.g., "padel-checker-state"
GCS_STATE_FILE = os.environ.get("GCS_STATE_FILE", "padel_state.json")
GAMES_API_URL = "https://activezone.fun/api/v1/settings/games"
GAME_LEVELS = [
    level.strip()
    for level in os.environ.get("GAME_LEVELS", "C,CPlus").split(",")
    if level.strip()
]
GAME_TYPE = os.environ.get("GAME_TYPE", "skirmish")
GAME_SPORT_TYPE = os.environ.get("GAME_SPORT_TYPE", "padel")
GAME_LOCATION_IDS = [
    loc.strip()
    for loc in os.environ.get("GAME_LOCATION_IDS", LOCATION_ID).split(",")
    if loc.strip()
]
GAME_LOOKAHEAD_DAYS = int(
    os.environ.get("GAME_LOOKAHEAD_DAYS", str(DAYS_TO_CHECK))
)
GAME_FROM_DELAY_MINUTES = int(os.environ.get("GAME_FROM_DELAY_MINUTES", "0"))
GAME_TIME_TO = os.environ.get("GAME_TIME_TO", "23:59:59")
GAME_PAGE_SIZE = max(int(os.environ.get("GAME_PAGE_SIZE", "50")), 1)
MAX_TRACKED_GAMES = max(int(os.environ.get("MAX_TRACKED_GAMES", "200")), 1)


def to_int(value):
    """Best-effort conversion to integer."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_gcs_client():
    """Initialize GCS client"""
    try:
        return storage.Client()
    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {e}")
        return None


def load_previous_state():
    """Load previous state from GCS"""
    if not GCS_BUCKET_NAME:
        logger.warning("GCS_BUCKET_NAME not set, skipping state comparison")
        return None

    try:
        client = get_gcs_client()
        if not client:
            return None

        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(GCS_STATE_FILE)

        if not blob.exists():
            logger.info("No previous state found, treating as first run")
            return None

        state_data = blob.download_as_text()
        return json.loads(state_data)
    except Exception as e:
        logger.error(f"Failed to load previous state: {e}")
        return None


def save_current_state(state):
    """Save current state to GCS"""
    if not GCS_BUCKET_NAME:
        logger.warning("GCS_BUCKET_NAME not set, skipping state save")
        return False

    try:
        client = get_gcs_client()
        if not client:
            return False

        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(GCS_STATE_FILE)

        state_json = json.dumps(state, indent=2)
        blob.upload_from_string(state_json, content_type="application/json")

        logger.info("State saved successfully to GCS")
        return True
    except Exception as e:
        logger.error(f"Failed to save state: {e}")
        return False


def generate_state_hash_for_date(groups):
    """Generate a hash for a specific date's availability"""
    # Sort and serialize the groups to ensure consistent hashing
    state_data = sorted(
        [
            {
                "times": [t.isoformat() for t in group["times"]],
                "courts": group["courts_used"],
                "is_preferred": group["is_preferred"],
            }
            for group in groups
        ],
        key=lambda x: str(x),
    )
    
    # Generate hash
    state_str = json.dumps(state_data, sort_keys=True)
    return hashlib.sha256(state_str.encode()).hexdigest()


def generate_state_by_date(consecutive_groups_by_date):
    """Generate state with hash for each date"""
    state_by_date = {}
    for date_str, groups in consecutive_groups_by_date.items():
        state_by_date[date_str] = {
            "hash": generate_state_hash_for_date(groups),
            "times": sorted(list(set(
                t.strftime("%H:%M")
                for group in groups
                for t in group["times"]
            ))),
        }
    return state_by_date


def find_changed_dates(previous_state, current_groups_by_date):
    """Find which dates have changed availability
    
    Returns:
        set: Set of date strings that have changed
    """
    if previous_state is None:
        logger.info("No previous state, all dates are new")
        return set(current_groups_by_date.keys())
    
    current_state_by_date = generate_state_by_date(current_groups_by_date)
    previous_state_by_date = previous_state.get("dates", {})
    
    changed_dates = set()
    
    # Check for new dates or changed dates
    for date_str, current_date_state in current_state_by_date.items():
        if date_str not in previous_state_by_date:
            logger.info(f"New date found: {date_str}")
            changed_dates.add(date_str)
        elif current_date_state["hash"] != previous_state_by_date[date_str].get("hash", ""):
            logger.info(f"Date changed: {date_str}")
            logger.info(f"  Previous times: {previous_state_by_date[date_str].get('times', [])}")
            logger.info(f"  Current times: {current_date_state['times']}")
            changed_dates.add(date_str)
    
    # Check for removed dates (dates that had availability but no longer do)
    for date_str in previous_state_by_date:
        if date_str not in current_state_by_date:
            logger.info(f"Date removed (no longer has availability): {date_str}")
            # We don't notify about removals, just log them
    
    if not changed_dates:
        logger.info("No dates have changed")
    
    return changed_dates


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
    """Find 3+ consecutive time slots (90+ minutes) that can be booked with at most 2 different courts"""
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

    # Need at least 3 unique times
    if len(unique_times) < 3:
        return []

    # Find all groups of 3+ consecutive time slots
    consecutive_groups = []
    seen_groups = set()

    # Find consecutive sequences starting from each position
    for start_idx in range(len(unique_times) - 2):
        # Check if we have at least 3 consecutive slots
        consecutive_times = [unique_times[start_idx]]
        
        for j in range(start_idx + 1, len(unique_times)):
            if unique_times[j] == consecutive_times[-1] + timedelta(minutes=30):
                consecutive_times.append(unique_times[j])
            else:
                break
        
        # We need at least 3 consecutive times (90 minutes)
        if len(consecutive_times) < 3:
            continue
        
        # For each group of exactly 3 consecutive times
        for end_idx in range(2, len(consecutive_times)):
            three_times = consecutive_times[:end_idx + 1]
            if len(three_times) != 3:
                continue
                
            # Get all available slots for these times
            time_slots = {
                time: [s for s in slots if s["datetime"] == time]
                for time in three_times
            }
            
            # Try to find a court combination that uses at most 2 different courts
            # Get all courts available at each time
            courts_by_time = {
                time: set(s["court"] for s in time_slots[time])
                for time in three_times
            }
            
            # Try to find valid combinations (at most 2 different courts)
            valid_combinations = []
            
            # Get all possible court combinations
            for court1 in time_slots[three_times[0]]:
                for court2 in time_slots[three_times[1]]:
                    for court3 in time_slots[three_times[2]]:
                        courts_used = {court1["court"], court2["court"], court3["court"]}
                        
                        if len(courts_used) <= 2:
                            is_preferred = len(courts_used) == 1
                            
                            combination = {
                                "times": three_times,
                                "slot1": court1,
                                "slot2": court2,
                                "slot3": court3,
                                "courts_used": sorted(list(courts_used)),
                                "is_preferred": is_preferred,
                            }
                            valid_combinations.append(combination)
            
            # Add unique combinations to results
            for combo in valid_combinations:
                # Create a unique key for this combination
                combo_key = (
                    tuple(combo["times"]),
                    combo["slot1"]["court"],
                    combo["slot2"]["court"],
                    combo["slot3"]["court"],
                )
                
                if combo_key not in seen_groups:
                    seen_groups.add(combo_key)
                    consecutive_groups.append(combo)

    # Deduplicate: keep only one option per unique time combination
    # Prefer "is_preferred" options (same court) over regular ones
    unique_groups = {}
    
    for group in consecutive_groups:
        time_key = tuple(group["times"])
        
        # If we haven't seen this time combination yet, add it
        if time_key not in unique_groups:
            unique_groups[time_key] = group
        # If we have seen it, keep the preferred one
        elif group["is_preferred"] and not unique_groups[time_key]["is_preferred"]:
            unique_groups[time_key] = group
    
    # Convert back to list and sort by time
    deduplicated_groups = list(unique_groups.values())
    deduplicated_groups.sort(key=lambda x: (not x["is_preferred"], x["times"][0]))

    return deduplicated_groups


def format_message(date, consecutive_groups):
    """Format the Telegram message"""
    date_str = date.strftime("%Y-%m-%d (%A)")
    message = f"🎾 <b>Padel Court Available!</b>\n\n"
    message += f"📅 Date: {date_str}\n\n"

    # Separate preferred and non-preferred bookings
    preferred = [g for g in consecutive_groups if g["is_preferred"]]
    regular = [g for g in consecutive_groups if not g["is_preferred"]]

    # Show preferred bookings first
    if preferred:
        message += f"⭐ <b>PREFERRED (Same Court):</b>\n\n"
        for idx, group in enumerate(preferred, 1):
            times_str = " → ".join([t.strftime("%H:%M") for t in group["times"]])
            total_price = (
                group["slot1"]["price"] + 
                group["slot2"]["price"] + 
                group["slot3"]["price"]
            )
            
            court_name = group["slot1"]["court"]
            
            message += f"<b>Option {idx}:</b>\n"
            message += f"⏰ Times: {times_str}\n"
            message += f"🏟 Court: {court_name}\n"
            message += f"💰 Total Price: €{total_price/100:.2f}\n\n"

    # Show regular bookings (2 courts)
    if regular:
        if preferred:
            message += f"📋 <b>Regular (2 Courts):</b>\n\n"
        
        start_idx = len(preferred) + 1
        for idx, group in enumerate(regular, start_idx):
            times_str = " → ".join([t.strftime("%H:%M") for t in group["times"]])
            total_price = (
                group["slot1"]["price"] + 
                group["slot2"]["price"] + 
                group["slot3"]["price"]
            )
            
            courts_str = " / ".join(group["courts_used"])
            court_details = (
                f"{group['slot1']['court']} → "
                f"{group['slot2']['court']} → "
                f"{group['slot3']['court']}"
            )
            
            message += f"<b>Option {idx}:</b>\n"
            message += f"⏰ Times: {times_str}\n"
            message += f"🏟 Courts: {court_details}\n"
            message += f"💰 Total Price: €{total_price/100:.2f}\n\n"

    return message


def parse_game_datetime(datetime_str):
    """Parse datetime strings returned by the games endpoint."""
    if not datetime_str:
        return None

    try:
        return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        except ValueError:
            logger.debug(f"Unable to parse game datetime: {datetime_str}")
            return None


def format_game_price(price_value):
    """Format price integers (cents) to a readable string."""
    if price_value is None:
        return "N/A"

    try:
        price_num = float(price_value)
    except (TypeError, ValueError):
        return str(price_value)

    if price_num >= 100:
        return f"€{price_num / 100:.2f}"
    return f"€{price_num:.2f}"


def normalize_game_record(game, earliest_start, latest_start):
    """Filter and annotate games that match configured constraints."""
    if not game:
        return None

    level = (game.get("level") or "").strip()
    if level not in GAME_LEVELS:
        return None

    vacancy = to_int(game.get("vacancy"))
    if vacancy is None or vacancy <= 0:
        return None

    if bool(game.get("privateGame")):
        return None

    status = (game.get("status") or "").lower()
    if status and status != "open":
        return None

    start_dt = parse_game_datetime(game.get("gameStart"))
    if not start_dt:
        return None
    if start_dt < earliest_start or start_dt > latest_start:
        return None

    normalized = dict(game)
    normalized["parsed_start"] = start_dt
    normalized["parsed_end"] = parse_game_datetime(game.get("gameEnd"))
    normalized["vacancy_normalized"] = vacancy
    return normalized


def fetch_available_games():
    """Fetch upcoming games that have available spots."""
    if not GAME_LEVELS:
        logger.warning("GAME_LEVELS not configured; skipping game scraping")
        return []

    if not GAME_LOCATION_IDS:
        logger.warning("GAME_LOCATION_IDS not configured; skipping game scraping")
        return []

    now = datetime.now()
    earliest_start = now + timedelta(minutes=GAME_FROM_DELAY_MINUTES)
    latest_start = now + timedelta(days=GAME_LOOKAHEAD_DAYS)

    aggregated_games = {}
    base_params = [
        ("gameFrom", earliest_start.strftime("%Y-%m-%d %H:%M:%S")),
        ("timeTo", GAME_TIME_TO),
        ("showFull", "false"),
        ("gameType", GAME_TYPE),
        ("infiniteScroll", "false"),
        ("sort", "gameStart,asc"),
        ("sportTypes", GAME_SPORT_TYPE),
    ]

    for level in GAME_LEVELS:
        page = 0
        while True:
            params = list(base_params)
            params.append(("page", page))
            params.append(("gameLevels", level))
            for location_id in GAME_LOCATION_IDS:
                params.append(("locationIds", location_id))

            try:
                response = requests.get(GAMES_API_URL, params=params, timeout=15)
                response.raise_for_status()
            except Exception as exc:
                logger.error(
                    "Failed to fetch games for level %s (page %s): %s",
                    level,
                    page,
                    exc,
                )
                break

            payload = response.json()
            for game in payload.get("content", []):
                normalized = normalize_game_record(game, earliest_start, latest_start)
                if not normalized:
                    continue

                game_uuid = normalized.get("gameUUID") or str(normalized.get("id"))
                if not game_uuid or game_uuid in aggregated_games:
                    continue

                aggregated_games[game_uuid] = normalized

            if payload.get("last", True):
                break

            page += 1

    games = list(aggregated_games.values())
    games.sort(key=lambda g: g.get("parsed_start", datetime.max))

    if games:
        logger.info("Found %d open game(s) matching filters", len(games))
    else:
        logger.info("No open games matched the configured filters")

    return games


def format_game_notification(game):
    """Build the Telegram payload for a single game."""
    start_dt = game.get("parsed_start") or parse_game_datetime(game.get("gameStart"))
    end_dt = game.get("parsed_end") or parse_game_datetime(game.get("gameEnd"))

    location = (game.get("locations") or [{}])[0]
    address = location.get("address") or {}
    city = (address.get("city") or {}).get("name")

    vacancy = game.get("vacancy_normalized")
    if vacancy is None:
        vacancy = to_int(game.get("vacancy")) or 0

    total_players = to_int(game.get("totalAcceptedPlayers")) or to_int(
        (game.get("sport") or {}).get("totalAcceptedPlayers")
    )

    name = (game.get("name") or "Padel Game").strip()
    level = (game.get("level") or "?").strip()

    lines = [
        "🔥 <b>New Padel Game Found!</b>",
        "",
        f"🏷 {name} ({level})",
    ]

    if start_dt:
        lines.append(f"📅 {start_dt.strftime('%Y-%m-%d (%A) %H:%M')}")

    if end_dt:
        lines.append(f"⏱ Ends: {end_dt.strftime('%H:%M')}")

    location_line = f"📍 {location.get('name', 'Unknown location')}"
    if city:
        location_line += f", {city}"
    lines.append(location_line)

    spots_line = f"👥 Spots: {vacancy}"
    if total_players:
        spots_line += f"/{total_players}"
    lines.append(spots_line)

    lines.append(f"💰 Price: {format_game_price(game.get('price'))}")

    court_list = (game.get("courtList") or "").strip()
    if court_list:
        lines.append(f"🏟 Courts: {court_list}")

    external_link = (game.get("externalLink") or "").strip()
    if external_link:
        lines.extend(["", f"🔗 {external_link}"])

    return "\n".join(lines)


def prune_notified_games(notified_games):
    """Prevent the stored state from growing indefinitely."""
    if not notified_games or len(notified_games) <= MAX_TRACKED_GAMES:
        return

    sorted_items = sorted(
        notified_games.items(),
        key=lambda item: item[1].get("notified_at", item[1].get("gameStart", "")),
    )
    excess = len(sorted_items) - MAX_TRACKED_GAMES
    for game_id, _ in sorted_items[:excess]:
        notified_games.pop(game_id, None)


def scrape_and_notify_games(previous_games_state):
    """Fetch games and notify about those we have not alerted before."""
    available_games = fetch_available_games()
    previous_games_state = previous_games_state or {}
    notified_games = dict(previous_games_state.get("notified", {}))

    notifications_sent = 0
    for game in available_games:
        game_uuid = game.get("gameUUID") or str(game.get("id"))
        if not game_uuid or game_uuid in notified_games:
            continue

        message = format_game_notification(game)
        if send_telegram_message(message):
            notifications_sent += 1
            notified_games[game_uuid] = {
                "name": game.get("name"),
                "gameStart": game.get("gameStart"),
                "level": game.get("level"),
                "notified_at": datetime.now().isoformat(),
            }
            logger.info(
                "Notified about game %s at %s",
                game.get("name"),
                game.get("gameStart"),
            )
        else:
            logger.warning(
                "Failed to send Telegram notification for game %s",
                game_uuid,
            )

    prune_notified_games(notified_games)

    if notifications_sent:
        logger.info("Sent %d new game notification(s)", notifications_sent)
    else:
        logger.info("No new game notifications to send")

    return {"notified": notified_games}, notifications_sent > 0


def check_availability():
    """Main function to check availability for upcoming days"""
    logger.info("Starting availability check...")

    previous_state_raw = load_previous_state()
    previous_state = previous_state_raw or {}
    state_payload = {
        "dates": previous_state.get("dates", {}),
        "games": previous_state.get("games", {}),
    }
    state_changed = False

    # Collect all availability data
    all_consecutive_groups = {}

    for day_offset in range(DAY_DELAY, DAYS_TO_CHECK + DAY_DELAY):
        check_date = datetime.now() + timedelta(days=day_offset)
        logger.info(f"Checking {check_date.strftime('%Y-%m-%d')}...")

        data = fetch_available_slots(check_date)
        if not data:
            continue

        consecutive_groups = find_consecutive_slots(data, check_date)

        if consecutive_groups:
            date_str = check_date.strftime("%Y-%m-%d")
            all_consecutive_groups[date_str] = consecutive_groups
            logger.info(
                f"Found {len(consecutive_groups)} consecutive slot group(s) on {date_str}"
            )

    # if not all_consecutive_groups:
    #     logger.info("No consecutive slots found in any of the checked days")
    # else:
    #     changed_dates = find_changed_dates(previous_state_raw, all_consecutive_groups)

    #     if changed_dates:
    #         for date_str in sorted(changed_dates):
    #             if date_str not in all_consecutive_groups:
    #                 continue

    #             consecutive_groups = all_consecutive_groups[date_str]
    #             check_date = datetime.strptime(date_str, "%Y-%m-%d")
    #             message = format_message(check_date, consecutive_groups)
    #             send_telegram_message(message)

    #         state_payload["dates"] = generate_state_by_date(all_consecutive_groups)
    #         state_changed = True
    #         logger.info(f"Sent notifications for {len(changed_dates)} date(s)")
    #     else:
    #         logger.info("No changes detected for court availability; skipping alerts")

    # if not all_consecutive_groups and previous_state.get("dates"):
    #     state_payload["dates"] = {}
    #     state_changed = True

    games_state, games_changed = scrape_and_notify_games(previous_state.get("games"))
    state_payload["games"] = games_state
    state_changed = state_changed or games_changed

    if state_changed:
        state_payload["last_updated"] = datetime.now().isoformat()
        save_current_state(state_payload)
    else:
        logger.info("State unchanged; skipping state persistence")


if __name__ == "__main__":
    logger.info("Padel Court Checker Started")
    check_availability()
    logger.info("Check completed")
