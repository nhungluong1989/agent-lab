import json
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime, timedelta

from backend.database.database import get_db
from backend.database.models import (
    District, MarketMetrics, InvestmentScore, PropertyListing, PriceSnapshot
)
from backend.api.auth import get_current_user
from backend.database.models import User
from backend.crawlers.scheduler import run_crawl_all

router = APIRouter(prefix="/analytics", tags=["analytics"])

_crawl_running = False


@router.post("/refresh")
async def trigger_refresh(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    global _crawl_running
    if _crawl_running:
        raise HTTPException(status_code=409, detail="Crawl already in progress")
    _crawl_running = True

    async def _run():
        global _crawl_running
        try:
            await run_crawl_all()
        finally:
            _crawl_running = False

    background_tasks.add_task(_run)
    return {"message": "Crawl started", "status": "running"}


@router.get("/refresh/status")
async def refresh_status(current_user: User = Depends(get_current_user)):
    return {"running": _crawl_running}


def _latest_score(scores):
    return max(scores, key=lambda s: s.computed_at) if scores else None


def _latest_metrics(metrics):
    return max(metrics, key=lambda m: m.computed_at) if metrics else None


@router.get("/districts")
async def get_all_districts_analytics(db: AsyncSession = Depends(get_db)):
    districts = (await db.execute(
        select(District).options(selectinload(District.scores), selectinload(District.metrics)).order_by(District.name)
    )).scalars().all()
    result = []
    for d in districts:
        score = _latest_score(d.scores)
        metrics = _latest_metrics(d.metrics)
        result.append({
            "code": d.code,
            "name": d.name,
            "name_short": d.name_short,
            "district_type": d.district_type,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "overall_score": score.overall_score if score else None,
            "recommendation": score.recommendation if score else None,
            "capital_appreciation_score": score.capital_appreciation_score if score else None,
            "rental_income_score": score.rental_income_score if score else None,
            "risk_score": score.risk_score if score else None,
            "estimated_rental_yield": score.estimated_rental_yield if score else None,
            "estimated_appreciation_1y": score.estimated_appreciation_1y if score else None,
            "avg_sale_price_per_m2": metrics.avg_sale_price_per_m2 if metrics else None,
            "avg_rental_monthly": metrics.avg_rental_monthly if metrics else None,
            "supply_count": metrics.supply_count if metrics else None,
        })
    return sorted(result, key=lambda x: x["overall_score"] or 0, reverse=True)


@router.get("/districts/{district_code}")
async def get_district_detail(district_code: int, db: AsyncSession = Depends(get_db)):
    d = (await db.execute(
        select(District).options(selectinload(District.scores), selectinload(District.metrics)).where(District.code == district_code)
    )).scalar_one_or_none()
    if not d:
        raise HTTPException(404, "District not found")

    score = _latest_score(d.scores)
    metrics = _latest_metrics(d.metrics)

    return {
        "code": d.code,
        "name": d.name,
        "name_short": d.name_short,
        "district_type": d.district_type,
        "latitude": d.latitude,
        "longitude": d.longitude,
        "score": {
            "overall_score": score.overall_score if score else None,
            "capital_appreciation_score": score.capital_appreciation_score if score else None,
            "rental_income_score": score.rental_income_score if score else None,
            "liquidity_score": score.liquidity_score if score else None,
            "growth_score": score.growth_score if score else None,
            "risk_score": score.risk_score if score else None,
            "short_term_score": score.short_term_score if score else None,
            "medium_term_score": score.medium_term_score if score else None,
            "long_term_score": score.long_term_score if score else None,
            "recommendation": score.recommendation if score else None,
            "strengths": json.loads(score.strengths) if score and score.strengths else [],
            "weaknesses": json.loads(score.weaknesses) if score and score.weaknesses else [],
            "opportunities": json.loads(score.opportunities) if score and score.opportunities else [],
            "risks": json.loads(score.risks) if score and score.risks else [],
            "estimated_appreciation_1y": score.estimated_appreciation_1y if score else None,
            "estimated_rental_yield": score.estimated_rental_yield if score else None,
        } if score else None,
        "metrics": {
            "avg_sale_price_per_m2": metrics.avg_sale_price_per_m2 if metrics else None,
            "avg_rental_price_per_m2": metrics.avg_rental_price_per_m2 if metrics else None,
            "avg_rental_monthly": metrics.avg_rental_monthly if metrics else None,
            "rental_yield": metrics.rental_yield if metrics else None,
            "price_to_income_ratio": metrics.price_to_income_ratio if metrics else None,
            "price_to_rent_ratio": metrics.price_to_rent_ratio if metrics else None,
            "supply_count": metrics.supply_count if metrics else None,
            "rental_count": metrics.rental_count if metrics else None,
        } if metrics else None,
    }


@router.get("/top-opportunities")
async def get_top_opportunities(
    limit: int = 10,
    recommendation: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    districts = (await db.execute(
        select(District).options(selectinload(District.scores), selectinload(District.metrics))
    )).scalars().all()
    items = []
    for d in districts:
        score = _latest_score(d.scores)
        metrics = _latest_metrics(d.metrics)
        if not score:
            continue
        if recommendation and score.recommendation != recommendation:
            continue
        items.append({
            "rank": 0,
            "code": d.code,
            "name": d.name,
            "district_type": d.district_type,
            "overall_score": score.overall_score,
            "recommendation": score.recommendation,
            "capital_appreciation_score": score.capital_appreciation_score,
            "rental_income_score": score.rental_income_score,
            "risk_score": score.risk_score,
            "estimated_appreciation_1y": score.estimated_appreciation_1y,
            "estimated_rental_yield": score.estimated_rental_yield,
            "avg_sale_price_per_m2": metrics.avg_sale_price_per_m2 if metrics else None,
            "strengths": json.loads(score.strengths) if score.strengths else [],
        })

    items.sort(key=lambda x: x["overall_score"], reverse=True)
    for i, item in enumerate(items[:limit]):
        item["rank"] = i + 1
    return items[:limit]


@router.get("/comparison")
async def compare_districts(
    codes: str = Query(..., description="Comma-separated district codes"),
    db: AsyncSession = Depends(get_db),
):
    code_list = [int(c.strip()) for c in codes.split(",") if c.strip().isdigit()]
    result = []
    for code in code_list:
        d = (await db.execute(
            select(District).options(selectinload(District.scores), selectinload(District.metrics)).where(District.code == code)
        )).scalar_one_or_none()
        if not d:
            continue
        score = _latest_score(d.scores)
        metrics = _latest_metrics(d.metrics)
        result.append({
            "code": d.code,
            "name": d.name,
            "overall_score": score.overall_score if score else None,
            "recommendation": score.recommendation if score else None,
            "capital_appreciation_score": score.capital_appreciation_score if score else None,
            "rental_income_score": score.rental_income_score if score else None,
            "risk_score": score.risk_score if score else None,
            "short_term_score": score.short_term_score if score else None,
            "medium_term_score": score.medium_term_score if score else None,
            "long_term_score": score.long_term_score if score else None,
            "avg_sale_price_per_m2": metrics.avg_sale_price_per_m2 if metrics else None,
            "avg_rental_monthly": metrics.avg_rental_monthly if metrics else None,
            "rental_yield": metrics.rental_yield if metrics else None,
            "supply_count": metrics.supply_count if metrics else None,
        })
    return result


@router.get("/market-summary")
async def get_market_summary(db: AsyncSession = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=7)

    total_listings = (await db.execute(
        select(func.count(PropertyListing.id)).where(PropertyListing.crawled_at >= since)
    )).scalar_one()

    avg_pm2 = (await db.execute(
        select(func.avg(PropertyListing.price_per_m2)).where(
            PropertyListing.listing_type == "sale",
            PropertyListing.price_per_m2 > 0,
            PropertyListing.crawled_at >= since,
        )
    )).scalar_one()

    avg_rent = (await db.execute(
        select(func.avg(PropertyListing.price)).where(
            PropertyListing.listing_type == "rent",
            PropertyListing.price > 0,
            PropertyListing.crawled_at >= since,
        )
    )).scalar_one()

    all_scores = (await db.execute(select(InvestmentScore))).scalars().all()
    latest_by_district: dict = {}
    for s in all_scores:
        if s.district_code not in latest_by_district or s.computed_at > latest_by_district[s.district_code].computed_at:
            latest_by_district[s.district_code] = s

    recs = {"strong_buy": 0, "buy": 0, "hold": 0, "avoid": 0}
    for s in latest_by_district.values():
        recs[s.recommendation] = recs.get(s.recommendation, 0) + 1

    return {
        "total_listings": total_listings,
        "city_avg_price_per_m2": round(avg_pm2, 0) if avg_pm2 else None,
        "city_avg_rental_monthly": round(avg_rent, 0) if avg_rent else None,
        "districts_scored": len(latest_by_district),
        "recommendation_breakdown": recs,
        "last_updated": datetime.utcnow().isoformat(),
    }
