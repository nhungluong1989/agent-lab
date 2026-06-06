from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
from datetime import datetime, timedelta

from backend.database.database import get_db
from backend.database.models import PropertyListing, District, PriceSnapshot

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("/")
async def get_listings(
    district_code: Optional[int] = None,
    property_type: Optional[str] = None,
    listing_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(PropertyListing).order_by(PropertyListing.crawled_at.desc())
    if district_code:
        q = q.where(PropertyListing.district_code == district_code)
    if property_type:
        q = q.where(PropertyListing.property_type == property_type)
    if listing_type:
        q = q.where(PropertyListing.listing_type == listing_type)
    if min_price:
        q = q.where(PropertyListing.price >= min_price)
    if max_price:
        q = q.where(PropertyListing.price <= max_price)

    total_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(total_q)).scalar_one()

    rows = (await db.execute(q.limit(limit).offset(offset))).scalars().all()

    return {
        "total": total,
        "listings": [
            {
                "id": r.id,
                "source": r.source,
                "district_code": r.district_code,
                "district_name": r.district_name,
                "ward_name": r.ward_name,
                "street_name": r.street_name,
                "property_type": r.property_type,
                "listing_type": r.listing_type,
                "price": r.price,
                "price_per_m2": r.price_per_m2,
                "area_m2": r.area_m2,
                "bedrooms": r.bedrooms,
                "title": r.title,
                "url": r.url,
                "listed_at": r.listed_at.isoformat() if r.listed_at else None,
            }
            for r in rows
        ],
    }


@router.get("/districts")
async def get_districts(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(District).order_by(District.name))).scalars().all()
    return [
        {
            "code": d.code,
            "name": d.name,
            "name_short": d.name_short,
            "district_type": d.district_type,
            "latitude": d.latitude,
            "longitude": d.longitude,
        }
        for d in rows
    ]


@router.get("/price-trend")
async def get_price_trend(
    district_code: int,
    property_type: str = "apartment",
    listing_type: str = "sale",
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    rows = (await db.execute(
        select(PriceSnapshot)
        .where(
            PriceSnapshot.district_code == district_code,
            PriceSnapshot.property_type == property_type,
            PriceSnapshot.listing_type == listing_type,
            PriceSnapshot.snapshot_date >= since,
        )
        .order_by(PriceSnapshot.snapshot_date)
    )).scalars().all()

    return [
        {
            "date": r.snapshot_date.isoformat(),
            "avg_price": r.avg_price,
            "avg_price_per_m2": r.avg_price_per_m2,
            "total_listings": r.total_listings,
        }
        for r in rows
    ]


@router.get("/summary")
async def get_listing_summary(db: AsyncSession = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=7)
    total = (await db.execute(
        select(func.count(PropertyListing.id))
        .where(PropertyListing.crawled_at >= since)
    )).scalar_one()

    sale_count = (await db.execute(
        select(func.count(PropertyListing.id))
        .where(PropertyListing.listing_type == "sale", PropertyListing.crawled_at >= since)
    )).scalar_one()

    rent_count = (await db.execute(
        select(func.count(PropertyListing.id))
        .where(PropertyListing.listing_type == "rent", PropertyListing.crawled_at >= since)
    )).scalar_one()

    avg_pm2 = (await db.execute(
        select(func.avg(PropertyListing.price_per_m2))
        .where(
            PropertyListing.listing_type == "sale",
            PropertyListing.price_per_m2.isnot(None),
            PropertyListing.price_per_m2 > 0,
            PropertyListing.crawled_at >= since,
        )
    )).scalar_one()

    return {
        "total_listings": total,
        "sale_listings": sale_count,
        "rent_listings": rent_count,
        "avg_price_per_m2": round(avg_pm2, 0) if avg_pm2 else None,
        "last_updated": datetime.utcnow().isoformat(),
    }
