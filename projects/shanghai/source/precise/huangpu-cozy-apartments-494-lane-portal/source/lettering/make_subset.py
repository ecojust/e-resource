"""Subset four traditional characters for the inscription on the No. 494 lane gate."""

from pathlib import Path
import argparse, hashlib, json
from fontTools import subset
from fontTools.ttLib import TTFont

here = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument(
    "--source", type=Path, default=Path("/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc")
)
args = parser.parse_args()
font = TTFont(args.source, fontNumber=2, recalcTimestamp=False)
text = "康綏公寓"
selector = subset.Subsetter()
selector.populate(text=text)
selector.subset(font)
postscript = "CozyGateInscription"
name = "Cozy Gate Inscription"
for rec in font["name"].names:
    replacement = {
        1: name,
        2: "Bold",
        3: postscript,
        4: name,
        6: postscript,
        16: name,
        17: "Bold",
    }.get(rec.nameID)
    if replacement:
        rec.string = replacement.encode(rec.getEncoding())
cff = font["CFF "].cff
cff.fontNames[0] = postscript
cff.topDictIndex[0].FamilyName = name
cff.topDictIndex[0].FullName = name
target = here / "CozyGateInscription.otf"
font.save(target)
receipt = dict(
    characters=text,
    source="Noto Serif CJK SC Bold, face 2",
    upstream="https://github.com/notofonts/noto-cjk/tree/main/Serif",
    license="SIL Open Font License 1.1",
    original_sha256=hashlib.sha256(args.source.read_bytes()).hexdigest(),
    subset_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    use="A conventional serif representation of the four name characters. The relief does not trace the original sign strokes.",
)
(here / "provenance.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
