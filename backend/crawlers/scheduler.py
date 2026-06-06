import logging
from datetime import datetime, timedelta
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.database import AsyncSessionLocal
from backend.database.models import District, PropertyListing, PriceSnapshot, MarketMetrics, InvestmentScore
from backend.crawlers.chotot import fetch_all_vietnam, VIETNAM_PROVINCES
from backend.services.scoring import compute_market_metrics, compute_investment_score

logger = logging.getLogger(__name__)

# All 63 Vietnam provinces: code → (name, short_name, type, lat, lng)
PROVINCE_META = {
    1:  ("An Giang",           "An Giang",   "province", 10.3877, 105.4357),
    2:  ("Bà Rịa - Vũng Tàu", "BR-VT",      "province", 10.5417, 107.2431),
    3:  ("Bạc Liêu",           "Bạc Liêu",   "province",  9.2941, 105.7278),
    4:  ("Bến Tre",            "Bến Tre",    "province", 10.2433, 106.3756),
    5:  ("Bình Định",          "Bình Định",  "province", 13.7820, 109.2196),
    6:  ("Bình Dương",         "Bình Dương", "province", 11.1574, 106.7034),
    7:  ("Bình Phước",         "Bình Phước", "province", 11.7511, 106.7234),
    8:  ("Bình Thuận",         "Bình Thuận", "province", 11.0904, 108.0721),
    9:  ("Cà Mau",             "Cà Mau",     "province",  9.1769, 105.1523),
    10: ("Cần Thơ",            "Cần Thơ",    "city",     10.0452, 105.7469),
    11: ("Cao Bằng",           "Cao Bằng",   "province", 22.6657, 106.2522),
    12: ("Hà Nội",             "Hà Nội",     "city",     21.0278, 105.8342),
    13: ("Hồ Chí Minh",        "HCM",        "city",     10.8231, 106.6297),
    14: ("Đà Nẵng",            "Đà Nẵng",    "city",     16.0544, 108.2022),
    15: ("Hải Phòng",          "Hải Phòng",  "city",     20.8449, 106.6881),
    16: ("Đắk Lắk",            "Đắk Lắk",   "province", 12.7100, 108.2378),
    17: ("Đắk Nông",           "Đắk Nông",  "province", 12.0043, 107.6897),
    18: ("Điện Biên",          "Điện Biên",  "province", 21.3883, 103.0230),
    19: ("Đồng Nai",           "Đồng Nai",   "province", 10.9600, 106.8432),
    20: ("Đồng Tháp",          "Đồng Tháp",  "province", 10.4937, 105.6882),
    21: ("Gia Lai",            "Gia Lai",    "province", 13.9830, 108.0000),
    22: ("Hà Giang",           "Hà Giang",   "province", 22.8025, 104.9784),
    23: ("Hà Nam",             "Hà Nam",     "province", 20.5453, 105.9229),
    24: ("Hà Tĩnh",            "Hà Tĩnh",    "province", 18.3429, 105.9057),
    25: ("Hải Dương",          "Hải Dương",  "province", 20.9374, 106.3145),
    26: ("Hậu Giang",          "Hậu Giang",  "province",  9.7579, 105.6413),
    27: ("Hòa Bình",           "Hòa Bình",   "province", 20.8172, 105.3376),
    28: ("Hưng Yên",           "Hưng Yên",   "province", 20.6464, 106.0511),
    29: ("Khánh Hòa",          "Khánh Hòa",  "province", 12.2388, 109.1967),
    30: ("Kiên Giang",         "Kiên Giang", "province", 10.0126, 105.0809),
    31: ("Kon Tum",            "Kon Tum",    "province", 14.3497, 108.0005),
    32: ("Lai Châu",           "Lai Châu",   "province", 22.3964, 103.4584),
    33: ("Lâm Đồng",           "Lâm Đồng",  "province", 11.9404, 108.4583),
    34: ("Lạng Sơn",           "Lạng Sơn",  "province", 21.8537, 106.7615),
    35: ("Lào Cai",            "Lào Cai",    "province", 22.4809, 103.9752),
    36: ("Long An",            "Long An",    "province", 10.5355, 106.4095),
    37: ("Nam Định",           "Nam Định",   "province", 20.4388, 106.1621),
    38: ("Nghệ An",            "Nghệ An",    "province", 18.6796, 105.6813),
    39: ("Ninh Bình",          "Ninh Bình",  "province", 20.2506, 105.9745),
    40: ("Ninh Thuận",         "Ninh Thuận", "province", 11.5645, 108.9885),
    41: ("Phú Thọ",            "Phú Thọ",    "province", 21.3995, 105.2274),
    42: ("Phú Yên",            "Phú Yên",    "province", 13.0882, 109.0928),
    43: ("Quảng Bình",         "Quảng Bình", "province", 17.4766, 106.5988),
    44: ("Quảng Nam",          "Quảng Nam",  "province", 15.5394, 108.0191),
    45: ("Quảng Ngãi",         "Quảng Ngãi", "province", 15.1214, 108.8046),
    46: ("Quảng Ninh",         "Quảng Ninh", "province", 21.0064, 107.2925),
    47: ("Quảng Trị",          "Quảng Trị",  "province", 16.7943, 107.0420),
    48: ("Sóc Trăng",          "Sóc Trăng",  "province",  9.6027, 105.9739),
    49: ("Sơn La",             "Sơn La",     "province", 21.3178, 103.9145),
    50: ("Tây Ninh",           "Tây Ninh",   "province", 11.3100, 106.0980),
    51: ("Thái Bình",          "Thái Bình",  "province", 20.4463, 106.3366),
    52: ("Thái Nguyên",        "Thái Nguyên","province", 21.5942, 105.8480),
    53: ("Thanh Hóa",          "Thanh Hóa",  "province", 19.8067, 105.7851),
    54: ("Thừa Thiên Huế",     "Huế",        "province", 16.4637, 107.5909),
    55: ("Tiền Giang",         "Tiền Giang", "province", 10.3600, 106.3600),
    56: ("Trà Vinh",           "Trà Vinh",   "province",  9.9347, 106.3451),
    57: ("Tuyên Quang",        "Tuyên Quang","province", 21.8233, 105.2141),
    58: ("Vĩnh Long",          "Vĩnh Long",  "province", 10.2397, 105.9571),
    59: ("Vĩnh Phúc",          "Vĩnh Phúc",  "province", 21.3608, 105.5474),
    60: ("Yên Bái",            "Yên Bái",    "province", 21.7227, 104.9113),
    61: ("Bắc Giang",          "Bắc Giang",  "province", 21.2810, 106.1977),
    62: ("Bắc Kạn",            "Bắc Kạn",    "province", 22.1473, 105.8348),
    63: ("Bắc Ninh",           "Bắc Ninh",   "province", 21.1861, 106.0763),
}


async def ensure_districts_exist(db: AsyncSession):
    for code, (name, short, dtype, lat, lng) in PROVINCE_META.items():
        result = await db.execute(select(District).where(District.code == code))
        if not result.scalar_one_or_none():
            db.add(District(code=code, name=name, name_short=short,
                            district_type=dtype, latitude=lat, longitude=lng))
    await db.commit()
    logger.info("Provinces seeded")


async def run_crawl_all():
    logger.info("Starting Vietnam real estate crawl...")
    async with AsyncSessionLocal() as db:
        await ensure_districts_exist(db)

        data = await fetch_all_vietnam()
        sale_listings = data["sale"]
        rent_listings = data["rent"]
        all_listings = sale_listings + rent_listings

        # Evict listings older than 7 days
        cutoff = datetime.utcnow() - timedelta(days=7)
        await db.execute(delete(PropertyListing).where(PropertyListing.crawled_at < cutoff))

        # Insert new listings (skip duplicates by external_id)
        existing_q = await db.execute(select(PropertyListing.external_id))
        existing_ids = {row[0] for row in existing_q}

        added = 0
        for listing in all_listings:
            if listing["external_id"] and listing["external_id"] in existing_ids:
                continue
            db.add(PropertyListing(**listing))
            existing_ids.add(listing["external_id"])
            added += 1

        await db.commit()
        logger.info(f"[Chotot] +{added} listings ({len(sale_listings)} sale / {len(rent_listings)} rent)")

        # Daily price snapshots per province
        now = datetime.utcnow()
        for code in VIETNAM_PROVINCES:
            for prop_type in ["apartment", "house", "land"]:
                for listing_type in ["sale", "rent"]:
                    q = await db.execute(
                        select(
                            func.avg(PropertyListing.price).label("avg_price"),
                            func.avg(PropertyListing.price_per_m2).label("avg_pm2"),
                            func.min(PropertyListing.price).label("min_price"),
                            func.max(PropertyListing.price).label("max_price"),
                            func.count(PropertyListing.id).label("cnt"),
                        ).where(
                            PropertyListing.district_code == code,
                            PropertyListing.property_type == prop_type,
                            PropertyListing.listing_type == listing_type,
                            PropertyListing.price.isnot(None),
                        )
                    )
                    row = q.first()
                    if row and row.cnt and row.cnt > 0:
                        db.add(PriceSnapshot(
                            district_code=code,
                            property_type=prop_type,
                            listing_type=listing_type,
                            snapshot_date=now,
                            avg_price=row.avg_price,
                            avg_price_per_m2=row.avg_pm2,
                            min_price=row.min_price,
                            max_price=row.max_price,
                            total_listings=row.cnt,
                        ))
        await db.commit()
        logger.info("Price snapshots saved")

        # Market metrics + investment scores per province
        all_metrics = []
        for code in VIETNAM_PROVINCES:
            m = await compute_market_metrics(code, db)
            if m:
                all_metrics.append(m)
                db.add(MarketMetrics(**m, computed_at=now))
        await db.commit()

        for m in all_metrics:
            score = compute_investment_score(m["district_code"], m, all_metrics)
            db.add(InvestmentScore(**score, computed_at=now))
        await db.commit()

        logger.info(f"Scores computed for {len(all_metrics)} provinces")
        logger.info("Vietnam real estate crawl completed.")