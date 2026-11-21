"""Generate the present-day entrance lettering in metres using open-licensed fonts."""
import json
from pathlib import Path
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from shapely import affinity
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

SOURCE=Path(__file__).parent
SANS='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
SERIF='/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
CHINESE='/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'


def outlines(text,font,x,y,width,height):
    paths=TextPath((0,0),text,size=1,prop=FontProperties(fname=font)).to_polygons()
    shape=Polygon()
    for path in paths:
        ring=Polygon(path).buffer(0)
        if not ring.is_empty:shape=shape.symmetric_difference(ring)
    left,bottom,right,top=shape.bounds
    shape=affinity.translate(shape,-left,-bottom)
    shape=affinity.scale(shape,width/(right-left),height/(top-bottom),origin=(0,0))
    shape=affinity.translate(shape,x,y)
    def coords(boundary):return [[round(a,5),round(b,5)]for a,b in boundary.coords]
    pieces=[shape] if shape.geom_type=='Polygon' else shape.geoms
    return [[coords(p.exterior),*[coords(hole)for hole in p.interiors]] for p in pieces]


if __name__=='__main__':
    rows=[('19',SANS,-.98,.49,.64,.55),('叁',CHINESE,-.26,.49,.59,.55),
          ('III',SERIF,.39,.49,.59,.55),('1933 SHANGHAI',SERIF,-.73,.268,1.46,.151),
          ('老场坊',CHINESE,-.43,0,.86,.193)]
    record=[{'text':s,'polygons':outlines(s,font,x,y,w,h)}for s,font,x,y,w,h in rows]
    (SOURCE/'entrance-letters.json').write_text(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n')
