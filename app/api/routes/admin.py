from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, or_, desc
from app.api.dependencies import DB, Admin
from app.core.security import hash_password
from app.models import *
from app.schemas.admin import *

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
def dashboard(user: Admin, db: DB):
    def count(q):
        return q.scalar() or 0

    return {
        "success": True,
        "data": {
            "users": count(db.query(func.count(User.id))),
            "customers": count(db.query(func.count(Customer.id))),
            "shipments": count(db.query(func.count(Shipment.id))),
            "pending": count(
                db.query(func.count(Shipment.id)).filter(
                    Shipment.shipment_status == ShipmentStatus.PENDING
                )
            ),
            "in_transit": count(
                db.query(func.count(Shipment.id)).filter(
                    Shipment.shipment_status == ShipmentStatus.IN_TRANSIT
                )
            ),
            "out_for_delivery": count(
                db.query(func.count(Shipment.id)).filter(
                    Shipment.shipment_status == ShipmentStatus.OUT_FOR_DELIVERY
                )
            ),
            "delivered": count(
                db.query(func.count(Shipment.id)).filter(
                    Shipment.shipment_status == ShipmentStatus.DELIVERED
                )
            ),
            "cancelled": count(
                db.query(func.count(Shipment.id)).filter(
                    Shipment.shipment_status == ShipmentStatus.CANCELLED
                )
            ),
            "revenue": float(
                db.query(func.coalesce(func.sum(Payment.amount), 0))
                .filter(Payment.status == PaymentStatus.PAID)
                .scalar()
                or 0
            ),
        },
    }


@router.get("/users")
def users(
    user: Admin,
    db: DB,
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    q = db.query(User)
    if search:
        t = f"%{search}%"
        q = q.filter(or_(User.name.ilike(t), User.email.ilike(t), User.phone.ilike(t)))
    total = q.count()
    items = (
        q.order_by(desc(User.created_at)).offset((page - 1) * limit).limit(limit).all()
    )
    return {
        "success": True,
        "data": [
            {
                "id": x.id,
                "name": x.name,
                "email": x.email,
                "phone": x.phone,
                "role": x.role,
                "status": x.status,
                "created_at": x.created_at,
            }
            for x in items
        ],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
        },
    }


@router.post("/users", status_code=201)
def create_user(data: UserAdminCreate, user: Admin, db: DB):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(409, "Email already exists")
    u = User(
        name=data.name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return {
        "success": True,
        "message": "User created",
        "data": {"id": u.id, "email": u.email, "role": u.role},
    }


@router.patch("/users/{id}")
def update_user(id: int, data: UserUpdate, user: Admin, db: DB):
    u = db.get(User, id)
    if not u:
        raise HTTPException(404, "User not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(u, k, v)
    db.commit()
    return {"success": True, "message": "User updated"}


@router.delete("/users/{id}")
def delete_user(id: int, user: Admin, db: DB):
    if id == user.id:
        raise HTTPException(400, "You cannot delete yourself")
    u = db.get(User, id)
    if not u:
        raise HTTPException(404, "User not found")
    db.delete(u)
    db.commit()
    return {"success": True, "message": "User deleted"}


@router.get("/customers")
def customers(
    user: Admin,
    db: DB,
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    q = db.query(Customer)
    if search:
        q = q.filter(
            or_(
                Customer.name.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%"),
                Customer.phone.ilike(f"%{search}%"),
            )
        )
    total = q.count()
    items = q.offset((page - 1) * limit).limit(limit).all()
    return {
        "success": True,
        "data": items,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
        },
    }


@router.post("/customers", status_code=201)
def create_customer(data: CustomerCreate, user: Admin, db: DB):
    c = Customer(**data.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.patch("/customers/{id}")
def update_customer(id: int, data: CustomerUpdate, user: Admin, db: DB):
    c = db.get(Customer, id)
    if not c:
        raise HTTPException(404, "Customer not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    return c


@router.delete("/customers/{id}")
def delete_customer(id: int, user: Admin, db: DB):
    c = db.get(Customer, id)
    if not c:
        raise HTTPException(404, "Customer not found")
    db.delete(c)
    db.commit()
    return {"success": True, "message": "Customer deleted"}


@router.get("/delivery-agents")
def agents(user: Admin, db: DB):
    return db.query(DeliveryAgent).all()


@router.post("/delivery-agents", status_code=201)
def create_agent(data: DeliveryAgentCreate, user: Admin, db: DB):
    u = db.get(User, data.user_id)
    if not u or u.role != Role.DELIVERY_AGENT:
        raise HTTPException(400, "User must have DELIVERY_AGENT role")
    if db.query(DeliveryAgent).filter(DeliveryAgent.user_id == u.id).first():
        raise HTTPException(409, "Agent already exists")
    a = DeliveryAgent(**data.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.patch("/delivery-agents/{id}")
def update_agent(id: int, data: DeliveryAgentUpdate, user: Admin, db: DB):
    a = db.get(DeliveryAgent, id)
    if not a:
        raise HTTPException(404, "Delivery agent not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    db.commit()
    return a


@router.delete("/delivery-agents/{id}")
def delete_agent(id: int, user: Admin, db: DB):
    a = db.get(DeliveryAgent, id)
    if not a:
        raise HTTPException(404, "Delivery agent not found")
    db.delete(a)
    db.commit()
    return {"success": True, "message": "Delivery agent deleted"}


@router.patch("/shipments/{id}/assign")
def assign(id: int, data: AssignAgentRequest, user: Admin, db: DB):
    s = db.get(Shipment, id)
    a = db.get(DeliveryAgent, data.delivery_agent_id)
    if not s or not a:
        raise HTTPException(404, "Shipment or delivery agent not found")
    s.delivery_agent_id = a.id
    a.availability_status = AvailabilityStatus.BUSY
    db.commit()
    return {"success": True, "message": "Delivery agent assigned"}


@router.patch("/shipments/{id}/status")
def status_update(id: int, data: StatusUpdateRequest, user: Admin, db: DB):
    s = db.get(Shipment, id)
    if not s:
        raise HTTPException(404, "Shipment not found")
    s.shipment_status = data.status
    if data.status == ShipmentStatus.DELIVERED:
        s.delivered_at = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        )
    db.add(
        TrackingEvent(
            shipment_id=s.id,
            status=data.status,
            location=data.location,
            description=data.description,
            updated_by=user.id,
        )
    )
    db.commit()
    return {"success": True, "message": "Shipment status updated"}


@router.get("/payments")
def payments(
    user: Admin,
    db: DB,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    q = db.query(Payment).order_by(desc(Payment.created_at))
    total = q.count()
    items = q.offset((page - 1) * limit).limit(limit).all()
    return {
        "success": True,
        "data": items,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
        },
    }


@router.post("/payments", status_code=201)
def create_payment(data: PaymentCreate, user: Admin, db: DB):
    if not db.get(Shipment, data.shipment_id):
        raise HTTPException(404, "Shipment not found")
    p = Payment(**data.model_dump())
    db.add(p)
    if p.status == PaymentStatus.PAID:
        p.paid_at = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        )
    db.commit()
    db.refresh(p)
    return p


@router.patch("/payments/{id}")
def update_payment(id: int, data: PaymentUpdate, user: Admin, db: DB):
    p = db.get(Payment, id)
    if not p:
        raise HTTPException(404, "Payment not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    if p.status == PaymentStatus.PAID and not p.paid_at:
        p.paid_at = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        )
    db.commit()
    return p
