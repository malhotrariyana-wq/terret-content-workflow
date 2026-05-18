"""
Slack notification for new blog drafts AND for draft revisions
addressing reviewer feedback.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
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
                "elements": [{"type": "mrkdwn", "text": "Approve = merge PR · Reject = close PR · Request edits = comment on PR (agent will revise)"}]
            }
        ]
    }
    r = requests.post(SLACK_WEBHOOK_URL, json=payload)
    r.raise_for_status()
    return r.status_code


def notify_revision_pushed(pr_url: str, original_feedback: str, branch_name: str):
    """
    Post a Slack message when a draft has been revised in response to reviewer feedback.
    """
    feedback_preview = original_feedback[:200] + ("..." if len(original_feedback) > 200 else "")
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🔄 Draft revised in response to feedback"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Reviewer asked for:*\n>_{feedback_preview}_"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "I've pushed a revision addressing the feedback. The PR is updated — please re-review."}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🔗 Review revised PR"},
                        "url": pr_url,
                        "style": "primary"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"Branch: `{branch_name}`"}]
            }
        ]
    }
    r = requests.post(SLACK_WEBHOOK_URL, json=payload)
    r.raise_for_status()
    return r.status_code