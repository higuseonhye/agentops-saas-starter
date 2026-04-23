from collections import defaultdict
from datetime import date, datetime, timedelta
from random import random

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import FailureCase, Membership, Organization, PerformanceSnapshot, UsageLog, User
from app.pricing import calculate_cost


def run_agent(query: str) -> tuple[str, int, int]:
    # Placeholder for real LLM call and response.usage.
    input_tokens = max(20, len(query.split()) * 8)
    output_tokens = int(input_tokens * 1.5)
    result = f"Processed: {query}"
    return result, input_tokens, output_tokens


def _resolve_range(days: int | None, start_date: str | None, end_date: str | None) -> tuple[date, date]:
    today = datetime.utcnow().date()
    if start_date and end_date:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
        if end < start:
            raise ValueError("end_date must be greater than or equal to start_date")
        return start, end
    resolved_days = days or 7
    if resolved_days < 1:
        raise ValueError("days must be positive")
    start = today - timedelta(days=resolved_days - 1)
    return start, today


def build_usage_summary(
    db: Session,
    org_id: str,
    days: int | None = 7,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    logs = db.query(UsageLog).filter(UsageLog.org_id == org_id).all()
    total_cost = round(sum(log.cost for log in logs), 6)
    total_requests = sum(log.requests for log in logs)
    total_tokens = sum((log.tokens_input + log.tokens_output) for log in logs)

    range_start, range_end = _resolve_range(days, start_date, end_date)
    day_count = (range_end - range_start).days + 1
    by_day = defaultdict(float)
    for log in logs:
        d = log.created_at.date()
        if range_start <= d <= range_end:
            by_day[d.isoformat()] += log.cost
    daily_cost = []
    labels = []
    running_total = 0.0
    cumulative_cost = []
    for i in range(day_count):
        key = (range_start + timedelta(days=i)).isoformat()
        labels.append(key)
        value = round(by_day.get(key, 0.0), 6)
        daily_cost.append(value)
        running_total = round(running_total + value, 6)
        cumulative_cost.append(running_total)

    period_cost = round(sum(daily_cost), 6)

    return {
        "total_cost": total_cost,
        "total_requests": total_requests,
        "total_tokens": total_tokens,
        "period_cost": period_cost,
        "labels": labels,
        "daily_cost": daily_cost,
        "cumulative_cost": cumulative_cost,
        "range": {
            "start_date": range_start.isoformat(),
            "end_date": range_end.isoformat(),
            "days": day_count,
        },
    }


def build_org_usage_comparison(
    db: Session,
    days: int | None = 7,
    start_date: str | None = None,
    end_date: str | None = None,
    org_ids: list[str] | None = None,
) -> dict:
    range_start, range_end = _resolve_range(days, start_date, end_date)
    query = db.query(Organization)
    if org_ids:
        query = query.filter(Organization.id.in_(org_ids))
    orgs = query.all()
    org_costs = []
    for org in orgs:
        total = (
            db.query(func.sum(UsageLog.cost))
            .filter(UsageLog.org_id == org.id)
            .filter(UsageLog.created_at >= datetime.combine(range_start, datetime.min.time()))
            .filter(UsageLog.created_at <= datetime.combine(range_end, datetime.max.time()))
            .scalar()
        )
        org_costs.append(
            {
                "org_id": org.id,
                "org_name": org.name,
                "cost": round(total or 0.0, 6),
            }
        )
    org_costs.sort(key=lambda x: x["cost"], reverse=True)

    return {
        "range": {
            "start_date": range_start.isoformat(),
            "end_date": range_end.isoformat(),
            "days": (range_end - range_start).days + 1,
        },
        "org_costs": org_costs,
    }


def resolve_org_id_for_user(db: Session, user: User, org_id: str | None) -> str:
    requested_org_id = org_id or user.org_id
    membership = (
        db.query(Membership)
        .filter(Membership.user_id == user.id, Membership.org_id == requested_org_id)
        .first()
    )
    if membership:
        return requested_org_id
    raise ValueError("You do not have access to this organization")


def list_user_orgs(db: Session, user: User) -> list[dict]:
    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    org_ids = [m.org_id for m in memberships]
    if not org_ids:
        return []
    orgs = db.query(Organization).filter(Organization.id.in_(org_ids)).all()
    role_by_org = {m.org_id: m.role for m in memberships}
    return [
        {
            "id": org.id,
            "name": org.name,
            "role": role_by_org.get(org.id, "member"),
        }
        for org in orgs
    ]


def latest_performance(db: Session, org_id: str) -> dict:
    snapshot = (
        db.query(PerformanceSnapshot)
        .filter(PerformanceSnapshot.org_id == org_id)
        .order_by(PerformanceSnapshot.created_at.desc())
        .first()
    )
    if not snapshot:
        snapshot = PerformanceSnapshot(
            org_id=org_id,
            accuracy=0.78,
            retrieval_error_rate=0.22,
            generation_error_rate=0.18,
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
    return {
        "accuracy": snapshot.accuracy,
        "retrieval": snapshot.retrieval_error_rate,
        "generation": snapshot.generation_error_rate,
    }


def build_performance_history(
    db: Session,
    org_id: str,
    days: int | None = 7,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    range_start, range_end = _resolve_range(days, start_date, end_date)
    end_dt = datetime.combine(range_end, datetime.max.time())
    start_dt = datetime.combine(range_start, datetime.min.time())

    snapshots = (
        db.query(PerformanceSnapshot)
        .filter(PerformanceSnapshot.org_id == org_id)
        .filter(PerformanceSnapshot.created_at <= end_dt)
        .order_by(PerformanceSnapshot.created_at.asc())
        .all()
    )

    if not snapshots:
        latest_performance(db, org_id)
        snapshots = (
            db.query(PerformanceSnapshot)
            .filter(PerformanceSnapshot.org_id == org_id)
            .filter(PerformanceSnapshot.created_at <= end_dt)
            .order_by(PerformanceSnapshot.created_at.asc())
            .all()
        )

    before_start = [s for s in snapshots if s.created_at < start_dt]
    if before_start:
        carry = before_start[-1]
    else:
        carry = snapshots[0]

    by_day: dict[str, list[PerformanceSnapshot]] = defaultdict(list)
    for snap in snapshots:
        if start_dt <= snap.created_at <= end_dt:
            by_day[snap.created_at.date().isoformat()].append(snap)

    labels: list[str] = []
    accuracy: list[float] = []
    retrieval: list[float] = []
    generation: list[float] = []
    day_count = (range_end - range_start).days + 1

    for i in range(day_count):
        d = range_start + timedelta(days=i)
        key = d.isoformat()
        labels.append(key)

        day_snaps = by_day.get(key, [])
        if day_snaps:
            acc = sum(x.accuracy for x in day_snaps) / len(day_snaps)
            ret = sum(x.retrieval_error_rate for x in day_snaps) / len(day_snaps)
            gen = sum(x.generation_error_rate for x in day_snaps) / len(day_snaps)
            carry = day_snaps[-1]
        else:
            acc = carry.accuracy
            ret = carry.retrieval_error_rate
            gen = carry.generation_error_rate

        accuracy.append(round(acc, 6))
        retrieval.append(round(ret, 6))
        generation.append(round(gen, 6))

    return {
        "range": {
            "start_date": range_start.isoformat(),
            "end_date": range_end.isoformat(),
            "days": day_count,
        },
        "labels": labels,
        "accuracy": accuracy,
        "retrieval": retrieval,
        "generation": generation,
    }


def ensure_seed_failure_cases(db: Session, org_id: str):
    existing = db.query(FailureCase).filter(FailureCase.org_id == org_id).count()
    if existing > 0:
        return
    db.add_all(
        [
            FailureCase(
                org_id=org_id,
                question="What is our refund policy?",
                answer="No refunds are offered.",
                ground_truth="Refunds are allowed within 14 days.",
                context="Policy doc v3 states 14-day refund window.",
            ),
            FailureCase(
                org_id=org_id,
                question="How to rotate API keys?",
                answer="You cannot rotate keys.",
                ground_truth="Users can rotate keys from settings.",
                context="Settings -> Security -> Rotate API Key",
            ),
        ]
    )
    db.commit()


def replay_failure(db: Session, failure_id: str) -> str | None:
    case = db.query(FailureCase).filter(FailureCase.id == failure_id).first()
    if not case:
        return None
    # Simulate improved answer after replay.
    improved = case.ground_truth
    case.answer = improved
    db.commit()
    return improved


def run_optimize(db: Session, org_id: str):
    current = latest_performance(db, org_id)
    improved_accuracy = min(0.99, current["accuracy"] + (0.02 + random() * 0.02))
    retrieval = max(0.01, current["retrieval"] - 0.02)
    generation = max(0.01, current["generation"] - 0.02)
    db.add(
        PerformanceSnapshot(
            org_id=org_id,
            accuracy=improved_accuracy,
            retrieval_error_rate=retrieval,
            generation_error_rate=generation,
        )
    )
    db.commit()


def can_consume(user: User) -> bool:
    if user.plan == "free":
        return True
    return user.balance > 0


def cost_for_usage(user: User, input_tokens: int, output_tokens: int) -> float:
    return calculate_cost(user.plan, input_tokens, output_tokens)
