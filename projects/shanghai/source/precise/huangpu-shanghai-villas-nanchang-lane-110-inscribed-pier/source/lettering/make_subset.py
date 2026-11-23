"""Subset the vertical stone inscriptions and address marks at Lane 110, Nanchang Road."""

from pathlib import Path
import argparse, hashlib, json
from fontTools import subset
from fontTools.ttLib import TTFont

here = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--font-dir", type=Path, default=Path("/usr/share/fonts/opentype/noto"))
args = parser.parse_args()
records = []
for text, weight, postscript, name, purpose in (
    ("上海別墅", "Bold", "Lane110StoneLetters", "Lane 110 Stone Letters", "The dark incised names use a conventional open typeface in both piers."),
    ("012弄", "Regular", "NanchangAddresses", "Nanchang Addresses", "Painted 112 and 110弄 address marks."),
):
    source = args.font_dir / f"NotoSerifCJK-{weight}.ttc"
    font = TTFont(source, fontNumber=2, recalcTimestamp=False)

    selector = subset.Subsetter()
    selector.populate(text=text)
    selector.subset(font)


    for rec in font["name"].names:
        replacement = {
            1: name,
            2: weight,
            3: postscript,
            4: name,
            6: postscript,
            16: name,
            17: weight,
        }.get(rec.nameID)
        if replacement:
            rec.string = replacement.encode(rec.getEncoding())
    cff = font["CFF "].cff
    cff.fontNames[0] = postscript
    cff.topDictIndex[0].FamilyName = name
    cff.topDictIndex[0].FullName = name
    target = here / (postscript + ".otf")
    font.save(target)
    receipt = dict(
        characters=text,
        source=f"Noto Serif CJK SC {weight}, face 2",
        upstream="https://github.com/notofonts/noto-cjk/tree/main/Serif",
        license="SIL Open Font License 1.1",
        original_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        subset_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        use=purpose,
    )
    records.append(receipt)
(here / "provenance.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
