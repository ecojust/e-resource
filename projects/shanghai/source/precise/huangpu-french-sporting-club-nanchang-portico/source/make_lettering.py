"""Recover the photographed title as original geometric typesetting from an OFL font."""
import hashlib,io,json,sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools import subset
from shapely.affinity import translate
from shapely.geometry import mapping
p=Path(__file__).resolve().parents[2]/'hongkou-general-post-office/source/common'
sys.path.insert(0,str(p))
from sign_lettering import lettering_shapes
source=Path('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc')
text='上海科技发展展示馆'
face=TTFont(source,fontNumber=2)
holder=subset.Subsetter();holder.populate(text=text);holder.subset(face)
f=io.BytesIO();face.save(f);f.seek(0)
letters=[]
for char,g in lettering_shapes(text,1.76,.19,font=f):
    geom=translate(g.simplify(.0009,preserve_topology=True),yoff=3.01)
    letters.append(dict(character=char,shape=mapping(geom)))
out=Path(__file__).resolve().parent
(out/'sign-contours.json').write_text(json.dumps(letters,ensure_ascii=False,separators=(',',':'))+'\n')
(out/'sign-source.json').write_text(json.dumps(dict(text=text,source='Noto Serif CJK SC Regular',font_collection=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),license='SIL Open Font License 1.1',upstream='https://github.com/notofonts/noto-cjk',geometry='Original lettering layout approximating the 2014 exhibition name. The dated plaque is distinct from the original 1931 building name.'),ensure_ascii=False,indent=2)+'\n')
