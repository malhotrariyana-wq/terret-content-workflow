"""
Generation pipeline: LinkedIn post → blog post draft + metadata.

Each stage is a separate Claude call with a focused prompt.
Outputs flow forward through the pipeline.
"""

import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic, APIConnectionError, APIStatusError, APITimeoutError

load_dotenv()

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

ROOT = Path(__file__).parent.parent
PROMPTS = ROOT / "prompts"
ANCHORS = ROOT / "voice_anchors"


def load_prompt(name: str) -> str:
    return (PROMPTS / name).read_text()


def load_voice_anchors() -> list[str]:
    """Load the first 3 voice anchors as strings."""
    anchor_files = sorted(ANCHORS.glob("anchor_*.md"))[:3]
    return [f.read_text() for f in anchor_files]


def call_claude(prompt: str, model: str = "claude-sonnet-4-6", max_tokens: int = 2000) -> str:
    """Single Claude API call. Returns the model's text response.

    Retries on transient Anthropic errors (overload 529, rate limit 429, unavailable 503).
    """
    backoff_s = 2.0
    max_attempts = 6
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except APIStatusError as e:
            if e.status_code in (429, 503, 529) and attempt < max_attempts:
                print(
                    f"   ⏳ API returned HTTP {e.status_code} (busy). "
                    f"Retry in {backoff_s:.0f}s ({attempt}/{max_attempts})..."
                )
                time.sleep(backoff_s)
                backoff_s = min(backoff_s * 2, 60)
                continue
            raise
        except (APIConnectionError, APITimeoutError):
            if attempt < max_attempts:
                print(
                    f"   ⏳ Connection/timeout. Retry in {backoff_s:.0f}s ({attempt}/{max_attempts})..."
                )
                time.sleep(backoff_s)
                backoff_s = min(backoff_s * 2, 60)
                continue
            raise


def parse_json(text: str) -> dict:
    """Safely parse JSON from a Claude response. Strips code fences if present."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


# ----- STAGE A: Insight extraction -----
def stage_a_extract_insight(post: dict) -> dict:
    prompt = load_prompt("stage_a_insight.txt").format(post_text=post["text"])
    raw = call_claude(prompt, model="claude-haiku-4-5", max_tokens=1000)
    return parse_json(raw)


# ----- STAGE B: Angle development -----
def stage_b_develop_angle(insight: dict) -> dict:
    terret_positioning = """
    Terret is an AI-native revenue intelligence platform. Three layers:
    - Revenue Graph: unifies CRM, calls, emails, warehouse data into one model
    - AI Architects: analyze the graph to find patterns that drive wins
    - AI Agents: embed playbooks into CRM, generate call briefs, coach reps
    The system compounds over time. Built for revenue leaders — CROs, RevOps, sales operators.
    """
    prompt = load_prompt("stage_b_angle.txt").format(
        core_insight=insight["core_insight"],
        supporting_points=insight["supporting_points"],
        terret_positioning=terret_positioning
    )
    raw = call_claude(prompt, model="claude-sonnet-4-6", max_tokens=1500)
    return parse_json(raw)


# ----- STAGE C: Outline -----
def stage_c_outline(angle: dict) -> dict:
    prompt = load_prompt("stage_c_outline.txt").format(
        blog_angle=angle["blog_angle"],
        target_reader=angle["target_reader"],
        terret_connection=angle["terret_connection"]
    )
    raw = call_claude(prompt, model="claude-sonnet-4-6", max_tokens=2000)
    return parse_json(raw)


# ----- STAGE D: Draft -----
def stage_d_draft(outline: dict, voice_anchors: list[str]) -> str:
    prompt = load_prompt("stage_d_draft.txt").format(
        voice_anchor_1=voice_anchors[0],
        voice_anchor_2=voice_anchors[1] if len(voice_anchors) > 1 else "",
        voice_anchor_3=voice_anchors[2] if len(voice_anchors) > 2 else "",
        title_draft=outline["title_draft"],
        hook=outline["hook"],
        problem=outline["problem"],
        insight=outline["insight"],
        application=outline["application"],
        terret_connection=outline["terret_connection"],
        cta=outline["cta"]
    )
    return call_claude(prompt, model="claude-sonnet-4-6", max_tokens=3000)


# ----- STAGE E: Refinement -----
def stage_e_refine(draft: str, voice_anchors: list[str]) -> str:
    prompt = load_prompt("stage_e_refine.txt").format(
        draft=draft,
        voice_anchor_1=voice_anchors[0]
    )
    return call_claude(prompt, model="claude-sonnet-4-6", max_tokens=3000)


# ----- STAGE F: SEO metadata -----
def stage_f_seo(draft: str) -> dict:
    prompt = load_prompt("stage_f_seo.txt").format(draft=draft)
    raw = call_claude(prompt, model="claude-haiku-4-5", max_tokens=1500)
    return parse_json(raw)


# ----- ORCHESTRATOR -----
def run_pipeline(post: dict) -> dict:
    """Run the full pipeline on a single LinkedIn post."""
    print(f"📥 Stage A: extracting insight from {post['id']}...")
    insight = stage_a_extract_insight(post)

    if not insight.get("blog_worthy"):
        print(f"⏭  Skipping — not blog-worthy. Reason: {insight['blog_worthy_reasoning']}")
        return {"skipped": True, "insight": insight}

    print(f"🎯 Stage B: developing angle...")
    angle = stage_b_develop_angle(insight)

    print(f"📋 Stage C: outlining...")
    outline = stage_c_outline(angle)

    print(f"✍️  Stage D: drafting...")
    voice_anchors = load_voice_anchors()
    draft = stage_d_draft(outline, voice_anchors)

    print(f"🪞 Stage E: refining...")
    refined = stage_e_refine(draft, voice_anchors)

    print(f"🔎 Stage F: generating metadata...")
    metadata = stage_f_seo(refined)

    return {
        "source_post": post,
        "insight": insight,
        "angle": angle,
        "outline": outline,
        "draft_v1": draft,
        "draft_final": refined,
        "metadata": metadata
    }


if __name__ == "__main__":
    from evals.genericness import check_genericness
    from evals.voice_fit import check_voice_fit
    from evals.aeo_compliance import check_aeo_compliance
    from notify.slack import notify_draft_ready
    from publish.github_pr import publish_draft_as_pr

    posts = json.loads((ROOT / "data" / "justin_posts.json").read_text())
    result = run_pipeline(posts[0])

    if result.get("skipped"):
        print("Pipeline skipped — post not blog-worthy")
        exit(0)

    print("\n🔬 Running evals...")
    result["evals"] = {
        "genericness": check_genericness(result["draft_final"]),
        "voice_fit": check_voice_fit(result["draft_final"]),
        "aeo_compliance": check_aeo_compliance(result["metadata"])
    }

    eval_summary = (
        f"Genericness {result['evals']['genericness']['score']}/10 | "
        f"Voice {result['evals']['voice_fit']['voice_fit_score']}/10 | "
        f"AEO {'✅' if result['evals']['aeo_compliance']['passes'] else '❌'}"
    )
    print(f"   {eval_summary}")

    print("\n📤 Publishing draft as PR...")
    pr_url = publish_draft_as_pr(result)
    print(f"   PR opened: {pr_url}")

    print("\n📣 Notifying Slack...")
    title = result["metadata"]["title"]
    preview = result["draft_final"][:300]
    notify_draft_ready(title, preview, pr_url, eval_summary)
    print(f"   Slack notification sent")

    # Save the full result for the README/example
    result["pr_url"] = pr_url
    output_path = ROOT / "examples" / f"{posts[0]['id']}_result.json"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2))
    print(f"\n✅ Full result saved to {output_path}")