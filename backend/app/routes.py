from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from database import get_db, Salon, Report
from models import (
    SalonCreate, SalonResponse, ReportCreate, ReportResponse,
    SalonCheck, DateRequest
)

router = APIRouter(prefix="/api")

# САЛОНЫ
@router.post("/salons/add", response_model=SalonResponse)
def add_salon(salon: SalonCreate, db: Session = Depends(get_db)):
    # Проверка на уникальность имени салона
    existing_salon = db.query(Salon).filter(Salon.salon_name == salon.salon_name).first()
    if existing_salon:
        raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Отчёт с таким названием и датой уже существует"
                )

    db_salon = Salon(salon_name=salon.salon_name)
    db.add(db_salon)
    db.commit()
    db.refresh(db_salon)
    return db_salon


@router.post("/salons/check")
def check_salon(salon: SalonCheck, db: Session = Depends(get_db)):
    exists = db.query(Salon).filter(Salon.salon_name == salon.salon_name).first() is not None
    return {"exists": exists}

@router.delete("/salons/remove/{id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_salon(
        id: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    try:
        db_report = db.query(Salon).get(id)
        if not db_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Салон не найден"
            )

        # Удаляем отчеты салона
        db.query(Report).filter(Report.id_salon == id).delete()
        # Удаляем сам салон
        db.query(Salon).filter(Salon.id == id).delete()
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка удаления салона: {str(e)}"
        )


@router.post("/salons/get")
def get_reports(db: Session = Depends(get_db)):

    salons = db.query(Salon).all()
    result = salons

    return result


# ОТЧЕТЫ
@router.post("/reports/get")
def get_reports(date_req: DateRequest = None, db: Session = Depends(get_db)):
    target_date = date_req.date if date_req and date_req.date else date.today()

    salons = db.query(Salon).all()
    result = []

    for salon in salons:
        report = db.query(Report).filter(
            Report.id_salon == salon.id,
            Report.date == target_date
        ).first()

        if report:
            result.append({
                "id": report.id,
                "salon_id": salon.id,
                "salon_name": salon.salon_name,
                "date": report.date,
                "card_sales": report.card_sales,
                "sbp_sales": report.sbp_sales
            })
        else:
            result.append({
                "id": report.id,
                "salon_id": salon.id,
                "salon_name": salon.salon_name,
                "date": target_date,
                "card_sales": 0,
                "sbp_sales": 0
            })

    return result


@router.post("/reports/update", response_model=ReportResponse)
def update_report(report: ReportCreate, db: Session = Depends(get_db)):
    # Проверяем существование салона
    salon = db.query(Salon).filter(Salon.id == report.id_salon).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Ищем существующий отчет
    existing_report = db.query(Report).filter(
        Report.id_salon == report.id_salon,
        Report.date == report.date
    ).first()

    if existing_report:
        # Обновляем существующий отчет
        existing_report.card_sales = report.card_sales
        existing_report.sbp_sales = report.sbp_sales
    else:
        # Создаем новый отчет
        existing_report = Report(**report.dict())
        db.add(existing_report)

    db.commit()
    db.refresh(existing_report)
    return existing_report

