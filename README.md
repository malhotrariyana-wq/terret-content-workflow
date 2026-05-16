# Terret Content Workflow
 
> An agentic content workflow that converts Justin Shriber's LinkedIn posts into polished Terret blog posts — with human approval before publication.
 
**Live demo:** [terret-content-workflow.vercel.app][LIVE_URL] · **Example post:** [Why your sales forecast breaks where reps stop updating CRM][POST_URL] · **Example PR (the approval moment):** [#2][PR_URL]
 
> *Replace the bracketed links above with your actual URLs before publishing.*
 
---
 
## TL;DR
 
A 6-stage Claude-powered generation pipeline. An eval layer that explicitly checks for "generic AI slop" — the brief's stated failure mode. A GitHub PR-as-approval flow. A dark-themed Astro site that auto-deploys to Vercel.
 
Built around one principle: **output quality is the only thing that matters. Automation is secondary.**
 
---
 
## The Problem
 
A small marketing team wants to scale content output by turning an influencer's posts into branded blog content. The hard part isn't automation.
 
It's avoiding the generic AI slop that makes most "AI-generated content" unusable.
 
The brief flagged it directly:
 
> *"Generic AI-generated blog posts that could have been written about anything"* is what fails this project.
 
So this system is designed first for output quality, second for everything else.
 
---
 
## Architecture
 
Four layers — mapping directly to the brief's evaluation criteria.
 
```
┌─────────────────────────────────────────────────────────────┐
│  MONITORING       Justin's LinkedIn posts → posts.json      │
├─────────────────────────────────────────────────────────────┤
│  SYNTHESIS        6-stage pipeline:                         │
│                   A. Insight   →  B. Angle  →  C. Outline   │
│                   D. Draft     →  E. Refine →  F. SEO/AEO   │
├─────────────────────────────────────────────────────────────┤
│  HUMAN CONTROL    Slack notification → GitHub PR → merge    │
├─────────────────────────────────────────────────────────────┤
│  ACTIVATION       Astro markdown → Vercel auto-deploy       │
└─────────────────────────────────────────────────────────────┘
 
         CROSS-CUTTING:  eval layer
         (genericness  ·  voice fit  ·  AEO compliance)
```
 
### What each layer does — and why
 
**Monitoring.** Justin's posts in `data/justin_posts.json`. Manual ingestion for the prototype; production would use Apify. The brief invited me to scope this out, so I did — LinkedIn scraping is a multi-week ToS problem and output quality is where the project is actually graded.
 
**Synthesis.** Six focused Claude calls instead of one mega-prompt. The mega-prompt would be faster to build, but black-box when it fails. Six stages = per-stage evals when something drifts.
 
**Human control.** Slack notification fires with a link to a GitHub PR. Merge = approve. Close = reject. Comment = request edits. Git history *is* the audit log.
 
**Activation.** Approved markdown gets committed to main and Vercel auto-deploys. The live post has full structured data — JSON-LD, FAQ schema, `llms.txt` at site root — so the content surfaces in AI answer engines, not just human search.
 
---
 
## Live Example
 
One complete LinkedIn post → blog post cycle, fully run.
 
| Stage | What it does | Output |
|---|---|---|
| **Source** | Justin's Ferrari-analogy LinkedIn post | [`data/justin_posts.json` → post_001][SRC_URL] |
| **Stage A — Insight** | Extracts the core operator argument | [JSON][STAGE_A] |
| **Stage B — Angle** | Develops the Terret-specific framing | [JSON][STAGE_B] |
| **Stage C — Outline** | Structures the blog post | [JSON][STAGE_C] |
| **Stage D — Draft** | Drafts in Terret's voice (grounded in anchors) | [draft][STAGE_D] |
| **Stage E — Refine** | Editor pass for voice fit + AI tells | [refined][STAGE_E] |
| **Stage F — SEO/AEO** | Generates title, slug, FAQ schema, JSON-LD | [metadata][STAGE_F] |
| **Notification** | Slack message with eval scores + PR link | [screenshot][SLACK_SS] |
| **Approval** | The PR (merge = approval) | [PR #2 — merged][PR_URL] |
| **Published** | Auto-deployed to Vercel | [live blog post][POST_URL] |
 
### Eval scores on the published version
 
| Metric | Score | Status |
|---|---|---|
| Genericness | 6/10 | ⚠ improving (see iteration log) |
| Voice fit | 8/10 | ✓ |
| AEO compliance | passes all checks | ✓ |
 
The full diagnostic JSON is at `examples/post_001_result.json`.
 
---
 
## Judgment Calls
 
The seven decisions I'd defend in a code review.
 
### Multi-stage pipeline over single mega-prompt
 
Six focused Claude calls. Each stage has a tight system prompt, isolated context, and per-piece evals. The mega-prompt alternative would be faster to write but I'd have no idea which step broke when it fails.
 
### Sonnet 4.6 for drafting, Haiku 4.5 for classification
 
Voice quality matters most in Stage D. Sonnet shows up there. Stages A and F are classification/extraction work — Haiku is plenty smart for that and ~10x cheaper. Production agents mix models like this rather than pay Sonnet rates for the inner loop.
 
### The "what this is NOT" field in Stage B
 
> *The move I'm most proud of.*
 
The brief explicitly warned against generic AI content. Most prompt engineering tries to prevent generic output indirectly. I made the agent name the generic angle it's *rejecting* as part of its output. That single field is what moved my genericness eval score from 4 → 6 in iteration 3.
 
### GitHub PR merge as the approval action
 
Free, audit-logged via git history, no UI to build. The Slack notification deep-links to the PR. Merge = approve.
 
The downside: reviewers need GitHub access. Fine for engineering-adjacent marketing teams; not fine for pure marketing orgs — that's a v2 fix.
 
### The genericness eval (LLM-as-judge)
 
> *Most candidates will skip this.*
 
The brief literally describes its own failure mode as *"generic AI-generated blog posts that could have been written about anything."* Building an eval that checks for exactly that — by asking the model to mentally swap "Terret" with "Acme Corp" and check if the post still makes sense — is the most direct response to the brief's stated risk.
 
Imperfect (LLM-as-judge has known calibration issues). But any measurable signal beats no signal.
 
### JSON-LD + FAQ schema + llms.txt for AEO
 
AEO (Answer Engine Optimization) is the 2025–26 concern of being cited by ChatGPT, Perplexity, and Google AI Overviews. Distinct from SEO.
 
The brief specifically asked how the post would *"surface in AI-generated answers, not just human search"* — this is the technical answer. Most blog systems ignore this layer.
 
### Astro + Vercel + GitHub for the CMS
 
Markdown frontmatter = real structured content. Git commit = real publish event. Vercel auto-deploy = real publish UX. All free.
 
WordPress was the conventional alternative but its API is heavier; the integration would have eaten time better spent on output quality.
 
### Site design intentionally mimics Terret's visual brand
 
Dark theme. Orange TL;DR bullets. Statement-style H2 borders. Monospace dates.
 
Inspired-by, not pixel-cloned. The brief tests *"does it read like something a real marketing team would publish?"* — visual fit matters as much as voice fit.
 
---
 
## Iteration Log
 
The blog draft went through three iterations. Each was driven by the eval layer flagging a specific failure.
 
| Iteration | Genericness | Voice fit | AEO |
|---|---|---|---|
| **v1** (manual rubric) | 31/42 overall | — | — |
| **v2** | 4/10 ❌ | 7/10 ⚠ | ❌ |
| **v3 (shipped)** | 6/10 ⚠ | 8/10 ✓ | ✓ |
 
### v1 → v2: structural failures
 
**What broke.** No TL;DR. No FAQ. One fabricated statistic. Title at 92 characters (over the cap). Generic "book a demo" CTA. Heavy product-pitch paragraph.
 
**What I changed.** Stage D rewritten with mandatory TL;DR + FAQ structure, real-customers-only rule, no-fabricated-stats rule, soft Terret mention cap. Stage E rewritten as a systematic 11-item verification checklist. Stage F with a hard 65-character title cap.
 
### v2 → v3: genericness defense
 
**What broke.** Genericness still at 4/10. The post argued a generic SaaS point, not a Terret-specific one. Title at 49 characters, one below the 50-char minimum.
 
**What I changed.** Added a "Genericness Defense" block to Stage D — mandatory named Terret customer with specific outcome, mandatory Terret-signature terminology in the body, mandatory reference to Terret's compounding-system thesis (not just "AI helps"). Loosened Stage F's title minimum after observing real Terret titles range from 26 to 70 characters.
 
> The diagnostic-driven loop — eval flags a specific failure → targeted prompt update → re-run → measure — is the workflow the brief was actually testing for.
 
---
 
## What Breaks
 
Honest failure modes. Production fixes named.
 
**1. The genericness eval is itself an LLM judge.** Calibration risk: if my judge thinks "Terret-specific" looks one way and a real reviewer thinks it looks another, drafts pass the eval and still feel generic. *Fix: multi-reviewer eval set, not pure LLM-as-judge.*
 
**2. The voice anchor library is static.** As Terret's editorial voice evolves, the agent drifts toward yesterday's voice. *Fix: marketer edits feed back into anchor updates so the system compounds.*
 
**3. LinkedIn ingestion is the real long-term hard part.** Manual works for the prototype. Apify is the production path, but ToS risk is real and would need legal sign-off.
 
**4. GitHub PR approval requires GitHub access.** Fine for engineering-adjacent teams; bad for pure marketing orgs. *Fix: Retool app or Slack interactive buttons with audit.*
 
**5. The Astro `slug` schema bug.** Astro 4.x deprecated user-defined `slug` fields in content schemas. My deployment failed on Vercel until I removed `slug` from the schema and switched the template to `post.slug`. Two-line fix — but exactly the integration-layer brittleness that bites every CMS workflow. *Fix: local CI build step that catches schema mismatches before pushing.*
 
**6. Video-format LinkedIn posts.** The pipeline ingests text only. Justin's video posts have thin written captions. *Fix: extend to Whisper or AssemblyAI transcription and route through the same pipeline.*
 
**7. No learning loop across drafts.** Approved drafts don't improve future ones. Rejected drafts don't either. The system is iterative within a single draft, not iterative across drafts.
 
---
 
## What I'd Build Next
 
Prioritized by impact, not effort.
 
1. **Close the eval loop.** Marketer edits feed back into voice anchors and prompt updates. The system compounds — every approval makes the next draft better.
2. **Production approval UI.** Slack interactive buttons or a Retool app. Removes the GitHub dependency for non-technical reviewers.
3. **Automated LinkedIn ingestion.** Apify integration with rate-limit handling and a fallback to manual upload for thin posts.
4. **Multi-author voice fingerprinting.** Generalize from Justin to arbitrary Terret leadership.
5. **A/B angle variants.** Generate 2–3 versions per insight; let marketing pick. The choice itself becomes signal.
---
 
## How to Run It
 
```bash
git clone https://github.com/[username]/terret-content-workflow.git
cd terret-content-workflow
 
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
 
cd site && npm install && cd ..
 
cp .env.example .env
# fill in: ANTHROPIC_API_KEY, SLACK_WEBHOOK_URL, GITHUB_TOKEN, GITHUB_REPO
 
python -m generate.pipeline
```
 
The pipeline takes ~30–60 seconds, opens a PR with the draft, and sends a Slack notification.
 
---
 
## Tech Stack
 
| Layer | Tool | Why |
|---|---|---|
| LLM | Claude Sonnet 4.6 + Haiku 4.5 | Mix: Sonnet for planning/drafting, Haiku for classification |
| Orchestration | Plain Python | Readable, debuggable, no framework lock-in |
| Notification | Slack incoming webhook | Free, where marketers live |
| Approval | GitHub PR merge | Free, audit-logged, no UI to build |
| CMS | Astro + Vercel | Markdown frontmatter + auto-deploy + free |
| Evals | Custom Python | LLM-as-judge (genericness, voice) + rule-based (AEO) |
 
---
 
## Repo Structure
 
```
terret-content-workflow/
├── data/
│   └── justin_posts.json          # 12 ranked Justin LinkedIn posts
├── voice_anchors/                  # 6 Terret blog voice anchors
├── prompts/                        # 6 stage prompt files (v3)
├── generate/
│   └── pipeline.py                 # 6-stage orchestrator
├── evals/
│   ├── genericness.py              # LLM-as-judge
│   ├── voice_fit.py                # LLM-as-judge
│   └── aeo_compliance.py           # rule-based
├── notify/
│   └── slack.py
├── publish/
│   └── github_pr.py                # commit + open PR
├── site/                           # Astro CMS, auto-deploys to Vercel
├── examples/
│   ├── post_001_result.json        # full diagnostic for live example
│   └── iteration_log.md            # v1 → v2 → v3 detail
└── voice_guidelines.md
```
 
---
 
*Built as a project submission for the Terret Agentic Workflow Intern role — 2026*
*Riyana Malhotra · [LinkedIn][AUTHOR_LINKEDIN]*
 
[LIVE_URL]: #
[POST_URL]: #
[PR_URL]: #
[SRC_URL]: #
[STAGE_A]: #
[STAGE_B]: #
[STAGE_C]: #
[STAGE_D]: #
[STAGE_E]: #
[STAGE_F]: #
[SLACK_SS]: #
[AUTHOR_LINKEDIN]: #