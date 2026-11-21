"""Check Savoy Apartments' own viewer and its single card in the city directory."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen

from bs4 import BeautifulSoup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Project containing the model and sources")
    parser.add_argument("--site", help="Read actual served HTML and manifest from this URL")
    parser.add_argument("--candidate-only", action="store_true", help="Check the viewer before the directory is generated")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    model = "xuhui-savoy-apartments-street-front"
    page = "savoy-apartments.html"
    source = f"source/precise/{model}/README.md"
    route = f"index.html#landmark={model}&mode=overview"
    files = {}

    def get(path, local=False):
        if args.site and not local:
            with urlopen(urljoin(args.site.rstrip("/") + "/", path), timeout=30) as response:
                assert response.status == 200
                data = response.read()
        else:
            data = (args.project / path).read_bytes()
        files[path] = hashlib.sha256(data).hexdigest()
        return data

    manifest = json.loads(get(f"assets/models/candidates/{model}/manifest.json"))
    assert manifest["id"] == model and manifest["viewer_page"] == page
    assert manifest["name"] == "赛华公寓常熟路、延庆路转角立面"
    assert "2020–21" in manifest["status"]
    references = get(source, local=True).decode()
    for text in ("2D047", "赛华公寓", "瑞华公寓", "1928年始建", "2020年", "2021年", "常熟路209弄1–4号"):
        assert text in references, text

    viewer = BeautifulSoup(get(page), "html.parser")
    title = viewer.title.get_text(strip=True)
    district = viewer.select_one("header .eyebrow").get_text(strip=True)
    caption = viewer.select_one("aside .scope").get_text(strip=True)
    assert title == "赛华公寓 · 两街转角" and viewer.h1.get_text(strip=True) == "赛华公寓"
    assert district == "徐汇区 · 常熟路209号"
    assert viewer.find("a", href=route) and viewer.find("a", href=source)
    assert f"showCandidateAssetViewer('{model}')" in viewer.find("script", type="module").get_text()
    assert "常熟路与延庆路" in viewer.select_one("#model-view")["aria-label"]
    assert all(word in caption for word in ("瑞华公寓", "两翼各有两处敞开楼梯", "五层折面凸窗", "浅色"))
    assert viewer.select_one('button[data-view="front"]').get_text(strip=True) == "两街转角"

    # Restrict the check to user-visible text within this viewer and its own card.
    # Other buildings in the complete directory legitimately mention their names.
    forbidden = ("自由公寓", "皇家公寓", "帝国公寓", "密丹公寓", "永业公寓", "扬子公寓",
                 "联合公寓", "黄浦区", "静安区", "海格公寓", "重庆南路", "复兴中路", "单面外廊")
    visible = viewer.get_text(" ", strip=True) + " " + viewer.select_one("#model-view")["aria-label"]
    card_data = None
    if not args.candidate_only:
        directory = BeautifulSoup(get("landmarks.html"), "html.parser")
        cards = directory.select(f'article.landmark-card[data-landmark="{model}"]')
        assert len(cards) == 1
        card = cards[0]
        assert card.h3.get_text(strip=True) == manifest["name"]
        assert "徐汇区" in card.select_one(".card-meta").get_text()
        assert card.find("a", href=page) and card.find("a", href=route)
        description = card.p.get_text(strip=True)
        assert "敞开楼梯" in description and ("凸窗" in description or "窗肚墙" in description)
        visible += " " + card.get_text(" ", strip=True) + " " + card.get("data-search", "")
        card_data = {"title": card.h3.get_text(strip=True), "district": card.select_one(".card-meta").get_text(" ", strip=True), "description": description}
    assert not any(word in visible for word in forbidden)
    years = sorted(set(re.findall(r"(?<!\d)(?:18|19|20)\d{2}(?!\d)", visible)))
    assert all(y in {"1928", "2016", "2020", "2021"} for y in years)
    result = {"id": model, "site": args.site, "file_sha256": files,
              "viewer": {"title": title, "location": district, "scope": caption},
              "directory_card": card_data, "years_printed_in_viewer_and_card": years,
              "construction_year_in_source": 1928, "model_repair_period": "2020–2021",
              "other_building_terms_checked": forbidden, "passed": True}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
