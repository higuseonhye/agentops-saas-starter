from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.db import SessionLocal
from app.models import UsageLog, User


class UsageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        usage = getattr(request.state, "usage", None)
        user_id = getattr(request.state, "user_id", None)
        org_id = getattr(request.state, "org_id", None)

        if usage and user_id and org_id:
            db = SessionLocal()
            try:
                # append-only usage event
                usage_log = UsageLog(
                    user_id=user_id,
                    org_id=org_id,
                    endpoint=request.url.path,
                    requests=1,
                    tokens_input=usage["input"],
                    tokens_output=usage["output"],
                    cost=usage["cost"],
                )
                db.add(usage_log)

                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    user.balance = max(0.0, user.balance - usage["cost"])
                db.commit()
            finally:
                db.close()

        return response
