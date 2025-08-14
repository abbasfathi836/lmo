import os
import sys
import time
import json
import signal
import requests
from flask import Flask, jsonify
import threading

app = Flask(__name__)

# -------- تنظیمات اولیه --------
TOKEN = "329776201:mAet5gsviBr2xjJWGvueSg2OUa3B2Np913cc3u8f"
BASE_URL = f'https://tapi.bale.ai/bot{TOKEN}/'

# مسیر فایل‌ها
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
FILES_PATH = os.path.join(BASE_PATH, 'files')  # مسیر فایل‌های قابل دانلود
LOCK_FILE = os.path.join(BASE_PATH, 'bale.lock')
DATA_FILE = os.path.join(BASE_PATH, 'data.json')
TRACKING_FILE = os.path.join(BASE_PATH, 'tracking.txt')

user_states = {}  # برای مدیریت وضعیت کاربران

# بارگذاری محتوای منوها
with open(DATA_FILE, 'r', encoding='utf-8') as f:
    content_data = json.load(f)

# بارگذاری اطلاعات پیگیری
def load_tracking_data():
    tracking_data = {}
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if ':' in line:
                    case_num, tracking_num = line.strip().split(':', 1)
                    tracking_data[case_num.strip()] = tracking_num.strip()
    return tracking_data

# تبدیل اعداد فارسی به انگلیسی
def persian_to_english(number):
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    return number.translate(translation_table)

# تبدیل اعداد انگلیسی به فارسی برای نمایش
def english_to_persian(number):
    english_digits = '0123456789'
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    translation_table = str.maketrans(english_digits, persian_digits)
    return str(number).translate(translation_table)

# -------- قفل اجرا --------
def is_running():
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE, 'r') as f:
            pid = f.read().strip()
        try:
            os.kill(int(pid), 0)
            print("⚠️ ربات در حال اجراست.")
            return True
        except:
            print("🧹 فایل قفل پاک شد.")
            os.remove(LOCK_FILE)
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
    return False

def remove_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def handle_exit(signum, frame):
    print("🔴 خروج از ربات...")
    remove_lock()
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

# -------- API بله --------
def get_updates(offset=None):
    url = BASE_URL + 'getUpdates'
    params = {'timeout': 100, 'offset': offset}
    try:
        return requests.get(url, params=params, timeout=30).json()
    except:
        return {}

def send_message(chat_id, text, keyboard=None):
    url = BASE_URL + 'sendMessage'
    payload = {'chat_id': chat_id, 'text': text}
    if keyboard:
        payload['reply_markup'] = {
            'keyboard': keyboard,
            'resize_keyboard': True,
            'one_time_keyboard': False
        }
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def send_document(chat_id, file_path, caption=None):
    url = BASE_URL + 'sendDocument'
    files = {'document': open(file_path, 'rb')}
    data = {'chat_id': chat_id}
    if caption:
        data['caption'] = caption
    try:
        requests.post(url, files=files, data=data, timeout=30)
    except Exception as e:
        print(f"Error sending document: {e}")

# -------- حلقه اصلی ربات --------
def run_bot():
    print("✅ ربات فعال شد.")
    last_update_id = None

    while True:
        updates = get_updates(last_update_id)
        if 'result' in updates:
            for update in updates['result']:
                if 'message' not in update:
                    continue

                msg = update['message']
                chat_id = msg['chat']['id']
                text = msg.get('text', '').strip()
                current_state = user_states.get(chat_id, {})

                # --- /start
                if text == '/start':
                    welcome = (
                        "🏥 به *بازوی خدمت پزشکی قانونی گیلان* خوش آمدید.\n\n"
                        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
                    )
                    user_states[chat_id] = {'menu': 'main'}
                    send_message(chat_id, welcome,
                        keyboard=[
                            ['📌 آدرس و تلفن مراکز', '🩺 خدمات'],
                            ['ℹ️ درباره ما', '📄 پیگیری نامه'],
                            ['🔙 بازگشت']
                        ])
                    last_update_id = update['update_id'] + 1
                    continue

                # --- بازگشت به منوی اصلی
                if text == '🔙 بازگشت':
                    user_states[chat_id] = {'menu': 'main'}
                    send_message(chat_id, 'منوی اصلی:',
                        keyboard=[
                            ['📌 آدرس و تلفن مراکز', '🩺 خدمات'],
                            ['ℹ️ درباره ما', '📄 پیگیری نامه'],
                            ['🔙 بازگشت']
                        ])
                    last_update_id = update['update_id'] + 1
                    continue

                # --- منوی اصلی
                if text == '📌 آدرس و تلفن مراکز':
                    user_states[chat_id] = {'menu': 'address'}
                    cities = list(content_data.get('شهرستان‌ها', {}).keys())
                    keyboard = []
                    for i in range(0, len(cities), 2):
                        keyboard.append(cities[i:i+2])
                    keyboard.append(['🔙 بازگشت'])
                    send_message(chat_id, 'لطفاً شهرستان مورد نظر را انتخاب کنید:', keyboard=keyboard)
                    last_update_id = update['update_id'] + 1
                    continue

                if text == '🩺 خدمات':
                    user_states[chat_id] = {'menu': 'services'}
                    send_message(chat_id, 'لطفاً نوع خدمت مورد نظر را انتخاب کنید:',
                        keyboard=[
                            ['معاینات بالینی', 'متوفیات'],
                            ['کمیسیون', 'آزمایشگاه'],
                            ['🔙 بازگشت']
                        ])
                    last_update_id = update['update_id'] + 1
                    continue

                if text == 'ℹ️ درباره ما':
                    user_states[chat_id] = {'menu': 'about'}
                    send_message(chat_id, content_data.get('درباره ما', 'اطلاعاتی موجود نیست.'),
                        keyboard=[['🔙 بازگشت']])
                    last_update_id = update['update_id'] + 1
                    continue

                if text == '📄 پیگیری نامه':
                    # بارگذاری مجدد اطلاعات پیگیری
                    tracking_data = load_tracking_data()
                    user_states[chat_id] = {'menu': 'tracking', 'awaiting_case': True}
                    
                    # ارسال پیام اطلاع‌رسانی
                    info_msg = (
                        "ℹ️ توجه:\n"
                        "قبل از وارد کردن کد ملی به این نکته توجه داشته باشید که باید از زمان مراجعه شما به پزشکی قانونی در صورت خاتمه پرونده حداقل ۲ روز کاری گذشته باشد.\n\n"
                        "اطلاعات این قسمت مربوط به نامه‌های ارسال شده از تاریخ ۱۴۰۴/۰۵/۱۳ به بعد کلانتری‌های حوزه رشت می‌باشد.\n\n"
                        "لطفاً کد ملی شخص دارای پرونده را وارد کنید:"
                    )
                    
                    send_message(chat_id, info_msg, keyboard=[['🔙 بازگشت']])
                    last_update_id = update['update_id'] + 1
                    continue

                # --- پردازش وضعیت‌های خاص
                current_state = user_states.get(chat_id, {})
                
                # پیگیری نامه
                if current_state.get('awaiting_case'):
                    # بارگذاری مجدد اطلاعات پیگیری قبل از جستجو
                    tracking_data = load_tracking_data()
                    case_number = persian_to_english(text.strip())
                    
                    # بررسی صحت کد ملی
                    if len(case_number) != 10 or not case_number.isdigit():
                        send_message(chat_id, '❌ لطفاً کد ملی شخص دارای پرونده را وارد کنید(10 رقم).',
                            keyboard=[['🔙 بازگشت']])
                        last_update_id = update['update_id'] + 1
                        continue
                    
                    # جستجو با 5 رقم آخر
                    last_five = case_number[-5:]
                    tracking_number = tracking_data.get(last_five)
                    
                    if not tracking_number:
                        # اگر با 5 رقم پیدا نشد، با 6 رقم آخر جستجو می‌کنیم
                        last_six = case_number[-6:]
                        tracking_number = tracking_data.get(last_six)
                    
                    if tracking_number:
                        response = (
                            f"📌 کد ملی وارد شده: {english_to_persian(case_number)}\n"
                            f"🔖 وضعیت پرونده و یا کد رهگیری ارسال پاسخ به مرجع: {english_to_persian(tracking_number)}"
                        )
                    else:
                        response = (
                            f"📌 کد ملی وارد شده: {english_to_persian(case_number)}\n"
                            f"❌ اطلاعاتی برای این کد ملی ثبت نشده است."
                        )
                    
                    send_message(chat_id, response,
                        keyboard=[
                            ['📄 پیگیری نامه جدید'],
                            ['🔙 بازگشت']
                        ])
                    user_states[chat_id] = {'menu': 'main'}
                    last_update_id = update['update_id'] + 1
                    continue

                # آدرس شهرستان‌ها
                if current_state.get('menu') == 'address' and text in content_data.get('شهرستان‌ها', {}):
                    city_info = content_data['شهرستان‌ها'][text]
                    response = (
                        f"🏢 {text}\n\n"
                        f"📌 آدرس:\n{city_info['آدرس']}\n\n"
                        f"☎️ تلفن: {city_info['تلفن']}\n"
                    )
                    
                    if 'نمابر' in city_info:
                        response += f"📠 نمابر: {city_info['نمابر']}\n"
                    if 'پست الکترونیک' in city_info:
                        response += f"📧 پست الکترونیک: {city_info['پست الکترونیک']}\n"
                    
                    send_message(chat_id, response,
                        keyboard=[
                            ['📌 آدرس و تلفن مراکز'],
                            ['🔙 بازگشت']
                        ])
                    last_update_id = update['update_id'] + 1
                    continue

                # خدمات
                if current_state.get('menu') == 'services':
                    if text == 'معاینات بالینی':
                        service_info = content_data.get('معاینات بالینی', 'اطلاعاتی موجود نیست.')
                        response = "🩺 *معاینات بالینی*\n\n" + service_info
                        send_message(chat_id, response)
                        
                        # ارسال فایل‌های مربوطه
                        files_to_send = [
                            ('m1.pdf', 'راهنمای اول معاینات بالینی'),
                            ('m2.pdf', 'راهنمای دوم معاینات بالینی')
                        ]
                        
                        for filename, caption in files_to_send:
                            file_path = os.path.join(FILES_PATH, filename)
                            if os.path.exists(file_path):
                                send_document(chat_id, file_path, caption)
                            else:
                                send_message(chat_id, f"⚠️ فایل {filename} یافت نشد.")
                        
                        send_message(chat_id, 
                            "📋 [مشاهده تعرفه‌های خدمات](https://lmo.ir/fa/index.php?module=cdk&func=loadmodule&system=cdk&sismodule=user/content_view.php&sisOp=view&ctp_id=602&cnt_id=111396&id=2888)",
                            keyboard=[
                                ['🩺 خدمات'],
                                ['🔙 بازگشت']
                            ])
                    
                    elif text == 'متوفیات':
                        service_info = content_data.get('متوفیات', 'اطلاعاتی موجود نیست.')
                        response = "⚰️ *متوفیات*\n\n" + service_info
                        send_message(chat_id, response)
                        
                        # ارسال فایل‌های مربوطه
                        files_to_send = [
                            ('mo1.pdf', 'راهنمای اول متوفیات'),
                            ('mo2.pdf', 'راهنمای دوم متوفیات'),
                            ('mo3.pdf', 'راهنمای سوم متوفیات')
                        ]
                        
                        for filename, caption in files_to_send:
                            file_path = os.path.join(FILES_PATH, filename)
                            if os.path.exists(file_path):
                                send_document(chat_id, file_path, caption)
                            else:
                                send_message(chat_id, f"⚠️ فایل {filename} یافت نشد.")
                        
                        send_message(chat_id, 
                            "📋 [مشاهده تعرفه‌های خدمات](https://lmo.ir/fa/index.php?module=cdk&func=loadmodule&system=cdk&sismodule=user/content_view.php&sisOp=view&ctp_id=602&cnt_id=111396&id=2888)",
                            keyboard=[
                                ['🩺 خدمات'],
                                ['🔙 بازگشت']
                            ])
                    
                    elif text == 'کمیسیون':
                        service_info = content_data.get('کمیسیون', 'اطلاعاتی موجود نیست.')
                        response = (
                            "📝 *کمیسیون*\n\n"
                            f"{service_info}\n\n"
                            "💰 [مشاهده تعرفه‌های مصوب پزشکی قانونی](https://lmo.ir/fa/index.php?module=cdk&func=loadmodule&system=cdk&sismodule=user/content_view.php&sisOp=view&ctp_id=602&cnt_id=111396&id=2888)"
                        )
                        send_message(chat_id, response,
                            keyboard=[
                                ['🩺 خدمات'],
                                ['🔙 بازگشت']
                            ])
                    
                    elif text == 'آزمایشگاه':
                        service_info = content_data.get('آزمایشگاه', 'اطلاعاتی موجود نیست.')
                        response = (
                            "🔬 *آزمایشگاه*\n\n"
                            f"{service_info}\n\n"
                            "💰 [مشاهده تعرفه‌های مصوب پزشکی قانونی](https://lmo.ir/fa/index.php?module=cdk&func=loadmodule&system=cdk&sismodule=user/content_view.php&sisOp=view&ctp_id=602&cnt_id=111396&id=2888)"
                        )
                        send_message(chat_id, response,
                            keyboard=[
                                ['🩺 خدمات'],
                                ['🔙 بازگشت']
                            ])
                    
                    last_update_id = update['update_id'] + 1
                    continue

                # --- پاسخ پیش‌فرض
                user_states[chat_id] = {'menu': 'main'}
                send_message(chat_id, 'لطفاً یکی از گزینه‌های منو را انتخاب کنید:',
                    keyboard=[
                        ['📌 آدرس و تلفن مراکز', '🩺 خدمات'],
                        ['ℹ️ درباره ما', '📄 پیگیری نامه'],
                        ['🔙 بازگشت']
                    ])
                last_update_id = update['update_id'] + 1

        time.sleep(1)

@app.route('/')
def home():
    return "🩺 ربات میز خدمت پزشکی قانونی استان گیلان فعال است | gl.lmo.ir"

@app.route('/info')
def info():
    return jsonify(content_data)

if __name__ == "__main__":
    if is_running():
        print("ربات در حال اجراست. خروج...")
        sys.exit(0)
    
    try:
        # Start bot in a separate thread
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        
        # Start Flask app
        app.run(host='0.0.0.0', port=8080)
    finally:
        remove_lock()
