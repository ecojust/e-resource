"""Create original typesetting of the inscription in Noto Serif CJK, licensed under the SIL OFL."""
from pathlib import Path
from argparse import ArgumentParser
import json
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from shapely import affinity
from shapely.geometry import Polygon
if __name__=='__main__':
    parser=ArgumentParser()
    parser.add_argument('font',type=Path,help='Path to the Noto Serif CJK regular font')
    args=parser.parse_args()
    lines=[]
    for text,x,z,width,height in [('毓',-2.17,3.57,.43,.45),('秀',-.21,3.57,.42,.45),('樓',1.73,3.57,.44,.45)]:
        shape=Polygon()
        for ring in TextPath((0,0),text,size=1,prop=FontProperties(fname=str(args.font))).to_polygons():
            shape=shape.symmetric_difference(Polygon(ring).buffer(0))
        left,bottom,right,top=shape.bounds
        shape=affinity.translate(shape,xoff=-left,yoff=-bottom)
        shape=affinity.scale(shape,xfact=width/(right-left),yfact=height/(top-bottom),origin=(0,0))
        shape=affinity.translate(shape,xoff=x,yoff=z)
        pieces=[shape]if shape.geom_type=='Polygon'else shape.geoms
        polys=[[[[round(a,6),round(b,6)]for a,b in ring.coords]for ring in [p.exterior,*p.interiors]]for p in pieces]
        lines.append(dict(text=text,polygons=polys))
    Path(__file__).with_name('inscription.json').write_text(json.dumps(lines,ensure_ascii=False,separators=(',',':'))+'\n')
