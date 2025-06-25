
# Output2 Web App (Render-Ready)

## ✅ วิธีใช้งานกับ Render.com

1. อัปโหลดโฟลเดอร์นี้ขึ้น GitHub
2. สร้าง Web Service บน Render แล้วตั้งค่า:

- **Environment**: Python
- **Build Command**: (เว้นว่าง)
- **Start Command**: `gunicorn app:app`
- **Instance Type**: Free หรือ Starter

3. เมื่อ Deploy แล้ว คุณสามารถเข้าผ่าน:  
   `https://<your-service-name>.onrender.com`

## 📦 สิ่งที่รวมในโปรเจกต์:
- `app.py`: Flask backend พร้อม route และ logic
- `templates/index.html`: หน้าเว็บที่ใช้งาน
- `requirements.txt`: Dependency รวม gunicorn
