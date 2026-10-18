"""Check this library's documented Markdown convention; standard library only."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[[^\]\n]+\]\(([^\s)]+)\)")
KEYS = {"title", "description", "content_type", "status", "example_business", "source_checked", "annotation"}


def prose(text: str) -> str:
    return re.sub(r"^```[^\n]*\n.*?^```\s*$", "", text, flags=re.M | re.S)


def anchors(text: str) -> set[str]:
    counts: dict[str, int] = {}
    result: set[str] = set()
    for heading in re.findall(r"^#{1,6}\s+(.+)$", prose(text), flags=re.M):
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        result.add(slug if count == 0 else f"{slug}-{count}")
        counts[slug] = count + 1
    return result


def check_external(url: str) -> tuple[str, bool, str]:
    try:
        request = Request(url, headers={"User-Agent": "SepticContentLibrary-LinkCheck/1.0"})
        with urlopen(request, timeout=25) as response:
            response.read(1024)
            status = response.status
            final = response.url
        return url, 200 <= status < 300, f"{status}" + (f" -> {final}" if final != url else "")
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        return url, False, str(error)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external", action="store_true", help="also check live HTTP links")
    args = parser.parse_args()
    errors: list[str] = []
    urls: set[str] = set()
    local_count = 0
    documents = sorted(ROOT.rglob("*.md"))
    articles = 0
    for path in documents:
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        body = text
        if relative.startswith("examples/"):
            articles += 1
            if not text.startswith("---\n") or "\n---\n" not in text[4:]:
                errors.append(f"{relative}: missing frontmatter")
                continue
            header, body = text[4:].split("\n---\n", 1)
            fields: dict[str, str] = {}
            for line in header.splitlines():
                match = re.fullmatch(r"([a-z_]+): (.+)", line)
                if not match:
                    errors.append(f"{relative}: malformed frontmatter line")
                    continue
                key, raw = match.groups()
                try:
                    value = json.loads(raw)
                    if not isinstance(value, str) or not value:
                        raise ValueError("expected nonempty quoted string")
                except (ValueError, json.JSONDecodeError):
                    errors.append(f"{relative}: invalid string for {key}")
                    continue
                if key in fields:
                    errors.append(f"{relative}: duplicate key {key}")
                fields[key] = value
            if set(fields) != KEYS:
                errors.append(f"{relative}: keys differ from documented convention")
            if fields.get("status") != "educational-sample":
                errors.append(f"{relative}: incorrect sample status")
            if fields.get("content_type") not in {"service-example", "informational-example"}:
                errors.append(f"{relative}: unsupported content type")
            try:
                date.fromisoformat(fields.get("source_checked", ""))
            except ValueError:
                errors.append(f"{relative}: invalid source-check date")
            annotation = (path.parent / fields.get("annotation", "")).resolve()
            if not annotation.is_relative_to(ROOT / "annotations") or not annotation.is_file():
                errors.append(f"{relative}: invalid annotation path")
            if not re.search(r"^> .*Educational", body, re.M | re.I):
                errors.append(f"{relative}: missing visible educational notice")
            if re.search(r"\b(?:TODO|TBD|FIXME|INSERT HERE)\b|\{\{|\[YOUR\b|PLACEHOLDER", body, re.I):
                errors.append(f"{relative}: possible unresolved draft marker")
        clean = prose(body)
        headings = re.findall(r"^(#{1,6})\s+", clean, flags=re.M)
        if headings.count("#") != 1:
            errors.append(f"{relative}: expected one H1")
        previous = 0
        for heading in headings:
            if len(heading) > previous + 1:
                errors.append(f"{relative}: skipped heading level")
                break
            previous = len(heading)
        for target in LINK.findall(clean):
            parsed = urlsplit(target)
            if parsed.scheme in {"http", "https"}:
                urls.add(target)
                continue
            if parsed.scheme or parsed.netloc:
                errors.append(f"{relative}: unsupported link scheme {target}")
                continue
            local_count += 1
            destination = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not destination.is_relative_to(ROOT) or not destination.is_file():
                errors.append(f"{relative}: broken/outside local link {target}")
            elif parsed.fragment and destination.suffix == ".md":
                if unquote(parsed.fragment) not in anchors(destination.read_text(encoding="utf-8")):
                    errors.append(f"{relative}: missing anchor {target}")
    if articles == 0:
        errors.append("No example articles found")
    if args.external:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for url, ok, result in pool.map(check_external, sorted(urls)):
                print(f"{'OK' if ok else 'CHECK'} {url} {result}")
                if not ok:
                    errors.append(f"External link requires investigation: {url} ({result})")
    print(f"Checked {len(documents)} Markdown files, {articles} examples, {local_count} relative links, {len(urls)} unique external links.")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print("PASS" if not errors else f"FAIL: {len(errors)} finding(s)")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
