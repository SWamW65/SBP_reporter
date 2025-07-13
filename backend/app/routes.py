from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Path, status, Body
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db, Salon, Report
from models import (
    SalonCreate, SalonResponse, ReportCreate, ReportResponse,
    SalonCheck, DateRequest, SalonUpdate
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

@router.post("/salons/update/{id}", response_model=SalonResponse, status_code=status.HTTP_202_ACCEPTED)
def update_salon(
        id: int = Path(..., gt=0, description="The ID of the report to update"),
        salon_update: SalonUpdate = Body(...),
        db: Session = Depends(get_db)
):
    try:
        # Получаем текущий отчет (без изменений)
        db_salon = db.query(Salon).filter(Salon.id == id).first()
        if not db_salon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Салон не найден"
            )

        # Проверка дубликата (без изменений)
        if salon_update.salon_name and salon_update.salon_name != db_salon.salon_name:
            existing_report = db.execute(
                select(Salon)
                .where(Salon.salon_name == salon_update.salon_name)
                .where(Salon.id != id)
            ).scalar_one_or_none()

            if existing_report:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Салон с таким названием и датой уже существует"
                )

        # Обновление полей (оптимизированная версия)
        update_data = salon_update.model_dump(exclude_unset=True)

        # Добавим проверку на пустой update_data
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нет данных для обновления"
            )
        print(f"Обновляемые поля: {update_data}")
        for field, value in update_data.items():
            # Добавляем проверку на существование атрибута
            if hasattr(db_salon, field):
                setattr(db_salon, field, value)
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Поле {field} не существует в модели"
                )

        print("Текущие данные в БД:", db_salon.__dict__)
        print("Данные для обновления:", update_data)

        db.commit()
        db.refresh(db_salon)

        return db_salon

    except HTTPException:
        # Перехватываем только HTTPException чтобы не скрывать важные ошибки
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении салона: {str(e)}"
        )



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

