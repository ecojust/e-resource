"""Create the renamed SIL OFL font subset for the independently photographed house-number plaque."""
from pathlib import Path
from hashlib import sha256
import json
from fontTools import subset
from fontTools.ttLib import TTFont

root=Path(__file__).parent
origin=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
chars='124南昌路'
f=TTFont(origin,fontNumber=2)
sub=subset.Subsetter();sub.populate(text=chars);sub.subset(f)
ps='HouseNumber124'; family='House Number 124'
for n in f['name'].names:
    v={1:family,2:'Regular',3:ps,4:family,6:ps,16:family,17:'Regular'}.get(n.nameID)
    if v:n.string=v.encode(n.getEncoding())
c=f['CFF '].cff;c.fontNames[0]=ps;c.topDictIndex[0].FullName=family;c.topDictIndex[0].FamilyName=family
file=root/'HouseNumber124.otf';f.save(file)
(root/'provenance.json').write_text(json.dumps(dict(font='Noto Sans CJK SC Regular, face 2',upstream='https://github.com/notofonts/noto-cjk/tree/main/Sans',license='SIL Open Font License 1.1',source_sha256=sha256(origin.read_bytes()).hexdigest(),renamed_subset_sha256=sha256(file.read_bytes()).hexdigest(),characters=chars),ensure_ascii=False,indent=2)+'\n')
