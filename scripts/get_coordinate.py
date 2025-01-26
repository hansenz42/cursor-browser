import argparse
import sys
from tools.tencent_map import get_coordinate, batch_get_coordinates

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='获取地点的经纬度坐标')
    parser.add_argument('location', nargs='?', help='要查询的地点名称')
    parser.add_argument('-f', '--file', help='包含地点列表的文件路径，每行一个地点')
    parser.add_argument('-k', '--key', default="ZIEBZ-RF5RL-N3XPI-MX6MU-HINTO-LJFEX",
                        help='腾讯地图 API key')
    
    args = parser.parse_args()
    
    if not args.location and not args.file:
        parser.print_help()
        sys.exit(1)
    
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                locations = [line.strip() for line in f if line.strip()]
            results = batch_get_coordinates(locations, args.key)
            for loc, coords in results.items():
                print(f"{loc} 的坐标是：经度 {coords[0]}, 纬度 {coords[1]}")
        except FileNotFoundError:
            print(f"错误：找不到文件 {args.file}")
            sys.exit(1)
    else:
        result = get_coordinate(args.location, args.key)
        if result:
            print(f"{args.location} 的坐标是：经度 {result[0]}, 纬度 {result[1]}")
