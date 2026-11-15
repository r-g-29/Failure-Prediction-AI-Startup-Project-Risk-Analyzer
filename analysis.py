# Member 3: asks Gemini for market size, trends and competitors
import os
import json
import requests

KEY = os.getenv("GEMINI_API_KEY")
URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
       "gemini-2.5-flash:generateContent?key=" + str(KEY))

PROMPT = """You are a market analyst. Estimate the market for this project.
Project: {project_name} ({project_type})
Target market: {target_market}
Budget (USD): {budget}
Description: {description}

Reply ONLY with JSON in exactly this shape:
{{"tam": "$2.4B", "sam": "$850M", "som": "$12M",
  "trends": [{{"year": 2020, "market_size_usd_m": 100}}],
  "competitors": [{{"name": "", "type": "Direct or Indirect", "market_share": "22%",
                    "revenue": "$38M", "growth": "+8%", "risk": "High, Medium or Low"}}]}}
Give trends for every year 2020 to 2026 and 3 competitors. These are estimates."""


def analyze(project):
    body = {
        "contents": [{"parts": [{"text": PROMPT.format(**project)}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    r = requests.post(URL, json=body, timeout=60)
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)
