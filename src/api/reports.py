"""
Daily sentiment report generator.

Queries today's tickets, computes metrics, and asks Gemini
to write a human-readable narrative summary.
Saves the result to the daily_reports table.
"""

import json
import os
from collections import Counter
from datetime import date, datetime, timezone

from google import genai
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import DailyReport, Ticket, TicketStatus


async def generate_daily_report(db: AsyncSession) -> dict:
    today = date.today()

    # ── Aggregate today's tickets ──────────────────────────────────────────────
    result = await db.execute(
        select(Ticket).where(func.date(Ticket.created_at) == today)
    )
    tickets = result.scalars().all()

    total = len(tickets)
    resolved = sum(1 for t in tickets if t.status == TicketStatus.resolved)
    escalated = sum(1 for t in tickets if t.status == TicketStatus.escalated)

    sentiments = [t.sentiment_score for t in tickets if t.sentiment_score is not None]
    avg_sentiment = round(sum(sentiments) / len(sentiments), 3) if sentiments else 0.0

    subject_words = " ".join(t.subject.lower() for t in tickets).split()
    stopwords = {"a", "an", "the", "is", "in", "on", "at", "to", "for", "of", "and", "my", "i"}
    keywords = [w for w in subject_words if w not in stopwords and len(w) > 3]
    top_issues = [{"keyword": kw, "count": cnt} for kw, cnt in Counter(keywords).most_common(5)]

    # ── Ask Gemini for a narrative summary ────────────────────────────────────
    summary_text = await _gemini_narrative(today, total, resolved, escalated, avg_sentiment, top_issues)

    # ── Upsert report ──────────────────────────────────────────────────────────
    existing = await db.execute(select(DailyReport).where(DailyReport.report_date == today))
    report = existing.scalar_one_or_none()

    if report:
        report.total_tickets = total
        report.resolved = resolved
        report.escalated = escalated
        report.avg_sentiment = avg_sentiment
        report.top_issues = top_issues
        report.summary_text = summary_text
    else:
        report = DailyReport(
            report_date=today,
            total_tickets=total,
            resolved=resolved,
            escalated=escalated,
            avg_sentiment=avg_sentiment,
            top_issues=top_issues,
            summary_text=summary_text,
        )
        db.add(report)

    await db.commit()

    return {
        "date": today.isoformat(),
        "total_tickets": total,
        "resolved": resolved,
        "escalated": escalated,
        "resolution_rate": round(resolved / total, 2) if total else 0,
        "avg_sentiment": avg_sentiment,
        "top_issues": top_issues,
        "summary": summary_text,
    }


async def _gemini_narrative(
    report_date: date,
    total: int,
    resolved: int,
    escalated: int,
    avg_sentiment: float,
    top_issues: list,
) -> str:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "Gemini API key not configured — narrative unavailable."

    client = genai.Client(api_key=api_key)

    sentiment_label = (
        "positive" if avg_sentiment > 0.2
        else "negative" if avg_sentiment < -0.2
        else "neutral"
    )
    issues_text = ", ".join(f"{i['keyword']} ({i['count']})" for i in top_issues)

    prompt = f"""Write a concise (3-4 sentence) daily customer success report narrative for {report_date}.
Data:
- Total tickets: {total}
- Resolved: {resolved} ({round(resolved/total*100) if total else 0}%)
- Escalated: {escalated}
- Average customer sentiment: {avg_sentiment} ({sentiment_label})
- Top issue keywords: {issues_text or 'none'}

Tone: professional, factual, optimistic where warranted. Address it to the CS team manager."""

    try:
        response = await client.aio.models.generate_content(
            model="gemini-1.5-flash-latest",
            contents=prompt,
        )
        return (response.text or "").strip()
    except Exception as e:
        print(f"Error generating Gemini narrative: {e}")
        return f"Daily report for {report_date}. Total tickets: {total}, Resolved: {resolved}, Escalated: {escalated}."
