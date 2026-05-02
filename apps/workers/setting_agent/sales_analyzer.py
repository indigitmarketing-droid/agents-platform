"""Claude analyzer for D-Phase2 sales call transcripts."""
import json
import logging

from apps.workers.setting_agent.transcript_analyzer import AnalysisError

logger = logging.getLogger(__name__)

VALID_OUTCOMES = {"accepted_pay", "interested_no_call", "rejected", "unclear"}
MAX_RETRIES = 3
MODEL = "claude-sonnet-4-6"


def analyze_sales_transcript(transcript: str, lead: dict, claude_client) -> dict:
    """Analyze sales call transcript. Returns {outcome, sales_brief}.

    Outcomes:
    - accepted_pay: customer agreed to pay, ready for the link
    - interested_no_call: customer wants info via SMS/email, will think about it
    - rejected: explicit no, do not call back
    - unclear: ambiguous, retry needed
    """
    if not transcript or not transcript.strip():
        raise AnalysisError("empty transcript")

    prompt = f"""You are analyzing a SALES call transcript for a website service.
The agent is closing a sale at $349 USD one-time fee. The first call already qualified the lead;
this second call is the close.

Transcript:
{transcript}

Customer info:
- Company: {lead.get('company_name', '?')}
- Phone: {lead.get('phone', '?')}

Classify the outcome as ONE of:
- accepted_pay: customer agreed to pay, ready to receive the link
- interested_no_call: customer said "send me info / I'll think about it / send to my email"
- rejected: explicit "no", do not call back, not interested
- unclear: ambiguous, retry needed

Respond ONLY with valid JSON: {{"outcome": "...", "sales_brief": "1-sentence summary"}}"""

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = claude_client.messages.create(
                model=MODEL,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            data = json.loads(text)
            if data.get("outcome") in VALID_OUTCOMES:
                return {
                    "outcome": data["outcome"],
                    "sales_brief": data.get("sales_brief", ""),
                }
            last_error = f"invalid outcome: {data.get('outcome')}"
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            last_error = str(e)
            continue

    raise AnalysisError(f"Could not parse sales outcome after {MAX_RETRIES} retries: {last_error}")
