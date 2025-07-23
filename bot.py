import os
import requests
import time
from flask import Flask

app = Flask(__name__)

class BaleBot:
    def __init__(self, token=None):
        self.token = token or os.getenv("BALE_BOT_TOKEN")
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
    
    def send_message(self, chat_id, text, reply_markup=None):
        url = self.base_url + "sendMessage"
        data = {"chat_id": chat_id, "text": text}
        if reply_markup:
            data["reply_markup"] = reply_markup
        try:
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            print(f"Error in send_message: {e}")
            return None
    
    def create_keyboard(self):
        keyboard = {
            "keyboard": [
                ["شهرهای دارای مرکز"],
                ["تعرفه خدمات"],
                ["مدارک لازم جهت مراجعه"]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        return keyboard
    
    def handle_message(self, message):
        text = message.get("text", "")
        chat_id = message["chat"]["id"]
        
        if text == "شهرهای دارای مرکز":
            response = "شهرهای دارای مرکز پزشکی قانونی در استان گیلان:\n\n- رشت (مرکز استان)\n- انزلی\n- لاهیجان\n- تالش\n- رودسر\n- آستارا\n- فومن\n- صومعه سرا"
        elif text == "تعرفه خدمات":
            response = "تعرفه خدمات پزشکی قانونی:\n\n- معاینه بالینی:00,000 ریال\n- آزمایشات تخصص00,000 ریال\n- تصویربرداری: 00,000 ریال\n- گواهی پزشکی00,00 ریال\n\n* قیمتها ممکن است تغییر کنند."
        elif text == "مدارک لازم جهت مراجعه":
            response = "مدارک لازم برای مراجعه به پزشکی قانونی:\n\n1- اصل شناسنامه\n2- کارت ملی\n3- معرفی نامه از مرجع قضایی\n4- پرونده پزشکی (در صورت وجود)\n5- عکس جدید 4*3\n6- رسید پرداخت هزینه ها"
        else:
            response = "به میز خدمت پزشکی قانونی استان گیلان خوش آمدید. لطفاً یکی از گزینه های زیر را انتخاب کنید:"
            return self.send_message(chat_id, response, reply_markup=self.create_keyboard())
        
        self.send_message(chat_id, response, reply_markup=self.create_keyboard())
    
    def run(self):
        last_update_id = 0
        print("Bot is running...")
        while True:
            updates = self.get_updates(offset=last_update_id + 1)
            for update in updates:
                last_update_id = update["update_id"]
                if "message" in update:
                    message = update["message"]
                    self.handle_message(message)
            time.sleep(1)

@app.route('/')
def home():
    return "ربات میز خدمت پزشکی قانونی استان گیلان فعال است!"

if __name__ == "__main__":
    import threading
    bot = BaleBot()
    bot_thread = threading.Thread(target=bot.run)
    bot_thread.start()
    app.run(host='0.0.0.0', port=8080)
