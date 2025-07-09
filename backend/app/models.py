from datetime import date
from typing import Optional
from pydantic import BaseModel

class SalonCreate(BaseModel):
    salon_name: str

class SalonResponse(BaseModel):
    id: int
    salon_name: str

    class Config:
        from_attributes = True

class ReportCreate(BaseModel):
    id_salon: int
    date: date
    card_sales: float = 0
    sbp_sales: float = 0

class ReportResponse(BaseModel):
    id: int
    id_salon: int
    date: date
    card_sales: float
    sbp_sales: float

    class Config:
        from_attributes = True

class SalonCheck(BaseModel):
    salon_name: str

class DateRequest(BaseModel):
    date: Optional[date] = None