#!/usr/bin/env python3
import sys
import json
import os
import time
from datetime import datetime
from duckduckgo_search import DDGS
from requests.exceptions import RequestException

class DuckDuckGoSearcher:
    def __init__(self, output_dir='cache/search_results'):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def search(self, query, max_retries=3, retry_delay=5):
        for attempt in range(max_retries):
            try:
                with DDGS() as ddgs:
                    if attempt > 0:
                        print(f"Retry attempt {attempt + 1}/{max_retries}, waiting {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    
                    try:
                        results = list(ddgs.text(query, max_results=10))
                    except Exception as e:
                        if "rate limit" in str(e).lower():
                            print(f"Rate limit hit, waiting longer ({retry_delay * 2} seconds) before retry...")
                            time.sleep(retry_delay * 2)
                            continue
                        raise e
                
                if not results:
                    return json.dumps({"error": "No results found."})
                
                formatted_results = {
                    "query": query,
                    "results": [
                        {
                            "title": result.get("title", ""),
                            "link": result.get("href", ""),
                            "snippet": result.get("body", "")
                        }
                        for result in results
                    ]
                }
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{self.output_dir}/{timestamp}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(formatted_results, f, ensure_ascii=False, indent=2)
                
                print(f"Search results saved to: {filename}")
                return
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    print(json.dumps({"error": f"Failed after {max_retries} attempts. Last error: {str(e)}"}))
                else:
                    print(f"Error occurred: {str(e)}")
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 search.py <query>")
        sys.exit(1)
    
    searcher = DuckDuckGoSearcher()
    searcher.search(sys.argv[1])
