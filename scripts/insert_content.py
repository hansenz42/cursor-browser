#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
import time
from typing import List, Dict, Any

# 将导入路径调整到上层目录
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.llm_client import LLMClient
from tools.search import DuckDuckGoSearcher
from tools.web_access import process_urls

def run_search(query: str) -> str:
    """执行搜索并返回结果文件路径"""
    print(f"\n[DEBUG] 开始搜索: {query}")
    searcher = DuckDuckGoSearcher()
    searcher.search(query)
    # 获取最新的搜索结果文件
    search_dir = 'cache/search_results'
    files = [os.path.join(search_dir, f) for f in os.listdir(search_dir) if f.endswith('.json')]
    if not files:
        raise Exception("No search results found")
    result_file = max(files, key=os.path.getctime)
    print(f"[DEBUG] 搜索结果保存到: {result_file}")
    return result_file

def read_search_results(file_path: str) -> List[Dict[str, str]]:
    """读取搜索结果"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('results', [])

def filter_urls_with_llm(llm_client: LLMClient, spot_name: str, search_results: List[Dict[str, str]]) -> List[str]:
    """使用LLM筛选最相关的URL"""
    print(f"\n[DEBUG] 开始使用LLM筛选URL，景点名称: {spot_name}")
    prompt = f"""
请帮我从以下搜索结果中选择最相关的URL，这些URL应该包含关于"{spot_name}"景点的详细介绍。
我会给你一个搜索结果列表，每个结果包含标题、URL和摘要。请选择最相关的3个URL，只返回URL列表，每行一个URL。

搜索结果：
{json.dumps(search_results, ensure_ascii=False, indent=2)}

请直接返回URL列表，每行一个URL，不要有任何其他内容。"""
    
    response = llm_client.get_completion(prompt)
    urls = [url.strip() for url in response.split('\n') if url.strip().startswith('http')]
    urls = urls[:3]  # 限制最多3个URL
    print(f"[DEBUG] LLM筛选出的URL: {json.dumps(urls, ensure_ascii=False, indent=2)}")
    return urls

def access_urls(urls: List[str]) -> str:
    """访问URL并返回结果文件路径"""
    process_urls(urls)
    # 获取最新的URL访问结果文件
    url_dir = 'cache/url_results'
    files = [os.path.join(url_dir, f) for f in os.listdir(url_dir) if f.endswith('.json')]
    if not files:
        raise Exception("No URL results found")
    return max(files, key=os.path.getctime)

def read_url_results(file_path: str) -> Dict[str, Any]:
    """读取URL访问结果"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def summarize_content_with_llm(llm_client: LLMClient, spot_name: str, url_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """使用LLM总结内容，返回符合JsonContent格式的内容列表"""
    print(f"\n[DEBUG] 开始使用LLM总结内容，景点名称: {spot_name}")
    # 准备所有文本内容
    all_texts = []
    all_images = []
    
    for result in url_results['results']:
        all_texts.append(result['content']['text'])
        all_images.extend(result['content']['images'])
    
    print(f"[DEBUG] 收集到的文本数量: {len(all_texts)}")
    print(f"[DEBUG] 收集到的图片数量: {len(all_images)}")
    
    # 合并文本并检查token数量
    combined_text = ' '.join(all_texts)
    total_tokens = llm_client.count_tokens(combined_text)
    print(f"[DEBUG] 文本总token数量: {total_tokens}")
    
    # 如果token数量超过限制的80%，进行分段处理
    max_safe_tokens = int(llm_client.max_tokens * 0.8)  # 留20%给其他内容
    if total_tokens > max_safe_tokens:
        print(f"[DEBUG] Token数量超过安全限制({max_safe_tokens})，进行分段处理")
        # 将文本按句子分割
        sentences = combined_text.split('。')
        current_segment = []
        current_tokens = 0
        segments = []
        
        for sentence in sentences:
            sentence = sentence.strip() + '。'
            sentence_tokens = llm_client.count_tokens(sentence)
            
            # 处理单个句子超过限制的情况
            if sentence_tokens > max_safe_tokens:
                print(f"[DEBUG] 发现超长句子 ({sentence_tokens} tokens)，进行拆分")
                # 如果当前segment不为空，先保存
                if current_segment:
                    segments.append(''.join(current_segment))
                    current_segment = []
                    current_tokens = 0
                
                # 按照字符数粗略拆分句子
                chars_per_token = len(sentence) / sentence_tokens
                safe_chars = int(max_safe_tokens * chars_per_token * 0.8)  # 留20%余量
                
                # 拆分句子
                for i in range(0, len(sentence), safe_chars):
                    sub_sentence = sentence[i:i + safe_chars]
                    if sub_sentence:
                        segments.append(sub_sentence)
                continue
            
            if current_tokens + sentence_tokens > max_safe_tokens:
                if current_segment:
                    segments.append(''.join(current_segment))
                current_segment = [sentence]
                current_tokens = sentence_tokens
            else:
                current_segment.append(sentence)
                current_tokens += sentence_tokens
        
        if current_segment:
            segments.append(''.join(current_segment))
        
        # 分别处理每个段落并合并结果
        all_content = []
        for i, segment in enumerate(segments):
            print(f"[DEBUG] 处理第 {i+1}/{len(segments)} 个文本段")
            prompt = f"""
请帮我总结关于"{spot_name}"景点的这部分介绍。这是文本的第{i+1}/{len(segments)}部分。
请生成1-2个重点段落，每个段落都应该有一个小标题(heading2)和正文(paragraph)。

文本内容：
{segment}

请按照以下JSON格式返回结果（确保是有效的JSON格式）：
{{
    "content": [
        {{"type": "heading2", "text": "部分标题"}},
        {{"type": "paragraph", "text": "部分正文..."}},
        ...
    ]
}}

除了JSON之外，不要返回其他内容。
"""
            
            try:
                response = llm_client.get_completion(prompt)
                result = json.loads(response)
                all_content.extend(result['content'])
            except Exception as e:
                print(f"[ERROR] 处理段落时出错: {str(e)}")
                continue
    else:
        # 如果token数量在限制内，使用原来的处理方式
        prompt = f"""
请帮我总结关于"{spot_name}"景点的介绍。我会给你一些原始文本和图片信息，请你：
1. 生成一个简短的标题作为heading1
2. 将文本整理成3-5个重点段落，每个段落都应该有一个小标题(heading2)和正文(paragraph)
3. 从提供的图片中选择最具代表性的2-3张，这些图片应该能展示景点的不同角度
4. 关注景点本身的历史文化内容，不要有其他的内容

原始文本：
{combined_text}

可用图片：
{json.dumps(all_images, ensure_ascii=False, indent=2)}

请按照以下JSON格式返回结果（确保是有效的JSON格式）：
{{
    "content": [
        {{"type": "heading1", "text": "景点总标题"}},
        {{"type": "heading2", "text": "第一部分标题"}},
        {{"type": "paragraph", "text": "第一部分正文..."}},
        {{"type": "image", "access_url": "图片URL"}},
        {{"type": "heading2", "text": "第二部分标题"}},
        {{"type": "paragraph", "text": "第二部分正文..."}},
        ...
    ]
}}

除了JSON之外，不要返回其他内容。
"""
        
        try:
            response = llm_client.get_completion(prompt)
            result = json.loads(response)
            all_content = result['content']
        except Exception as e:
            print(f"[ERROR] LLM处理失败: {str(e)}")
            raise e
    
    # 添加图片到内容中
    if all_images and isinstance(all_content, list):
        selected_images = all_images[:3]  # 选择前3张图片
        for image in selected_images:
            if image.get('url'):
                all_content.append({
                    'type': 'image',
                    'access_url': image['url']
                })
    
    return all_content

def format_raw_content(url_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """当LLM处理失败时，格式化原始内容"""
    content = []
    # 添加默认标题
    content.append({
        'type': 'heading1',
        'text': '景点介绍'
    })
    
    for result in url_results['results']:
        # 添加文本内容
        if result['content']['text'].strip():
            content.append({
                'type': 'paragraph',
                'text': result['content']['text']
            })
        
        # 添加图片内容
        for image in result['content']['images']:
            if image['url']:
                content.append({
                    'type': 'image',
                    'access_url': image['url']
                })
    return content

def process_spot(spot_name: str, llm_client: LLMClient) -> List[Dict[str, Any]]:
    """处理单个景点，返回content列表"""
    print(f"\n[DEBUG] ====== 开始处理景点: {spot_name} ======")
    # 1. 搜索景点信息
    search_file = run_search(f"{spot_name} 旅游 景点介绍")
    search_results = read_search_results(search_file)
    print(f"[DEBUG] 搜索到 {len(search_results)} 条结果")
    
    # 2. 使用LLM筛选最相关的URL
    selected_urls = filter_urls_with_llm(llm_client, spot_name, search_results)
    
    # 3. 访问选中的URL
    print("[DEBUG] 开始访问选中的URL")
    url_result_file = access_urls(selected_urls)
    url_results = read_url_results(url_result_file)
    print(f"[DEBUG] URL访问结果保存到: {url_result_file}")
    
    # 4. 使用LLM总结内容
    content = summarize_content_with_llm(llm_client, spot_name, url_results)
    print(f"[DEBUG] 内容总结完成，生成了 {len(content)} 个内容块")
    print("[DEBUG] ====== 景点处理完成 ======\n")
    return content

def process_ndjson_file(input_file: str):
    """处理NDJSON文件，添加content字段，处理一条立即更新源文件"""
    print(f"\n[DEBUG] 开始处理文件: {input_file}")
    llm_client = LLMClient()
    
    # 读取所有行
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    for i, line in enumerate(lines, 1):
        data = json.loads(line)
        print(f"\n[DEBUG] 处理第 {i}/{total_lines} 条数据")
        
        if 'name' in data and not data.get('content'):
            try:
                content = process_spot(data['name'], llm_client)
                data['content'] = content
                print(f"[DEBUG] 成功添加content字段")
                
                # 更新当前行
                lines[i-1] = json.dumps(data, ensure_ascii=False) + '\n'
                
                # 立即写入更新后的内容到源文件
                with open(input_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print(f"[DEBUG] 已更新源文件")
                
                time.sleep(1)  # 添加延迟，避免请求过快
            except Exception as e:
                print(f"[ERROR] 处理 {data['name']} 时出错: {str(e)}")
        else:
            print(f"[DEBUG] 跳过处理: {'name' not in data and '缺少name字段' or 'content已存在'}")
    
    print(f"[DEBUG] 处理完成")

def main():
    if len(sys.argv) != 2:
        print("Usage: python insert_content.py <input_ndjson_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Input file {input_file} does not exist")
        sys.exit(1)
    
    process_ndjson_file(input_file)

if __name__ == "__main__":
    main()
