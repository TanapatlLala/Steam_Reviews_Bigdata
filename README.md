# Steam Reviews Big Data Pipeline

## Project Overview
วิเคราะห์ข้อมูล Steam Reviews กว่า 88 ล้าน reviews โดยใช้ Big Data pipeline
ตั้งแต่การ ingest ข้อมูล → clean → แปลงเป็น Parquet → วิเคราะห์ → Dashboard

---

## Dataset
- **Source:** Kaggle — [100M+ Steam Reviews](https://www.kaggle.com/datasets/kieranpoc/steam-reviews)
- **ไฟล์ดิบ:** `data/raw/all_reviews/all_reviews.csv` — 42 GB
- **หลัง clean:** `data/cleaned/steam_reviews_cleaned.csv` — 88,051,726 rows
- **Parquet:** `data/parquet/steam_reviews.parquet` — 115 MB

## Columns สำคัญ
| Column | ความหมาย |
|---|---|
| `recommendationid` | ID ของ review |
| `appid` | ID ของเกม |
| `game` | ชื่อเกม |
| `author_steamid` | ID ของผู้รีวิว |
| `language` | ภาษาของ review |
| `review` | ข้อความ review |
| `timestamp_created` | เวลาที่รีวิว (unix) |
| `voted_up` | แนะนำหรือไม่ (1=แนะนำ, 0=ไม่แนะนำ) |
| `votes_up` | จำนวนคนที่กด helpful |
| `author_playtime_forever` | เวลาเล่นทั้งหมด (นาที) |
| `weighted_vote_score` | คะแนน weighted |

---

## โครงสร้างโปรเจกต์
Steam_Reviews_Bigdata/
├── data/
│   ├── raw/all_reviews/all_reviews.csv      # ข้อมูลดิบ 42GB
│   ├── cleaned/steam_reviews_cleaned.csv    # หลัง clean 88M rows
│   └── parquet/steam_reviews.parquet        # Parquet 115MB
├── src/
│   ├── ingest.py       # ดาวน์โหลดข้อมูลจาก Kaggle
│   ├── clean.py        # ทำความสะอาดข้อมูล
│   ├── transform.py    # แปลง CSV → Parquet + benchmark
│   └── analyze.py      # วิเคราะห์และสร้างกราฟ
├── dags/
│   └── steam_pipeline_dag.py    # Airflow DAG
├── dashboard/
│   └── app.py          # Streamlit Dashboard
├── docs/
│   └── charts/         # กราฟที่สร้างจาก analyze.py
├── notebooks/
├── tests/
├── requirements.txt
└── README.md

---

## Pipeline Steps

### ✅ 1. Ingest
- ดาวน์โหลดผ่าน Kaggle API
- คำสั่ง: `kaggle datasets download -d kieranpoc/steam-reviews -p data\raw`

### ✅ 2. Clean (`src/clean.py`)
- อ่าน CSV แบบ chunk (500,000 rows/chunk) รวม 228 chunks
- drop_duplicates, dropna (review, appid, voted_up)
- แปลง timestamp unix → datetime
- สร้าง column ใหม่: review_length, year, month
- กรอง review สั้นกว่า 10 ตัวอักษร
- ผลลัพธ์: 88,051,726 rows

### ✅ 3. Transform (`src/transform.py`)
- แปลง CSV → Parquet ด้วย PyArrow + Snappy compression
- อ่านแบบ chunk เพื่อประหยัด RAM
- ผลลัพธ์: 115 MB (ลดจาก CSV หลายเท่า)

### ✅ 4. Analyze (`src/analyze.py`)
- โหลดจาก Parquet (เร็วกว่า CSV มาก)
- สร้างกราฟ 5 อัน:
  - `sentiment_pie.png` — สัดส่วน recommended vs not
  - `top_games.png` — Top 10 เกมที่มี review เยอะสุด
  - `reviews_over_time.png` — จำนวน review ต่อเดือน
  - `languages.png` — Top 10 ภาษา
  - `playtime_vs_sentiment.png` — เวลาเล่นกับความพึงพอใจ

### ⬜ 5. Airflow (`dags/steam_pipeline_dag.py`)
- Orchestrate pipeline ทั้งหมด ingest → clean → transform → analyze
- ยังไม่ได้ทำ

### ⬜ 6. Dashboard (`dashboard/app.py`)
- Streamlit interactive dashboard
- ยังไม่ได้ทำ

---

## Key Insights จากข้อมูล
- คนที่ **Recommended** เล่นนานกว่า (median ~750 นาที) vs **Not Recommended** (median ~200 นาที)
- ข้อมูลมี 88 ล้าน reviews จาก games หลายพันเกม

---

## Environment
- **OS:** Windows 11
- **Python:** 3.13.13
- **Virtual Env:** venv
- **Key Libraries:** pandas, pyarrow, matplotlib, seaborn, streamlit, plotly

## How to Run
```bash
# 1. activate venv
venv\Scripts\activate

# 2. clean
python src/clean.py

# 3. transform
python src/transform.py

# 4. analyze
python src/analyze.py

# 5. dashboard
streamlit run dashboard/app.py
```