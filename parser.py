import google.generativeai as genai
import json


def extract_tender_data(content: str, api_key: str, source_url: str = ""):
    """
    Uses Google Gemini AI to extract structured tender data from raw webpage text.
    Returns (data_dict, error_message).
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""You are a data extraction specialist for commercial tenders and government projects.

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

        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown fences if model added them
        raw = raw.replace("```json", "").replace("```", "").strip()

        data = json.loads(raw)
        return data, None

    except json.JSONDecodeError as e:
        return None, f"AI returned invalid JSON: {str(e)}"
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
            return None, "Invalid API key. Please check your Gemini API key."
        if "quota" in error_msg.lower():
            return None, "Free quota exceeded. Please wait and try again later."
        return None, error_msg
