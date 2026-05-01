import pyarrow.parquet as pq
import os
import time

def validate_data():
    print("🔍 เริ่มต้นกระบวนการ Data Quality Check (PyArrow Version)...")
    parquet_dir = "/opt/airflow/data/parquet/"
    
    # เช็คว่ามีโฟลเดอร์และไฟล์อยู่จริงหรือไม่
    if not os.path.exists(parquet_dir):
        print(f"❌ ไม่พบโฟลเดอร์: {parquet_dir}")
        exit(1)

    print("🚀 ตรวจสอบความสมบูรณ์ของไฟล์ Parquet...")
    t0 = time.time()
    
    try:
        # ใช้ PyArrow โหลดเฉพาะคอลัมน์เดียวเพื่อนับจำนวนแถว (ประหยัด RAM ขั้นสุด)
        table = pq.read_table(parquet_dir, columns=['appid'])
        total_rows = table.num_rows
        
        elapsed = time.time() - t0
        
        print(f"{'='*50}")
        print(f"✅ Data Pipeline Completed Successfully!")
        print(f"📊 จำนวนรีวิวทั้งหมดที่แปลงสำเร็จ: {total_rows:,.0f} รายการ")
        print(f"⏱️ ใช้เวลาตรวจสอบ: {elapsed:.2f} วินาที")
        print(f"{'='*50}")
        print("🎉 ข้อมูลพร้อมสำหรับเชื่อมต่อกับ Streamlit Dashboard แล้ว!")
        
    except Exception as e:
        print(f"❌ พบข้อผิดพลาดในการอ่านไฟล์ Parquet: {e}")
        exit(1)

if __name__ == "__main__":
    validate_data()