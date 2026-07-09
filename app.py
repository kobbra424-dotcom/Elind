import time
import logging
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# إعداد السجلات (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# قراءة التوكن من متغير البيئة (Railway Variable)
TOKEN = os.environ.get("BOT_TOKEN", "8676015225:AAFBcPk9opIhPvBm4eubXREMRw8tKiBrcwc")

def run_indrive_process(phone_number, chat_id, context):
    """دالة لتشغيل عملية inDrive لرقم واحد بمحاولة واحدة فقط"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Railway-specific: use system Chrome if available
    chrome_binary = os.environ.get("CHROME_BINARY", "/usr/bin/chromium")
    if os.path.exists(chrome_binary):
        options.binary_location = chrome_binary

    driver = None
    try:
        try:
            driver = webdriver.Chrome(options=options)
        except Exception:
            chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
            if os.path.exists(chromedriver_path):
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                driver = webdriver.Chrome(options=options)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def send_msg(msg):
            await context.bot.send_message(chat_id=chat_id, text=msg, read_timeout=30, write_timeout=30, connect_timeout=30, pool_timeout=30)

        async def send_photo(photo_path, caption=""):
            if os.path.exists(photo_path):
                try:
                    with open(photo_path, 'rb') as photo:
                        await context.bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, read_timeout=60, write_timeout=60, connect_timeout=60, pool_timeout=60)
                    logging.info(f"Photo sent successfully for {phone_number}")
                except Exception as e:
                    logging.error(f"Failed to send photo for {phone_number}: {e}")
                    await send_msg(f"⚠️ فشل إرسال الصورة للرقم {phone_number}: {str(e)}")

        # 1. الدخول على صفحة التسجيل
        driver.get("https://couriers.indrive.com/register")
        wait = WebDriverWait(driver, 30)

        # 2. اختيار الدولة (مصر)
        try:
            country_selector = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[role="combobox"]')))
            country_selector.click()
            egypt_option_xpath = "//li[@role='option' and (contains(., 'Egypt') or contains(., 'مصر'))]"
            egypt_option = wait.until(EC.element_to_be_clickable((By.XPATH, egypt_option_xpath)))
            egypt_option.click()
        except Exception:
            pass

        # 3. إدخال رقم الهاتف
        phone_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"], input[type="tel"]')))
        phone_input.send_keys(Keys.CONTROL + "a")
        phone_input.send_keys(Keys.BACKSPACE)
        phone_input.send_keys(phone_number)

        # الضغط على Next
        next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Next')]")))
        next_button.click()

        time.sleep(10)
        screenshot_path = f"after_next_{phone_number}.png"
        driver.save_screenshot(screenshot_path)

        # التحقق من النجاح
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@autocomplete, 'one-time-code')] | //button[contains(., 'Request new code')]")))
            loop.run_until_complete(send_photo(screenshot_path, f"✅ الرقم {phone_number}: تم قبول الرقم."))
        except TimeoutException:
            error_msg = "غير معروف"
            try:
                error_element = driver.find_element(By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'Error')]")
                error_msg = error_element.text
            except:
                pass
            loop.run_until_complete(send_photo(screenshot_path, f"⚠️ الرقم {phone_number}: فشل الدخول. النتيجة: {error_msg}"))
            return

        # محاولة إعادة إرسال واحدة فقط
        try:
            loop.run_until_complete(send_msg(f"🔄 جاري محاولة إعادة إرسال الكود لمرة واحدة فقط للرقم {phone_number}..."))
            resend_button_xpath = "//button[contains(., 'Request new code') or contains(., 'إعادة إرسال')]"
            resend_button = WebDriverWait(driver, 100).until(
                EC.element_to_be_clickable((By.XPATH, resend_button_xpath))
            )
            driver.execute_script("arguments[0].click();", resend_button)
            loop.run_until_complete(send_msg(f"✅ الرقم {phone_number}: تم الضغط على إعادة الإرسال بنجاح."))
        except TimeoutException:
            loop.run_until_complete(send_msg(f"⚠️ الرقم {phone_number}: لم يظهر زر إعادة الإرسال."))

    except Exception as e:
        if 'loop' in locals():
            try:
                loop.run_until_complete(send_msg(f"❌ خطأ مع الرقم {phone_number}: {str(e)}"))
            except:
                pass
    finally:
        if driver:
            driver.quit()
        if 'loop' in locals():
            try:
                loop.run_until_complete(send_msg(f"🏁 انتهت العملية للرقم {phone_number}."))
            except:
                pass
            loop.close()

import threading

def thread_runner(phone, chat_id, context):
    run_indrive_process(phone, chat_id, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    phone_numbers = [n.strip() for n in text.split('\n') if n.strip().isdigit()]

    if not phone_numbers:
        await update.message.reply_text("الرجاء إرسال أرقام هواتف صحيحة.")
        return

    await update.message.reply_text(f"بدأت معالجة {len(phone_numbers)} رقم...")

    for phone in phone_numbers:
        t = threading.Thread(target=thread_runner, args=(phone, update.effective_chat.id, context))
        t.start()
        time.sleep(1)

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    application.add_handler(message_handler)
    print("البوت يعمل الآن مع تحسينات الـ Timeout...")
    application.run_polling()
