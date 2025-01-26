#!/usr/bin/env python3
import json
import argparse
import sys
import time
from pathlib import Path
from get_coordinate import get_coordinate

def process_file(input_file: str, output_file: str = None, key: str = "ZIEBZ-RF5RL-N3XPI-MX6MU-HINTO-LJFEX"):
    """
    处理 ndjson 文件，为每条记录添加坐标信息
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径，如果为 None 则覆盖输入文件
        key: 腾讯地图 API key
    """
    if output_file is None:
        output_file = input_file
        
    # 读取并处理每一行
    records = []
    total_count = 0
    processed_count = 0
    
    # 首先计算总数
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                total_count += 1
    
    print(f"总共发现 {total_count} 条记录")
    
    # 处理记录
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
                
            record = json.loads(line)
            if 'location' in record and not 'coordinate' in record:
                processed_count += 1
                print(f"正在处理第 {processed_count}/{total_count} 条记录: {record['name']}")
                
                coordinates = get_coordinate(record['location'], key)
                if coordinates:
                    record['coordinate'] = {
                        'longitude': coordinates[0],
                        'latitude': coordinates[1]
                    }
                    print(f"获取坐标成功: 经度 {coordinates[0]}, 纬度 {coordinates[1]}")
                else:
                    print(f"获取坐标失败")
                    
                # 添加 1 秒延时以遵守 API 限制
                time.sleep(1)
            records.append(record)
    
    # 写入结果
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in records:
            json.dump(record, f, ensure_ascii=False)
            f.write('\n')

def main():
    parser = argparse.ArgumentParser(description='为 ndjson 文件中的地点添加坐标信息')
    parser.add_argument('input_file', help='输入的 ndjson 文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径，默认覆盖输入文件')
    parser.add_argument('-k', '--key', default="ZIEBZ-RF5RL-N3XPI-MX6MU-HINTO-LJFEX",
                        help='腾讯地图 API key')
    
    args = parser.parse_args()
    
    if not Path(args.input_file).exists():
        print(f"错误：找不到输入文件 {args.input_file}")
        sys.exit(1)
        
    process_file(args.input_file, args.output, args.key)

if __name__ == "__main__":
    main()
