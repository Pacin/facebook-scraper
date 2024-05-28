import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from pyppeteer import launch
import json
from telegram import Bot
import asyncio
import time

# Load environment variables
print("Loading environment variables...")
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set in the environment variables.")
    exit(1)

print("Environment variables loaded successfully.")

# URL of the Facebook page
FACEBOOK_PAGE_URL = 'https://www.facebook.com/SerkanYaman006'

# File to store the latest post
LATEST_POST_FILE = 'latest_post.json'

# Function to send a message to Telegram
async def send_telegram_message(message):
    try:
        print("Sending message to Telegram...")
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
        print("Message sent to Telegram.")
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")

# Function to scrape the Facebook page using pyppeteer
async def scrape_facebook_page():
    try:
        print("Launching browser...")
        browser = await launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--window-size=1280x1024'
            ]
        )
        page = await browser.newPage()
        print(f"Navigating to {FACEBOOK_PAGE_URL}...")
        await page.goto(FACEBOOK_PAGE_URL)
        print("Waiting for selector...")
        await page.waitForSelector('[data-ad-preview="message"]', {'timeout': 10000})
        
        print("Fetching page content...")
        content = await page.content()
        await browser.close()
        
        print("Parsing page content with BeautifulSoup...")
        soup = BeautifulSoup(content, 'html.parser')
        posts = soup.find_all('div', {'data-ad-preview': 'message'})
        
        if posts:
            latest_post_text = posts[0].get_text(strip=True)
            print(f"Latest post text: {latest_post_text}")
            return latest_post_text
        else:
            print("No posts found on the page.")
            return None
    except Exception as e:
        print(f"Error scraping Facebook page: {e}")
        return None

# Function to load the latest post from file
def load_latest_post():
    try:
        print("Loading latest post from file...")
        with open(LATEST_POST_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading latest post from file: {e}")
        return None

# Function to save the latest post to file
def save_latest_post(post):
    try:
        print("Saving latest post to file...")
        with open(LATEST_POST_FILE, 'w') as file:
            json.dump(post, file)
        print("Latest post hash saved to file.")
    except Exception as e:
        print(f"Error saving latest post to file: {e}")

# Function to calculate a hash of the post content
def calculate_hash(content):
    return hash(content)

# Main function to check for new posts and send notifications
async def check_for_new_posts():
    try:
        print("Checking for new posts...")
        latest_post_text = await scrape_facebook_page()
        
        if latest_post_text:
            latest_post_hash = calculate_hash(latest_post_text)
            stored_post_hash = load_latest_post()
            
            print(f"Latest post hash: {latest_post_hash}")
            print(f"Stored post hash: {stored_post_hash}")
            
            if latest_post_hash != stored_post_hash:
                print("New post detected. Sending notification.")
                await send_telegram_message(f"New post detected:\n\n{latest_post_text}\n\n{FACEBOOK_PAGE_URL}")
                save_latest_post(latest_post_hash)
            else:
                print("No new post detected.")
        else:
            print("No posts found.")
    except Exception as e:
        print(f"Error checking for new posts: {e}")

# Schedule the scraper to run every minute
if __name__ == "__main__":
    print("Starting the script...")
    while True:
        asyncio.run(check_for_new_posts())
        time.sleep(30)
