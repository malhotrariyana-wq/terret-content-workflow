"""
Revision module: address reviewer feedback on a draft PR.

When a reviewer leaves a comment on an open draft PR, this module pulls the
current draft, runs a revision pass through Claude that addresses the
feedback while preserving voice, and pushes the revision back to the same
branch. The PR auto-updates.

Two ways to use this:

1. Manual mode — revise one PR based on its latest comment:
   python -m revise.handle_feedback --pr 7

2. Polling mode — check all open draft PRs for new feedback every 60 sec:
   python -m revise.handle_feedback --poll

For the demo, manual mode is what you'd typically show. Polling mode is what
the production system would run as a background job.
"""

import os
import time
import sys
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic
from github import Github

load_dotenv()

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
gh = Github(os.environ["GITHUB_TOKEN"])
repo = gh.get_repo(os.environ["GITHUB_REPO"])

ROOT = Path(__file__).parent.parent
PROMPTS = ROOT / "prompts"
ANCHORS = ROOT / "voice_anchors"


def load_revise_prompt() -> str:
    return (PROMPTS / "revise.txt").read_text()


def load_first_voice_anchor() -> str:
    anchors = sorted(ANCHORS.glob("anchor_*.md"))
    if not anchors:
        return ""
    return anchors[0].read_text()


def revise_draft(pr_number: int, feedback: str) -> str:
    """
    Pull the current draft from a PR, generate a revision addressing the
    feedback, push it to the same branch.

    Returns a status string.
    """
    print(f"\n🔄 Revising draft in PR #{pr_number}")
    print(f"   Feedback: {feedback[:120]}{'...' if len(feedback) > 120 else ''}\n")

    pr = repo.get_pull(pr_number)
    branch_name = pr.head.ref

    # Find the markdown file the pipeline added
    md_file = None
    for f in pr.get_files():
        if f.filename.endswith(".md") and "site/src/content/posts/" in f.filename:
            md_file = f
            break
    if not md_file:
        raise ValueError(f"No blog markdown file found in PR #{pr_number}")

    print(f"📄 Reading current draft: {md_file.filename}")
    current_content = repo.get_contents(md_file.filename, ref=branch_name)
    current_text = current_content.decoded_content.decode("utf-8")

    print(f"✍️  Generating revision (Sonnet)...")
    prompt = load_revise_prompt().format(
        original_draft=current_text,
        feedback=feedback,
        voice_anchor=load_first_voice_anchor(),
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    revised_text = response.content[0].text.strip()

    # Strip markdown code fences if Claude wrapped the response
    if revised_text.startswith("```"):
        lines = revised_text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        revised_text = "\n".join(lines)

    print(f"📤 Pushing revision to branch {branch_name}")
    repo.update_file(
        path=md_file.filename,
        message=f"Revision addressing reviewer feedback on PR #{pr_number}",
        content=revised_text,
        sha=current_content.sha,
        branch=branch_name,
    )

    # Post a confirmation comment on the PR
    pr.create_issue_comment(
        f"🤖 **Bot:** I've pushed a revision addressing the feedback above. "
        f"Please re-review the updated draft."
    )

    print(f"✅ Revision pushed and PR comment posted.\n")

    # Notify Slack
    try:
        from notify.slack import notify_revision_pushed
        notify_revision_pushed(pr.html_url, feedback, branch_name)
        print(f"📣 Slack notification sent.")
    except ImportError:
        print(f"⚠️  Slack notification function not found — add notify_revision_pushed to notify/slack.py")

    return f"Revision pushed to {branch_name}"


def _is_bot_comment(body: str) -> bool:
    """Detect comments posted by our bot to avoid infinite loops."""
    return "🤖 **Bot:**" in body or "Bot:" in body


def poll_for_feedback(interval_seconds: int = 60):
    """
    Continuously check all open draft PRs for new reviewer comments.
    When a new comment is found that hasn't been addressed yet, run revise_draft.

    Run this in a terminal during the demo OR as a background job in production.
    """
    print(f"👀 Polling for PR feedback every {interval_seconds}s... (Ctrl+C to stop)\n")

    while True:
        try:
            open_prs = repo.get_pulls(state="open")
            for pr in open_prs:
                # Skip non-pipeline PRs
                if "📝" not in pr.title:
                    continue

                comments = list(pr.get_issue_comments())
                if not comments:
                    continue

                latest = comments[-1]
                if _is_bot_comment(latest.body):
                    continue

                # If the latest non-bot comment hasn't been addressed
                # (no bot comment came after it), process it
                print(f"🆕 New feedback on PR #{pr.number} from {latest.user.login}")
                try:
                    revise_draft(pr.number, latest.body)
                except Exception as e:
                    print(f"❌ Failed to revise PR #{pr.number}: {e}")

            time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n👋 Polling stopped.")
            break
        except Exception as e:
            print(f"⚠️  Polling error: {e}")
            time.sleep(interval_seconds)


def _print_usage():
    print("Usage:")
    print("  python -m revise.handle_feedback --pr <pr_number>")
    print("       Revise the draft in PR <pr_number> based on its latest comment.")
    print()
    print("  python -m revise.handle_feedback --poll [interval_seconds]")
    print("       Continuously poll all open draft PRs for new feedback.")
    print("       Default interval: 60 seconds.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        _print_usage()
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "--pr" and len(sys.argv) == 3:
        pr_number = int(sys.argv[2])
        pr = repo.get_pull(pr_number)
        comments = list(pr.get_issue_comments())
        if not comments:
            print(f"No comments on PR #{pr_number} to address.")
            sys.exit(1)

        latest = next((c for c in reversed(comments) if not _is_bot_comment(c.body)), None)
        if not latest:
            print(f"No non-bot comments found on PR #{pr_number}.")
            sys.exit(1)

        revise_draft(pr_number, latest.body)

    elif mode == "--poll":
        interval = int(sys.argv[2]) if len(sys.argv) == 3 else 60
        poll_for_feedback(interval)

    else:
        _print_usage()
        sys.exit(1)