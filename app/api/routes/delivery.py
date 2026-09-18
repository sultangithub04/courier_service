from fastapi import APIRouter, HTTPException
from app.api.dependencies import Agent, DB
from app.models import Shipment, ShipmentStatus, TrackingEvent
from app.schemas.admin import StatusUpdateRequest
from app.services.shipment_service import list_shipments

router = APIRouter(prefix="/delivery", tags=["Delivery Agent"])


@router.get("/dashboard")
def dashboard(user: Agent, db: DB):
    aid = user.delivery_agent.id
    return {
        "success": True,
        "data": {
            "assigned": db.query(Shipment)
            .filter(Shipment.delivery_agent_id == aid)
            .count(),
            "pending": db.query(Shipment)
            .filter(
                Shipment.delivery_agent_id == aid,
                Shipment.shipment_status.in_(
                    [
                        ShipmentStatus.CONFIRMED,
                        ShipmentStatus.PICKED_UP,
                        ShipmentStatus.IN_TRANSIT,
                        ShipmentStatus.OUT_FOR_DELIVERY,
                    ]
                ),
            )
            .count(),
            "completed": db.query(Shipment)
            .filter(
                Shipment.delivery_agent_id == aid,
                Shipment.shipment_status == ShipmentStatus.DELIVERED,
            )
            .count(),
        },
    }


@router.get("/shipments")
def assigned(user: Agent, db: DB):
    return (
        db.query(Shipment)
        .filter(Shipment.delivery_agent_id == user.delivery_agent.id)
        .order_by(Shipment.created_at.desc())
        .all()
    )


@router.patch("/shipments/{id}/status")
def update(id: int, data: StatusUpdateRequest, user: Agent, db: DB):
    s = db.get(Shipment, id)
    if not s or s.delivery_agent_id != user.delivery_agent.id:
        raise HTTPException(404, "Assigned shipment not found")
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
    return {"success": True, "message": "Delivery status updated"}
