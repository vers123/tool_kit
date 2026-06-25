import sys
import time
from typing import Optional


class ProgressBar:
    def __init__(self, total: int, desc: str = "处理中", bar_length: int = 40):
        self.total = total
        self.desc = desc
        self.bar_length = bar_length
        self.current = 0
        self.start_time = time.time()
        self._last_update = 0
        self._update_interval = 0.1

    def update(self, n: int = 1) -> None:
        self.current += n

        current_time = time.time()
        if current_time - self._last_update < self._update_interval:
            return

        self._last_update = current_time
        elapsed = current_time - self.start_time

        if self.total > 0:
            percent = min(100.0, self.current / self.total * 100)
            filled = int(self.bar_length * self.current / self.total)
            bar = '█' * filled + '░' * (self.bar_length - filled)

            if self.current > 0:
                eta = elapsed * (self.total - self.current) / self.current
                eta_str = f"预计剩余: {eta:.1f}s"
            else:
                eta_str = "预计剩余: 计算中..."

            sys.stdout.write(
                f'\r{self.desc}: |{bar}| {percent:.1f}% '
                f'({self.current}/{self.total}) 耗时: {elapsed:.1f}s {eta_str}'
            )
        else:
            sys.stdout.write(f'\r{self.desc}: 已处理 {self.current} 项，耗时: {elapsed:.1f}s')

        sys.stdout.flush()

    def close(self) -> None:
        elapsed = time.time() - self.start_time
        sys.stdout.write(f'\r{self.desc}: 完成！共处理 {self.current} 项，总耗时: {elapsed:.1f}s\n')
        sys.stdout.flush()


def create_progress_bar(total: int, desc: str = "处理中") -> ProgressBar:
    return ProgressBar(total, desc)


def track_progress(iterable, desc: str = "处理中", total: Optional[int] = None):
    if total is None:
        try:
            total = len(iterable)
        except TypeError:
            total = None

    progress = ProgressBar(total if total is not None else 0, desc)

    for item in iterable:
        yield item
        progress.update(1)

    progress.close()