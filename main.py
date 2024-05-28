import os
from dotenv import load_dotenv
import requests
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


# Load environment variables from .env file
load_dotenv()

# Telegram bot token and chat ID from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# URL of the Facebook page
FACEBOOK_PAGE_URL = os.getenv('FACEBOOK_PAGE_URL')

# File to store the latest post hash
LATEST_POST_FILE = 'latest_post_hash.json'

# Function to send a message to Telegram
async def send_telegram_message(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# Function to scrape the Facebook page
def scrape_facebook_page():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")  # Suppress logs
    options.add_argument("--silent")       # Suppress logs
    options.add_argument("--disable-extensions")  # Disable extensions
    options.add_argument("--disable-popup-blocking")  # Disable pop-ups

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(FACEBOOK_PAGE_URL)
    time.sleep(5)  # Wait for the page to load completely

    page_source = driver.page_source
    driver.quit()
    
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Extract posts using the data attribute
    posts = soup.find_all('div', {'data-ad-preview': 'message'})
    
    if posts:
        latest_post = posts[0]  # Assuming the latest post is the first one
        latest_post_text = latest_post.get_text(strip=True)  # Extract text content
        return latest_post_text
    return None

# Function to calculate the hash of a post
def calculate_hash(post):
    return hashlib.md5(post.encode('utf-8')).hexdigest()

# Function to load the latest post hash from file
def load_latest_post_hash():
    try:
        with open(LATEST_POST_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

# Function to save the latest post hash to file
def save_latest_post_hash(post_hash):
    with open(LATEST_POST_FILE, 'w') as file:
        json.dump(post_hash, file)

# Main function to check for new posts and send notifications
async def check_for_new_posts():
    latest_post_text = scrape_facebook_page()
    
    if latest_post_text:
        latest_post_hash = calculate_hash(latest_post_text)
        stored_post_hash = load_latest_post_hash()

        print("Latest post hash:", latest_post_hash)
        print("Stored post hash:", stored_post_hash)
        print("Are they equal: ", latest_post_hash == stored_post_hash)
        
        if stored_post_hash is None or latest_post_hash != stored_post_hash:
            await send_telegram_message(f"New post detected: \n \n{latest_post_text} \n \n{FACEBOOK_PAGE_URL}")
            save_latest_post_hash(latest_post_hash)

# Schedule the scraper to run every minute
if __name__ == "__main__":
    while True:
        asyncio.run(check_for_new_posts())
        time.sleep(15)
