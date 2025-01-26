import pandas as pd
import json
import sys
from pathlib import Path

def json_to_ndjson(input_file: str, output_file: str = None):
    """
    将 JSON 文件转换为 NDJSON 格式
    
    Args:
        input_file: 输入的 JSON 文件路径
        output_file: 输出的 NDJSON 文件路径，如果不指定则自动生成
    """
    # 读取 JSON 文件
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 将景点数据转换为 DataFrame
    df = pd.DataFrame(data['attractions'])
    
    # 如果没有指定输出文件，则自动生成
    if output_file is None:
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"{input_path.stem}.ndjson")
    
    # 将每行数据转换为 JSON 字符串并写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        for _, row in df.iterrows():
            f.write(json.dumps(row.to_dict(), ensure_ascii=False) + '\n')
    
    print(f"已将数据转换为 NDJSON 格式并保存到: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python to_ndjson.py <input_json_file> [output_ndjson_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    json_to_ndjson(input_file, output_file) 