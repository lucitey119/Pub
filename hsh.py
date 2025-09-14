import requests
import json
import random
import string
import re
import time
import os
from datetime import datetime, timedelta
import pytz

# Base URL and headers
BASE_URL = "https://www.hashj.io"
BASE_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/index/user/register.html",
    "X-Requested-With": "XMLHttpRequest"
}

# Fixed password for all accounts
FIXED_PASSWORD = "Larry5000@."

# Nigeria time zone
nigeria_tz = pytz.timezone('Africa/Lagos')

# Device profiles for User-Agent, sec-ch-ua, platform, and resolution
device_profiles = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
        "sec-ch-ua-platform": "\"Windows\"",
        "screen_resolution": "1920x1080",
        "viewport_width": "1920"
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
        "sec-ch-ua": "\"Safari\";v=\"17\", \"Not/A)Brand\";v=\"99\"",
        "sec-ch-ua-platform": "\"macOS\"",
        "screen_resolution": "1440x900",
        "viewport_width": "1440"
    },
    {
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-A505F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
        "sec-ch-ua": "\"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"99\"",
        "sec-ch-ua-platform": "\"Android\"",
        "screen_resolution": "360x800",
        "viewport_width": "360"
    },
    {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
        "sec-ch-ua": "\"Safari\";v=\"17\", \"Not/A)Brand\";v=\"99\"",
        "sec-ch-ua-platform": "\"iOS\"",
        "screen_resolution": "390x844",
        "viewport_width": "390"
    },
]

# Function to get a random device profile
def get_device_profile():
    return random.choice(device_profiles)

# Function to generate diverse email patterns
def generate_random_email(counter, used_emails):
    first_names = ["john", "emma", "michael", "sarah", "david", "laura", "james", "kate", "chris", "anna"]
    last_names = ["smith", "johnson", "brown", "taylor", "wilson", "davis", "clark", "harris", "lewis", "walker"]
    adjectives = ["sunny", "blue", "happy", "star", "bright", "cloud", "moon", "sky", "green", "spark"]
    nouns = ["river", "hill", "tree", "stone", "lake", "wind", "flame", "wave", "path", "dawn"]
    email_domains = ["gmail.com", "yahoo.com", "outlook.com", "protonmail.com", "hotmail.com", "aol.com", "icloud.com"]
    
    patterns = [
        lambda: f"{random.choice(first_names)}{random.choice(['.', '_', ''])}"
                f"{random.choice(last_names)}{random.randint(100, 9999)}@{random.choice(email_domains)}",
        lambda: f"{random.choice(first_names)[0]}{random.choice(['.', '_', ''])}{random.choice(last_names)}"
                f"{random.randint(80, 99)}@{random.choice(email_domains)}",
        lambda: f"{random.choice(first_names)}{random_string(3)}"
                f"{random.randint(10, 99)}@{random.choice(email_domains)}",
    ]

    def random_string(length):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

    while True:
        email = random.choice(patterns)()
        if counter > 0:
            email = email.rsplit('@', 1)[0] + random_string(3) + '@' + email.rsplit('@', 1)[1]
        if email not in used_emails:
            return email
        counter += 1

# Function to load used emails from hashj.txt
def load_used_emails():
    used_emails = set()
    try:
        with open("hashj.txt", "r") as f:
            for line in f:
                if line.strip():
                    email = line.split(" ")[0]
                    used_emails.add(email)
    except FileNotFoundError:
        pass  # File may not exist yet, which is fine
    return used_emails

# Function to load proxies from prox.txt
def load_proxies():
    try:
        if os.path.exists("prox.txt"):
            with open("prox.txt", "r") as file:
                proxies = [f"http://{line.strip()}" for line in file if line.strip()]
            return proxies
        else:
            print("prox.txt not found.")
            return []
    except Exception as e:
        print(f"Error loading proxies: {e}")
        return []

# Function to load used proxies from used_proxies.txt
def load_used_proxies():
    try:
        if os.path.exists("used_proxies.txt"):
            with open("used_proxies.txt", "r") as file:
                return set(line.strip() for line in file if line.strip())
        return set()
    except Exception as e:
        print(f"Error loading used proxies: {e}")
        return set()

# Function to save a used proxy to used_proxies.txt
def save_used_proxy(proxy, error=False):
    try:
        proxy_clean = proxy.replace("http://", "").strip()
        time.sleep(random.uniform(8, 16) if error else random.uniform(6, 9))
        if os.path.exists("used_proxies.txt") and os.path.getsize("used_proxies.txt") > 0:
            with open("used_proxies.txt", "rb") as f:
                f.seek(-1, os.SEEK_END)
                last_char = f.read(1)
                if last_char != b'\n':
                    with open("used_proxies.txt", "a") as file_append:
                        file_append.write("\n")
                        file_append.flush()
        with open("used_proxies.txt", "a") as file:
            file.write(f"{proxy_clean}\n")
            file.flush()
    except Exception as e:
        print(f"Error saving used proxy {proxy}: {e}")

# Function to initialize session with optional proxy
def initialize_session(proxy=None, proxy_number=None, total_proxies=None):
    session = requests.Session()
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
        if proxy_number and total_proxies:
            print(f"Using proxy {proxy_number}/{total_proxies}: {proxy}")
        else:
            print(f"Using proxy: {proxy}")
    return session

# Function to get captcha
def get_captcha(session):
    url = f"{BASE_URL}/index/login/captcha"
    profile = get_device_profile()
    headers = BASE_HEADERS.copy()
    headers.update({
        "User-Agent": profile["User-Agent"],
        "Sec-Ch-Ua": profile["sec-ch-ua"],
        "Sec-Ch-Ua-Platform": profile["sec-ch-ua-platform"],
        "sec-ch-viewport-width": profile["viewport_width"],
        "Screen-Resolution": profile["screen_resolution"]
    })
    response = session.post(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 1:
            return data["data"]["code"], data["data"]["uniqid"]
    return None, None

# Function to register account
def register_account(session, email, password, captcha_code, uniqid):
    url = f"{BASE_URL}/index/login/reg"
    profile = get_device_profile()
    headers = BASE_HEADERS.copy()
    headers.update({
        "User-Agent": profile["User-Agent"],
        "Sec-Ch-Ua": profile["sec-ch-ua"],
        "Sec-Ch-Ua-Platform": profile["sec-ch-ua-platform"],
        "sec-ch-viewport-width": profile["viewport_width"],
        "Screen-Resolution": profile["screen_resolution"]
    })
    payload = {
        "phone": email,
        "password": password,
        "top": random_string(6),
        "captcha": captcha_code,
        "uniqid": uniqid,
        "__qd": "",
        "zz_referer": ""
    }
    response = session.post(url, headers=headers, data=payload)
    return response.status_code == 200 and response.json().get("code") == 1

# Function to login
def login(session, email, password):
    url = f"{BASE_URL}/index/login/index"
    profile = get_device_profile()
    headers = BASE_HEADERS.copy()
    headers.update({
        "User-Agent": profile["User-Agent"],
        "Sec-Ch-Ua": profile["sec-ch-ua"],
        "Sec-Ch-Ua-Platform": profile["sec-ch-ua-platform"],
        "sec-ch-viewport-width": profile["viewport_width"],
        "Screen-Resolution": profile["screen_resolution"]
    })
    payload = {
        "phone": email,
        "password": password
    }
    response = session.post(url, headers=headers, data=payload)
    return response.status_code == 200 and response.json().get("code") == 1

# Function to buy product
def buy_product(session, product_id=84, quantity=1, password=""):
    url = f"{BASE_URL}/index/index/mall_form"
    profile = get_device_profile()
    headers = BASE_HEADERS.copy()
    headers.update({
        "User-Agent": profile["User-Agent"],
        "Sec-Ch-Ua": profile["sec-ch-ua"],
        "Sec-Ch-Ua-Platform": profile["sec-ch-ua-platform"],
        "sec-ch-viewport-width": profile["viewport_width"],
        "Screen-Resolution": profile["screen_resolution"],
        "Referer": f"{BASE_URL}/index/index/mall_form?id={product_id}&num={quantity}"
    })
    payload = {
        "id": product_id,
        "buynum": quantity,
        "ty": 1,
        "tran_type": 0,
        "password": password
    }
    response = session.post(url, headers=headers, data=payload)
    return response.status_code == 200 and response.json().get("code") == 1

# Function to read credentials from hashj.txt
def read_credentials():
    credentials = []
    try:
        with open("hashj.txt", "r") as f:
            for line in f:
                if line.strip():
                    email, password = line.strip().split(" ", 1)
                    credentials.append((email, password))
    except FileNotFoundError:
        print("hashj.txt not found. Please run option 1 first to create accounts.")
    return credentials

# Function to generate random string
def random_string(length):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

# Main function
def main():
    print("Select an option:")
    print("1. Register accounts")
    print("2. Login and buy")
    option = input("Enter option (1 or 2): ")

    if option == "1":
        num_accounts = int(input("How many accounts do you want to create? "))
        use_proxies = input("Do you want to use proxies from prox.txt? (y/n): ").strip().lower() == 'y'
        proxies = load_proxies() if use_proxies else []
        if use_proxies and not proxies:
            print("No proxies available in prox.txt. Exiting.")
            return
        used_proxies = load_used_proxies()
        proxy_index = 0
        used_emails = load_used_emails()
        email_counter = 0
        total_proxies = len(proxies) if use_proxies else None

        with open("hashj.txt", "a") as f:
            for i in range(num_accounts):
                print(f"Processing account {i+1}/{num_accounts}")
                proxy = None
                proxy_number = None
                if use_proxies:
                    while proxy_index < len(proxies):
                        candidate_proxy = proxies[proxy_index]
                        proxy_number = proxy_index + 1
                        candidate_proxy_clean = candidate_proxy.replace("http://", "")
                        if candidate_proxy_clean not in used_proxies:
                            proxy = candidate_proxy
                            used_proxies.add(candidate_proxy_clean)
                            proxy_index += 1
                            break
                        else:
                            print(f"Proxy {proxy_number}/{total_proxies}: {candidate_proxy} already used, skipping to next")
                            proxy_index += 1
                    else:
                        print("No unused proxies available. Exiting.")
                        return

                session = initialize_session(proxy, proxy_number, total_proxies)
                # Generate email
                email = generate_random_email(email_counter, used_emails)
                used_emails.add(email)
                email_counter += 1
                password = FIXED_PASSWORD
                
                # Get captcha
                captcha_code, uniqid = get_captcha(session)
                if not captcha_code or not uniqid:
                    print(f"Failed to get captcha for account {email}")
                    if proxy:
                        save_used_proxy(proxy, error=True)
                    session.close()
                    time.sleep(random.uniform(2, 4))  # Random delay of 2-4 seconds
                    continue
                
                # Register account
                if register_account(session, email, password, captcha_code, uniqid):
                    print(f"Successfully registered account: {email}")
                    # Save account details in the format: email password
                    f.write(f"{email} {password}\n")
                    f.flush()
                    if proxy:
                        save_used_proxy(proxy, error=False)
                else:
                    print(f"Failed to register account: {email}")
                    if proxy:
                        save_used_proxy(proxy, error=True)
                session.close()
                time.sleep(random.uniform(2, 4))  # Random delay of 2-4 seconds
    
    elif option == "2":
        while True:
            credentials = read_credentials()
            if not credentials:
                print("No credentials found in hashj.txt. Exiting.")
                return
            
            last_cycle_time = datetime.now(nigeria_tz)
            print(f"Starting cycle at: {last_cycle_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            use_proxies = input("Do you want to use proxies from prox.txt? (y/n): ").strip().lower() == 'y'
            proxies = load_proxies() if use_proxies else []
            if use_proxies and not proxies:
                print("No proxies available in prox.txt. Exiting.")
                return
            used_proxies = load_used_proxies()
            total_proxies = len(proxies) if use_proxies else None

            for i, (email, password) in enumerate(credentials, 1):
                print(f"Processing account {i}/{len(credentials)}")
                proxy = None
                proxy_number = None
                if use_proxies:
                    available_proxies = [p for p in proxies if p.replace("http://", "") not in used_proxies]
                    if not available_proxies:
                        print("No unused proxies available. Exiting.")
                        return
                    proxy = random.choice(available_proxies)
                    proxy_number = proxies.index(proxy) + 1
                    used_proxies.add(proxy.replace("http://", ""))

                session = initialize_session(proxy, proxy_number, total_proxies)
                # Login
                if login(session, email, password):
                    print(f"Successfully logged in with account: {email}")
                    # Buy product
                    if buy_product(session, product_id=84, quantity=1, password=password):
                        print(f"Successfully purchased product for account: {email}")
                        if proxy:
                            save_used_proxy(proxy, error=False)
                    else:
                        print(f"Failed to purchase product for account: {email}")
                        if proxy:
                            save_used_proxy(proxy, error=True)
                else:
                    print(f"Failed to login with account: {email}")
                    if proxy:
                        save_used_proxy(proxy, error=True)
                session.close()
                time.sleep(random.uniform(2, 3))  # Random delay of 2-3 seconds
            
            print(f"Cycle completed at: {datetime.now(nigeria_tz).strftime('%Y-%m-%d %H:%M:%S %Z')}")
            next_cycle_time = last_cycle_time + timedelta(hours=24, seconds=2)
            print(f"Next cycle starts at: {next_cycle_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print("Waiting 24 hours and 2 seconds before restarting cycle...")
            time.sleep(24 * 3600 + 2)  # 24 hours and 2 seconds
    
    else:
        print("Invalid option. Please choose 1 or 2.")

if __name__ == "__main__":
    main()
