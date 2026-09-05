import json
from pathlib import Path
from app.database import SessionLocal, engine
from app.models import Job, Base


def reset_and_init_db():
    """
    删除旧表并重新创建。
    这能解决你之前遇到的 'column jobs.job_name does not exist' 报错。
    """
    print("正在重置 PostgreSQL 表结构 (Drop & Create)...")
    # 注意：这会清空 jobs 表里的所有现有数据！
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("表结构初始化完成。")


def import_jobs_fast(json_path):
    db = SessionLocal()
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            jobs_data = json.load(f)

        if isinstance(jobs_data, dict):
            jobs_data = [jobs_data]

        job_objects = []
        for item in jobs_data:
            # 直接创建对象，不进行任何查询判断
            job = Job(
                job_name=item.get("job_name"),
                company_name=item.get("company_name"),
                industry_name=item.get("industry_name"),
                industry_list=item.get("industry_list"),  # PostgreSQL ARRAY
                work_city=item.get("work_city"),
                city_district=item.get("city_district"),
                street_name=item.get("street_name"),
                work_major=item.get("work_major"),
                work_type=item.get("work_type"),
                your_education=item.get("your_education"),
                working_exp=item.get("working_exp"),
                company_size=item.get("company_size"),
                job_salary=item.get("job_salary"),
                salary_min=item.get("salary_min"),
                salary_max=item.get("salary_max"),
                job_summary=item.get("job_summary"),
                job_summary_cut=item.get("job_summary_cut"),
                job_summary_cut_filtered=item.get("job_summary_cut_filtered"),
                company_benefits=item.get("company_benefits"),
                company_benefits_cut=item.get("company_benefits_cut")
            )
            job_objects.append(job)

        # 使用 bulk_save_objects 实现快速批量插入
        if job_objects:
            db.bulk_save_objects(job_objects)
            db.commit()
            print(f"✅ 已处理: {json_path.name} | 写入: {len(job_objects)} 条")

    except Exception as e:
        print(f"❌ 处理文件 {json_path.name} 时出错: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # 1. 强制重置数据库结构
    reset_and_init_db()

    # 2. 你的绝对路径
    data_dir = Path(r"E:\allgraduate\forjob\backend\dataclean\output")

    # 3. 扫描并执行快速导入
    if not data_dir.exists():
        print(f"❌ 错误：路径不存在 -> {data_dir}")
    else:
        json_files = list(data_dir.glob("*_cleaned.json"))

        if not json_files:
            print(f"❓ 在 {data_dir} 下未发现 *_cleaned.json 文件")
        else:
            print(f"🚀 找到 {len(json_files)} 个文件，开始全量导入...")
            for file in json_files:
                import_jobs_fast(file)
            print("-" * 30)
            print("🎉 所有数据已成功写入 PostgreSQL！")