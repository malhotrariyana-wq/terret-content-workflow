"""
AEO/SEO deterministic checks. No LLM needed — just rules.
"""


def check_aeo_compliance(metadata: dict) -> dict:
    issues = []

    title = metadata.get("title", "")
    if not (30 <= len(title) <= 70):
        issues.append(f"Title length {len(title)} not in 30-70 range")

    meta_desc = metadata.get("meta_description", "")
    if not (130 <= len(meta_desc) <= 185):
        issues.append(f"Meta description length {len(meta_desc)} not in 130-185 range")

    slug = metadata.get("slug", "")
    if not slug or " " in slug or slug != slug.lower():
        issues.append("Slug must be lowercase with hyphens, no spaces")

    faq = metadata.get("faq_schema", [])
    if len(faq) < 2:
        issues.append(f"Need at least 2 FAQ schema entries, got {len(faq)}")

    if "primary_keyword" not in metadata or not metadata["primary_keyword"]:
        issues.append("Missing primary keyword")

    return {
        "passes": len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues
    }