import time
from collections import defaultdict, deque
from fastapi import Request, HTTPException

_hits = defaultdict(deque)


def auth_rate_limit(request: Request):
    key = request.client.host if request.client else "unknown"
    now = time.time()
    q = _hits[key]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= 20:
        raise HTTPException(429, "Too many authentication requests. Try again later.")
    q.append(now)
