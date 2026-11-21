"""Check Residence A on Dongping Road' own viewer and its single card in the city directory."""
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
    model = "xuhui-ailu-residence-garden-loggia"
    page = "ailu-residence.html"
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
    assert manifest["name"] == "东平路9号爱庐甲楼花园敞廊"
    assert "2015" in manifest["status"]
    references = get(source, local=True).decode()
    for text in ("2D046", "甲楼", "乙楼", "1927年", "1930年", "2015年7月18日", "东平路9号"):
        assert text in references, text

    viewer = BeautifulSoup(get(page), "html.parser")
    title = viewer.title.get_text(strip=True)
    district = viewer.select_one("header .eyebrow").get_text(strip=True)
    caption = viewer.select_one("aside .scope").get_text(strip=True)
    assert title == "东平路9号爱庐甲楼 · 花园敞廊" and viewer.h1.get_text(strip=True) == "爱庐甲楼"
    assert district == "徐汇区 · 东平路9号"
    assert viewer.find("a", href=route) and viewer.find("a", href=source)
    assert f"showCandidateAssetViewer('{model}')" in viewer.find("script", type="module").get_text()
    assert "花园宽券" in viewer.select_one("#model-view")["aria-label"]
    assert all(word in caption for word in ("花园", "宽券", "石栏", "窄券", "2015年"))
    assert viewer.select_one('button[data-view="front"]').get_text(strip=True) == "花园正面"

    # Restrict the check to user-visible text within this viewer and its own card.
    # Other buildings in the complete directory legitimately mention their names.
    forbidden = ("自由公寓", "皇家公寓", "帝国公寓", "密丹公寓", "永业公寓", "扬子公寓",
                 "联合公寓", "黄浦区", "静安区", "海格公寓", "重庆南路", "复兴中路", "单面外廊", "赛华公寓", "瑞华公寓", "常熟路")
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
        assert "宽券" in description and "石栏" in description and "乙楼" in description
        visible += " " + card.get_text(" ", strip=True) + " " + card.get("data-search", "")
        card_data = {"title": card.h3.get_text(strip=True), "district": card.select_one(".card-meta").get_text(" ", strip=True), "description": description}
    assert not any(word in visible for word in forbidden)
    years = sorted(set(re.findall(r"(?<!\d)(?:18|19|20)\d{2}(?!\d)", visible)))
    assert all(y in {"2015"} for y in years)
    result = {"id": model, "site": args.site, "file_sha256": files,
              "viewer": {"title": title, "location": district, "scope": caption},
              "directory_card": card_data, "years_printed_in_viewer_and_card": years,
              "construction_year": None, "image_exif": "2015-07-18 18:18:09",
              "other_building_terms_checked": forbidden, "passed": True}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
