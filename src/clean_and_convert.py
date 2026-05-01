"""
src/clean_and_convert.py  (Final Fixed Type Version)
──────────────────────────────────────────────
"""

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import os, time, json, shutil, sys, csv

max_int = sys.maxsize
while True:
    try:
        csv.field_size_limit(max_int)
        break
    except OverflowError:
        max_int = int(max_int/10)

INPUT_PATH = '/opt/airflow/data/raw/all_reviews/all_reviews.csv'
OUTPUT_DIR = '/opt/airflow/data/parquet/' 
CHECKPOINT_FILE  = "/opt/airflow/data/parquet/.checkpoint.json"
CHUNK_SIZE       = 200_000
CHECKPOINT_EVERY = 10   

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            ckpt = json.load(f)
        print(f"🔖 Checkpoint found!")
        print(f"   Last chunk : {ckpt['last_chunk']}")
        print(f"   Rows done  : {ckpt['total_rows']:,}")
        return ckpt
    return {"last_chunk": 0, "total_rows": 0}

def save_checkpoint(chunk_num, total_rows):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({
            "last_chunk": chunk_num,
            "total_rows": total_rows,
            "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, f, indent=2)
    print(f"\n  💾 Checkpoint saved — chunk {chunk_num} | {total_rows:,} rows")

def clean_chunk(df):
    df = df.drop_duplicates()
    df = df.dropna(subset=["review", "appid", "voted_up"])
    df["timestamp_created"] = pd.to_datetime(df["timestamp_created"], unit="s", errors="coerce")
    df["review_length"] = df["review"].str.len()
    df["year"]  = df["timestamp_created"].dt.year
    df["month"] = df["timestamp_created"].dt.month
    df = df[df["review_length"] > 10]
    df["voted_up"] = df["voted_up"].astype(int)
    
    # --- เพิ่มการบังคับ Data Type เพื่อป้องกันปัญหา Schema Mismatch ---
    # บังคับคอลัมน์ที่เป็นตัวเลขเวลาเล่นและสถิติให้เป็น float64 ให้หมด
    numeric_cols = [
        "author_playtime_forever", "author_playtime_last_two_weeks",
        "author_playtime_at_review", "author_last_played",
        "author_num_games_owned", "author_num_reviews",
        "votes_up", "votes_funny", "weighted_vote_score", "comment_count"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
            
    return df

def clean_and_convert():
    ckpt        = load_checkpoint()
    resume_from = ckpt["last_chunk"]
    total_rows  = ckpt["total_rows"]

    if resume_from == 0:
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print(f"\n🚀 Fresh start | chunk size: {CHUNK_SIZE:,}")
    else:
        print(f"\n▶️  Resuming from chunk {resume_from + 1}")

    t0, chunk_num = time.time(), 0
    dtype_spec = {"recommendationid": str, "appid": str, "steam_china_location": str}
    
    reader = pd.read_csv(INPUT_PATH, chunksize=CHUNK_SIZE, dtype=dtype_spec, on_bad_lines="skip")
    
    accumulated_tables = [] 

    for chunk in reader:
        chunk_num += 1

        if chunk_num <= resume_from:
            if chunk_num % 20 == 0:
                print(f"  ⏩ Skipping chunk {chunk_num}/{resume_from}...", end="\r")
            continue

        cleaned = clean_chunk(chunk)
        total_rows += len(cleaned)
        
        table = pa.Table.from_pandas(cleaned, preserve_index=False)
        accumulated_tables.append(table)

        elapsed = time.time() - t0
        rate    = (total_rows - ckpt["total_rows"]) / elapsed if elapsed > 0 else 0
        print(f"  chunk {chunk_num:>4} | rows: {total_rows:>12,} | {rate:>9,.0f} rows/s", end="\r")

        if chunk_num % CHECKPOINT_EVERY == 0:
            # เอา promote=True ออก เพราะเราบังคับ Type ใน clean_chunk เรียบร้อยแล้ว
            combined_table = pa.concat_tables(accumulated_tables)
            part_filename  = os.path.join(OUTPUT_DIR, f"part_{chunk_num:06d}.parquet")
            pq.write_table(combined_table, part_filename, compression="snappy")
            
            accumulated_tables = [] 
            save_checkpoint(chunk_num, total_rows)

    if accumulated_tables:
        combined_table = pa.concat_tables(accumulated_tables)
        part_filename  = os.path.join(OUTPUT_DIR, f"part_final.parquet")
        pq.write_table(combined_table, part_filename, compression="snappy")
        save_checkpoint(chunk_num, total_rows)

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"✅ Done! Total {total_rows:,} rows | Time: {elapsed/60:.1f} min")
    
if __name__ == "__main__":
    clean_and_convert()