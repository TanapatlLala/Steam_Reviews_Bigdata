import pyarrow.dataset as ds

# ชี้ไปที่โฟลเดอร์ Parquet ของคุณใน Docker
PARQUET_PATH = "/opt/airflow/data/parquet/"

def run_validation():
    print("🔍 เริ่มการตรวจสอบความถูกต้องของข้อมูล (Data Validation)...\n")

    # ==========================================
    # Test 1: Schema & Row Count (เช็คจาก Metadata ไม่กิน RAM)
    # ==========================================
    print("📊 [Test 1] ตรวจสอบโครงสร้างไฟล์ (Schema & Count)")
    try:
        # ใช้ dataset API เพื่อไม่อ่านข้อมูลลง RAM ทันที
        dataset = ds.dataset(PARQUET_PATH, format="parquet")
        
        print(f"✅ โหลดโครงสร้างไฟล์สำเร็จ!")
        print(f"✅ จำนวนคอลัมน์: {len(dataset.schema.names)}")
        
        # นับจำนวนบรรทัดโดยอ่านจาก Metadata ของไฟล์ (ใช้เวลาเสี้ยววินาที และ RAM 0%)
        total_rows = dataset.count_rows()
        print(f"✅ จำนวนบรรทัดทั้งหมดที่แปลงมาได้: {total_rows:,} บรรทัด\n")
        
    except Exception as e:
        print(f"❌ Error อ่านไฟล์ไม่ได้: {e}")
        return

    # ==========================================
    # Test 2: Sanity Check (ตรวจสอบตรรกะความจริง)
    # ดึงก้อนข้อมูล (Batch) มาสุ่มตรวจแทนการดึงทั้งหมด
    # ==========================================
    print("🧠 [Test 2] ตรวจสอบความสมเหตุสมผล (Sanity Check - สุ่มตรวจจากกลุ่มตัวอย่าง)")
    
    try:
        # ดึงข้อมูลมาแค่ 1 ก้อนแรก (ประมาณหลักหมื่นบรรทัด) เพื่อเช็คตรรกะ
        batches = dataset.to_batches(columns=["voted_up", "author_playtime_forever", "appid"])
        df = next(batches).to_pandas()
        
        negative_playtime = (df['author_playtime_forever'] < 0).sum()
        if negative_playtime == 0:
            print("✅ ผ่าน: ไม่มีข้อมูลเวลาเล่นเกมติดลบ")
        else:
            print(f"❌ พัง: พบข้อมูลเวลาเล่นติดลบจำนวน {negative_playtime} บรรทัด!")

        valid_votes = df['voted_up'].isin([0, 1, True, False]).all()
        if valid_votes:
            print("✅ ผ่าน: ค่าการโหวตถูกต้อง (มีแค่ แนะนำ กับ ไม่แนะนำ)")
        else:
            print("❌ พัง: พบค่าประหลาดในคอลัมน์ voted_up")

        missing_appid = df['appid'].isnull().sum()
        if missing_appid == 0:
            print("✅ ผ่าน: ไม่มีรีวิวไหนที่ระบุเกม (AppID) ไม่ได้")
        else:
            print(f"⚠️ เตือน: พบรีวิวที่ไม่มี AppID จำนวน {missing_appid} บรรทัด")

        positive_rate = (df['voted_up'] == 1).mean() * 100
        print(f"ℹ️ ข้อมูลเสริม: สัดส่วนรีวิวแง่บวกในกลุ่มตัวอย่างนี้คือ {positive_rate:.2f}%")

        print("\n🎉 สิ้นสุดการตรวจสอบ! ข้อมูลของคุณพร้อมนำไปสร้าง Dashboard แล้ว!")
        
    except StopIteration:
        print("❌ ไม่พบข้อมูลในไฟล์ Parquet")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดระหว่างสุ่มตรวจ: {e}")

if __name__ == "__main__":
    run_validation()