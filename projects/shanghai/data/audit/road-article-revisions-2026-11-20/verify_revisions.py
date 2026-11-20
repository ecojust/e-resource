"""Replay pinned Wikipedia revisions and verify the road index and extracted link positions."""
import argparse
import json
import time
from collections import defaultdict
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from extract import SOURCES, building_titles, digest, explicit_mentions

ENDPOINT = "https://zh.wikipedia.org/w/api.php"
AGENT = "e-resource Shanghai road reference review/1.0 (+https://github.com/ecojust/e-resource)"


def request_batch(revisions):
    params = {"action": "query", "format": "json", "formatversion": 2, "prop": "revisions",
              "revids": "|".join(map(str, revisions)), "rvprop": "ids|timestamp|content",
              "rvslots": "main", "maxlag": 5}
    request = Request(ENDPOINT + "?" + urlencode(params), headers={"User-Agent": AGENT})
    for attempt in range(4):
        try:
            with urlopen(request, timeout=45) as response:
                result = json.load(response)
        except HTTPError as exc:
            if exc.code not in (429, 503) or attempt == 3:
                raise
            time.sleep(int(exc.headers.get("Retry-After", "10")))
            continue
        if result.get("error", {}).get("code") == "maxlag" and attempt < 3:
            time.sleep(10)
            continue
        return result["query"]["pages"]


def verify(index):
    roads = json.loads((SOURCES / "discovered-streets.json").read_bytes())["roads"]
    for key, file in [("road_index_sha256", "discovered-streets.json"), ("building_index_sha256", "discovered-buildings.json")]:
        if digest((SOURCES / file).read_bytes()) != index[key]:
            raise ValueError(f"Source index changed: {file}")
    if [(r["id"], r["name"]) for r in roads] != [(r["road_id"], r["indexed_name"]) for r in index["roads"]]:
        raise ValueError("Road IDs or indexed names differ")
    known = building_titles()
    groups = defaultdict(list)
    for road, row in zip(roads, index["roads"]):
        if not road["article_url"]:
            if row.get("status") != "name-only-in-original-road-index" or "revision" in row:
                raise ValueError(f"Indexed name without source URL: {row['road_id']}")
            continue
        groups[row["revision"]].append(row)
    revisions = sorted(groups)
    checked = set()
    for start in range(0, len(revisions), 25):
        for page in request_batch(revisions[start:start + 25]):
            for rev in page["revisions"]:
                revision = rev["revid"]
                body = rev["slots"]["main"]["content"]
                raw = body.encode()
                actual = (page["pageid"], page["title"], rev["timestamp"], len(raw), digest(raw), explicit_mentions(body, known))
                for row in groups[revision]:
                    recorded = (row["page_id"], row["title"], row["revision_utc"], row["wikitext_bytes"],
                                row["wikitext_sha256"], row.get("numbered_building_list_links", []))
                    if actual != recorded:
                        raise ValueError(f"Revision data differs for {row['road_id']} ({revision})")
                checked.add(revision)
        if start + 25 < len(revisions):
            time.sleep(1.25)
    if checked != set(revisions):
        raise ValueError("At least one pinned revision was unavailable")
    print(f"Verified {len(checked)} unique revisions for {sum(map(len, groups.values()))} indexed links.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path)
    verify(json.loads(parser.parse_args().index.read_bytes()))
