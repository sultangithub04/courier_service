
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import DB, CurrentUser, Admin, Agent
from app.models import *
from app.schemas.shipment import *
from app.schemas.common import ListResponse
from app.services.shipment_service import (
    next_tracking,
    list_shipments,
    add_tracking,
)

router = APIRouter(prefix="/shipments", tags=["Shipments"])


# ============================================================
# CREATE SHIPMENT
# ============================================================

@router.post(
    "",
    response_model=ShipmentResponse,
    status_code=201,
)
def create(
    data: ShipmentCreate,
    user: CurrentUser,
    db: DB,
):
    s = Shipment(
        tracking_number=next_tracking(db),
        sender_id=user.id,
        **data.model_dump(),
    )

    db.add(s)
    db.commit()
    db.refresh(s)

    add_tracking(
        db,
        s,
        user,
        TrackingCreate(
            status=ShipmentStatus.PENDING,
            description="Shipment created",
        ),
    )

    return s


# ============================================================
# LIST SHIPMENTS
# ============================================================

@router.get(
    "",
    response_model=ListResponse,
)
def listing(
    user: CurrentUser,
    db: DB,
    search: str | None = None,
    status: ShipmentStatus | None = None,
    payment_status: PaymentStatus | None = None,
    city: str | None = None,
    delivery_agent_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    # Validate sort order
    if sort_order not in ("asc", "desc"):
        raise HTTPException(
            status_code=400,
            detail="sort_order must be asc or desc",
        )

    # Get shipments from service
    items, total, pages = list_shipments(
        db,
        user,
        search,
        status,
        payment_status,
        city,
        delivery_agent_id,
        start_date,
        end_date,
        sort_by,
        sort_order,
        page,
        limit,
    )

    # IMPORTANT:
    # Convert SQLAlchemy Shipment objects
    # into Pydantic ShipmentResponse objects.
    shipment_data = [
        ShipmentResponse.model_validate(item)
        for item in items
    ]

    return {
        "success": True,
        "data": shipment_data,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": pages,
        },
    }


# ============================================================
# GET OWNED SHIPMENT
# ============================================================

def get_owned(
    db,
    user,
    id: int,
):
    s = db.get(Shipment, id)

    if not s:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found",
        )

    # Normal USER can only access own shipments
    if user.role == Role.USER and s.sender_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot access this shipment",
        )

    # DELIVERY_AGENT can only access assigned shipments
    if user.role == Role.DELIVERY_AGENT and (
        not user.delivery_agent
        or s.delivery_agent_id != user.delivery_agent.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You cannot access this shipment",
        )

    return s


# ============================================================
# GET SINGLE SHIPMENT
# ============================================================

@router.get(
    "/{id}",
    response_model=ShipmentResponse,
)
def get_one(
    id: int,
    user: CurrentUser,
    db: DB,
):
    return get_owned(db, user, id)


# ============================================================
# UPDATE SHIPMENT
# ============================================================

@router.patch(
    "/{id}",
    response_model=ShipmentResponse,
)
def update(
    id: int,
    data: ShipmentUpdate,
    user: CurrentUser,
    db: DB,
):
    s = get_owned(
        db,
        user,
        id,
    )

    # Only ADMIN and USER can update
    if user.role not in (
        Role.ADMIN,
        Role.USER,
    ):
        raise HTTPException(
            status_code=403,
            detail="Not permitted",
        )

    # USER cannot directly change shipment status
    if (
        user.role == Role.USER
        and data.shipment_status is not None
    ):
        raise HTTPException(
            status_code=403,
            detail="Users cannot directly change shipment status",
        )

    # Update only provided fields
    for key, value in data.model_dump(
        exclude_unset=True
    ).items():
        setattr(
            s,
            key,
            value,
        )

    db.commit()
    db.refresh(s)

    return s


# ============================================================
# DELETE SHIPMENT
# ============================================================

@router.delete(
    "/{id}",
)
def delete(
    id: int,
    user: Admin,
    db: DB,
):
    s = db.get(
        Shipment,
        id,
    )

    if not s:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found",
        )

    db.delete(s)
    db.commit()

    return {
        "success": True,
        "message": "Shipment deleted",
    }


# ============================================================
# GET SHIPMENT TRACKING
# ============================================================

@router.get(
    "/{id}/tracking",
    response_model=list[TrackingResponse],
)
def tracking(
    id: int,
    user: CurrentUser,
    db: DB,
):
    s = get_owned(
        db,
        user,
        id,
    )

    return (
        db.query(TrackingEvent)
        .filter(
            TrackingEvent.shipment_id == s.id
        )
        .order_by(
            TrackingEvent.created_at.asc()
        )
        .all()
    )


# ============================================================
# ADD TRACKING EVENT
# ============================================================

@router.post(
    "/{id}/tracking",
    response_model=TrackingResponse,
    status_code=201,
)
def add(
    id: int,
    data: TrackingCreate,
    user: CurrentUser,
    db: DB,
):
    # USER cannot add tracking events
    if user.role == Role.USER:
        raise HTTPException(
            status_code=403,
            detail="Users cannot add tracking events",
        )

    s = get_owned(
        db,
        user,
        id,
    )

    return add_tracking(
        db,
        s,
        user,
        data,
    )

