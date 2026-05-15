"""
Voice fit check: how closely does the draft match Terret's voice anchors?
"""

import os
import json
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

ROOT = Path(__file__).parent.parent


VOICE_FIT_PROMPT = """You are evaluating how closely a draft matches Terret's editorial voice.

Compare the DRAFT to the VOICE ANCHOR. Look at:
- Sentence rhythm (short vs long)
- Vocabulary (operator-y vs corporate)
- Use of "you" vs third person
- Concreteness (specific examples vs abstract claims)
- Confidence (assertive vs hedging)

VOICE ANCHOR:
\"\"\"
{anchor}
\"\"\"

DRAFT TO EVALUATE:
\"\"\"
{draft}
\"\"\"

Return ONLY valid JSON:
{{
  "voice_fit_score": <integer 1-10>,
  "matches_well": ["<thing 1>", "<thing 2>"],
  "drifts_in": ["<thing 1>", "<thing 2>"],
  "suggested_fixes": ["<fix 1>", "<fix 2>"]
}}
"""


def check_voice_fit(draft: str) -> dict:
    anchor_path = sorted((ROOT / "voice_anchors").glob("anchor_*.md"))[0]
    anchor = anchor_path.read_text()

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": VOICE_FIT_PROMPT.format(anchor=anchor, draft=draft)}]
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)