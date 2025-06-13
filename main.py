from datetime import date
from fastapi import FastAPI, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from typing import Optional
import database
from pydantic import BaseModel, Field, validator
from fastapi import Body  # Добавляем импорт

app = FastAPI()


# Pydantic модели для валидации
class ReportCreate(BaseModel):
    salon_name: str = Field(..., min_length=1, max_length=100)
    card_sales: float = Field(..., ge=0)
    sbp_sales: float = Field(..., ge=0)

    @validator('salon_name')
    def validate_salon_name(cls, v):
        if not v.strip():
            raise ValueError("Salon name cannot be empty")
        return v.strip()


class ReportUpdate(BaseModel):
    salon_name: Optional[str] = Field(None, min_length=1, max_length=100)
    card_sales: Optional[float] = Field(None, ge=0)
    sbp_sales: Optional[float] = Field(None, ge=0)
    is_submitted: Optional[bool] = None

    @validator('salon_name')
    def validate_salon_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Salon name cannot be empty")
        return v.strip() if v else v


class ReportResponse(BaseModel):
    id: int
    salon_name: str
    date: date
    card_sales: float
    sbp_sales: float
    is_submitted: bool

    class Config:
        orm_mode = True


@app.post("/api/reports/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
        report: ReportCreate,
        db: Session = Depends(database.get_db)
):
    # Проверяем дубликат
    existing_report = db.query(database.DailyReport).filter(
        database.DailyReport.salon_name == report.salon_name,
        database.DailyReport.date == date.today()
    ).first()

    if existing_report:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Отчёт с таким названием и датой уже существует"
        )

    # Создаём новый отчёт
    new_report = database.DailyReport(
        salon_name=report.salon_name,
        date=date.today(),
        card_sales=report.card_sales,
        sbp_sales=report.sbp_sales,
        is_submitted=False
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report


@app.get("/api/reports/", response_model=list[ReportResponse])
def get_reports(db: Session = Depends(database.get_db)):
    try:
        return db.query(database.DailyReport).order_by(database.DailyReport.date.desc()).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch reports: {str(e)}"
        )


@app.get("/api/reports/{id}", response_model=ReportResponse)
def get_report(
        id: int = Path(..., gt=0, description="The ID of the report to get"),
        db: Session = Depends(database.get_db)
):
    report = db.query(database.DailyReport).get(id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Салон не найден"
        )
    return report



@app.delete("/api/reports/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
        id: int = Path(..., gt=0),
        db: Session = Depends(database.get_db)
):
    try:
        db_report = db.query(database.DailyReport).get(id)
        if not db_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Салон не найден"
            )

        db.delete(db_report)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка удаления салона: {str(e)}"
        )


@app.put("/api/reports/{id}", response_model=ReportResponse, status_code=status.HTTP_202_ACCEPTED)
def update_report(
        id: int = Path(..., gt=0, description="The ID of the report to update"),
        report_update: ReportUpdate = Body(...),
        db: Session = Depends(database.get_db)
):
    try:
        # Получаем текущий отчет
        db_report = db.query(database.DailyReport).filter(database.DailyReport.id == id).first()
        if not db_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Салон не найден"
            )

        # Проверяем дубликат только если изменилось имя салона
        if report_update.salon_name and report_update.salon_name != db_report.salon_name:
            existing_report = db.query(database.DailyReport).filter(
                database.DailyReport.salon_name == report_update.salon_name,
                database.DailyReport.date == date.today(),
                database.DailyReport.id != id  # Исключаем текущую запись из проверки
            ).first()

            if existing_report:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Салон с таким названием и датой уже существует"
                )

        # Обновляем только те поля, которые были переданы
        for field, value in report_update.dict(exclude_unset=True).items():
            setattr(db_report, field, value)

        db.commit()
        db.refresh(db_report)

        return db_report
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении салона: {str(e)}"
        )