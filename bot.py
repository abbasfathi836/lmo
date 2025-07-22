import os
import requests
import time
from flask import Flask

app = Flask(__name__)

class BaleBot:
    def __init__(self, token=None):
        self.token = token or os.getenv("1470628476:7pIGfQhkk3h3TZx5K93dP5wMzXRCA5Zk5xjaPWP2")
        if not self.token:
            raise ValueError("1470628476:7pIGfQhkk3h3TZx5K93dP5wMzXRCA5Zk5xjaPWP2")
        self.base_url = f"https://tapi.bale.ai/bot{self.token}/"
        
    def get_updates(self, offset=None, timeout=30):
        url = self.base_url + "getUpdates"
        params = {"timeout": timeout}
        if offset:
            params["offset"] = offset
            
        try:
            response = requests.get(url, params=params)
            return response.json().get("result", [])
        except Exception as e:
            print(f"Error in get_updates: {e}")
            return []
    
    def send_message(self, chat_id, text):
        url = self.base_url + "sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text
        }
        
        try:
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            print(f"Error in send_message: {e}")
            return None
    
    def run(self):
        last_update_id = 0
        print("Bot is running...")
        
        while True:
            updates = self.get_updates(offset=last_update_id + 1)
            
            for update in updates:
                last_update_id = update["update_id"]
                
                if "message" in update:
                    message = update["message"]
                    chat_id = message["chat"]["id"]
                    text = message.get("text", "")
                    
                    if text:
                        print(f"Received message: {text}")
                        response_text = f"شما گفتید: {text}"
                        self.send_message(chat_id, response_text)
            time.sleep(1)

def run_bot():
    bot = BaleBot()
    bot.run()

@app.route('/')
def home():
    return "ربات در حال اجراست!"

if __name__ == "__main__":
    import threading
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    app.run(host='0.0.0.0', port=8080)  # پورت 8080 برای Render
