import stripe
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.db import Base, engine, get_db
from app.middleware import UsageMiddleware
from app.models import FailureCase, UsageLog, User
from app.schemas import QueryRequest, ReplayRequest
from app.services import (
    build_usage_summary,
    build_performance_history,
    build_org_usage_comparison,
    can_consume,
    cost_for_usage,
    ensure_seed_failure_cases,
    latest_performance,
    list_user_orgs,
    replay_failure,
    resolve_org_id_for_user,
    run_agent,
    run_optimize,
)

app = FastAPI(title="AgentOps API")
app.add_middleware(UsageMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stripe.api_key = settings.stripe_secret_key
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/query")
def query_agent(
    payload: QueryRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    if not can_consume(user):
        raise HTTPException(status_code=402, detail="Out of credits")

    result, input_tokens, output_tokens = run_agent(payload.q)
    cost = cost_for_usage(user, input_tokens, output_tokens)

    request.state.user_id = user.id
    request.state.org_id = user.org_id
    request.state.usage = {"input": input_tokens, "output": output_tokens, "cost": cost}

    return {"result": result, "usage": request.state.usage}


@app.get("/usage")
def usage(
    days: int | None = 7,
    start_date: str | None = None,
    end_date: str | None = None,
    org_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        resolved_org_id = resolve_org_id_for_user(db=db, user=user, org_id=org_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    try:
        return build_usage_summary(
            db=db,
            org_id=resolved_org_id,
            days=days,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/usage/compare")
def usage_compare(
    days: int | None = 7,
    start_date: str | None = None,
    end_date: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed_org_ids = [org["id"] for org in list_user_orgs(db, user)]
    try:
        return build_org_usage_comparison(
            db=db,
            days=days,
            start_date=start_date,
            end_date=end_date,
            org_ids=allowed_org_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/performance")
def performance(
    org_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    try:
        resolved_org_id = resolve_org_id_for_user(db=db, user=user, org_id=org_id)
        return latest_performance(db, resolved_org_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.get("/performance/history")
def performance_history(
    days: int | None = 7,
    start_date: str | None = None,
    end_date: str | None = None,
    org_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        resolved_org_id = resolve_org_id_for_user(db=db, user=user, org_id=org_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    try:
        return build_performance_history(
            db=db,
            org_id=resolved_org_id,
            days=days,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/failures")
def failures(org_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        resolved_org_id = resolve_org_id_for_user(db=db, user=user, org_id=org_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    ensure_seed_failure_cases(db, resolved_org_id)
    rows = (
        db.query(FailureCase)
        .filter(FailureCase.org_id == resolved_org_id)
        .order_by(FailureCase.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": row.id,
            "question": row.question,
            "answer": row.answer,
            "ground_truth": row.ground_truth,
            "context": row.context,
        }
        for row in rows
    ]


@app.post("/replay")
def replay(
    payload: ReplayRequest,
    org_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        resolved_org_id = resolve_org_id_for_user(db=db, user=user, org_id=org_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    row = (
        db.query(FailureCase)
        .filter(FailureCase.id == payload.id, FailureCase.org_id == resolved_org_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Failure case not found")
    answer = replay_failure(db, payload.id)
    return {"id": payload.id, "answer": answer}


@app.post("/optimize")
def optimize(org_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        resolved_org_id = resolve_org_id_for_user(db=db, user=user, org_id=org_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    run_optimize(db, resolved_org_id)
    return {"status": "started"}


@app.get("/config")
def config():
    return {
        "alert_accuracy_threshold": settings.alert_accuracy_threshold,
        "alert_daily_cost_threshold": settings.alert_daily_cost_threshold,
        "billing_model": {
            "free": "100 req/mo",
            "pro": "$0.002/req + token usage",
            "team": "monthly + usage",
        },
    }


@app.post("/billing/checkout")
def create_checkout(user: User = Depends(get_current_user)):
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=400, detail="Stripe key is not configured")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": "AgentOps Credits"},
                    "unit_amount": 1000,
                },
                "quantity": 1,
            }
        ],
        success_url="http://localhost:3000/success",
        cancel_url="http://localhost:3000/cancel",
        metadata={"user_id": user.id},
    )
    return {"url": session.url}


@app.post("/billing/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=400, detail="Webhook secret is not configured")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid webhook: {exc}") from exc

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.balance += settings.default_credit_on_payment
            db.commit()
    return {"received": True}


@app.get("/org/usage")
def org_usage(org_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        resolved_org_id = resolve_org_id_for_user(db=db, user=user, org_id=org_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    total = (
        db.query(func.sum(UsageLog.cost))
        .filter(UsageLog.org_id == resolved_org_id)
        .scalar()
    )
    return {"org_id": resolved_org_id, "monthly_cost": round(total or 0.0, 6)}


@app.get("/orgs")
def orgs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"orgs": list_user_orgs(db, user)}
