"""Compare the two published numbering systems for Shanghai's second heritage batch."""
import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(path):
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def comparable_name(value):
    return "".join(unicodedata.normalize("NFKC", value or "").split())


def generate():
    registry, city_hash = read(HERE / "register.json")
    work, work_hash = read(HERE.parent.parent / "model-todo/discovered-buildings.json")
    city, = [batch for batch in registry["batches"] if batch["batch"] == 2]
    stories = [row for row in work["records"] if row["batch"] == 2]
    by_code = defaultdict(list)
    for item in stories:
        code = unicodedata.normalize("NFKC", item["official_code"])
        match = re.fullmatch(r"([A-Z])-III-([0-9]+)", code)
        if not match:
            raise ValueError(f"Unrecognized working code: {code}")
        by_code[f"2{match[1]}{int(match[2]):03d}"].append(item)
    rows, used = [], set()
    for record in city["records"]:
        keys = re.findall(r"2[A-Z][0-9]{3}", record["code"])
        hits = [(key, item) for key in keys for item in by_code[key]]
        if len(hits) != 1 or hits[0][1]["id"] in used:
            raise ValueError(f"Ambiguous code correspondence: {record['code']}")
        key, item = hits[0]
        used.add(item["id"])
        original = comparable_name(record["original_name_or_user"]) == comparable_name(item["name"])
        address = comparable_name(record["address"]) in {comparable_name(v) for v in item["addresses"]}
        rows.append({"official_table_row": record["table_row"], "printed_official_code": record["code"],
                     "matched_printed_code": key, "working_id": item["id"], "printed_working_code": item["official_code"],
                     "official_original_name": record["original_name_or_user"], "working_name": item["name"],
                     "official_address": record["address"], "working_addresses": item["addresses"],
                     "same_original_name": original, "same_one_address": address})
    if len(rows) != len(stories) or len(used) != len(rows):
        raise ValueError("The numbering systems did not give one row per record")
    counts = Counter((r["same_original_name"],r["same_one_address"]) for r in rows)
    return {"batch": 2, "official_rows_source_sha256": city_hash, "working_register_source_sha256": work_hash,
            "counts": {"rows":len(rows), "both":counts[True,True], "name_only":counts[True,False],
                       "address_only":counts[False,True], "neither":counts[False,False]},
            "records": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    result = generate()
    parser.parse_args().output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(result["counts"])
