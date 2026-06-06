"""Investment scoring engine for Vietnam provinces."""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database.models import PropertyListing

logger = logging.getLogger(__name__)

# Infrastructure scores per province (transport, economy, development pipeline)
INFRASTRUCTURE_SCORES = {
    13: 95,  # Hồ Chí Minh - metro, expressways, financial hub
    12: 92,  # Hà Nội - capital, metro, political center
    14: 80,  # Đà Nẵng - international airport, tourism, tech park
    15: 72,  # Hải Phòng - major port, expressway to Hanoi
    6:  78,  # Bình Dương - VSIP industrial parks, highway
    19: 75,  # Đồng Nai - Long Thành airport zone, highway
    2:  68,  # Bà Rịa - Vũng Tàu - port, oil & gas, coastal
    29: 70,  # Khánh Hòa - Nha Trang tourism, airport
    33: 65,  # Lâm Đồng - Đà Lạt tourism, airport
    46: 67,  # Quảng Ninh - Hạ Long tourism, Vân Đồn airport
    44: 62,  # Quảng Nam - Hội An tourism, Da Nang proximity
    63: 70,  # Bắc Ninh - Samsung factories, Hanoi proximity
    59: 65,  # Vĩnh Phúc - industrial zones, Hanoi proximity
    28: 60,  # Hưng Yên - Hanoi proximity, industrial
    25: 58,  # Hải Dương - industrial corridor
    36: 55,  # Long An - gateway to HCMC, industrial
    10: 62,  # Cần Thơ - Mekong Delta hub, airport
    54: 60,  # Thừa Thiên Huế - Huế heritage tourism, airport
    5:  55,  # Bình Định - Quy Nhơn port, coastal
    38: 52,  # Nghệ An - large province, Vinh city
    53: 50,  # Thanh Hóa - coastal, Nghi Sơn industrial
    42: 50,  # Phú Yên - coastal, tourism emerging
    30: 55,  # Kiên Giang - Phú Quốc island, airport
    8:  52,  # Bình Thuận - Mũi Né tourism, wind energy
    50: 48,  # Tây Ninh - border trade, HCMC proximity
    52: 48,  # Thái Nguyên - Samsung factory, Hanoi proximity
    16: 45,  # Đắk Lắk - Buôn Ma Thuột, coffee region
    23: 48,  # Hà Nam - Hanoi proximity, industrial
    39: 47,  # Ninh Bình - tourism (Tràng An), Hanoi day-trip
    41: 45,  # Phú Thọ - Việt Trì industrial
    45: 45,  # Quảng Ngãi - Dung Quất industrial port
    43: 43,  # Quảng Bình - Phong Nha tourism
    61: 48,  # Bắc Giang - Hanoi proximity, industrial
    24: 42,  # Hà Tĩnh - Vũng Áng industrial
    37: 42,  # Nam Định - traditional textile
    51: 42,  # Thái Bình - agriculture
    55: 45,  # Tiền Giang - Mekong Delta, HCMC proximity
    1:  42,  # An Giang - border trade, Mekong Delta
    20: 40,  # Đồng Tháp - Mekong Delta agriculture
    21: 42,  # Gia Lai - Central Highlands, Pleiku
    4:  40,  # Bến Tre - Mekong Delta
    56: 38,  # Trà Vinh - Mekong Delta
    58: 40,  # Vĩnh Long - Mekong Delta
    26: 38,  # Hậu Giang - Mekong Delta
    48: 38,  # Sóc Trăng - Mekong Delta
    3:  37,  # Bạc Liêu - Mekong Delta
    9:  36,  # Cà Mau - southernmost, remote
    40: 38,  # Ninh Thuận - coastal, wind/solar energy
    7:  38,  # Bình Phước - border, rubber plantations
    27: 38,  # Hòa Bình - hydropower, Hanoi weekend
    17: 35,  # Đắk Nông - Central Highlands
    31: 35,  # Kon Tum - remote Central Highlands
    47: 38,  # Quảng Trị - DMZ tourism, wind energy
    57: 35,  # Tuyên Quang - mountainous, remote
    60: 35,  # Yên Bái - mountainous
    34: 35,  # Lạng Sơn - China border trade
    35: 38,  # Lào Cai - Sapa tourism, China border
    49: 33,  # Sơn La - mountainous, hydropower
    22: 30,  # Hà Giang - remote mountains
    11: 30,  # Cao Bằng - remote, border
    62: 28,  # Bắc Kạn - remote, mountainous
    32: 28,  # Lai Châu - remote, mountainous
    18: 28,  # Điện Biên - remote, historical
}

# National average monthly household income estimate (VND)
INCOME_ESTIMATE_VND = 12_000_000

# Province-level income multipliers (relative to national avg)
INCOME_MULTIPLIERS = {
    13: 1.8,  # HCM
    12: 1.7,  # Hanoi
    14: 1.3,  # Da Nang
    15: 1.2,  # Hai Phong
    6:  1.3,  # Binh Duong
    19: 1.2,  # Dong Nai
    2:  1.1,  # BR-VT
    63: 1.2,  # Bac Ninh
    10: 1.1,  # Can Tho
}


async def compute_market_metrics(province_code: int, db: AsyncSession) -> Optional[Dict[str, Any]]:
    since = datetime.utcnow() - timedelta(days=30)

    sale_q = await db.execute(
        select(
            func.avg(PropertyListing.price_per_m2).label("avg_pm2"),
            func.count(PropertyListing.id).label("count"),
        ).where(
            PropertyListing.district_code == province_code,
            PropertyListing.listing_type == "sale",
            PropertyListing.price_per_m2.isnot(None),
            PropertyListing.price_per_m2 > 0,
            PropertyListing.crawled_at >= since,
        )
    )
    sale_row = sale_q.first()
    avg_sale_pm2 = sale_row.avg_pm2 if sale_row else None
    supply_count = sale_row.count if sale_row else 0

    rent_q = await db.execute(
        select(
            func.avg(PropertyListing.price).label("avg_rent"),
            func.avg(PropertyListing.price_per_m2).label("avg_rent_pm2"),
            func.count(PropertyListing.id).label("count"),
        ).where(
            PropertyListing.district_code == province_code,
            PropertyListing.listing_type == "rent",
            PropertyListing.price.isnot(None),
            PropertyListing.price > 0,
            PropertyListing.crawled_at >= since,
        )
    )
    rent_row = rent_q.first()
    avg_rental_monthly = rent_row.avg_rent if rent_row else None
    avg_rental_pm2 = rent_row.avg_rent_pm2 if rent_row else None
    rental_count = rent_row.count if rent_row else 0

    rental_yield = None
    if avg_rental_monthly and avg_sale_pm2 and avg_sale_pm2 > 0:
        avg_property_price = avg_sale_pm2 * 60
        rental_yield = round((avg_rental_monthly * 12) / avg_property_price * 100, 2)

    local_income = INCOME_ESTIMATE_VND * INCOME_MULTIPLIERS.get(province_code, 1.0)
    price_to_income = None
    if avg_sale_pm2:
        price_to_income = round((avg_sale_pm2 * 60) / (local_income * 12), 1)

    price_to_rent = None
    if avg_sale_pm2 and avg_rental_monthly and avg_rental_monthly > 0:
        price_to_rent = round((avg_sale_pm2 * 60) / (avg_rental_monthly * 12), 1)

    return {
        "district_code": province_code,
        "avg_sale_price_per_m2": round(avg_sale_pm2, 0) if avg_sale_pm2 else None,
        "avg_rental_price_per_m2": round(avg_rental_pm2, 0) if avg_rental_pm2 else None,
        "avg_rental_monthly": round(avg_rental_monthly, 0) if avg_rental_monthly else None,
        "rental_yield": rental_yield,
        "price_to_income_ratio": price_to_income,
        "price_to_rent_ratio": price_to_rent,
        "supply_count": supply_count,
        "rental_count": rental_count,
        "price_change_1m": None,
        "price_change_3m": None,
        "price_change_6m": None,
    }


def compute_investment_score(
    province_code: int,
    metrics: Dict[str, Any],
    all_metrics: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Score a province 0-100 across multiple investment dimensions."""

    valid_pm2 = [m["avg_sale_price_per_m2"] for m in all_metrics if m.get("avg_sale_price_per_m2")]
    valid_yield = [m["rental_yield"] for m in all_metrics if m.get("rental_yield")]
    valid_supply = [m["supply_count"] for m in all_metrics if m.get("supply_count")]

    national_avg_pm2 = sum(valid_pm2) / len(valid_pm2) if valid_pm2 else 30_000_000
    national_avg_yield = sum(valid_yield) / len(valid_yield) if valid_yield else 4.0
    national_avg_supply = sum(valid_supply) / len(valid_supply) if valid_supply else 30

    avg_pm2 = metrics.get("avg_sale_price_per_m2") or national_avg_pm2
    rental_yield = metrics.get("rental_yield") or national_avg_yield
    supply = metrics.get("supply_count") or 0
    pti = metrics.get("price_to_income_ratio") or 20

    infra = INFRASTRUCTURE_SCORES.get(province_code, 40)

    # Rental income score: 2-8% → 0-100
    rental_score = min(100, max(0, (rental_yield - 2) / 6 * 100))

    # Capital appreciation: infrastructure + price competitiveness vs national avg
    price_ratio = avg_pm2 / national_avg_pm2 if national_avg_pm2 > 0 else 1.0
    affordability = min(100, max(0, (2 - price_ratio) * 50 + 50))
    capital_score = infra * 0.6 + affordability * 0.4

    # Liquidity: listing volume vs national avg
    liquidity_score = min(100, (supply / max(national_avg_supply, 1)) * 50)

    # Growth: infrastructure + affordability proxy
    growth_score = infra * 0.7 + affordability * 0.3

    # Risk: high PTI = risky; remote provinces = risky
    risk_score = min(100, max(0, pti * 2.5))
    if infra < 35:
        risk_score = min(100, risk_score + 15)

    overall = (
        capital_score * 0.30 +
        rental_score * 0.25 +
        growth_score * 0.20 +
        liquidity_score * 0.15 +
        (100 - risk_score) * 0.10
    )
    overall = round(min(100, max(0, overall)), 1)

    if overall >= 70:
        recommendation = "strong_buy"
    elif overall >= 55:
        recommendation = "buy"
    elif overall >= 40:
        recommendation = "hold"
    else:
        recommendation = "avoid"

    short_term = round(liquidity_score * 0.4 + capital_score * 0.4 + rental_score * 0.2, 1)
    medium_term = round(capital_score * 0.5 + growth_score * 0.3 + rental_score * 0.2, 1)
    long_term = round(infra * 0.5 + growth_score * 0.3 + (100 - risk_score) * 0.2, 1)

    strengths, weaknesses, opportunities, risks_list = [], [], [], []

    if infra >= 75:
        strengths.append("Major economic hub with strong infrastructure")
    elif infra >= 60:
        strengths.append("Good infrastructure and transport links")
    if rental_yield >= national_avg_yield:
        strengths.append(f"Above-average rental yield ({rental_yield:.1f}%)")
    if supply >= national_avg_supply:
        strengths.append("Active market with good listing volume")
    if price_ratio < 0.7:
        strengths.append("Significantly below national average price — high upside")

    if price_ratio > 1.5:
        weaknesses.append("Premium pricing limits capital upside")
    if rental_yield < national_avg_yield * 0.8:
        weaknesses.append("Below-average rental yield")
    if infra < 40:
        weaknesses.append("Limited infrastructure and urban amenities")
    if supply < national_avg_supply * 0.3:
        weaknesses.append("Thin market — low liquidity risk")

    if infra >= 55:
        opportunities.append("Ongoing infrastructure investment to boost values")
    if price_ratio < 0.8:
        opportunities.append("Undervalued vs national average — upside potential")
    if province_code in [30, 29, 33, 46, 44, 54]:
        opportunities.append("Strong tourism growth driving short-term rental demand")
    if province_code in [6, 19, 63, 59, 28]:
        opportunities.append("Industrial zone expansion attracting workforce housing demand")

    if pti > 30:
        risks_list.append("High price-to-income ratio — affordability risk")
    if risk_score >= 60:
        risks_list.append("Elevated market risk — limited fundamentals support")
    if infra < 35:
        risks_list.append("Remote location reduces exit liquidity")

    est_yield = round(rental_yield, 2) if rental_yield else None
    est_appreciation = round(max(0, (infra / 100) * 12 - 3), 1)

    return {
        "district_code": province_code,
        "overall_score": overall,
        "capital_appreciation_score": round(capital_score, 1),
        "rental_income_score": round(rental_score, 1),
        "liquidity_score": round(liquidity_score, 1),
        "growth_score": round(growth_score, 1),
        "risk_score": round(risk_score, 1),
        "short_term_score": short_term,
        "medium_term_score": medium_term,
        "long_term_score": long_term,
        "recommendation": recommendation,
        "strengths": json.dumps(strengths),
        "weaknesses": json.dumps(weaknesses),
        "opportunities": json.dumps(opportunities),
        "risks": json.dumps(risks_list),
        "estimated_appreciation_1y": est_appreciation,
        "estimated_rental_yield": est_yield,
    }
