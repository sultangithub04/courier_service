from datetime import datetime,timezone
from math import ceil
from sqlalchemy import or_, asc, desc, func
from sqlalchemy.orm import Session
from app.models import Shipment,TrackingEvent,ShipmentStatus,User,Role
def next_tracking(db):
    year=datetime.now().year
    count=db.query(func.count(Shipment.id)).scalar() or 0
    return f"CR-{year}-{count+1:06d}"
SORTS={"created_at":Shipment.created_at,"updated_at":Shipment.updated_at,"tracking_number":Shipment.tracking_number,"delivery_charge":Shipment.delivery_charge,"weight":Shipment.weight,"receiver_name":Shipment.receiver_name}
def list_shipments(db,user,search,status,payment_status,city,delivery_agent_id,start_date,end_date,sort_by,sort_order,page,limit):
    q=db.query(Shipment)
    if user.role==Role.USER: q=q.filter(Shipment.sender_id==user.id)
    if user.role==Role.DELIVERY_AGENT:
        agent=user.delivery_agent
        q=q.filter(Shipment.delivery_agent_id==agent.id if agent else False)
    if search:
        term=f"%{search}%"; q=q.filter(or_(Shipment.tracking_number.ilike(term),Shipment.receiver_name.ilike(term),Shipment.receiver_phone.ilike(term),Shipment.destination.ilike(term),Shipment.origin.ilike(term)))
    if status:q=q.filter(Shipment.shipment_status==status)
    if payment_status:q=q.filter(Shipment.payment_status==payment_status)
    if city:q=q.filter(Shipment.destination.ilike(f"%{city}%"))
    if delivery_agent_id:q=q.filter(Shipment.delivery_agent_id==delivery_agent_id)
    if start_date:q=q.filter(Shipment.created_at>=start_date)
    if end_date:q=q.filter(Shipment.created_at<=end_date)
    col=SORTS.get(sort_by,Shipment.created_at); q=q.order_by(desc(col) if sort_order=="desc" else asc(col))
    total=q.count(); items=q.offset((page-1)*limit).limit(limit).all()
    return items,total,ceil(total/limit) if total else 0
def add_tracking(db,shipment,user,data):
    event=TrackingEvent(shipment_id=shipment.id,status=data.status,location=data.location,description=data.description,updated_by=user.id)
    shipment.shipment_status=data.status
    if data.status==ShipmentStatus.DELIVERED: shipment.delivered_at=datetime.now(timezone.utc)
    db.add(event); db.commit(); db.refresh(event); return event
