import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import json
import hashlib
from telegram import Bot
import asyncio
from datetime import datetime  # Import datetime module

# Load environment variables from .env file
load_dotenv()

# Telegram bot token and chat ID from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
# URL of the Facebook page
FACEBOOK_PAGE_URL = os.getenv('FACEBOOK_PAGE_URL')
# File to store the latest post hash
LATEST_POST_FILE = 'latest_post_hash.json'
# Retry delay in seconds
RETRY_DELAY = 30
# Retry attempt count
RETRY_ATTEMPT_COUNT = 9999999

# ANSI color codes
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    LIGHTBLUE = '\033[94m'
    DARKBLUE = '\033[34m'
    LIGHTGREEN = '\033[92m'
    DARKGREEN = '\033[32m'
    LIGHTRED = '\033[91m'
    DARKRED = '\033[31m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BLACK = '\033[30m'
    GRAY = '\033[90m'
    LIGHTGRAY = '\033[37m'
    BROWN = '\033[33m'
    ORANGE = '\033[38;5;208m'
    PINK = '\033[38;5;206m'
    PURPLE = '\033[35m'

# Function to send a message to Telegram
async def send_telegram_message(message):
    for attempt in range(RETRY_ATTEMPT_COUNT):
        try:
            print(f"{bcolors.OKBLUE}Attempt {attempt + 1}: Sending message to Telegram.{bcolors.ENDC}")
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
            print(f"{bcolors.OKGREEN}Message sent to Telegram successfully.{bcolors.ENDC}")
            return
        except Exception as e:
            print(f"{bcolors.FAIL}Error sending message: {e}. Retrying in {RETRY_DELAY} seconds...{bcolors.ENDC}")
            time.sleep(RETRY_DELAY)
    print(f"{bcolors.FAIL}Failed to send message after multiple attempts.{bcolors.ENDC}")

# Function to scrape the Facebook page
def scrape_facebook_page():
    options = Options()
    options.add_argument("--headless")  # Comment this line to run in non-headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")  # Suppress logs
    options.add_argument("--silent")       # Suppress logs
    options.add_argument("--disable-extensions")  # Disable extensions
    options.add_argument("--disable-popup-blocking")  # Disable pop-ups
    options.add_argument("--remote-debugging-port=9222")  # Enable remote debugging
    options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images
    options.add_argument("--disable-javascript")  # Disable JavaScript

    for attempt in range(RETRY_ATTEMPT_COUNT):
        try:
            print(f"{bcolors.OKBLUE}Attempt {attempt + 1}: Initializing Chrome driver.{bcolors.ENDC}")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.set_page_load_timeout(60)  # Set a longer timeout for loading the page

            print(f"{bcolors.OKBLUE}Opening Facebook page.{bcolors.ENDC}")
            driver.get(FACEBOOK_PAGE_URL)
            time.sleep(10)  # Wait for the page to load completely

            print(f"{bcolors.OKGREEN}Page loaded successfully. Retrieving page source.{bcolors.ENDC}")
            page_source = driver.page_source
            driver.quit()

            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract posts using the data attribute
            print(f"{bcolors.OKBLUE}Extracting posts from the page.{bcolors.ENDC}")
            posts = soup.find_all('div', {'data-ad-preview': 'message'})

            if posts:
                latest_post = posts[0]  # Assuming the latest post is the first one
                latest_post_text = latest_post.get_text(strip=True)  # Extract text content
                print(f"{bcolors.OKGREEN}Post extracted successfully.{bcolors.ENDC}")
                return latest_post_text
            print(f"{bcolors.WARNING}No posts found on the page.{bcolors.ENDC}")
            return None
        except Exception as e:
            print(f"{bcolors.FAIL}Error scraping page: {e}. Retrying in {RETRY_DELAY} seconds...{bcolors.ENDC}")
            time.sleep(RETRY_DELAY)
    print(f"{bcolors.FAIL}Failed to scrape page after multiple attempts.{bcolors.ENDC}")
    return None

# Function to calculate the hash of a post
def calculate_hash(post):
    print(f"{bcolors.OKBLUE}Calculating hash of the post.{bcolors.ENDC}")
    return hashlib.md5(post.encode('utf-8')).hexdigest()

# Function to load the latest post hash from file
def load_latest_post_hash():
    for attempt in range(RETRY_ATTEMPT_COUNT):
        try:
            print(f"{bcolors.OKBLUE}Attempt {attempt + 1}: Loading latest post hash from file.{bcolors.ENDC}")
            with open(LATEST_POST_FILE, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"{bcolors.FAIL}Error loading latest post hash: {e}. Retrying in {RETRY_DELAY} seconds...{bcolors.ENDC}")
            time.sleep(RETRY_DELAY)
    print(f"{bcolors.FAIL}Failed to load latest post hash after multiple attempts.{bcolors.ENDC}")
    return None

# Function to save the latest post hash to file
def save_latest_post_hash(post_hash):
    for attempt in range(RETRY_ATTEMPT_COUNT):
        try:
            print(f"{bcolors.OKBLUE}Attempt {attempt + 1}: Saving latest post hash to file.{bcolors.ENDC}")
            with open(LATEST_POST_FILE, 'w') as file:
                json.dump(post_hash, file)
                print(f"{bcolors.OKGREEN}Latest post hash saved successfully.{bcolors.ENDC}")
                return
        except Exception as e:
            print(f"{bcolors.FAIL}Error saving latest post hash: {e}. Retrying in {RETRY_DELAY} seconds...{bcolors.ENDC}")
            time.sleep(RETRY_DELAY)
    print(f"{bcolors.FAIL}Failed to save latest post hash after multiple attempts.{bcolors.ENDC}")

# Main function to check for new posts and send notifications
async def check_for_new_posts():
    while True:
        print(f"{bcolors.HEADER}\n-------------------START-------------------\n{bcolors.ENDC}")
        latest_post_text = None
        while latest_post_text is None:
            print(f"{bcolors.OKBLUE}Starting to scrape Facebook page.{bcolors.ENDC}")
            latest_post_text = scrape_facebook_page()
            if latest_post_text is None:
                print(f"{bcolors.FAIL}Failed to reach the Facebook page. Retrying in 30 seconds...{bcolors.ENDC}")
                time.sleep(RETRY_DELAY)
        
        latest_post_hash = calculate_hash(latest_post_text)
        stored_post_hash = load_latest_post_hash()
        print(f"{bcolors.OKBLUE}Latest post hash: {bcolors.WHITE}{latest_post_hash}{bcolors.ENDC}")
        print(f"{bcolors.OKBLUE}Stored post hash: {bcolors.WHITE}{stored_post_hash}{bcolors.ENDC}")
        print(f"{bcolors.OKBLUE}Are they equal: {bcolors.BOLD}{bcolors.OKCYAN}{latest_post_hash == stored_post_hash}{bcolors.ENDC}")

        if stored_post_hash is None or latest_post_hash != stored_post_hash:
            print(f"{bcolors.WARNING}New post detected. Sending notification to Telegram.{bcolors.ENDC}")
            await send_telegram_message(f"New post detected: \n \n{latest_post_text} \n \n{FACEBOOK_PAGE_URL}")
            save_latest_post_hash(latest_post_hash)
        
        # Get current local date and time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{bcolors.OKBLUE}Last checked date and time: {bcolors.BOLD}{bcolors.LIGHTRED}{current_time}{bcolors.ENDC}")
        
        print(f"{bcolors.OKBLUE}Waiting for 5 minutes before checking again.{bcolors.ENDC}")
        print(f"{bcolors.HEADER}\n-------------------END-------------------\n{bcolors.ENDC}")
        time.sleep(300)  # Wait for 5 minutes before checking again

# Schedule the scraper to run every minute
if __name__ == "__main__":
    asyncio.run(check_for_new_posts())