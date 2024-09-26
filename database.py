import os
from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, Float, ForeignKey, DateTime, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logger = logging.getLogger(__name__)

engine = create_engine('sqlite:///laptime_tracker.db')
Base = declarative_base()

class Race(Base):
    __tablename__ = 'races'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    date = Column(Date)
    archived = Column(Boolean, default=False)
    drivers = relationship("Driver", back_populates="race", cascade="all, delete-orphan")

class LapTime(Base):
    __tablename__ = 'lap_times'

    id = Column(Integer, primary_key=True)
    race_id = Column(Integer, ForeignKey('races.id'))
    car_number = Column(Integer)
    lap = Column(Integer)
    time = Column(Float)
    driver_id = Column(Integer, ForeignKey('drivers.id'), nullable=True)

class Position(Base):
    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True)
    race_id = Column(Integer, ForeignKey('races.id'))
    car_number = Column(Integer)
    position = Column(Integer)
    timestamp = Column(DateTime)

class Admin(Base):
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

class Driver(Base):
    __tablename__ = 'drivers'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    car_number = Column(Integer, nullable=False)
    race_id = Column(Integer, ForeignKey('races.id'), nullable=False)
    race = relationship("Race", back_populates="drivers")

class DriverChange(Base):
    __tablename__ = 'driver_changes'
    id = Column(Integer, primary_key=True)
    race_id = Column(Integer, ForeignKey('races.id'), nullable=False)
    car_number = Column(Integer, nullable=False)
    driver_id = Column(Integer, ForeignKey('drivers.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)

def migrate_database():
    engine = create_engine('sqlite:///laptime_tracker.db')
    inspector = inspect(engine)
    with engine.connect() as connection:
        if 'driver_id' not in inspector.get_columns('lap_times'):
            connection.execute(text("ALTER TABLE lap_times ADD COLUMN driver_id INTEGER"))
    
    Base.metadata.create_all(engine)

def init_db():
    logger.info("Initializing database...")
    Base.metadata.create_all(engine)
    migrate_database()
    logger.info("Database initialized and migrated")

Session = sessionmaker(bind=engine)

def create_race(name, date):
    session = Session()
    new_race = Race(name=name, date=date)
    session.add(new_race)
    session.commit()
    race_id = new_race.id
    session.close()
    return race_id

def get_races():
    session = Session()
    races = session.query(Race).filter_by(archived=False).order_by(Race.date.desc()).all()
    result = [{"id": race.id, "name": race.name, "date": race.date} for race in races]
    session.close()
    return result

def archive_race(race_id):
    session = Session()
    race = session.query(Race).filter_by(id=race_id).first()
    if race:
        race.archived = True
        session.commit()
        session.close()
        return True
    session.close()
    return False

# Keep all other functions unchanged
# ...
