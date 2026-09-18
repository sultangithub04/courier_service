from datetime import datetime
from pydantic import BaseModel, Field
from app.models.enums import ShipmentStatus, PaymentStatus


class ShipmentCreate(BaseModel):
    customer_id: int | None = None
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    origin: str
    destination: str
    package_type: str
    package_description: str | None = None
    weight: float = Field(ge=0)
    quantity: int = Field(default=1, ge=1)
    delivery_charge: float = Field(ge=0)
    cod_amount: float = Field(default=0, ge=0)
    estimated_delivery_date: datetime | None = None


class ShipmentUpdate(BaseModel):
    receiver_name: str | None = None
    receiver_phone: str | None = None
    receiver_address: str | None = None
    origin: str | None = None
    destination: str | None = None
    package_type: str | None = None
    package_description: str | None = None
    weight: float | None = Field(default=None, ge=0)
    quantity: int | None = Field(default=None, ge=1)
    delivery_charge: float | None = Field(default=None, ge=0)
    cod_amount: float | None = Field(default=None, ge=0)
    estimated_delivery_date: datetime | None = None
    shipment_status: ShipmentStatus | None = None


class ShipmentResponse(BaseModel):
    id: int
    tracking_number: str
    sender_id: int
    customer_id: int | None
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    origin: str
    destination: str
    package_type: str
    package_description: str | None
    weight: float
    quantity: int
    delivery_charge: float
    cod_amount: float
    payment_status: PaymentStatus
    shipment_status: ShipmentStatus
    delivery_agent_id: int | None
    estimated_delivery_date: datetime | None
    delivered_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrackingCreate(BaseModel):
    status: ShipmentStatus
    location: str | None = None
    description: str | None = None


class TrackingResponse(BaseModel):
    id: int
    shipment_id: int
    status: ShipmentStatus
    location: str | None
    description: str | None
    updated_by: int | None
    created_at: datetime

    class Config:
        from_attributes = True
