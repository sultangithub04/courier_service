from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import User, Role, UserStatus, DeliveryAgent, Customer


def main():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == "admin@example.com").first():
            db.add(
                User(
                    name="Admin",
                    email="admin@example.com",
                    password_hash=hash_password("Admin@123456"),
                    role=Role.ADMIN,
                    status=UserStatus.ACTIVE,
                )
            )
        if not db.query(User).filter(User.email == "user1@example.com").first():
            db.add(
                User(
                    name="Demo User",
                    email="user1@example.com",
                    password_hash=hash_password("User@123456"),
                    role=Role.USER,
                    status=UserStatus.ACTIVE,
                )
            )
        agent = db.query(User).filter(User.email == "delivery1@example.com").first()
        if not agent:
            agent = User(
                name="Demo Delivery",
                email="delivery1@example.com",
                password_hash=hash_password("Delivery@123456"),
                role=Role.DELIVERY_AGENT,
                status=UserStatus.ACTIVE,
            )
            db.add(agent)
            db.flush()
        if (
            not db.query(DeliveryAgent)
            .filter(DeliveryAgent.user_id == agent.id)
            .first()
        ):
            db.add(
                DeliveryAgent(
                    user_id=agent.id,
                    vehicle_type="Motorbike",
                    vehicle_number="DHK-DEMO-01",
                )
            )
        db.commit()
        print("Development seed completed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
