import config
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DataSource(Base):
    __tablename__ = 'datasource'

    id = Column(Integer, primary_key=True)
    update_time = Column(DateTime)
    data = Column(String)


if __name__ == "__main__":
    engine = create_engine(config.DATABASE_URL)
    Base.metadata.create_all(engine)
