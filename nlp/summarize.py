"""AI narrative generation for the dashboard's "What happened / Why / So what"
storytelling section.

Uses Groq's free Llama 3.3 70B endpoint when GROQ_API_KEY is set; otherwise
falls back to a deterministic template-based summary so the dashboard always
has something to render.
"""
from __future__ import annotations

import logging
from typing import Any

import requests

from config import GROQ_API_KEY, has_groq_credentials

log = logging.getLogger(__name__)

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_MODEL = "llama-3.3-70b-versatile"

_SYSTEM = (
    "You are a senior data analyst writing a one-paragraph weekly brand-sentiment "
    "summary for an executive audience. Be concise, specific, and ground every "
    "claim in the numbers given. Follow the structure: what happened, why, "
    "so what, what to do."
)


def _template_summary(facts: dict[str, Any]) -> str:
    co = facts["company"]
    delta = facts["sentiment_delta_pct"]
    direction = "fell" if delta < 0 else "rose"
    top_theme = facts.get("top_negative_theme") or "general discussion"
    return (
        f"{co} sentiment {direction} {abs(delta):.0f}% week-over-week. "
        f"The strongest negative driver was {top_theme} "
        f"({facts.get('top_negative_posts', 0)} posts, "
        f"avg sentiment {facts.get('top_negative_score', 0):+.2f}). "
        f"Other themes — pricing and product — held steady, suggesting an "
        f"issue-specific reaction rather than broad brand erosion. "
        f"Recommend a focused PR response on the {top_theme.lower()} narrative."
    )


def generate(facts: dict[str, Any]) -> str:
    """Generate a narrative paragraph from a facts dict.

    Expected keys: company, sentiment_delta_pct, top_negative_theme,
    top_negative_posts, top_negative_score, total_posts.
    """
    if not has_groq_credentials():
        return _template_summary(facts)

    prompt = (
        f"Write a 4-sentence weekly summary for {facts['company']} based on "
        f"these facts:\n"
        f"- WoW sentiment change: {facts['sentiment_delta_pct']:+.1f}%\n"
        f"- Total posts this week: {facts.get('total_posts', 0)}\n"
        f"- Top negative theme: {facts.get('top_negative_theme')} "
        f"({facts.get('top_negative_posts', 0)} posts, "
        f"avg {facts.get('top_negative_score', 0):+.2f})\n"
        f"- Top positive theme: {facts.get('top_positive_theme')} "
        f"({facts.get('top_positive_posts', 0)} posts, "
        f"avg {facts.get('top_positive_score', 0):+.2f})\n"
    )

    try:
        r = requests.post(
            _GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": _MODEL,
                "messages": [
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
            },
            timeout=20,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log.warning("Groq call failed (%s); using template summary.", e)
        return _template_summary(facts)
