import os
import sys
import time
import json
import signal
import requests
from flask import Flask, jsonify
import threading
from pathlib import Path

app = Flask(__name__)

# ----------------- تنظیمات اصلی -----------------
TOKEN = "329776201:mAet5gsviBr2xjJWGvueSg2OUa3B2Np913cc3u8f"
BASE_URL = f'https://tapi.bale.ai/bot{TOKEN}/'

# مسیرهای فایل
BASE_PATH = Path(__file__).parent.absolute()
DATA_FILE = BASE_PATH / 'data.json'
TRACKING_FILE = BASE_PATH / 'tracking.txt'
LOCK_FILE = BASE_PATH / 'bale.lock'

# مدیریت وضعیت کاربران
user_states = {}

# ----------------- توابع کمکی -----------------
def load_json_data():
    """بارگذاری داده‌های JSON"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"خطا در بارگذاری فایل داده: {e}")
        return {}

def load_tracking_data():
    """بارگذاری داده‌های پیگیری"""
    tracking_data = {}
    if TRACKING_FILE.exists():
        try:
            with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if ':' in line:
                        case_num, tracking_num = line.strip().split(':', 1)
                        tracking_data[case_num.strip()] = tracking_num.strip()
        except Exception as e:
            print(f"خطا در بارگذاری فایل پیگیری: {e}")
    return tracking_data

def persian_to_english(number):
    """تبدیل اعداد فارسی به انگلیسی"""
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    return number.translate(str.maketrans(persian_digits, english_digits))

def english_to_persian(number):
    """تبدیل اعداد انگلیسی به فارسی"""
    english_digits = '0123456789'
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    return str(number).translate(str.maketrans(english_digits, persian_digits))

# ----------------- مدیریت اجرا -----------------
def is_running():
    """بررسی وجود نمونه در حال اجرا"""
    if LOCK_FILE.exists():
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
                os.kill(pid, 0)
                return True
        except:
            LOCK_FILE.unlink(missing_ok=True)
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
    return False

def remove_lock():
    """حذف فایل قفل"""
    LOCK_FILE.unlink(missing_ok=True)

def handle_exit(signum, frame):
    """مدیریت خروج"""
    print("\n🔴 خاتمه دادن به ربات...")
    remove_lock()
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

# ----------------- ارتباط با API بله -----------------
def get_updates(offset=None):
    """دریافت آپدیت‌ها"""
    url = BASE_URL + 'getUpdates'
    params = {'timeout': 100, 'offset': offset} if offset else {'timeout': 100}
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json().get('result', [])
    except Exception as e:
        print(f"خطا در دریافت آپدیت‌ها: {e}")
        return []

def send_message(chat_id, text, keyboard=None):
    """ارسال پیام"""
    url = BASE_URL + 'sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    if keyboard:
        payload['reply_markup'] = {
            'keyboard': keyboard,
            'resize_keyboard': True,
            'one_time_keyboard': False
        }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"خطا در ارسال پیام: {e}")

def send_document(chat_id, file_name, caption=None):
    """ارسال فایل PDF از ریشه پروژه"""
    file_path = BASE_PATH / file_name
    if not file_path.exists():
        print(f"⚠️ فایل {file_name} یافت نشد!")
        send_message(chat_id, f"⚠️ فایل راهنما یافت نشد: {file_name}")
        return

    url = BASE_URL + 'sendDocument'
    try:
        with open(file_path, 'rb') as file:
            files = {'document': file}
            data = {'chat_id': chat_id}
            if caption:
                data['caption'] = caption
            requests.post(url, files=files, data=data, timeout=30)
    except Exception as e:
        print(f"خطا در ارسال فایل: {e}")

# ----------------- پردازش پیام‌ها -----------------
def handle_start(chat_id):
    """مدیریت دستور /start"""
    welcome = (
        "🏥 به *سامانه خدمات الکترونیک پزشکی قانونی استان گیلان* خوش آمدید.\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    user_states[chat_id] = {'menu': 'main'}
    send_message(chat_id, welcome, [
        ['📌 آدرس مراکز', '🩺 خدمات تخصصی'],
        ['📄 مدارک لازم', 'ℹ️ اطلاعات تماس'],
        ['🏢 درباره ما', '📋 پروسه‌های اداری'],
        ['پیگیری نامه با شماره پرونده']
    ])

def handle_tracking(chat_id, national_code):
    """مدیریت پیگیری پرونده"""
    tracking_data = load_tracking_data()
    code = persian_to_english(national_code.strip())
    
    if len(code) != 10 or not code.isdigit():
        send_message(chat_id, "❌ شماره پرونده باید 10 رقمی باشد.", [['🔙 بازگشت']])
        return
    
    # جستجو با 5 رقم آخر
    tracking_number = tracking_data.get(code[-5:])
    
    if not tracking_number:
        # جستجو با 6 رقم آخر اگر با 5 رقم پیدا نشد
        tracking_number = tracking_data.get(code[-6:])
    
    if tracking_number:
        response = (
            f"📌 کد ملی وارد شده: {english_to_persian(code)}\n"
            f"🔖 کد رهگیری: {english_to_persian(tracking_number)}\n\n"
            f"برای پیگیری بیشتر با تلفن ۰۱۳۳۳۵۴۳۴۲۶ تماس بگیرید."
        )
    else:
        response = (
            f"📌 کد ملی وارد شده: {english_to_persian(code)}\n"
            f"❌ پرونده‌ای با این شماره یافت نشد.\n\n"
            f"لطفاً از صحت شماره وارد شده اطمینان حاصل نمایید."
        )
    
    send_message(chat_id, response, [
        ['پیگیری نامه جدید'],
        ['🔙 بازگشت به منوی اصلی']
    ])
    user_states[chat_id] = {'menu': 'main'}

# ----------------- حلقه اصلی ربات -----------------
def run_bot():
    """حلقه اصلی ربات"""
    print("✅ ربات پزشکی قانونی گیلان فعال شد...")
    content_data = load_json_data()
    last_update_id = None

    while True:
        updates = get_updates(last_update_id)
        
        for update in updates:
            last_update_id = update['update_id'] + 1
            
            if 'message' not in update:
                continue
                
            msg = update['message']
            chat_id = msg['chat']['id']
            text = msg.get('text', '').strip()
            
            # مدیریت دستور /start
            if text == '/start':
                handle_start(chat_id)
                continue
                
            # مدیریت بازگشت
            if text == '🔙 بازگشت به منوی اصلی':
                handle_start(chat_id)
                continue
                
            # پیگیری پرونده
            if text == 'پیگیری نامه با شماره پرونده':
                user_states[chat_id] = {'menu': 'tracking'}
                send_message(chat_id, 
                    "لطفاً شماره پرونده (کد ملی) خود را وارد نمایید:",
                    [['🔙 بازگشت به منوی اصلی']])
                continue
                
            # پردازش شماره پرونده
            current_state = user_states.get(chat_id, {})
            if current_state.get('menu') == 'tracking' and text.isdigit():
                handle_tracking(chat_id, text)
                continue
                
            # نمایش اطلاعات شهرستان‌ها
            if text == '📌 آدرس مراکز':
                cities = list(content_data.get('شهرستان‌ها', {}).keys())
                keyboard = [cities[i:i+2] for i in range(0, len(cities), 2)]
                keyboard.append(['🔙 بازگشت به منوی اصلی'])
                send_message(chat_id, "شهرستان مورد نظر را انتخاب کنید:", keyboard)
                continue
                
            if text in content_data.get('شهرستان‌ها', {}):
                city = content_data['شهرستان‌ها'][text]
                response = (
                    f"🏢 *{text}*\n\n"
                    f"📌 آدرس: {city['آدرس']}\n"
                    f"☎️ تلفن: {city['تلفن']}\n"
                )
                if 'نمابر' in city:
                    response += f"📠 نمابر: {city['نمابر']}\n"
                send_message(chat_id, response)
                continue
                
            # نمایش خدمات
            if text == '🩺 خدمات تخصصی':
                services = list(content_data.get('خدمات', {}).keys())
                keyboard = [services[i:i+2] for i in range(0, len(services), 2)]
                keyboard.append(['🔙 بازگشت به منوی اصلی'])
                send_message(chat_id, "خدمت مورد نظر را انتخاب کنید:", keyboard)
                continue
                
            if text in content_data.get('خدمات', {}):
                service = content_data['خدمات'][text]
                send_message(chat_id, f"🩺 *{text}*\n\n{service}")
                
                # ارسال فایل‌های مرتبط
                if text == 'معاینات بالینی':
                    send_document(chat_id, 'm1.pdf', 'راهنمای معاینات بالینی - بخش اول')
                    send_document(chat_id, 'm2.pdf', 'راهنمای معاینات بالینی - بخش دوم')
                elif text == 'متوفیات':
                    send_document(chat_id, 'mo1.pdf', 'راهنمای متوفیات - بخش اول')
                continue
                
            # پاسخ پیش‌فرض
            handle_start(chat_id)
        
        time.sleep(1)

# ----------------- وب سرویس Flask -----------------
@app.route('/')
def home():
    return "🩺 ربات میز خدمت پزشکی قانونی استان گیلان فعال است | gl.lmo.ir"

@app.route('/info')
def info():
    return jsonify(load_json_data())

# ----------------- اجرای برنامه -----------------
if __name__ == "__main__":
    if is_running():
        print("⚠️ ربات در حال اجراست. خروج...")
        sys.exit(0)
        
    try:
        # اجرای ربات در یک رشته جداگانه
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        
        # اجرای وب سرویس
        app.run(host='0.0.0.0', port=8080)
    finally:
        remove_lock()
