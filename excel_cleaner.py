import pandas as pd

def clean_excel(input_path, output_path):
    # 读取Excel文件
    df = pd.read_excel(input_path, engine='openpyxl')
    
    # 数据清洗流程
    # 1. 按序号降序排列（从大到小）
    df_sorted = df.sort_values('序号', ascending=False)
    
    # 2. 去除重复序号（保留第一个出现的记录）
    df_cleaned = df_sorted.drop_duplicates(subset=['序号'], keep='first')
    
    # 3. 按原始顺序重新排序（从1开始连续编号）
    df_final = df_cleaned.sort_values('序号').reset_index(drop=True)
    
    # 保存处理结果
    df_final.to_excel(output_path, index=False, engine='openpyxl')
    print(f"处理完成，共保留 {len(df_final)} 条唯一记录")

if __name__ == "__main__":
    input_file = "/Users/cailibo/Documents/code/crawler/sxwhkj/安徽省/combined_results/2022.xlsx"
    output_file = "/Users/cailibo/Documents/code/crawler/sxwhkj/安徽省/combined_results/2022_cleaned.xlsx"
    
    clean_excel(input_file, output_file)