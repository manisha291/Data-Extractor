import google.generativeai as genai
import json
import time

# Models to try in order — if one is rate-limited, falls back to next
# Using stable, free-tier compatible models
MODELS = [
    "gemini-1.5-flash",      # Most reliable for free tier
    "gemini-pro",             # Fallback option
]

PROMPT_TEMPLATE = """You are a data extraction specialist for commercial tenders and government projects.

Analyze the webpage content below and extract all relevant tender/project information.

Return a JSON object with EXACTLY these fields (use null for any field not found):
{{
  "title": "Full project or tender title",
  "tender_id": "Reference number or tender ID",
  "issuing_authority": "Organization, department, or government body issuing the tender",
  "category": "Type of work (e.g. Civil Works, IT Services, Supply of Goods, Consultancy, Construction)",
  "deadline": "Submission or closing deadline date",
  "budget": "Estimated value, contract amount, or budget range",
  "location": "City, state, region, or country",
  "status": "Current status (Open / Closed / Under Evaluation / Upcoming)",
  "description": "Brief 1-2 sentence summary of what the project involves",
  "source_url": "{source_url}"
}}

Rules:
- Return ONLY the JSON object. No explanation, no markdown, no code fences.
- If a field genuinely cannot be found, use null.
- Keep description concise and factual.
- For budget, include currency symbol if visible.

Webpage content:
{content}"""


def extract_tender_data(content: str, api_key: str, source_url: str = ""):
    """
    Uses Google Gemini AI to extract structured tender data from raw webpage text.
    Retries up to 3 times with delays, and falls back across multiple models.
    Returns (data_dict, error_message).
    """
    genai.configure(api_key=api_key)
    prompt = PROMPT_TEMPLATE.format(source_url=source_url, content=content)
    last_error = "Unknown error"

    for model_name in MODELS:
        for attempt in range(3):  # up to 3 retries per model
            try:
                # Add delay between requests to avoid rate limiting
                time.sleep(2)
                
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                raw = response.text.strip()
                raw = raw.replace("```json", "").replace("```", "").strip()
                data = json.loads(raw)
                return data, None

            except json.JSONDecodeError as e:
                return None, f"AI returned invalid JSON: {str(e)}"

            except Exception as e:
                error_msg = str(e)

                if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
                    return None, "Invalid API key. Please check your Gemini API key in Streamlit Secrets."

                is_quota = (
                    "quota" in error_msg.lower() or
                    "rate" in error_msg.lower() or
                    "429" in error_msg or
                    "resource_exhausted" in error_msg.lower() or
                    "404" in error_msg  # Handle 404 model not found errors
                )

                if is_quota:
                    last_error = error_msg
                    wait = (attempt + 1) * 15  # 15s, 30s, 45s
                    time.sleep(wait)
                    continue  # retry same model

                # Non-quota error — try next model immediately
                last_error = error_msg
                break

    return None, (
        "All Gemini models are currently rate-limited on the free tier. "
        "Please wait 1-2 minutes and try again. "
        f"Last error: {last_error}"
    )
