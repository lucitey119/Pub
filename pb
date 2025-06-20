import requests
import time
import hashlib
import json
import random
import string
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "https://beta.publicai.io/"

# Load token from account.json
with open('account.json', 'r') as f:
    account_data = json.load(f)
    TOKEN = account_data.get('token', '')

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}
TIMEOUT = 300  # Request timeout in seconds (from extension: 3e5 ms = 300s)

# Load proxies from proxy.txt
with open('proxy.txt', 'r') as f:
    PROXIES = [line.strip() for line in f if line.strip()]

# Placeholder payloads (customize based on PublicAI requirements)
EVENT_PAYLOAD = {
    "event_type": "user_action",
    "data": {"action": "generic_event"}
}
PING_PAYLOAD = {
    "status": "active",
    "data": {"timestamp": ""}
}

def generate_nonce(length=4):
    """Generate a random nonce string."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_signature(params, body, secret=""):
    """Generate MD5 signature for request as per extension logic."""
    # Combine query params and body params, excluding arrays and non-primitive types
    combined = {**params}
    if body:
        try:
            body_data = json.loads(body) if isinstance(body, str) else body
            combined.update({k: v for k, v in body_data.items() if not isinstance(v, (list, dict))})
        except json.JSONDecodeError:
            logger.warning("Invalid body JSON for signature; ignoring body.")

    # Sort keys and concatenate key-value pairs
    sorted_keys = sorted(k for k, v in combined.items() if not isinstance(v, (list, dict)))
    signature_string = "".join(f"{k}{combined[k]}" for k in sorted_keys)
    logger.debug(f"Signature string: {signature_string}")
    return hashlib.md5(signature_string.encode()).hexdigest()

def make_signed_request(method, endpoint, payload=None, params=None, retry_unsigned=False):
    """Make a signed API request with timestamp, nonce, and MD5 signature."""
    url = f"{BASE_URL}{endpoint}"
    params = params or {}

    # Add timestamp and nonce
    timestamp = int(datetime.now().timestamp())
    nonce = generate_nonce()
    params.update({"t": str(timestamp), "n": nonce})

    # Generate signature unless retrying without signature
    if not retry_unsigned:
        body_str = json.dumps(payload) if payload else ""
        params["s"] = generate_signature(params, payload)

    # Log request details
    request_url = requests.Request(method, url, headers=HEADERS, params=params, json=payload).prepare().url
    logger.debug(f"Sending {method} request to: {request_url}")

    # Try request with each proxy
    for proxy in PROXIES:
        proxy_dict = {
            "http": proxy,
            "https": proxy
        }
        try:
            if method == "GET":
                response = requests.get(url, headers=HEADERS, params=params, proxies=proxy_dict, timeout=TIMEOUT)
            elif method == "POST":
                response = requests.post(url, headers=HEADERS, params=params, json=payload, proxies=proxy_dict, timeout=TIMEOUT)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()

            # Parse JSON response
            data = response.json()
            if data.get("code", 200) != 200:
                raise Exception(f"API error: {data.get('msg', 'Unknown error')} (code: {data.get('code')})")

            logger.debug(f"Response: {json.dumps(data, indent=2)}")
            return data

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("Login Expired: Reconnect with a new Bearer token to continue earning points.")
            elif e.response.status_code == 400 and not retry_unsigned:
                logger.warning("Parameter error; retrying without signature.")
                return make_signed_request(method, endpoint, payload, params, retry_unsigned=True)
            else:
                logger.error(f"HTTP error with proxy {proxy}: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Request failed with proxy {proxy}: {e}")
        continue  # Try next proxy if current one fails

    logger.error("All proxies failed")
    raise Exception("All proxies failed")

def fetch_user_data():
    """Fetch user data from api/data_hunter/self."""
    try:
        data = make_signed_request("GET", "api/data_hunter/self")
        logger.info(f"User data: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        logger.error(f"Failed to fetch user data: {e}")
        return None

def send_event():
    """Send an event to api/data_hunter/event."""
    try:
        data = make_signed_request("POST", "api/data_hunter/event", EVENT_PAYLOAD)
        logger.info(f"Event sent successfully: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        logger.error(f"Failed to send event: {e}")
        return None

def send_ping():
    """Send a ping to api/data_hunter/ping."""
    try:
        ping_payload = PING_PAYLOAD.copy()
        ping_payload["data"]["timestamp"] = datetime.now().isoformat()
        data = make_signed_request("POST", "api/data_hunter/ping", ping_payload)
        logger.info(f"Ping sent successfully: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        logger.error(f"Failed to send ping: {e}")
        return None

def main():
    """Main loop to simulate extension behavior."""
    logger.info("Starting PublicAI point earner script...")

    # Initial user data fetch
    user_data = fetch_user_data()
    if not user_data:
        logger.warning("Initial user data fetch failed. Continuing with pings and events.")

    ping_interval = 60  # Send ping every 60 seconds
    event_interval = 300  # Send event every 300 seconds
    user_data_interval = 600  # Fetch user data every 10 minutes
    last_ping = last_event = last_user_data = time.time()

    while True:
        try:
            current_time = time.time()

            # Send ping
            if current_time - last_ping >= ping_interval:
                send_ping()
                last_ping = current_time

            # Send event
            if current_time - last_event >= event_interval:
                send_event()
                last_event = current_time

            # Fetch user data
            if current_time - last_user_data >= user_data_interval:
                fetch_user_data()
                last_user_data = current_time

            # Sleep to avoid excessive CPU usage
            time.sleep(10)

        except KeyboardInterrupt:
            logger.info("Script stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    main()
