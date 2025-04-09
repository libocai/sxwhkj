import os
import pandas as pd

def clean_excel(input_dir, output_path):
    # 新增：遍历目录收集所有Excel文件
    all_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(('.xlsx', '.xls')):
                all_files.append(os.path.join(root, file))
    
    # 新增：读取并合并所有文件
    dfs = []
    for file in all_files:
        try:
            df = pd.read_excel(file, engine='openpyxl')
            dfs.append(df)
        except Exception as e:
            print(f"跳过无法读取的文件: {file} - 错误原因: {str(e)}")
            continue
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # 新增：状态过滤
    combined_df = combined_df[combined_df['状态'] != '冻结']  # 新增过滤逻辑

    # 新增：按文件名排序（提取纯数字文件名转换为整数排序）
    all_files = sorted(all_files, key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))

    # 修改后的清洗流程
    # 1. 按购买日期降序排列（确保最新记录在前）
    df_sorted = combined_df.sort_values('购机日期', ascending=False)
    
    # 新增：按经销商分组计算补贴金额
    def calculate_subsidy(group):
        first_row = group.iloc[0].copy()
        first_row['单台中央补贴额(元)'] = group['单台中央补贴额(元)'].sum()
        first_row['总补贴额(元)'] = group['总补贴额(元)'].sum()
        if '单台省级补贴额(元)' in group.columns:
            first_row['单台省级补贴额(元)'] = group['单台省级补贴额(元)'].sum()
        else:
            first_row['单台省级补贴额(元)'] = None
        return first_row
    
    df_grouped = df_sorted.groupby('经销商', as_index=False).apply(calculate_subsidy)
    
    # 2. 根据经销商去重（保留最新记录）
    df_cleaned = df_grouped.drop_duplicates(
        subset=['经销商'], 
        keep='first'  # 保留排序后第一条（即最新日期）
    )
    
    # 3. 按序号排序输出
    df_final = df_cleaned.sort_values('序号').reset_index(drop=True)
    
    # 保存合并结果
    df_final.to_excel(output_path, index=False, engine='openpyxl')
    print(f"处理完成，共合并 {len(all_files)} 个文件，保留 {len(df_final)} 条唯一记录")

if __name__ == "__main__":
    # 修改输入输出路径为目录处理
    input_dir = "/Users/cailibo/Documents/code/crawler/sxwhkj/交付/安徽/"
    output_file = "/Users/cailibo/Desktop/安徽.xlsx"
    
    clean_excel(input_dir, output_file)