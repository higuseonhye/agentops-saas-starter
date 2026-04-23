import secrets

from app.db import Base, SessionLocal, engine
from app.models import Membership, Organization, User


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.name == "Demo Org").first()
        if not org:
            org = Organization(name="Demo Org")
            db.add(org)
            db.commit()
            db.refresh(org)

        user = db.query(User).filter(User.email == "demo@agentops.dev").first()
        if not user:
            user = User(
                email="demo@agentops.dev",
                api_key=secrets.token_urlsafe(24),
                plan="pro",
                balance=50.0,
                org_id=org.id,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        member = (
            db.query(Membership)
            .filter(Membership.user_id == user.id, Membership.org_id == org.id)
            .first()
        )
        if not member:
            db.add(Membership(user_id=user.id, org_id=org.id, role="owner"))
            db.commit()

        print(f"Demo API Key: {user.api_key}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
