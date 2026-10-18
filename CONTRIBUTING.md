# Contribute a useful example

Read the [workflow](docs/authoring-workflow.md), choose one distinct reader decision, and create both a complete article and a companion annotation. Use primary sources for factual guidance. Identify the example business openly and keep its factual claims within verified scope.

Do not submit private business records, credentials, customer identifiers, fabricated reviews or projects, hidden promotional personas, keyword lists, or near-identical county pages. Keep unresolved information in the editorial brief rather than inside example copy. Write original explanations and tools instead of copying source prose.

## Article convention

Each file under `examples/` uses a small, deliberately restricted frontmatter format: one JSON-quoted string per line, no nested YAML, and these keys:

```yaml
title: "An accurate title"
description: "A plain summary of the reader's task"
content_type: "informational-example"
status: "educational-sample"
example_business: "Out West Septic"
source_checked: "2026-10-18"
annotation: "../../annotations/the-article-name.md"
```

Wrap the block in `---` delimiters in the actual article. Use the real source-review date. `content_type` may be `service-example` or `informational-example`. Include one H1 and a visible educational-example notice; link to the matching annotation. Suggested metadata does not become website metadata unless the publishing system maps it.

The annotation should cover audience, search intent, title/description, heading logic, sources and limitations, internal links, CTA, and adaptation. Add new source entries to the [register](docs/source-register.md).

## Run checks

Python 3.10 or newer is sufficient; no third-party packages are needed. From the repository root:

```text
python scripts/check_content.py
python scripts/check_content.py --external
git diff --check
```

The local check validates the article convention, heading structure, annotation references, repository-relative Markdown links and fragments, and obvious draft markers in articles. `--external` additionally makes an HTTP GET request for every unique external Markdown link, follows redirects, and reports non-success responses. It does not validate the meaning or trustworthiness of the destination, and HTTP success can still hide a soft error page. The human review must open the cited material and compare it with the claim.

The link parser covers the ordinary inline links used in this library; use percent encoding for parentheses in URLs. It is not a general Markdown linter. Network blocks and rate limits should be investigated and reported separately from confirmed broken links.

Before requesting review, inspect the full diff for private content, check that no placeholder became a factual claim, and confirm every story and business statement has evidence. Test the destination website separately if publishing there.

There is no hosted CI workflow in this initial library. Keep the exact local results with the PR. All publication and merge decisions remain with the repository owner.
