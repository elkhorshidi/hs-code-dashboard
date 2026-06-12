# داشبورد بررسی کد تعرفه

یک داشبورد ساده Streamlit برای بررسی کدهای تعرفه ایران در فهرست‌های بند ۱ و بند ۲.

## اجرای محلی

ابتدا وابستگی‌ها را نصب کنید:

```bash
pip install -r requirements.txt
```

سپس برنامه را اجرا کنید:

```bash
streamlit run app.py
```

## ساختار پروژه

```text
hs-code-dashboard/
├── app.py
├── requirements.txt
└── README.md
```

## منبع داده

برنامه داده‌ها را مستقیماً از دو CSV عمومی Google Sheets می‌خواند:

- Band 1
- Band 2

داده‌ها با `st.cache_data(ttl=300)` برای ۵ دقیقه کش می‌شوند.

## انتشار در Streamlit Community Cloud

1. این پوشه را به GitHub push کنید.
2. وارد [Streamlit Community Cloud](https://streamlit.io/cloud) شوید.
3. گزینه **New app** را انتخاب کنید.
4. Repository و branch مربوط به این پروژه را انتخاب کنید.
5. در بخش **Main file path** مقدار زیر را وارد کنید:

```text
hs-code-dashboard/app.py
```

6. روی **Deploy** کلیک کنید.

Streamlit به صورت خودکار فایل `hs-code-dashboard/requirements.txt` را برای نصب وابستگی‌ها استفاده می‌کند.
