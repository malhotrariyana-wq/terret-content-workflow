"""
Slack notification for a new draft ready for review.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
# Set SLACK_WEBHOOK_URL in .env (do not commit the URL to git).
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]


def notify_draft_ready(title: str, preview: str, pr_url: str, eval_summary: str):
    """Post an interactive Slack message announcing a new blog draft."""
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📝 New blog draft ready for review"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{title}*"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"_Preview:_\n{preview[:300]}..."}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Eval results:* {eval_summary}"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🔗 Review PR"},
                        "url": pr_url,
                        "style": "primary"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": "Approve = merge PR. Reject = close PR. Request edits = comment on PR."}]
            }
        ]
    }
    r = requests.post(SLACK_WEBHOOK_URL, json=payload)
    r.raise_for_status()
    return r.status_code