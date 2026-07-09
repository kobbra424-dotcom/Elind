import time
import logging
import os
import asyncio
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8676015225:AAEPPWCUR22z4cxzpK7wNSgJmuA_Xbclgy8"

def run_indrive(phone, chat_id, context):
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    
    if os.path.exists("/usr/bin/google-chrome"):
        opts.binary_location = "/usr/bin/google-chrome"
    
    driver = None
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def msg(text):
        try: await context.bot.send_message(chat_id=chat_id, text=text)
        except: pass

    async def photo(path, cap):
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    await context.bot.send_photo(chat_id=chat_id, photo=f, caption=cap)
            except: pass

    try:
        try:
            srv = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
            driver = webdriver.Chrome(service=srv, options=opts)
        except:
            driver = webdriver.Chrome(options=opts)

        driver.get("https://couriers.indrive.com/register")
        wait = WebDriverWait(driver, 30)
        
        try:
            btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[role="combobox"]')))
            btn.click()
            opt = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[@role='option' and (contains(., 'Egypt') or contains(., 'مصر'))]")))
            opt.click()
        except: pass
        
        inp = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"], input[type="tel"]')))
        inp.send_keys(Keys.CONTROL + "a")
        inp.send_keys(Keys.BACKSPACE)
        inp.send_keys(phone)
        
        nxt = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Next')]")))
        nxt.click()
        
        time.sleep(10)
        path = f"s_{phone}.png"
        driver.save_screenshot(path)
        
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@autocomplete, 'one-time-code')] | //button[contains(., 'Request new code')]")))
            loop.run_until_complete(photo(path, f"✅ {phone}: OK"))
        except:
            loop.run_until_complete(photo(path, f"⚠️ {phone}: Failed"))
            return

        try:
            loop.run_until_complete(msg(f"🔄 Resending for {phone}..."))
            re = WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Request new code') or contains(., 'إعادة إرسال')]")))
            driver.execute_script("arguments[0].click();", re)
            loop.run_until_complete(msg(f"✅ {phone}: Resent"))
        except:
            loop.run_until_complete(msg(f"⚠️ {phone}: No button"))

    except Exception as e:
        loop.run_until_complete(msg(f"❌ Error {phone}: {str(e)}"))
    finally:
        if driver: driver.quit()
        loop.run_until_complete(msg(f"🏁 Done {phone}"))
        loop.close()

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    nums = [n.strip() for n in txt.split('\n') if n.strip().isdigit()]
    if not nums: return
    await update.message.reply_text(f"Processing {len(nums)}...")
    for n in nums:
        threading.Thread(target=run_indrive, args=(n, update.effective_chat.id, context)).start()
        time.sleep(1)

if __name__ == '__main__':
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))
    bot.run_polling()
