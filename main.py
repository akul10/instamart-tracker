import re
import time
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
ITEM_URL = "https://instamart.in/item/GVS45O45D9?share=true"
TARGET_PRICE = 21000.00  
CHECK_INTERVAL = 3600  
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1563945021693100032/4JkPrLrakQCZoKpR627s-PesjoMr44_qnhJOMVNro8u1Snrp-_FpIYuB-XFh-JIaeo2X"


def get_instamart_price():
    """Extracts pricing securely by leveraging an open cors/proxy proxy to bypass 403 errors."""
    # We use a public proxy bridge to mask the VS Code network connection footprint
    proxy_url = f"https://allorigins.win{requests.utils.quote(ITEM_URL)}"
    
    try:
        response = requests.get(proxy_url, timeout=20)
        if response.status_code != 200:
            print(f"Proxy network error code: {response.status_code}")
            return None, None
            
        # Allorigins packages the target html inside a JSON object wrapper
        json_data = response.json()
        html_content = json_data.get("contents", "")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Scrape item name context
        title_element = soup.find('h1')
        item_name = title_element.text.strip() if title_element else "Redmi Note 15 SE"
        
        # Read the raw page texts to parse out price values
        page_text = soup.get_text()
        
        # Isolate the exact price structure digits (e.g., 24087)
        price_match = re.search(r'(?:₹|Rs\.?)\s*(\d{4,5}(?:\.\d{2})?)', page_text)
        
        if price_match:
            return item_name, float(price_match.group(1))
            
        # Fallback digit scanner if explicitly formatting inside un-labeled blocks
        digits = re.findall(r'\b2\d{4}\b', page_text)  # Looks for 5 digit numbers starting with 2 (like 24087)
        if digits:
            return item_name, float(digits[0])
            
        print("Bypass successful, but unable to isolate structural price tokens.")
        return item_name, None
            
    except Exception as e:
        print(f"Bypass routine exception triggered: {e}")
        return "Unknown Item", None


def send_discord_alert(item_name, current_price):
    """Sends a rich formatted notification embed directly to your Discord channel."""
    data = {
        "username": "Instamart Watcher",
        "avatar_url": "https://imgur.com",
        "embeds": [
            {
                "title": "🛒 INSTAMART PRICE ALERT!",
                "description": f"**{item_name}** has hit your price target!",
                "url": ITEM_URL,
                "color": 16742912,
                "fields": [
                    {
                        "name": "Live Price",
                        "value": f"₹{current_price:.2f}",
                        "inline": True,
                    },
                    {
                        "name": "Target Limit",
                        "value": f"₹{TARGET_PRICE:.2f}",
                        "inline": True,
                    },
                ],
                "footer": {"text": "Automated Proxy E-Commerce Tracking"},
            }
        ],
    }
    try:
        res = requests.post(DISCORD_WEBHOOK_URL, json=data)
        if res.status_code == 204:
            print("Alert successfully sent to Discord!")
    except Exception as e:
        print(f"Failed to post to webhook channel: {e}")


# --- MAIN MONITORING LOOP ---
print("Launching proxy-wrapped Instamart item monitor...")
while True:
    name, price = get_instamart_price()
    if price is not None:
        print(f"Current update for '{name}': Price is ₹{price:.2f}")
        if price <= TARGET_PRICE:
            print("Target price hit! Pushing alert to Discord...")
            send_discord_alert(name, price)
            break
    time.sleep(CHECK_INTERVAL)
