"""
Genericness check: would this post work for any B2B SaaS, or is it Terret-specific?

LLM-as-judge. Asks Claude to swap "Terret" with a generic competitor name
and decide whether the post still makes sense.
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


GENERICNESS_PROMPT = """You are evaluating whether a blog post is Terret-specific or could have been written by any B2B SaaS company.

Read the post. Mentally replace every instance of "Terret" with "Acme Corp." If the post still makes sense and is still useful, it's generic. If replacing Terret breaks the post or makes it lose meaning, it's Terret-specific.

POST:
\"\"\"
{post}
\"\"\"

Return ONLY valid JSON:
{{
  "is_generic": true | false,
  "score": <integer 1-10, where 10 = highly Terret-specific>,
  "reasoning": "<2-3 sentence explanation>",
  "specific_things_that_make_it_terret": ["<thing 1>", "<thing 2>"]
}}
"""


def check_genericness(post: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": GENERICNESS_PROMPT.format(post=post)}]
    )
    import json
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)