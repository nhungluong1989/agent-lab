import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict

from groq import Groq
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from backend.config import settings
from backend.database.models import District, MarketMetrics, InvestmentScore, PropertyListing

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Vietnamese real estate investment advisor covering all 63 provinces and municipalities across Vietnam.
You have access to live market data including property listings, prices, rental yields, and investment scores for every province.

When answering questions:
- Always cite specific data from the market context provided
- Give concrete investment recommendations with reasoning
- Use province/city names in Vietnamese (e.g., Hồ Chí Minh, Hà Nội, Đà Nẵng, Bình Dương)
- Format prices in VND (e.g., 85 triệu/m², 15 tỷ)
- Reference rental yields as annual percentages
- Be direct about risks and opportunities
- For "where should I invest" questions, rank top 3 provinces with reasons
- Consider the investor's time horizon if mentioned (short/medium/long term)
- Compare provinces across regions (North/Central/South) when relevant

Respond in the same language as the user's question (Vietnamese or English)."""


async def build_context(db: AsyncSession) -> str:
    lines = [f"=== Vietnam Real Estate Market Data ({datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}) ===\n"]

    # Market summary
    since = datetime.utcnow() - timedelta(days=7)
    total = (await db.execute(
        select(func.count(PropertyListing.id)).where(PropertyListing.crawled_at >= since)
    )).scalar_one()
    avg_pm2 = (await db.execute(
        select(func.avg(PropertyListing.price_per_m2)).where(
            PropertyListing.listing_type == "sale",
            PropertyListing.price_per_m2 > 0,
            PropertyListing.crawled_at >= since,
        )
    )).scalar_one()

    lines.append(f"Total active listings: {total}")
    if avg_pm2:
        lines.append(f"City avg sale price: {avg_pm2/1_000_000:.0f} triệu/m²")

    # Top districts by score
    districts = (await db.execute(
        select(District).options(selectinload(District.scores), selectinload(District.metrics))
    )).scalars().all()
    scored = []
    for d in districts:
        if not d.scores:
            continue
        score = max(d.scores, key=lambda s: s.computed_at)
        metrics = max(d.metrics, key=lambda m: m.computed_at) if d.metrics else None
        scored.append((d, score, metrics))

    scored.sort(key=lambda x: x[1].overall_score, reverse=True)

    lines.append("\n--- DISTRICT INVESTMENT SCORES (Top 15) ---")
    lines.append("District | Score | Rec | Price/m² | Yield | Risk")
    for d, score, metrics in scored[:15]:
        pm2 = f"{metrics.avg_sale_price_per_m2/1_000_000:.0f}M" if metrics and metrics.avg_sale_price_per_m2 else "N/A"
        yld = f"{score.estimated_rental_yield:.1f}%" if score.estimated_rental_yield else "N/A"
        rec_map = {"strong_buy": "STRONG BUY", "buy": "BUY", "hold": "HOLD", "avoid": "AVOID"}
        lines.append(
            f"{d.name} | {score.overall_score:.0f}/100 | {rec_map.get(score.recommendation, score.recommendation)} | {pm2} | {yld} | {score.risk_score:.0f}/100"
        )

    # Short/medium/long term rankings
    lines.append("\n--- SHORT TERM TOP 3 (1-3 years) ---")
    for d, score, _ in sorted(scored, key=lambda x: x[1].short_term_score, reverse=True)[:3]:
        lines.append(f"  {d.name}: {score.short_term_score:.0f}/100")

    lines.append("\n--- LONG TERM TOP 3 (7-15 years) ---")
    for d, score, _ in sorted(scored, key=lambda x: x[1].long_term_score, reverse=True)[:3]:
        lines.append(f"  {d.name}: {score.long_term_score:.0f}/100")

    return "\n".join(lines)


async def chat(messages: List[Dict[str, str]], db: AsyncSession) -> str:
    if not settings.GROQ_API_KEY:
        return "AI chat is not configured. Please set GROQ_API_KEY in your .env file."

    try:
        context = await build_context(db)
        client = Groq(api_key=settings.GROQ_API_KEY)
        system = f"{SYSTEM_PROMPT}\n\n{context}"
        groq_messages = [{"role": "system", "content": system}] + messages

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=groq_messages,
            max_tokens=1500,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return f"Sorry, I encountered an error: {str(e)}"


async def generate_daily_summary(role: str, db: AsyncSession) -> str:
    if not settings.GROQ_API_KEY:
        return "AI service not configured."

    context = await build_context(db)
    instructions = {
        "investor": "Provide a market overview: top opportunities, price movements, rental yield highlights. 4-5 bullet points.",
        "analyst": "Focus on supply-demand dynamics, price-to-income ratios, risk indicators. 4-5 bullet points.",
        "developer": "Focus on high-growth areas, infrastructure pipeline, and emerging hotspots. 4-5 bullet points.",
    }
    instruction = instructions.get(role, instructions["investor"])

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a Vietnamese real estate market analyst. Be concise and data-driven."},
                {"role": "user", "content": f"{context}\n\nTask: {instruction}\nDate: {datetime.utcnow().strftime('%Y-%m-%d')}"},
            ],
            max_tokens=600,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq summary error: {e}")
        return "Could not generate summary."
