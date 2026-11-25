
import os
import json
import requests

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-2.5-flash:generateContent"
)

PROMPT = """
You are a market analyst. Estimate the market for this project.

Project: {project_name} ({project_type})
Target market: {target_market}
Budget (USD): {budget}
Description: {description}

Reply ONLY with valid JSON in exactly this shape:

{{
    "tam": "$2.4B",
    "sam": "$850M",
    "som": "$12M",
    "trends": [
        {{
            "year": 2020,
            "market_size_usd_m": 100
        }}
    ],
    "competitors": [
        {{
            "name": "",
            "type": "Direct or Indirect",
            "market_share": "22%",
            "revenue": "$38M",
            "growth": "+8%",
            "risk": "High, Medium or Low"
        }}
    ]
}}

Requirements:
- Give market trends for every year from 2020 to 2026.
- Include exactly 3 competitors.
- Use realistic estimates.
- Return JSON only, without Markdown formatting.
"""


def analyze(project):

    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Check your .env file."
        )

    # Prepare prompt
    try:
        formatted_prompt = PROMPT.format(**project)

    except KeyError as e:
        raise RuntimeError(
            f"Missing project information required for market analysis: {e}"
        )

    # Prepare Gemini request
    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": formatted_prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.3
        }
    }

    try:
        response = requests.post(
            GEMINI_API_URL,
            params={"key": api_key},
            json=body,
            timeout=60
        )

        # Check HTTP errors
        if not response.ok:
            try:
                error_data = response.json()
                error_message = error_data.get(
                    "error", {}
                ).get("message", response.text)
            except ValueError:
                error_message = response.text

            raise RuntimeError(
                f"Gemini API error ({response.status_code}): "
                f"{error_message}"
            )

        # Parse response
        try:
            data = response.json()
        except ValueError:
            raise RuntimeError(
                "Gemini returned an invalid JSON response."
            )

        # Check whether candidates exist
        candidates = data.get("candidates")

        if not candidates:
            error_message = data.get(
                "error", {}
            ).get("message", "No candidates returned by Gemini.")

            raise RuntimeError(
                f"Gemini did not generate a response: {error_message}"
            )

        candidate = candidates[0]

        # Check candidate content
        content = candidate.get("content", {})
        parts = content.get("parts", [])

        if not parts:
            finish_reason = candidate.get(
                "finishReason", "Unknown"
            )

            raise RuntimeError(
                f"Gemini returned no text. Finish reason: {finish_reason}"
            )

        generated_text = parts[0].get("text", "")

        if not generated_text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        # Convert generated JSON text into a Python dictionary
        try:
            result = json.loads(generated_text)

        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Gemini returned invalid JSON: {e}"
            )

        # Validate expected response structure
        required_keys = [
            "tam",
            "sam",
            "som",
            "trends",
            "competitors"
        ]

        missing_keys = [
            key for key in required_keys
            if key not in result
        ]

        if missing_keys:
            raise RuntimeError(
                f"Market analysis response is missing fields: {missing_keys}"
            )

        return result

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Gemini API request timed out. Please try again."
        )

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Could not connect to Gemini API. Check your internet connection."
        )
