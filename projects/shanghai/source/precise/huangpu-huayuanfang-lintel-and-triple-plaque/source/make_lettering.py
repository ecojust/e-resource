"""Lay out the photo-confirmed three traditional characters using Noto Serif CJK."""
from pathlib import Path
from hashlib import sha256
import argparse,io,json,sys
from fontTools import subset
from fontTools.ttLib import TTFont
from shapely.affinity import translate
from shapely.geometry import mapping
parser=argparse.ArgumentParser()
parser.add_argument('font',type=Path,help='NotoSerifCJK-Regular.ttc from notofonts/noto-cjk')
parser.add_argument('--project',type=Path,required=True)
args=parser.parse_args()
src=Path(__file__).resolve().parent
sys.path.insert(0,str(args.project/'source/precise/hongkou-general-post-office/source/common'))
from sign_lettering import lettering_shapes
characters='坊園花'
font=TTFont(args.font,fontNumber=2)
subset_font=subset.Subsetter();subset_font.populate(text=characters);subset_font.subset(font)
mem=io.BytesIO();font.save(mem);mem.seek(0)
shapes=[]
for ch,geom in lettering_shapes(characters,2.02,.521,font=mem):
    shape=translate(geom.simplify(.0014,preserve_topology=True),yoff=4.089)
    shapes.append(dict(character=ch,geometry=mapping(shape)))
(src/'three-characters.json').write_text(json.dumps(shapes,ensure_ascii=False,separators=(',',':'))+'\n')
record=dict(font='Noto Serif CJK SC Regular',distribution='NotoSerifCJK-Regular.ttc',font_sha256=sha256(args.font.read_bytes()).hexdigest(),source='https://github.com/notofonts/noto-cjk',license='SIL Open Font License 1.1',photo_confirmed_right_to_left='花園坊',left_to_right_in_elevation=characters,approximation='采用开放字库近似原题字的宋体笔画，三个字的位置由门额正照确定。')
(src/'lettering-source.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
