import logging
from datetime import datetime
from typing import List, Dict, Any
import httpx

logger = logging.getLogger(__name__)

CHOTOT_API = "https://gateway.chotot.com/v1/public/ad-listing"

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

CAT_ALL_SALE = 1000
CAT_ALL_RENT = 2000

PROPERTY_TYPE_MAP = {
    1010: "apartment",
    1020: "house",
    1030: "land",
    1040: "villa",
    1050: "commercial",
    1060: "warehouse",
    2010: "apartment",
    2020: "house",
    2030: "room",
}

# All 63 Vietnam provinces/municipalities with Chotot region codes
VIETNAM_PROVINCES = {
    1:  "An Giang",
    2:  "Bà Rịa - Vũng Tàu",
    3:  "Bạc Liêu",
    4:  "Bến Tre",
    5:  "Bình Định",
    6:  "Bình Dương",
    7:  "Bình Phước",
    8:  "Bình Thuận",
    9:  "Cà Mau",
    10: "Cần Thơ",
    11: "Cao Bằng",
    12: "Hà Nội",
    13: "Hồ Chí Minh",
    14: "Đà Nẵng",
    15: "Hải Phòng",
    16: "Đắk Lắk",
    17: "Đắk Nông",
    18: "Điện Biên",
    19: "Đồng Nai",
    20: "Đồng Tháp",
    21: "Gia Lai",
    22: "Hà Giang",
    23: "Hà Nam",
    24: "Hà Tĩnh",
    25: "Hải Dương",
    26: "Hậu Giang",
    27: "Hòa Bình",
    28: "Hưng Yên",
    29: "Khánh Hòa",
    30: "Kiên Giang",
    31: "Kon Tum",
    32: "Lai Châu",
    33: "Lâm Đồng",
    34: "Lạng Sơn",
    35: "Lào Cai",
    36: "Long An",
    37: "Nam Định",
    38: "Nghệ An",
    39: "Ninh Bình",
    40: "Ninh Thuận",
    41: "Phú Thọ",
    42: "Phú Yên",
    43: "Quảng Bình",
    44: "Quảng Nam",
    45: "Quảng Ngãi",
    46: "Quảng Ninh",
    47: "Quảng Trị",
    48: "Sóc Trăng",
    49: "Sơn La",
    50: "Tây Ninh",
    51: "Thái Bình",
    52: "Thái Nguyên",
    53: "Thanh Hóa",
    54: "Thừa Thiên Huế",
    55: "Tiền Giang",
    56: "Trà Vinh",
    57: "Tuyên Quang",
    58: "Vĩnh Long",
    59: "Vĩnh Phúc",
    60: "Yên Bái",
    61: "Bắc Giang",
    62: "Bắc Kạn",
    63: "Bắc Ninh",
}


def _parse_ad(ad: dict, listing_type: str, province_code: int) -> Dict[str, Any]:
    price = ad.get("price")
    size = ad.get("size")

    pm2_millions = ad.get("price_million_per_m2")
    price_per_m2 = round(pm2_millions * 1_000_000, 0) if pm2_millions and pm2_millions > 0 else None
    if not price_per_m2 and price and size and size > 0:
        price_per_m2 = round(price / size, 0)

    category = ad.get("category", 0)
    prop_type = PROPERTY_TYPE_MAP.get(category)
    if not prop_type:
        name = (ad.get("category_name") or "").lower()
        if "căn hộ" in name or "chung cư" in name:
            prop_type = "apartment"
        elif "nhà" in name:
            prop_type = "house"
        elif "đất" in name:
            prop_type = "land"
        elif "biệt thự" in name:
            prop_type = "villa"
        else:
            prop_type = "other"

    listed_ts = ad.get("list_time")
    listed_at = datetime.utcfromtimestamp(listed_ts / 1000) if listed_ts else None

    return {
        "source": "chotot",
        "external_id": str(ad.get("ad_id") or ad.get("list_id", "")),
        "district_code": province_code,
        "district_name": ad.get("region_name") or VIETNAM_PROVINCES.get(province_code, ""),
        "ward_name": ad.get("area_name", ""),
        "street_name": ad.get("street_name", ""),
        "property_type": prop_type,
        "listing_type": listing_type,
        "price": float(price) if price else None,
        "price_per_m2": round(price_per_m2, 0) if price_per_m2 else None,
        "area_m2": float(size) if size else None,
        "bedrooms": None,
        "bathrooms": None,
        "floors": None,
        "title": ad.get("subject", ""),
        "url": f"https://nhatot.com/{ad.get('list_id', '')}",
        "latitude": ad.get("latitude"),
        "longitude": ad.get("longitude"),
        "crawled_at": datetime.utcnow(),
        "listed_at": listed_at,
    }


async def fetch_listings(
    category: int,
    listing_type: str,
    limit_per_province: int = 100,
) -> List[Dict[str, Any]]:
    results = []
    timeout = httpx.Timeout(20.0)

    async with httpx.AsyncClient(headers=HEADERS, timeout=timeout, follow_redirects=True) as client:
        for province_code in VIETNAM_PROVINCES:
            offset = 0
            fetched = 0
            while fetched < limit_per_province:
                batch = min(50, limit_per_province - fetched)
                try:
                    resp = await client.get(CHOTOT_API, params={
                        "cg": category,
                        "o": offset,
                        "limit": batch,
                        "key_param_included": "true",
                        "region": province_code,
                    })
                    resp.raise_for_status()
                    data = resp.json()
                    ads = data.get("ads", [])
                    if not ads:
                        break
                    for ad in ads:
                        results.append(_parse_ad(ad, listing_type, province_code))
                    fetched += len(ads)
                    offset += len(ads)
                    if len(ads) < batch:
                        break
                except Exception as e:
                    logger.warning(f"[Chotot] fetch failed province={province_code} cat={category}: {e}")
                    break

    logger.info(f"[Chotot] fetched {len(results)} listings (cat={category})")
    return results


async def fetch_all_vietnam() -> Dict[str, List[Dict[str, Any]]]:
    """Fetch sale + rental listings for all Vietnam provinces."""
    sale = await fetch_listings(CAT_ALL_SALE, "sale", limit_per_province=100)
    rent = await fetch_listings(CAT_ALL_RENT, "rent", limit_per_province=50)
    return {"sale": sale, "rent": rent}
