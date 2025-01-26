#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from lib.env import config
import concurrent.futures
import threading
import argparse
import time
import json
import sys
import os

class ChromeDriver:
    """Chrome 浏览器驱动的封装类"""
    
    def __init__(self):
        """
        初始化 Chrome 驱动
        
        Args:
            chromium_path: Chromium 浏览器的安装路径
        """
        self.chromium_path = config.chrome_path

        self.driver = None
    
    def _create_options(self):
        """
        创建并配置 Chrome 选项
        
        Returns:
            Options: 配置好的 Chrome 选项
        """
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 无界面模式
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # 添加反爬虫配置
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 设置 User-Agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        chrome_options.binary_location = self.chromium_path
        
        return chrome_options
    
    def create_driver(self):
        """
        创建并配置 Chrome 驱动
        
        Returns:
            webdriver.Chrome: 配置好的 Chrome 驱动实例
        """
        options = self._create_options()
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        self.driver = webdriver.Chrome(service=service, options=options)
        return self.driver
    
    def quit(self):
        """关闭浏览器并清理资源"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def get_page_content(self, url, wait_time=2):
        """
        获取网页内容
        
        Args:
            url: 要访问的网页URL
            wait_time: 等待页面加载的时间（秒）
            
        Returns:
            tuple: (页面源代码, 当前URL)
            
        Raises:
            Exception: 当获取页面失败时抛出异常
        """
        try:
            if not self.driver:
                self.create_driver()
            
            # 打开网页
            self.driver.get(url)
            time.sleep(wait_time)  # 等待页面加载
            
            # 获取页面内容
            page_source = self.driver.page_source
            current_url = self.driver.current_url  # 获取当前页面的URL（可能经过重定向）
            
            return page_source, current_url
            
        except Exception as e:
            self.quit()
            raise
    
    def __enter__(self):
        """上下文管理器入口"""
        self.create_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.quit()

class FileHandler:
    """处理文件操作的工具类"""
    
    def __init__(self, base_dir='cache/url_results'):
        """
        初始化文件处理器
        
        Args:
            base_dir: 基础输出目录
        """
        self.base_dir = base_dir
        self.ensure_output_dir()
    
    def ensure_output_dir(self):
        """确保输出目录存在"""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
        return self.base_dir
    
    def save_results(self, results, timestamp=None):
        """
        保存结果到文件
        
        Args:
            results: 要保存的结果列表
            timestamp: 可选的时间戳，如果不提供则使用当前时间
            
        Returns:
            str: 保存的文件路径
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"{timestamp}.json"
        filepath = os.path.join(self.base_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'total_urls': len(results),
                'results': results
            }, f, ensure_ascii=False, indent=2)
        
        return filepath

class ResultCollector:
    """结果收集器，用于收集和保存网页内容"""
    
    def __init__(self):
        self.results = []
        self.lock = threading.Lock()
        self.file_handler = FileHandler()
    
    def add_result(self, url, content):
        with self.lock:
            self.results.append({
                'url': url,
                'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'content': content
            })
    
    def save_to_file(self):
        return self.file_handler.save_results(self.results)

def convert_to_absolute_url(base_url, relative_url):
    """将相对URL转换为绝对URL"""
    if not relative_url:
        return None
    if relative_url.startswith(('http://', 'https://')):
        return relative_url
    if relative_url.startswith('//'):
        return f'https:{relative_url}'
    if relative_url.startswith('/'):
        parsed_base = urlparse(base_url)
        return f"{parsed_base.scheme}://{parsed_base.netloc}{relative_url}"
    return urljoin(base_url, relative_url)

def extract_content(html, base_url):
    """从HTML中提取内容，包括文本、图片和链接"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # 提取所有文本，去除脚本和样式内容
    for script in soup(['script', 'style']):
        script.decompose()
    text = ' '.join(soup.stripped_strings)
    
    # 提取图片
    images = []
    for img in soup.find_all('img'):
        src = img.get('src')
        alt = img.get('alt', '')
        if src:
            absolute_src = convert_to_absolute_url(base_url, src)
            if absolute_src:
                images.append({
                    'url': absolute_src,
                    'alt': alt
                })
    
    # 提取链接
    links = []
    for a in soup.find_all('a'):
        href = a.get('href')
        link_text = a.get_text(strip=True)
        if href and link_text:
            absolute_href = convert_to_absolute_url(base_url, href)
            if absolute_href:
                links.append({
                    'url': absolute_href,
                    'text': link_text
                })
    
    return {
        'text': text,
        'images': images,
        'links': links
    }

def get_webpage_content(url):
    """获取网页内容的主函数"""
    try:
        with ChromeDriver() as driver:
            page_source, current_url = driver.get_page_content(url)
            content = extract_content(page_source, current_url)
            return content
    except Exception as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        raise

def process_single_url(url, collector):
    """处理单个URL并收集结果"""
    try:
        content = get_webpage_content(url)
        collector.add_result(url, content)
        return f"Successfully processed {url}"
    except Exception as e:
        return f"Failed to process {url}: {str(e)}"

def process_urls(urls, max_workers=5):
    """并发处理多个URL"""
    collector = ResultCollector()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(process_single_url, url, collector): url for url in urls}
        results = []
        
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
                print(result)
            except Exception as e:
                results.append(f"Error processing {url}: {str(e)}")
                print(f"Error processing {url}: {str(e)}", file=sys.stderr)
    
    output_file = collector.save_to_file()
    print(f"\nAll results saved to: {output_file}")
    return results

if __name__ == '__main__':
    """命令行入口函数"""
    parser = argparse.ArgumentParser(description='获取网页内容的命令行工具')
    parser.add_argument('urls', nargs='+', help='要访问的URL列表')
    parser.add_argument('--wait', type=float, default=2, help='每个页面加载等待时间（秒），默认2秒')
    parser.add_argument('--workers', type=int, default=5, help='最大并发数，默认5')
    args = parser.parse_args()
    
    process_urls(args.urls, max_workers=args.workers)