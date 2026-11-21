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
    # The lane name is written from right to left on the original tablet.
    rows={'lane':outlines('里安永',CHINESE,-.76,0,1.52,.36),'address':outlines('174',SANS,-.081,0,.162,.078)}
    (SOURCE/'sign-outlines.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':'))+'\n')
