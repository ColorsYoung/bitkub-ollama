# Bitkub AI Trading Bot with Local Ollama 🚀

บอทเทรดคริปโตอัตโนมัติสำหรับ Bitkub ที่ใช้พลังของ Local LLM (ผ่าน Ollama) ในการวิเคราะห์ทางเทคนิคและตัดสินใจซื้อขายแบบ Real-time

## ✨ คุณสมบัติหลัก
- **AI-Powered Decision**: ใช้ Local Ollama (เช่น Llama 3.1) ในการวิเคราะห์ข้อมูลแทนการใช้แค่ Rules-based แบบเดิม
- **Bitkub v3 Integration**: เชื่อมต่อกับ Bitkub API v3 โดยตรง (รองรับทั้ง Public และ Private endpoints)
- **Technical Analysis**: คำนวณอินดิเคเตอร์ยอดนิยม (RSI, EMA, MACD) อัตโนมัติด้วย `pandas_ta`
- **Flexible Strategy**: ปรับเปลี่ยนกลยุทธ์ผ่าน AI Prompt ได้ง่ายๆ ใน `engine/ai_engine.py`
- **Security**: ออกแบบมาให้แยกส่วน API Key และทำงานผ่าน Virtual Environment (venv) เพื่อความปลอดภัย

---

## 📂 โครงสร้างโปรเจกต์
- `main.py`: จุดเริ่มต้นของโปรเจกต์ จัดการ Loop การเทรดและประสานงานแต่ละ Engine
- `engine/bitkub_api.py`: หัวใจหลักในการคุยกับ Bitkub (จัดการเรื่อง Signature SHA256 และ API v3)
- `engine/market_engine.py`: ดึงราคา Real-time และคำนวณ Technical Indicators
- `engine/ai_engine.py`: ส่วนติดต่อกับ Ollama เพื่อส่ง Market Summary ไปให้ AI วิเคราะห์
- `engine/execution_engine.py`: จัดการการส่งคำสั่งซื้อ/ขายจริง และเช็คยอดเงินในกระเป๋า
- `config/settings.py`: จัดการการตั้งค่าผ่านไฟล์ `.env`

---

## 🛠️ สิ่งที่ต้องเตรียมก่อนเริ่ม
1. **Python 3.10+**
2. **Ollama**: ติดตั้งและรันอยู่ในเครื่อง ([ดาวน์โหลดที่นี่](https://ollama.com))
   - ดึงโมเดลที่ต้องการใช้: `ollama pull llama3.1:8b`
3. **Bitkub API Keys**: สร้างได้ที่เมนู API ใน Bitkub (ต้องมีสิทธิ์ Read และ Trade เท่านั้น **ห้ามติ๊ก Withdraw**)

---

## 🚀 วิธีติดตั้งและใช้งาน

1. **Clone โปรเจกต์ลงเครื่อง:**
   ```bash
   git clone https://github.com/ColorsYoung/bitkub-ollama.git
   cd bitkub-ollama
   ```

2. **สร้างและใช้งาน Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # สำหรับ Mac/Linux
   # หรือ venv\Scripts\activate สำหรับ Windows
   ```

3. **ติดตั้ง Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **ตั้งค่า API Keys:**
   - ก๊อปปี้ไฟล์ `.env.template` เป็น `.env`
   ```bash
   cp .env.template .env
   ```
   - ใส่ `BITKUB_API_KEY` และ `BITKUB_API_SECRET` ของคุณลงในไฟล์ `.env`

5. **เริ่มรันบอท:**
   ```bash
   python main.py
   ```

---

## 💡 โหมดการทำงาน
- **Dry Run Mode**: หากคุณไม่ใส่ API Key ในไฟล์ `.env` บอทจะแสดงแค่การวิเคราะห์ของ AI แต่จะไม่ส่งคำสั่งซื้อขายจริง (เหมาะสำหรับการทดสอบกลยุทธ์)
- **Real Trading**: ใส่ API Key และ Secret เพื่อให้บอททำการซื้อขายจริงตามยอดเงิน `TRADE_AMOUNT_THB` ที่ตั้งไว้

## ⚠️ คำเตือน (Disclaimer)
การลงทุนในคริปโทเคอร์เรนซีมีความเสี่ยงสูง บอทตัวนี้เป็นเพียงเครื่องมือช่วยอำนวยความสะดวกในการวิเคราะห์ ผู้พัฒนาไม่รับผิดชอบต่อความสูญเสียใดๆ ที่อาจเกิดขึ้นจากการใช้งาน โปรดศึกษาและทดสอบให้มั่นใจก่อนลงสนามจริง

---
**พัฒนาโดย:** ColorsYoung  
**License:** MIT
