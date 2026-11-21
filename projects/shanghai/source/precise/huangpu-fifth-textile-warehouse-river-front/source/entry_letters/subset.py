"""Reproduce the small OFL subset used for the photographed street plaques."""
from pathlib import Path
import hashlib
import json
import sys
from fontTools import subset
from fontTools.ttLib import TTFont

dest = Path(__file__).resolve().parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
font = TTFont(src, fontNumber=2, recalcTimestamp=False)
family = 'River Front Entry'
characters = 'UVWORKING1295南苏州路'
copyright_text = font['name'].getDebugName(0)
copyright_license = font['name'].getDebugName(13)
opts = subset.Options()
opts.layout_features = []
opts.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14, 16, 17]
subsetter = subset.Subsetter(options=opts)
subsetter.populate(text=characters)
subsetter.subset(font)
names = {1:family, 2:'Bold', 3:'RiverFrontEntry-Bold-1', 4:family + ' Bold', 6:'RiverFrontEntry-Bold', 16:family, 17:'Bold'}
for record in font['name'].names:
    if record.nameID in names:
        record.string = names[record.nameID].encode(record.getEncoding())
if 'CFF ' in font:
    cff = font['CFF '].cff
    top = cff.topDictIndex[0]
    cff.fontNames[0] = names[6]
    top.FamilyName, top.FullName = family, names[4]
output = dest / 'RiverFrontEntry.otf'
font.save(output)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
(dest / 'origin.json').write_text(json.dumps({
    'source':'Noto Sans CJK SC Bold', 'upstream':'https://github.com/notofonts/noto-cjk/tree/main/Sans',
    'collection':src.name, 'face_index':2, 'original_sha256':sha(src), 'subset_sha256':sha(output),
    'copyright':copyright_text, 'license':copyright_license, 'license_file':'OFL.txt', 'glyphs':characters,
    'use':'Legible geometry approximating the photographed lettering. The original sign typeface is unconfirmed.'
}, ensure_ascii=False, indent=2)+'\n')
