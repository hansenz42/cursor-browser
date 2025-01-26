import random
import time
from functools import wraps
from typing import Callable, Any

def retry_with_backoff(max_retries: int = 3, initial_delay: float = 1):
    """指数回退重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for retry_count in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if retry_count == max_retries:
                        print(f"达到最大重试次数 {max_retries}，操作失败")
                        raise last_exception
                    
                    # 计算下一次重试的延迟时间（指数回退 + 随机抖动）
                    jitter = random.uniform(0, 0.1 * delay)
                    wait_time = delay + jitter
                    print(f"操作失败: {str(e)}")
                    print(f"等待 {wait_time:.2f} 秒后进行第 {retry_count + 1} 次重试...")
                    time.sleep(wait_time)
                    delay *= 2  # 指数增长
                    
            return None
        return wrapper
    return decorator 