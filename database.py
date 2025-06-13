from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import UniqueConstraint



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
    card_sales = Column(Float, nullable=False)
    sbp_sales = Column(Float, nullable=False)
    is_submitted = Column(Boolean, default=False)

    # Добавляем уникальное ограничение
    __table_args__ = (
        UniqueConstraint('salon_name', 'date', name='unique_salon_date'),
    )

    # Можно добавить:
    # - timestamp (автоматическое время внесения)
    # - user_id (кто внёс)


# Подключение к PostgreSQL
engine = create_engine('postgresql://postgres:samlink@localhost:5432/sbpreport', echo=True)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)