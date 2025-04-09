import os
import pandas as pd

def clean_excel(input_dir, output_path):
    # 收集所有Excel文件
    all_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(('.xlsx', '.xls')):
                all_files.append(os.path.join(root, file))
    
    dfs = []
    for file in all_files:
        try:
            # 提取纯净文件名（不含路径和扩展名）
            region = os.path.splitext(os.path.basename(file))[0]
            df = pd.read_excel(file, engine='openpyxl')
            # 添加区域列
            df = df.assign(区域=region)
            dfs.append(df)
        except Exception as e:
            print(f"跳过无法读取的文件: {file} - 错误原因: {str(e)}")
            continue
    
    if not dfs:
        print("警告：未找到任何有效Excel文件")
        return
    
    # 合并并过滤数据
    combined_df = pd.concat(dfs, ignore_index=True)
    # filtered_df = combined_df[combined_df['状态'] != '冻结']
    
    # 数据清洗流程
    df_sorted = combined_df.sort_values('购机日期', ascending=False)
    df_dedup = df_sorted.drop_duplicates(subset=['经销商'], keep='first')
    
    # 调整列顺序（保持原有列顺序，区域放在最后）
    columns = [col for col in df_dedup.columns if col != '区域'] + ['区域']
    # 新增双重排序
    df_ordered = df_dedup[columns].sort_values(by=['区域', '序号'])
    df_final = df_ordered.reset_index(drop=True)
    
    # 保存结果
    df_final.to_excel(output_path, index=False, engine='openpyxl')
    print(f"处理完成：合并 {len(all_files)} 个文件，保留 {len(df_final)} 条有效记录")

if __name__ == "__main__":
    input_dir = "/Users/cailibo/Desktop/all"
    output_file = "/Users/cailibo/Desktop/农机购置与应用补贴_v1.4.xlsx"
    clean_excel(input_dir, output_file)