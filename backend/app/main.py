from datetime import date
from typing import Optional

from fastapi import Body  # Добавляем импорт
from fastapi import FastAPI, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app import database

app = FastAPI()


# Pydantic модели для валидации
class ReportCreate(BaseModel):
    salon_name: str = Field(..., min_length=1, max_length=100)
    card_sales: float = Field(..., ge=0)
    sbp_sales: float = Field(..., ge=0)




class ReportUpdate(BaseModel):
    salon_name: Optional[str] = Field(None, min_length=0, max_length=100)
    card_sales: Optional[float] = Field(None, ge=0)
    sbp_sales: Optional[float] = Field(None, ge=0)
    is_submitted: Optional[bool] = None




class ReportResponse(BaseModel):
    id: int
    salon_name: str
    date: date
    card_sales: Optional[float] = 0  # Разрешаем None и устанавливаем значение по умолчанию
    sbp_sales: Optional[float] = 0   # Разрешаем None и устанавливаем значение по умолчанию
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

@app.get("/api/reports/today", response_model=list[ReportResponse])
def get_today_reports(db: Session = Depends(database.get_db)):
    try:
        # Получаем отчеты за сегодня
        today_reports = db.query(database.DailyReport) \
            .filter(database.DailyReport.date == date.today()) \
            .order_by(database.DailyReport.salon_name.asc()) \
            .all()

        return today_reports
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch today's reports: {str(e)}"
        )

@app.get("/api/salons/{id}", response_model=ReportResponse)
def get_all_salons(
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

@app.get("/api/salons")
def get_all_salons(db: Session = Depends(database.get_db)):
    try:
        # Получаем уникальные названия салонов
        salons = db.query(database.DailyReport.id, database.DailyReport.salon_name)\
               .distinct() \
               .order_by(database.DailyReport.salon_name.asc()) \
               .all()
        return [{"id": salon[0], "salon_name": salon[1]} for salon in salons]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка салонов: {str(e)}"
        )

@app.get("/api/unique-salons/")
def get_unique_salons(db: Session = Depends(database.get_db)):
    salons = db.query(database.DailyReport)\
               .distinct(database.DailyReport.salon_name)\
               .order_by(database.DailyReport.salon_name, database.DailyReport.id.desc())\
               .all()
    return salons

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
        # Получаем текущий отчет (без изменений)
        db_report = db.query(database.DailyReport).filter(database.DailyReport.id == id).first()
        if not db_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Салон не найден"
            )

        # Проверка дубликата (без изменений)
        if report_update.salon_name and report_update.salon_name != db_report.salon_name:
            existing_report = db.execute(
                select(database.DailyReport)
                .where(database.DailyReport.salon_name == report_update.salon_name)
                .where(database.DailyReport.date == date.today())
                .where(database.DailyReport.id != id)
            ).scalar_one_or_none()

            if existing_report:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Салон с таким названием и датой уже существует"
                )

        # Обновление полей (оптимизированная версия)
        update_data = report_update.model_dump(exclude_unset=True)

        # Добавим проверку на пустой update_data
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нет данных для обновления"
            )
        print(f"Обновляемые поля: {update_data}")
        for field, value in update_data.items():
            # Добавляем проверку на существование атрибута
            if hasattr(db_report, field):
                setattr(db_report, field, value)
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Поле {field} не существует в модели"
                )

        print("Текущие данные в БД:", db_report.__dict__)
        print("Данные для обновления:", update_data)

        db.commit()
        db.refresh(db_report)

        return db_report

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

