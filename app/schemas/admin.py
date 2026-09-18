from pydantic import BaseModel, EmailStr, Field
from app.models.enums import (
    Role,
    UserStatus,
    AvailabilityStatus,
    PaymentMethod,
    PaymentStatus,
    ShipmentStatus,
)


class UserAdminCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8)
    role: Role = Role.USER


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    role: Role | None = None
    status: UserStatus | None = None


class CustomerCreate(BaseModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    postal_code: str | None = None


class CustomerUpdate(CustomerCreate):
    pass


class DeliveryAgentCreate(BaseModel):
    user_id: int
    vehicle_type: str | None = None
    vehicle_number: str | None = None
    license_number: str | None = None
    availability_status: AvailabilityStatus = AvailabilityStatus.AVAILABLE


class DeliveryAgentUpdate(BaseModel):
    vehicle_type: str | None = None
    vehicle_number: str | None = None
    license_number: str | None = None
    availability_status: AvailabilityStatus | None = None


class AssignAgentRequest(BaseModel):
    delivery_agent_id: int


class StatusUpdateRequest(BaseModel):
    status: ShipmentStatus
    location: str | None = None
    description: str | None = None


class PaymentCreate(BaseModel):
    shipment_id: int
    amount: float = Field(gt=0)
    method: PaymentMethod
    status: PaymentStatus = PaymentStatus.PENDING
    transaction_id: str | None = None


class PaymentUpdate(BaseModel):
    status: PaymentStatus
    transaction_id: str | None = None
