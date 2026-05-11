import time
from collections import defaultdict
from fastapi import HTTPException, status


class InMemoryRateLimiter:
    """
    단순 슬라이딩 윈도우 방식 인메모리 레이트 리미터.
    서버 재시작 시 초기화됨. 다중 프로세스 환경에서는 Redis로 교체 필요.
    """
    def __init__(self, max_calls: int, period_seconds: int, label: str = "요청"):
        self.max_calls = max_calls
        self.period = period_seconds
        self.label = label
        self._log: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        """제한 초과 시 HTTP 429 발생."""
        now = time.monotonic()
        window = self._log[key]
        self._log[key] = [t for t in window if now - t < self.period]
        if len(self._log[key]) >= self.max_calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"{self.label} 횟수가 너무 많습니다. "
                    f"{self.period}초 후 다시 시도해 주세요."
                ),
                headers={"Retry-After": str(self.period)},
            )
        self._log[key].append(now)


# 분석 요청: 사용자당 60초에 최대 10건
analysis_limiter = InMemoryRateLimiter(
    max_calls=10,
    period_seconds=60,
    label="AI 분석",
)

# 인증 요청: IP당 60초에 최대 20건
auth_limiter = InMemoryRateLimiter(
    max_calls=20,
    period_seconds=60,
    label="인증",
)
