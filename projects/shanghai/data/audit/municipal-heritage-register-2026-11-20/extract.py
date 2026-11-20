"""Re-create the five municipal register tables from the verified HTML downloads."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from bs4 import BeautifulSoup


HERE = Path(__file__).resolve().parent
DISCOVERY = HERE.parent.parent / "model-todo" / "discovered-buildings.json"
FIELDS = ("code", "original_name_or_user", "listed_name_or_user", "address")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def key(value):
    return "".join(unicodedata.normalize("NFKC", value).split())


def read_rows(page, body):
    soup = BeautifulSoup(body, "html.parser")
    table, = soup.find_all("table")
    records = []
    notes = []
    district = ""
    subrows_left = 0
    for number, tr in enumerate(table.find_all("tr"), 1):
        cells = tr.find_all(["th", "td"], recursive=False)
        fields = [cell.get_text(" ", strip=True) for cell in cells]
        if not fields or key(fields[0]) == "编号":
            continue
        if len(fields) == 1:
            if re.fullmatch(r".+(区|县)", key(fields[0])):
                district = fields[0]
            else:
                notes.append({"table_row": number, "text": fields[0]})
            continue
        if len(fields) == 2:
            assert subrows_left > 0, (page["batch"], number)
            records[-1]["subrows"].append(dict(table_row=number, original_name_or_user=fields[0],
                                               listed_name_or_user=fields[1]))
            subrows_left -= 1
            continue
        assert len(fields) == 4 and district and subrows_left == 0, (page["batch"], number, fields)
        record = {"table_row": number, "district_heading": district, **dict(zip(FIELDS, fields))}
        # Some pages vertically merge all four cells, leaving an empty HTML row.
        # The university record merges only its code and address above six subentries.
        if int(cells[0].get("rowspan", 1)) > 1 and not cells[1].has_attr("rowspan"):
            subrows_left = int(cells[0]["rowspan"]) - 1
            record["subrows"] = []
        records.append(record)
    assert subrows_left == 0 and len(records) == page["expected_records"], page["batch"]
    return records, notes


def match_text(records, discovery):
    by_pair = defaultdict(set)
    by_address = defaultdict(set)
    for row in discovery:
        for address in row["addresses"]:
            if key(address):
                by_address[key(address)].add(row["id"])
                by_pair[key(row["name"]), key(address)].add(row["id"])

    for row in records:
        ids = by_pair[key(row["original_name_or_user"]), key(row["address"])]
        if ids:
            row["name_and_address_matches"] = sorted(ids)
        else:
            hits = by_address.get(key(row["address"]))
            if hits:
                row["address_only_matches"] = sorted(hits)


def extract(source_path, cache, destination):
    source = json.loads(source_path.read_bytes())
    raw_discovery = DISCOVERY.read_bytes()
    assert digest(raw_discovery) == source["discovery_sha256"]
    discovery = json.loads(raw_discovery)["records"]
    output = {"sources": "sources.json", "batches": []}
    for page in source["pages"]:
        body = (cache / page["cache_name"]).read_bytes()
        assert digest(body) == page["sha256"] and len(body) == page["bytes"], page["url"]
        records, notes = read_rows(page, body)
        match_text(records, [row for row in discovery if row["batch"] == page["batch"]])
        counts = Counter(row["code"] for row in records)
        output["batches"].append({
            "batch": page["batch"], "printed_records": len(records),
            "distinct_printed_codes": len(counts), "duplicate_printed_codes": sorted(k for k, count in counts.items() if count > 1),
            "table_notes": notes, "records": records,
        })
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True, help="Directory containing the original five HTML pages")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    extract(HERE / "sources.json", args.cache, args.output)
