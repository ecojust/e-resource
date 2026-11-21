"""Model the gable, window pairs and open lawn-side balcony at Fudan's Zibin Hall."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

SOURCE=Path(__file__).absolute().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as MetricBuilder
from photo_architecture import Facade
from plaster import CAST,TEXTURE,apply_metric_uv
from photographed_fixtures import CASE,METAL,BLADES,add_fixtures
from balcony import DECK,STONE,TRIM,GROOVE,add_balcony

ID='yangpu-fudan-zibin-hall-lawn-gable'
META=dict(id=ID,name='复旦大学子彬院草坪侧三角山墙与阳台',heritage_group='4G008',
          viewer_page='fudan-zibin-hall-lawn-gable.html',scope='子彬院面向草坪的中央凸部，仅含三对高窗、阁楼双窗、分格山墙、屋面截段与阳台。')
DIM=json.loads((SOURCE/'dimensions.json').read_bytes())
GLASS='Deep green glazing';BLUE='Reflected blue grey glass';FRAME='Graphite sash paint';BEAD='Weathered window fillet'
TILE='Old brown roof tile';TILE2='Sunlit terracotta rib';FIELD='Cool grey inset panel';CORE='Sectioned plaster core'

def pigment(rgb,rough=.82,metal=0):
    c=np.array(rgb)/255
    return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)

PALETTE={CAST:dict(color=[1,1,1],roughness=.94,texture=str(TEXTURE)),
         TRIM:pigment([209,207,185]),STONE:pigment([209,208,194]),DECK:pigment([197,196,178]),
         GROOVE:pigment([154,156,143]),GLASS:pigment([60,69,69],.29,.16),BLUE:pigment([87,100,103],.29,.18),
         FRAME:pigment([61,64,62],.58),BEAD:pigment([111,113,101],.64),TILE:pigment([119,82,68]),
         TILE2:pigment([146,103,83]),FIELD:pigment([145,152,151]),CORE:pigment([159,158,142]),
         CASE:pigment([176,176,159],.72),METAL:pigment([79,79,65],.59,.30),BLADES:pigment([120,118,100],.62,.23)}

class AggregateBuilder(MetricBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        target=Path(path);receipt=target.with_suffix('.geometry.json')
        if receipt.is_file():
            record=json.loads(receipt.read_bytes())
            with target.open('rb') as stream:record['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            record['bytes']=target.stat().st_size
            receipt.write_text(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n')

def sash(face,bounds,name,attic,lod):
    x0,z0,x1,z1=bounds
    hole=box(*bounds);x=(x0+x1)/2;z=(z0+z1)/2
    outer=hole.buffer(-.008,join_style=2);inner=hole.buffer(-.063,join_style=2)
    face.prism(outer.difference(inner),-.128,-.056,FRAME,name+' outer jambs')
    transom=z0+(z1-z0)*(.36 if attic else .72)
    # A continuous, recessed glazing bed closes oblique sightlines at the meeting stile.
    face.prism(hole.buffer(.012,join_style=2),-.215,-.202,GLASS,name+' glazing bed')
    split=box(x-.021,z0,x+.021,z1)
    rail=box(x0,transom-.024,x1,transom+.024)
    bars=split.union(rail).intersection(inner)
    face.prism(bars,-.141,-.103,FRAME,name+' sash divisions')
    for n,pane in enumerate(sorted(inner.difference(bars).geoms,key=lambda p:p.centroid.x+5*p.centroid.y)):
        face.prism(pane.buffer(.005,join_style=2),-.166,-.151,BLUE if (n+int(attic))%3==0 else GLASS,name+' recessed panes')
    if not lod:
        bead=inner.difference(inner.buffer(-.014,join_style=2))
        face.prism(bead,-.098,-.079,BEAD,name+' glazing bead')
    face.box(x,z0-.026,x1-x0+.115,.073,.19,.050,DECK,name+' sill')

def lower_wall(face,d,left,right,lod):
    holes=[box(*bounds)for bounds in d['lower']];top=d['cornice_bottom_z']
    face.prism(box(left,d['bottom'],right,top+.005).difference(unary_union(holes)),-.29,0,CAST,'pier and lintel wall')
    for i,b in enumerate(d['lower']):sash(face,b,'Tall sash '+str(i+1),False,lod)
    for i,x in enumerate([left+.16,-2.23,2.01,right-.22]):
        lab='Pier '+str(i+1)
        face.box(x,(top+d['bottom'])/2,.39,top-d['bottom'],.137,.063,TRIM,lab+' face')
        for k,(z,w,h,p) in enumerate([(d['deck_top_z']+.14,.47,.14,.10),(top-.15,.44,.105,.083),(top-.06,.50,.08,.094)]):
            face.box(x,z,w,h,.07+p,p/2,DECK,lab+' horizontal band '+str(k+1))
        if not lod:
            for offset in [-.119,.119]:face.box(x+offset,(top+.12)/2,.018,top-.40,.025,.141,STONE,lab+' incised edge')
    for zlo,zhi,projection,material,label in [(top,top+.09,.12,GROOVE,'soffit'),(top+.09,top+.20,.155,TRIM,'architrave'),
         (top+.20,top+.242,.196,DECK,'shadow drip'),(top+.242,d['base_band_z']+.12,.218,TRIM,'gable base lip')]:
        face.box((left+right)/2,(zlo+zhi)/2,right-left+.14,zhi-zlo,.29+projection,(projection-.29)/2,material,label)

def gable(face,builder,d,lod):
    left,peak,right=np.array(d['rake'])
    bottom=d['base_band_z']
    tri=Polygon([(left[0],bottom),(right[0],bottom),right,peak,left])
    hole=unary_union([box(*b)for b in d['attic']])
    face.prism(tri.difference(hole),-.31,0,TRIM,'gable with two real openings')
    for i,b in enumerate(d['attic']):sash(face,b,'Attic sash '+str(i+1),True,lod)
    for i,pts in enumerate(d['fields']):
        panel=Polygon(pts)
        face.prism(panel,.002,.014,FIELD,'inset grey field '+str(i+1))
        rim=panel.buffer(.072,join_style=2).difference(panel)
        face.prism(rim,.006,.045,CAST,'plaster border '+str(i+1))
        if i==2:
            xa,ya,xb,yb=panel.bounds
            inner=Polygon([(xa+.34,ya+.07),(xb-.35,ya+.07),((xa+xb)/2,yb-.60)]).intersection(panel)
            if inner.area>.01:face.prism(inner,.015,.033,CAST,'attic central tympanum')
    for i,(x0,x1)in enumerate([(-2.56,-1.83),(1.42,2.27)]):
        upper=np.interp((x0+x1)/2,[left[0],peak[0],right[0]],[left[1],peak[1],right[1]])-.58
        face.box((x0+x1)/2,(bottom+upper)/2,x1-x0,upper-bottom,.072,.034,TRIM,'attic pier '+str(i+1))
        for n in range(3):
            face.box((x0+x1)/2,upper-.12-.14*n,x1-x0-.12,.028,.033,.073,GROOVE,'attic pier course '+str(i+1))
    line=LineString([left,peak,right])
    for radius,back,front,mat,name in [(.135,-.35,.103,DECK,'rake foundation'),(.088,.094,.168,TRIM,'pale roof verge'),(.036,.159,.199,STONE,'outer crest bead')]:
        outline=line.buffer(radius,cap_style=2,join_style=2)
        face.prism(outline,back,front,mat,name)
    ridge=peak[1]+.07
    builder.lathe((peak[0],-.022),[(ridge,.085),(ridge+.066,.077),(ridge+.096,.112),(ridge+.156,.142),(ridge+.225,.121),
                            (ridge+.284,.060),(ridge+.298,.011)],DECK,9 if lod else 18,label='Gable/ridge finial')
    end=d['section_depth']
    for i,(a,b)in enumerate([(left,peak),(peak,right)]):
        cap=LineString([a,b]).buffer(.058,cap_style=2)
        face.prism(cap,-end,-.31,TILE,'pitched roof section '+str(i+1))
        n=max(2,round((b[0]-a[0])/(.43 if lod else .215)))
        for j in range(n):
            k=(j+.5)/n;u,z=a*(1-k)+b*k
            builder.tube([(u,.32,z+.056),(u,end-.02,z+.056)],.021,TILE2,5 if lod else 8,label='Roof '+str(i+1)+'/tile ribs')
    builder.tube([(peak[0],.22,peak[1]+.07),(peak[0],end,peak[1]+.07)],.079,TILE,7 if lod else 12,label='Roof/ridge cap')

def add_building(builder,lod):
    d=DIM;left=d['rake'][0][0]+.19;right=d['rake'][2][0]-.19
    face=Facade(builder,(-.5,0),(.5,0),'Lawn')
    lower_wall(face,d,left,right,lod);gable(face,builder,d,lod);add_balcony(builder,d,left,right,lod)
    for x in [left+.07,right-.07]:
        builder.box((x,(d['section_depth']+.27)/2,(d['cornice_bottom_z']+d['bottom'])/2),
                    (.14,d['section_depth']-.27,d['cornice_bottom_z']-d['bottom']),CORE,label='Section/return at cut')
    add_fixtures(face,builder,d['visible_grille_cases'],lod)
    apply_metric_uv(builder)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for raw mesh')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['ZIBIN_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
