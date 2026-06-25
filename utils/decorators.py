import functools
import time
from typing import Callable, Any, Tuple, Type
from loguru import logger


def handle_errors(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            logger.error(f"文件未找到错误: {e}")
            print(f"❌ 错误：文件未找到 - {e}")
            return None
        except ConnectionError as e:
            logger.error(f"网络连接错误: {e}")
            print(f"❌ 错误：网络连接失败 - {e}")
            return None
        except TimeoutError as e:
            logger.error(f"请求超时错误: {e}")
            print(f"❌ 错误：请求超时 - {e}")
            return None
        except Exception as e:
            logger.error(f"未知错误: {e}", exc_info=True)
            print(f"❌ 发生未知错误: {e}")
            return None

    return wrapper


def retry(max_attempts: int = 3, delay: float = 2.0, exceptions: Tuple[Type[Exception], ...] = (Exception,)) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        break
                    logger.warning(f"第{attempt + 1}次尝试失败，{delay}秒后重试...")
                    time.sleep(delay)

            if last_exception:
                logger.error(f"所有{max_attempts}次尝试均失败: {last_exception}")
                print(f"❌ 所有{max_attempts}次尝试均失败")
                raise last_exception

            return None

        return wrapper

    return decorator


def log_function_call(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        logger.info(f"调用函数: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"函数 {func.__name__} 执行成功")
            return result
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败: {e}", exc_info=True)
            raise

    return wrapper


def log_execution_time(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"函数 {func.__name__} 执行耗时: {execution_time:.2f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"函数 {func.__name__} 执行失败，耗时: {execution_time:.2f}秒: {e}")
            raise

    return wrapper