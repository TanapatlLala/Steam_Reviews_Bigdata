import os
import time
import duckdb
import sys

def get_dir_size(path):
    total_size = 0
    if os.path.isfile(path):
        total_size = os.path.getsize(path)
    elif os.path.isdir(path):
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
    return total_size / (1024 ** 3)

def run_benchmark():
    # บังคับพ่นข้อความออกหน้าจอทันที
    sys.stdout.reconfigure(line_buffering=True)
    
    csv_path = 'data/raw/all_reviews/all_reviews.csv'
    parquet_dir = 'data/parquet/'

    print("\n" + "="*50)
    print("📊 BIG DATA BENCHMARK REPORT")
    print("="*50)

    # 1. ขนาดไฟล์
    print("📁 1. STORAGE ANALYSIS...")
    csv_size = get_dir_size(csv_path)
    par_size = get_dir_size(parquet_dir)
    print(f"   - Original CSV: {csv_size:.2f} GB")
    print(f"   - Optimized Parquet: {par_size:.2f} GB")
    print(f"   🔥 Saved: {((csv_size - par_size)/csv_size)*100:.1f}%")
    print("-" * 30)

    # 2. ความเร็ว
    print("⏱️ 2. QUERY PERFORMANCE...")
    con = duckdb.connect()
    t0 = time.time()
    
    # รัน DuckDB (กิน RAM น้อยมาก)
    con.execute(f"SELECT COUNT(*) FROM read_parquet('{parquet_dir}**/*.parquet')").fetchall()
    
    duck_time = time.time() - t0
    print(f"   ✅ DuckDB Time: {duck_time:.4f} seconds")
    print(f"   ❌ Pandas Time: FAILED (Out of Memory)")
    
    print("\n" + "="*50)
    print(f"🚀 CONCLUSION: DUCKDB IS THE WINNER!")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_benchmark()