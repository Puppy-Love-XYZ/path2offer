import json
import re
from pathlib import Path
import jieba


def clean_text(text: str) -> str:

    if not text:
        return ""
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'[^\u4e00-\u9fa5A-Za-z0-9，。；：、（）()\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def clean_industry(industry: str):

    if not industry:
        return None, []
    separators = ['/', '｜', '、', ',', '，', ';', '；']
    for sep in separators:
        industry = industry.replace(sep, '|')
    parts = [i.strip() for i in industry.split('|') if i.strip()]
    seen = set()
    clean_parts = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            clean_parts.append(p)
    industry_str = '|'.join(clean_parts)
    return industry_str, clean_parts


def parse_salary_numeric(salary_str: str):

    if not salary_str or "面议" in salary_str:
        return None, None


    nums = re.findall(r"(\d+\.?\d*)", salary_str)
    if not nums:
        return None, None

    try:
        raw_nums = [float(n) for n in nums]
        low = raw_nums[0]
        high = raw_nums[1] if len(raw_nums) > 1 else low

        # 单位换算逻辑
        if "天" in salary_str:
           
            low, high = low * 21.75, high * 21.75
        elif "万" in salary_str:
            low, high = low * 10000, high * 10000
        elif low < 100:
           
            low, high = low * 10000, high * 10000

        if low > 50000:
            low, high = low / 12, high / 12

        return int(low), int(high)
    except:
        return None, None


def cut_words(text: str):

    return ' '.join(jieba.cut(text))


def load_stopwords(path="stopwords.txt"):
   
    if not Path(path).exists():
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def remove_stopwords(text, stopwords):
    if not text:
        return ""
    return " ".join([w for w in text.split() if w not in stopwords])




def clean_job_data(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    stopwords = load_stopwords("stopwords.txt")
    cleaned_data = []

    for item in raw_data:
        # 行业清洗
        industry_str, industry_list = clean_industry(item.get("industry_name"))

        # 薪资处理
        raw_salary = item.get("job_salary", "").strip()
        salary_min, salary_max = parse_salary_numeric(raw_salary)

        # JD 文本处理
        job_summary_clean = clean_text(item.get("job_summary"))
        job_summary_cut = cut_words(job_summary_clean)
        job_summary_cut_filtered = remove_stopwords(job_summary_cut, stopwords)

        # 福利文本处理
        benefits_clean = clean_text(item.get("company_benefits"))
        benefits_cut = cut_words(benefits_clean)

        cleaned_item = {
            "job_name": item.get("job_name"),
            "company_name": item.get("company_name"),
            "industry_name": industry_str,
            "industry_list": industry_list,
            "work_city": item.get("work_city"),
            "city_district": item.get("city_district"),
            "street_name": item.get("street_name"),
            "work_major": item.get("work_major"),
            "work_type": item.get("work_type"),
            "your_education": item.get("your_education"),
            "working_exp": item.get("working_exp"),
            "company_size": item.get("company_size"),

            # 原始薪资字符串（保留“面议”等）
            "job_salary": raw_salary,
            # 清洗后的数值薪资（用于开题报告中的可视分析）
            "salary_min": salary_min,
            "salary_max": salary_max,

            "job_summary": job_summary_clean,
            "job_summary_cut": job_summary_cut,
            "job_summary_cut_filtered": job_summary_cut_filtered,
            "company_benefits": benefits_clean,
            "company_benefits_cut": benefits_cut
        }
        cleaned_data.append(cleaned_item)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 清洗完成：{Path(input_path).name}，共 {len(cleaned_data)} 条数据")




if __name__ == "__main__":

    input_dir = Path("input")
    output_dir = Path("output")

    output_dir.mkdir(parents=True, exist_ok=True)
    json_files = list(input_dir.glob("*.json"))

    if not json_files:
        print("⚠️ input 目录下未找到 JSON 文件")
    else:
        print(f"📂 发现 {len(json_files)} 个待清洗文件")

    for input_file in json_files:
        output_file = output_dir / f"{input_file.stem}_cleaned.json"
        clean_job_data(input_file, output_file)

    print("🎉 所有文件薪资结构化及清洗完成")