import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import UniqueConstraint

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:samlink@localhost:5432/sbpreport")

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True)
    salon_name = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    card_sales = Column(Float, nullable=False, default=0)  # Добавляем default
    sbp_sales = Column(Float, nullable=False, default=0)   # Добавляем default
    is_submitted = Column(Boolean, default=False)

    # Добавляем уникальное ограничение
    __table_args__ = (
        UniqueConstraint('salon_name', 'date', name='unique_salon_date'),
    )

    @classmethod
    def get_all_salons(cls, db: Session):
        """Получаем уникальные названия всех салонов"""
        salons = db.query(cls.salon_name).distinct().all()
        return [{"salon_name": salon[0]} for salon in salons]

    # Можно добавить:
    # - timestamp (автоматическое время внесения)
    # - user_id (кто внёс)


# Подключение к PostgreSQL
engine = create_engine(DATABASE_URL, echo=True)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)