from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    'steam_pipeline_v1',
    start_date=datetime(2026, 4, 1),
    schedule_interval=None,
    catchup=False
) as dag:

    # รันการแปลงไฟล์ (Path ภายใน Docker จะเริ่มที่ /opt/airflow/)
    t1 = BashOperator(
        task_id='clean_and_convert',
        bash_command='python /opt/airflow/src/clean_and_convert.py'
    )

    # รันการวิเคราะห์กราฟ
    t2 = BashOperator(
        task_id='analyze_data',
        bash_command='python /opt/airflow/src/analyze.py'
    )

    t1 >> t2