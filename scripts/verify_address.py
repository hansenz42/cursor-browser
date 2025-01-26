import os
import sys
import json
import time
import subprocess
from typing import Dict
from tools.llm_client import LLMClient
from lib.utils import retry_with_backoff

class LocationVerifier:
    def __init__(self, attractions_file: str):
        self.llm_client = LLMClient()
        self.attractions_file = attractions_file
        # 从 JSON 文件中读取城市名
        with open(attractions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.city = data.get('city', '')
            if not self.city:
                raise ValueError("JSON 文件中缺少 'city' 字段")
        
    def load_attractions(self) -> Dict:
        """加载景点数据"""
        with open(self.attractions_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def save_attractions(self, data: Dict):
        """保存更新后的景点数据"""
        with open(self.attractions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    @retry_with_backoff(max_retries=3, initial_delay=2)
    def search_location(self, query: str) -> dict:
        """执行搜索并返回搜索结果"""
        cmd = f"python3 search.py \"{query}\""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"搜索失败: {result.stderr}")
            
        # 从输出中提取文件路径
        output = result.stdout.strip()
        if output.startswith("Search results saved to: "):
            search_result_file = output.replace("Search results saved to: ", "").strip()
        else:
            raise RuntimeError(f"无法解析搜索结果文件路径: {output}")
            
        # 读取搜索结果
        with open(search_result_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    @retry_with_backoff(max_retries=3, initial_delay=2)
    def verify_location(self, name: str, current_location: str) -> str:
        """验证单个景点的地址"""
        # 构建搜索查询
        query = f"{self.city}{name}具体地址"
        
        # 执行搜索
        try:
            search_data = self.search_location(query)
        except Exception as e:
            raise RuntimeError(f"搜索过程失败: {str(e)}")
            
        # 使用 DeepSeek 分析搜索结果中的地址
        prompt = f"""
        分析以下搜索结果，找出{self.city}{name}的具体地址。
        当前记录的地址是：{current_location}
        
        搜索结果：
        {json.dumps(search_data['results'][:5], ensure_ascii=False, indent=2)}
        
        请返回最准确的地址。如果搜索结果中没有找到明确的地址，或者当前地址更准确，则返回当前地址。
        只返回地址，不要包含任何其他内容。地址尽量详细。返回的地址中至少包含城市名。
        """
        
        system_prompt = "你是一个帮助提取和验证地址的助手。请只返回地址，不要包含任何其他内容。"
        
        try:
            return self.llm_client.get_completion(prompt, system_prompt)
        except Exception as e:
            raise RuntimeError(f"调用 DeepSeek API 失败: {e}")
        
    def verify_all_locations(self):
        """验证所有景点的地址"""
        data = self.load_attractions()
        updated_count = 0
        
        print(f"开始验证 {len(data['attractions'])} 个景点的地址...")
        
        for attraction in data['attractions']:
            name = attraction['name']
            current_location = attraction['location']
            print(f"\n正在验证: {name}")
            print(f"当前地址: {current_location}")
            
            new_location = self.verify_location(name, current_location)
            
            if new_location != current_location:
                print(f"更新地址: {new_location}")
                attraction['location'] = new_location
                updated_count += 1
            else:
                print("地址无需更新")
            
            # 添加 2 秒延迟
            time.sleep(2)
                
        if updated_count > 0:
            self.save_attractions(data)
            print(f"\n已更新 {updated_count} 个景点的地址")
        else:
            print("\n所有地址均准确，无需更新")

def main():
    if len(sys.argv) != 2:
        print("使用方法: python3 verify_address.py <attractions_file>")
        print("示例: python3 verify_address.py data/hangzhou_attractions.json")
        sys.exit(1)
        
    attractions_file = sys.argv[1]
    if not os.path.exists(attractions_file):
        print(f"错误：文件 {attractions_file} 不存在")
        sys.exit(1)
        
    verifier = LocationVerifier(attractions_file)
    verifier.verify_all_locations()

if __name__ == "__main__":
    main() 