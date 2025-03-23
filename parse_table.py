from bs4 import BeautifulSoup
import json
import os
import re  # 新增导入
from html import unescape

# 在原有解析函数中添加异常处理
def parse_html_to_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        # 使用html.unescape处理所有HTML实体
        headers = [unescape(th.div.text.strip()) for th in soup.select('thead th')]
        
        data = []
        for row in soup.select('tbody tr'):
            cells = [unescape(td.div.text.strip()) for td in row.find_all('td')]
            data.append(dict(zip(headers, cells)))
            
        return data
    except Exception as e:
        raise ValueError(f"解析失败: {str(e)}")

def process_directory(base_dir):
    output_dir = os.path.join(base_dir, "combined_results")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 遍历年份目录（按数字升序）
    for year in sorted(os.listdir(base_dir), key=lambda x: int(x) if x.isdigit() else 0):
        year_path = os.path.join(base_dir, year)
        if os.path.isdir(year_path) and year.isdigit():
            combined_data = []
            
            # 递归遍历时保持目录顺序
            for root, dirs, files in os.walk(year_path):
                # 对子目录和文件进行自然排序
                dirs.sort()
                # 修复文件排序逻辑
                files.sort(key=lambda f: [
                    int(text) if text.isdigit() else text.lower()
                    for text in re.split(r'(\d+)', f)
                ])
                
                # 按文件名数字顺序处理文件
                for file in files:
                    if file.endswith(".txt"):
                        file_path = os.path.join(root, file)
                        try:
                            data = parse_html_to_json(file_path)
                            combined_data.extend(data)
                            print(f"已处理 {file}，新增 {len(data)} 条数据")
                        except Exception as e:
                            print(f"处理文件 {file_path} 失败: {str(e)}")
                            continue
            
            # 生成合并文件
            output_path = os.path.join(output_dir, f"{year}.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, ensure_ascii=False, indent=2)
            
            print(f"成功生成 {year}.json，共 {len(combined_data)} 条数据")

            # 新增JSON转Excel功能
            try:
                import pandas as pd
                df = pd.read_json(output_path)
                excel_path = os.path.join(output_dir, f"{year}.xlsx")
                df.to_excel(excel_path, index=False, engine='openpyxl')
                print(f"成功生成Excel文件：{year}.xlsx")
            except Exception as e:
                print(f"Excel文件生成失败：{str(e)}")

if __name__ == "__main__":
    process_directory("/Users/cailibo/Documents/code/crawler/sxwhkj/山东省")