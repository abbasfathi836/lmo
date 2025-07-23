import os
import requests
import time
from flask import Flask, jsonify

app = Flask(__name__)

class BaleBot:
    def __init__(self, token=None):
        self.token = token or "1470628476:7pIGfQhkk3h3TZx5K93dP5wMzXRCA5Zk5xjaPWP2"
        self.base_url = f"https://tapi.bale.ai/bot{self.token}/"
        
        # اطلاعات استاتیک از سایت gl.lmo.ir
        self.data = {
            "main_center": {
                "address": "رشت، کمربندی شهید بهشتی، استقامت، ستاد مرکزی اداره کل پزشکی قانونی استان گیلان",
                "phone": "۰۱۳۳۳۵۴۳۴۲۶",
                "manager": "دکتر علی سلیمانپور"
            },
            "cities": {
                "رشت": "کمربندی شهید بهشتی، استقامت",
                "انزلی": "بلوار امام خمینی، جنب بیمارستان ۱۷ شهریور",
                "لاهیجان": "خیابان امام، جنب بیمارستان ۲۲ آبان",
                "تالش": "بلوار معلم، جنب درمانگاه تالش",
                "آستارا": "خیابان امام، روبروی اداره بهداشت",
                "فومن": "خیابان شهدا، جنب بیمارستان فومن",
                "صومعه‌سرا": "خیابان امام، جنب شبکه بهداشت",
                "رودسر": "خیابان امام، جنب درمانگاه رودسر",
                "املش": "خیابان شهید رجایی، جنب مرکز بهداشت",
                "سیاهکل": "خیابان امام، جنب بیمارستان سیاهکل",
                "ماسال": "خیابان شهید انصاری، جنب مرکز بهداشت",
                "رضوانشهر": "بلوار امام خمینی، جنب درمانگاه رضوانشهر",
                "لنگرود": "خیابان امام، جنب بیمارستان لنگرود",
                "رودبار": "خیابان شهدا، جنب مرکز بهداشت",
                "شفت": "خیابان امام، جنب بیمارستان شفت",
                "بندرانزلی": "بلوار ساحلی، جنب بیمارستان امیرالمومنین"
            },
            "services": {
                "تعیین سن": "برای افراد بدون مدارک شناسایی\nمدارک مورد نیاز: شناسنامه والدین + عکس فرد",
                "آزمایش DNA": "برای اثبات نسب\nهزینه: ۵-۲۰ میلیون تومان\nزمان نتیجه‌گیری: ۲-۴ هفته",
                "گواهی فوت": "صدور گواهی پزشکی قانونی\nمدارک: مدارک متوفی + گزارش اولیه مرگ",
                "معاینه بالینی": "در موارد ضرب و جرح، تجاوز و خشونت\nنیاز به معرفی نامه قضایی",
                "سم‌شناسی": "آزمایش تخصصی مواد مخدر و سموم\nزمان نتیجه‌گیری: ۱-۲ هفته",
                "تعیین هویت": "شناسایی اجساد و افراد ناشناس"
            },
            "documents": {
                "عمومی": [
                    "اصل شناسنامه و کارت ملی",
                    "معرفی‌نامه از مرجع قضایی",
                    "پرونده پزشکی مرتبط (در صورت وجود)",
                    "عکس ۴*۳ جدید"
                ],
                "ویژه": {
                    "تعیین سن": ["شناسنامه والدین", "عکس فرد"],
                    "گواهی فوت": ["شناسنامه متوفی", "گزارش پزشک معالج"],
                    "آزمایش DNA": ["شناسنامه درخواست‌دهنده", "نسبت مورد ادعا"]
                }
            },
            "procedures": {
                "مراجعه حضوری": "۱. دریافت نوبت از طریق تماس تلفنی\n۲. حضور در مرکز با مدارک کامل\n۳. انجام فرآیند مورد نظر",
                "دریافت نتیجه": "۱. مراجعه حضوری پس از اعلام آمادگی نتیجه\n۲. ارائه رسید پرونده\n۳. دریافت مدارک",
                "اعتراض به نتیجه": "ارسال درخواست کتبی به مدیرکل پزشکی قانونی استان"
            },
            "contact": {
                "تلفن": "۰۱۳۳۳۵۴۳۴۲۶",
                "ساعات کاری": "شنبه تا چهارشنبه: ۷:۳۰ تا ۱۴:۳۰\nپنجشنبه‌ها: ۷:۳۰ تا ۱۲:۳۰",
                "ایمیل": "gl.lmo@lmo.ir"
            }
        }
        
    def get_updates(self, offset=None, timeout=30):
        url = self.base_url + "getUpdates"
        params = {"timeout": timeout, "offset": offset} if offset else {"timeout": timeout}
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
    
    def create_main_keyboard(self):
        return {
            "keyboard": [
                ["📍 آدرس مراکز", "🩺 خدمات تخصصی"],
                ["📄 مدارک لازم", "ℹ️ اطلاعات تماس"],
                ["🏢 درباره ما", "📋 پروسه‌های اداری"]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
    
    def create_cities_keyboard(self):
        cities = list(self.data["cities"].keys())
        keyboard = [cities[i:i+2] for i in range(0, len(cities), 2)]
        keyboard.append(["🔙 بازگشت به منوی اصلی"])
        return {
            "keyboard": keyboard,
            "resize_keyboard": True
        }
    
    def create_services_keyboard(self):
        services = list(self.data["services"].keys())
        keyboard = [services[i:i+2] for i in range(0, len(services), 2)]
        keyboard.append(["🔙 بازگشت به منوی اصلی"])
        return {
            "keyboard": keyboard,
            "resize_keyboard": True
        }
    
    def handle_message(self, message):
        text = message.get("text", "").strip()
        chat_id = message["chat"]["id"]
        
        # دسته‌بندی پاسخ‌ها
        if text == "📍 آدرس مراکز":
            response = "شهر مورد نظر را انتخاب کنید:"
            self.send_message(chat_id, response, reply_markup=self.create_cities_keyboard())
        
        elif text in self.data["cities"]:
            address = self.data["cities"][text]
            response = f"📍 **مرکز {text}**:\n{address}\n\n📞 تماس: {self.data['contact']['تلفن']}"
            self.send_message(chat_id, response)
        
        elif text == "🩺 خدمات تخصصی":
            response = "خدمت مورد نظر را انتخاب کنید:"
            self.send_message(chat_id, response, reply_markup=self.create_services_keyboard())
        
        elif text in self.data["services"]:
            service_info = self.data["services"][text]
            response = f"**🩺 {text}**\n\n{service_info}"
            self.send_message(chat_id, response)
        
        elif text == "📄 مدارک لازم":
            general_docs = "\n".join([f"• {doc}" for doc in self.data["documents"]["عمومی"]])
            response = f"**مدارک عمومی مورد نیاز:**\n{general_docs}\n\nبرای مدارک خدمات خاص، نام خدمت را وارد کنید."
            self.send_message(chat_id, response)
        
        elif text == "ℹ️ اطلاعات تماس":
            contact_info = "\n".join([f"• **{key}**: {value}" for key, value in self.data["contact"].items()])
            response = f"**اطلاعات تماس:**\n{contact_info}"
            self.send_message(chat_id, response)
        
        elif text == "🏢 درباره ما":
            manager = self.data["main_center"]["manager"]
            response = f"**پزشکی قانونی استان گیلان**\n\n• مدیرکل: {manager}\n• مسئولیت: بررسی موارد قانونی پزشکی\n• زیرمجموعه قوه قضاییه"
            self.send_message(chat_id, response)
        
        elif text == "📋 پروسه‌های اداری":
            procedures = "\n\n".join([f"**{title}**\n{desc}" for title, desc in self.data["procedures"].items()])
            response = f"**پروسه‌های اداری:**\n\n{procedures}"
            self.send_message(chat_id, response)
        
        elif text == "🔙 بازگشت به منوی اصلی":
            response = "منوی اصلی:"
            self.send_message(chat_id, response, reply_markup=self.create_main_keyboard())
        
        else:
            welcome_msg = (
                "به سامانه خدمات الکترونیک پزشکی قانونی استان گیلان خوش آمدید. 🌿\n\n"
                "جهت دریافت اطلاعات، یکی از گزینه‌های زیر را انتخاب کنید:"
            )
            self.send_message(chat_id, welcome_msg, reply_markup=self.create_main_keyboard())
    
    def run(self):
        last_update_id = 0
        print("🤖 ربات میز خدمت پزشکی قانونی گیلان فعال است...")
        while True:
            updates = self.get_updates(offset=last_update_id + 1)
            for update in updates:
                last_update_id = update["update_id"]
                if "message" in update:
                    self.handle_message(update["message"])
            time.sleep(0.5)

@app.route('/')
def home():
    return "🩺 ربات میز خدمت پزشکی قانونی استان گیلان فعال است | gl.lmo.ir"

@app.route('/info')
def info():
    bot = BaleBot()
    return jsonify(bot.data)

if __name__ == "__main__":
    import threading
    bot = BaleBot()
    bot_thread = threading.Thread(target=bot.run)
    bot_thread.daemon = True
    bot_thread.start()
    app.run(host='0.0.0.0', port=8080)
