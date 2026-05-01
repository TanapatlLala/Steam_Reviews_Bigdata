# 🎮 Steam Big Data Pipeline: 100M+ Reviews Analytics

โปรเจกต์นี้เป็นระบบ **Data Engineering Pipeline** ครบวงจรสำหรับจัดการชุดข้อมูลรีวิวจาก Steam ขนาดใหญ่ (Original CSV **~39.57 GB**) ออกแบบมาเพื่อแก้ปัญหาข้อจำกัดด้านทรัพยากรบนเครื่อง Local (Out of Memory) โดยใช้เทคนิค Chunking และกระบวนการจัดเก็บข้อมูลที่มีประสิทธิภาพ

**จัดทำโดย:** ธนภัทร สมพงษ์ (Guide)
**สถาบัน:** มหาวิทยาลัยสยาม (Siam University)

---
## 📂 Dataset Source
*   **Dataset Name:** Steam Reviews Dataset
*   **Source:** [Kaggle - 100M+ Steam Reviews](https://www.kaggle.com/datasets/kieranpoc/steam-reviews/data)

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Data Processing** | Python (Pandas & PyArrow) พร้อมเทคนิค **Chunk-based Loading** |
| **Orchestration** | **Apache Airflow** (Docker Compose) |
| **Storage Format** | **Parquet** (Snappy Compression) |
| **Query Engine** | **DuckDB** (In-process OLAP) สำหรับการประมวลผลระดับวินาที |
| **Dashboard** | **Streamlit** Interactive Web Application |

---

## 📁 โครงสร้างโปรเจกต์
```text
Steam_Reviews_Bigdata/
├── docker-compose.yml      # ✅ ระบบ Airflow (Scheduler, Webserver, Postgres)
├── requirements.txt        # ✅ Python dependencies สำหรับเครื่อง Local
├── README.md               
│
├── dags/                   # Airflow DAGs (ควบคุม Pipeline)
│   └── steam_dag.py        #   - ขั้นตอน Clean & Convert -> Analyze
│
├── src/                    # โค้ดหลักของระบบ (Source Code)
│   ├── clean_and_convert.py #   - การประมวลผลแบบ Chunking (200k rows/chunk)
│   ├── analyze.py          #   - Data Quality Check ด้วย PyArrow
│   ├── benchmark.py        #   - สคริปต์เปรียบเทียบประสิทธิภาพ (CSV vs Parquet)
│   └── dashboard.py        #   - Web Dashboard (Streamlit)
│
└── data/                   # การจัดเก็บข้อมูล
    ├── raw/                #   - ข้อมูลดิบ (all_reviews.csv ~40GB)
    └── parquet/            #   - ข้อมูลที่ประมวลผลแล้ว (Partitioned Parquet)

    🚀 Pipeline Steps
✅ 1. Ingest & Clean (src/clean_and_convert.py)
อ่านไฟล์ CSV 39.57 GB แบบ Chunking (200,000 rows/chunk) เพื่อไม่ให้ RAM เต็ม

ทำความสะอาดข้อมูล: จัดการ Missing Values, ลบรีวิวที่สั้นเกินไป และแปลงประเภทข้อมูล (Data Type Casting)

Checkpoint System: สามารถรันงานต่อจากจุดเดิมได้ทันทีหากระบบหยุดชะงัก

✅ 2. Transform & Storage
แปลงข้อมูลเป็น Parquet Format พร้อมบีบอัดด้วย Snappy

ผลลัพธ์: ลดขนาดข้อมูลจาก ~40GB เหลือเพียง ~19.67 GB (ประหยัดพื้นที่ 50.3%)

✅ 3. Orchestration (Airflow)
ควบคุมลำดับการทำงานผ่าน Airflow DAG

Task 1: clean_and_convert — ประมวลผลข้อมูลดิบ

Task 2: analyze_data — ตรวจสอบคุณภาพและความสมบูรณ์ของไฟล์ Parquet

📊 Performance Benchmark (ผลการทดสอบ)
จากการทดสอบดึงข้อมูลจำนวนรีวิวแยกตามปีจากข้อมูลทั้งหมด:

🦆 DuckDB (Parquet): ใช้เวลาเพียง 0.43 วินาที

🐼 Pandas (Standard): FAILED (Out of Memory) เนื่องจากพยายามโหลดข้อมูลทั้งหมดลง RAM

🖥️ วิธีการรันโปรเจกต์
ขั้นตอนที่ 1: เตรียมสภาพแวดล้อม

# 1. Activate Virtual Environment
venv\Scripts\activate

# 2. ติดตั้ง Library ที่จำเป็น
pip install -r requirements.txt

ขั้นตอนที่ 2: รัน Pipeline ผ่าน Airflow
เปิด Docker Desktop และรันคำสั่ง docker-compose up -d

เข้าไปที่ http://localhost:8081 (admin/admin)

เปิดใช้งาน DAG steam_pipeline_v1 เพื่อเริ่มประมวลผล

ขั้นตอนที่ 3: เปิด Dashboard และ Benchmark
Bash
# รันการทดสอบประสิทธิภาพ
python src/benchmark.py

# เปิดหน้าจอวิเคราะห์ข้อมูล
streamlit run src/dashboard.py

📈 Dashboard Features
Total Reviews: แสดงจำนวนรีวิวมหาศาลที่ผ่านการตรวจสอบแล้ว

Sentiment Analysis: สัดส่วนรีวิวแง่บวกและแง่ลบของแต่ละเกม

Top Games: 10 อันดับเกมที่ได้รับความนิยมสูงสุดในฐานข้อมูล

Language Insights: การกระจายตัวของผู้เล่นในแต่ละภาษา
