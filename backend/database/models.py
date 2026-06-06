from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.database.database import Base


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(Integer, unique=True, index=True, nullable=False)  # Chotot area code
    name = Column(String(100), nullable=False)
    name_short = Column(String(50))
    district_type = Column(String(20), default="urban")  # urban, suburban, rural
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    listings = relationship("PropertyListing", back_populates="district")
    snapshots = relationship("PriceSnapshot", back_populates="district")
    metrics = relationship("MarketMetrics", back_populates="district")
    scores = relationship("InvestmentScore", back_populates="district")


class PropertyListing(Base):
    __tablename__ = "property_listings"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(20), nullable=False)          # chotot, homedy
    external_id = Column(String(50), index=True)
    district_code = Column(Integer, ForeignKey("districts.code"), nullable=True, index=True)
    district_name = Column(String(100))
    ward_name = Column(String(100))
    street_name = Column(String(200))
    property_type = Column(String(30), index=True)       # apartment, house, land, villa
    listing_type = Column(String(10), index=True)        # sale, rent
    price = Column(Float, nullable=True)                 # VND
    price_per_m2 = Column(Float, nullable=True)          # VND/m²
    area_m2 = Column(Float, nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    floors = Column(Integer, nullable=True)
    title = Column(String(500))
    url = Column(String(1000))
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    crawled_at = Column(DateTime, default=datetime.utcnow, index=True)
    listed_at = Column(DateTime, nullable=True)

    district = relationship("District", back_populates="listings")


class PriceSnapshot(Base):
    """Daily aggregated price data per district + property_type + listing_type."""
    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    district_code = Column(Integer, ForeignKey("districts.code"), nullable=False, index=True)
    property_type = Column(String(30), nullable=False)
    listing_type = Column(String(10), nullable=False)
    snapshot_date = Column(DateTime, default=datetime.utcnow, index=True)
    avg_price = Column(Float, nullable=True)
    avg_price_per_m2 = Column(Float, nullable=True)
    median_price = Column(Float, nullable=True)
    min_price = Column(Float, nullable=True)
    max_price = Column(Float, nullable=True)
    total_listings = Column(Integer, default=0)

    district = relationship("District", back_populates="snapshots")


class MarketMetrics(Base):
    """Computed analytics per district."""
    __tablename__ = "market_metrics"

    id = Column(Integer, primary_key=True, index=True)
    district_code = Column(Integer, ForeignKey("districts.code"), nullable=False, index=True)
    computed_at = Column(DateTime, default=datetime.utcnow, index=True)
    avg_sale_price_per_m2 = Column(Float, nullable=True)
    avg_rental_price_per_m2 = Column(Float, nullable=True)
    avg_rental_monthly = Column(Float, nullable=True)
    rental_yield = Column(Float, nullable=True)          # annual %, e.g. 4.5
    price_to_income_ratio = Column(Float, nullable=True)
    price_to_rent_ratio = Column(Float, nullable=True)
    supply_count = Column(Integer, default=0)
    rental_count = Column(Integer, default=0)
    price_change_1m = Column(Float, nullable=True)       # % change
    price_change_3m = Column(Float, nullable=True)
    price_change_6m = Column(Float, nullable=True)

    district = relationship("District", back_populates="metrics")


class InvestmentScore(Base):
    """Investment scoring 0-100 per district."""
    __tablename__ = "investment_scores"

    id = Column(Integer, primary_key=True, index=True)
    district_code = Column(Integer, ForeignKey("districts.code"), nullable=False, index=True)
    computed_at = Column(DateTime, default=datetime.utcnow, index=True)
    overall_score = Column(Float, default=0)
    capital_appreciation_score = Column(Float, default=0)
    rental_income_score = Column(Float, default=0)
    liquidity_score = Column(Float, default=0)
    growth_score = Column(Float, default=0)
    risk_score = Column(Float, default=0)               # higher = more risk
    short_term_score = Column(Float, default=0)         # 1-3 years
    medium_term_score = Column(Float, default=0)        # 3-7 years
    long_term_score = Column(Float, default=0)          # 7-15 years
    recommendation = Column(String(20), default="hold") # strong_buy, buy, hold, avoid
    strengths = Column(Text, default="[]")              # JSON array
    weaknesses = Column(Text, default="[]")
    opportunities = Column(Text, default="[]")
    risks = Column(Text, default="[]")
    estimated_appreciation_1y = Column(Float, nullable=True)
    estimated_rental_yield = Column(Float, nullable=True)

    district = relationship("District", back_populates="scores")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200))
    role = Column(String(20), default="investor")
    is_active = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=True)
    preferred_districts = Column(Text, default="")      # comma-separated district codes
    created_at = Column(DateTime, default=datetime.utcnow)
    last_notified_at = Column(DateTime, nullable=True)

    notification_logs = relationship("NotificationLog", back_populates="user")


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel = Column(String(20))
    status = Column(String(20))
    subject = Column(String(500))
    message = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notification_logs")
