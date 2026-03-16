from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from .db import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    location = Column(String(255), index=True, nullable=True)
    rest_type = Column(String(255), nullable=True)

    avg_rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)
    avg_cost_for_two = Column(Integer, nullable=True)

    online_order = Column(Boolean, default=False, nullable=False)
    book_table = Column(Boolean, default=False, nullable=False)

    source_url = Column(Text, nullable=True)

    cuisines = relationship("RestaurantCuisine", back_populates="restaurant")
    reviews = relationship("RestaurantReview", back_populates="restaurant")


class RestaurantCuisine(Base):
    __tablename__ = "restaurant_cuisines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False, index=True)
    cuisine = Column(String(255), index=True, nullable=False)

    restaurant = relationship("Restaurant", back_populates="cuisines")


class RestaurantReview(Base):
    __tablename__ = "restaurant_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False, index=True)
    rating = Column(Float, nullable=True)
    review_text = Column(Text, nullable=True)

    restaurant = relationship("Restaurant", back_populates="reviews")


class ETLRun(Base):
    __tablename__ = "etl_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(255), nullable=False)
    loaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    row_count = Column(Integer, nullable=False)

