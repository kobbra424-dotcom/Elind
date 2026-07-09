# inDrive Bot - Railway Deployment

بوت تليجرام لأتمتة تسجيل inDrive مع Selenium.

## الملفات المطلوبة

| الملف | الوصف |
|-------|-------|
| `app.py` | كود البوت الرئيسي |
| `requirements.txt` | مكتبات Python |
| `Procfile` | أمر التشغيل على Railway |
| `runtime.txt` | إصدار Python |
| `nixpacks.toml` | تثبيت Chrome/Chromium |
| `Dockerfile` | (اختياري) طريقة بديلة للتشغيل |

## خطوات النشر على Railway

### 1. أنشئ GitHub Repo
ارفع الملفات الـ 6 دي على GitHub repo جديد (public أو private).

### 2. سجل في Railway
- ادخل على [railway.app](https://railway.app)
- سجل بحساب GitHub

### 3. أنشئ مشروع جديد
- New Project → Deploy from GitHub repo
- اختار الـ repo اللي رفعته

### 4. أضف متغير البيئة (Environment Variables)
- روح على التاب **Variables**
- ضف متغير: `BOT_TOKEN` = توكن البوت بتاعك
- (اختياري) `CHROME_BINARY` = `/usr/bin/chromium`
- (اختياري) `CHROMEDRIVER_PATH` = `/usr/bin/chromedriver`

### 5. عدل إعدادات التشغيل
- روح على **Settings**
- **Start Command**: `python app.py`
- أو سيبه يتعرف تلقائي من الـ Procfile

### 6. Deploy!
- اضغط Deploy
- افتح Logs عشان تشوف البوت شغال ولا لأ

## ⚠️ ملاحظات مهمة

1. **Railway free tier** بيخلص بسرعة مع Selenium (بيستهلك CPU و RAM كتير). ممكن تحتاج paid plan.

2. **Chrome/Chromium** بيتحمل تلقائي بفضل `nixpacks.toml`.

3. لو البوت مش شغال، افتح Logs ودور على errors.

4. البوت بيستخدم `threading` مش `asyncio` للـ Selenium عشان يتجنب blocking.
