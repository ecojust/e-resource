"""Index the frozen Chinese Wikipedia road revisions without republishing the articles."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlparse

PROJECT = Path(__file__).resolve().parents[2]
SOURCES = PROJECT / "model-todo"
HEADINGS = re.compile(r"^\s*=+\s*([^=]+?)\s*=+\s*$")
BUILDING_HEADINGS = re.compile(r"建筑|建築|沿[途路街線线]|街景|保护单位|保護單位|历史遗迹|歷史遺跡|景點|景点")
EXCLUDED_HEADINGS = re.compile(r"线路|線路|车站|車站|公交|公共交通|交汇|交會|交叉|参见|參見")
WIKILINK = re.compile(r"\[\[([^\[\]|#]+)(?:#[^\[\]|]*)?(?:\|[^\[\]]*)?\]\]")
NUMBER = re.compile(r"[0-9０-９]+\s*[号號弄支]")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def title_for(url):
    path = urlparse(url).path
    if not path.startswith("/wiki/"):
        return None
    return unquote(path[6:]).replace("_", " ")


def explicit_mentions(wikitext, known_titles):
    """Retain the position of a link on a numbered line in a building-related section."""
    found = []
    heading = ""
    for number, line in enumerate(wikitext.splitlines(), 1):
        title = HEADINGS.match(line)
        if title:
            heading = title.group(1)
            continue
        if not BUILDING_HEADINGS.search(heading) or EXCLUDED_HEADINGS.search(heading):
            continue
        # Exclude inline citations, file captions, galleries and embedded templates.
        # Accept only an explicit bullet or numbered-list row that itself mentions a door number.
        if not line.lstrip().startswith(("*", "#")):
            continue
        body = re.split(r"<ref\b|\{\{|\[\[(?:File|Image|文件|檔案|图像|圖像):", line, maxsplit=1, flags=re.I)[0]
        if not NUMBER.search(body):
            continue
        for linked in dict.fromkeys(value.strip().replace("_", " ") for value in WIKILINK.findall(body)):
            if linked in known_titles:
                found.append({"line": number, "section": heading, "link_title": linked,
                              "possible_register_ids": known_titles[linked]})
    return found


def building_titles():
    buildings = json.loads((SOURCES / "discovered-buildings.json").read_bytes())["records"]
    known_titles = defaultdict(list)
    for row in buildings:
        for url in row["article_links"]:
            title = title_for(url)
            if title and row["id"] not in known_titles[title]:
                known_titles[title].append(row["id"])
    return known_titles


def build(cache):
    roads = json.loads((SOURCES / "discovered-streets.json").read_bytes())["roads"]
    known_titles = building_titles()
    by_input = {}
    for request_file in sorted(cache.glob("*.request")):
        receipt = json.loads(request_file.read_bytes())
        raw = request_file.with_suffix(".json").read_bytes()
        if receipt["status"] != 200 or digest(raw) != receipt["sha256"] or len(raw) != receipt["bytes"]:
            raise ValueError(f"API response does not match {request_file.name}")
        query = json.loads(raw)["query"]
        pages = {row["title"]: row for row in query["pages"]}
        aliases = {r["from"]: r["to"] for key in ("normalized", "converted", "redirects") for r in query.get(key, [])}
        for name in receipt["titles"]:
            title = name
            seen = set()
            while title in aliases:
                if title in seen:
                    raise ValueError(f"Redirect loop at {title}")
                seen.add(title)
                title = aliases[title]
            if name in by_input:
                raise ValueError(f"Duplicate API input {name}")
            by_input[name] = pages[title]
    if set(by_input) != {title_for(r["article_url"]) for r in roads if r["article_url"]}:
        raise ValueError("API inputs differ from indexed road links")
    output = []
    for road in roads:
        record = {"road_id": road["id"], "indexed_name": road["name"]}
        if road["article_url"]:
            page = by_input[title_for(road["article_url"])]
            revision, = page["revisions"]
            body = revision["slots"]["main"]["content"]
            encoded = body.encode()
            record.update(title=page["title"], page_id=page["pageid"], revision=revision["revid"],
                          revision_utc=revision["timestamp"], wikitext_bytes=len(encoded),
                          wikitext_sha256=digest(encoded), permalink=f'https://zh.wikipedia.org/w/index.php?oldid={revision["revid"]}')
            mentions = explicit_mentions(body, known_titles)
            if mentions:
                record["numbered_building_list_links"] = mentions
        else:
            record["status"] = "name-only-in-original-road-index"
        output.append(record)
    return {"road_index_sha256":digest((SOURCES / "discovered-streets.json").read_bytes()),
            "building_index_sha256":digest((SOURCES / "discovered-buildings.json").read_bytes()),"roads":output}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(args.cache), ensure_ascii=False, indent=2) + "\n")
