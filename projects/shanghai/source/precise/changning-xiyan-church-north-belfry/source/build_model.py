"""Build the freestanding north bell tower at the Catholic Country Church, Shanghai."""
import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder as ArchitectureBuilder
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
import belfry_finishes
class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in belfry_finishes.STEMS:belfry_finishes.metric_uv(self.parts[-1])
    def save(self,path,metadata=None):
        ArchitectureBuilder.save(self,path,metadata)
        return belfry_finishes.writer.embed_normals(path)

sys.path.insert(0,str(HERE.parent/'measurements'))
from fit_tower import surface,BASE
ID='changning-xiyan-church-north-belfry'
SLUG='xiyan-church-north-belfry'
FIT=json.loads((HERE.parent/'measurements/tower-stations.json').read_bytes())
H,TOP,SILL,TIP,OUTER,STEP,*SLITS=FIT['parameters'][:12]
CAP_RISE,CROSS_RISE=FIT['parameters'][12:14]
WALL='ochre stippled roughcast';STONE='brown dressed masonry';SLATE='weathered grey vents'
SHADE='deep belfry shadow';FLASH='dark cornice metal';UPPER='cream lantern roughcast'
MEMORIAL='polished dark stone';IRON='dark cross iron'
PALETTE={m:{'color':c,'roughness':r}for m,c,r in [
    (WALL,[.55,.455,.233],.94),(STONE,[.245,.191,.153],.82),(SLATE,[.149,.158,.152],.68),
    (SHADE,[.045,.040,.033],.97),(FLASH,[.105,.105,.091],.73),(UPPER,[.54,.472,.303],.90),
    (MEMORIAL,[.064,.059,.052],.42),(IRON,[.119,.113,.101],.68)]}
PALETTE.update(belfry_finishes.PALETTE)
META=dict(id=ID,name='息焉堂北侧独立钟楼',heritage_id='sh-historic-b2-076',address='可乐路1号；名录虹桥路2381号',
          source='https://commons.wikimedia.org/wiki/File:Catholic_Country_Church.jpg',
          viewer_page=SLUG+'.html',photos_embedded=False,geometry_license='MIT',
          scope='院前与隔河实照可辨的独立钟楼、上部尖券百叶、阶梯小窗、塔檐、短灯亭、十字及底部深色纪念碑。',
          estimated='按3.60米条件底宽配准，实宽、高度、背侧隐蔽位置及铜钟内部尚待实测。')
if (HERE/'cameras.json').exists():META['camera_views']=json.loads((HERE/'cameras.json').read_bytes())

def pointed(x,base,peak,width,curve=8):
    half=width/2;rise=half*1.16;spring=peak-rise
    # Intersect two circular arcs at the apex, with vertical tangents at the spring.
    r=(rise**2+half**2)/(2*half)
    left=[]
    for i in range(curve+1):
        y=rise*i/curve
        left.append((x+r-half-math.sqrt(max(0,r*r-y*y)),spring+y))
    return Polygon([(x-half,base),*left,*[(2*x-u,z)for u,z in reversed(left[:-1])],(x+half,base)])

def octagon(hw,chamfer):
    a=hw;c=hw-chamfer
    return [(-c,-a),(c,-a),(a,-c),(a,c),(c,a),(-c,a),(-a,c),(-a,-c)]
def tier(b,profiles,material,label):
    rings=[[(x,y,z)for x,y in octagon(w,c)]for z,w,c in profiles]
    n=len(rings[0]);verts=sum(rings,[]);faces=[tuple(range(n-1,-1,-1)),tuple(range(n*(len(rings)-1),n*len(rings)))]
    for i in range(len(rings)-1):
        for j in range(n):faces.append((n*i+j,n*i+(j+1)%n,n*(i+1)+(j+1)%n,n*(i+1)+j))
    b.add(verts,faces,material,label)

def element(b,side,shape,back,front,material,label):
    b.prism(shape,back,front,lambda u,z,d:surface(side,u,z,d,H,TOP),material,label)
def little_window(b,side,u,z,w,h):
    q=box(u-w/2,z-h/2,u+w/2,z+h/2)
    element(b,side,q,-.221,-.20,SHADE,'Stair lights/recess')
    element(b,side,box(u-w/2-.048,z-h/2-.035,u+w/2+.048,z-h/2+.021),-.008,.061,STONE,'Stair lights/projecting sill')
    for bias in [-.23,.23]:
        element(b,side,box(u-w/2+.018,z+h*bias-.014,u+w/2-.018,z+h*bias+.014),-.171,-.128,FLASH,'Stair lights/transom')
    return q

def add_building(b,lod=False):
    for side in range(4):
        # Each wall narrows toward the eaves. Corner returns close against their neighbours.
        outline=Polygon([(-BASE/2,0),(BASE/2,0),(TOP/2,H),(-TOP/2,H)])
        holes=[];n=5 if lod else 11;highest=TIP
        for idx,u in enumerate([-STEP,0,STEP]):
            q=pointed(u,SILL,highest,.63,n);holes.append(q)
            border=q.buffer(.055,join_style=2).difference(q)
            element(b,side,border,-.024,.055,STONE,'Belfry/pointed masonry surround '+str(side+1))
            element(b,side,q,-.317,-.286,SHADE,'Belfry/deep reveal '+str(side+1))
            inner=q.buffer(-.031,join_style=2)
            element(b,side,q.difference(inner),-.228,-.176,FLASH,'Belfry/arched shutter frame '+str(side+1))
            element(b,side,inner,-.258,-.229,SLATE,'Belfry/closed upper tympanum '+str(side+1))
            shutter_top=highest-.69
            for z in np.arange(SILL+.079,shutter_top-.04,.12 if lod else .067):
                # Fold each slat in depth. Visible lower shadow and sloping lips continue across each bay.
                y0,y1=.208,.093;h=.039 if lod else .026
                profile=Polygon([(y0,z+h+.030),(y1,z+h),(y1,z),(y0,z+.030)])
                b.prism(profile,u-.245,u+.245,
                    lambda d,v,s:surface(side,s,v,-d,H,TOP),SLATE,'Belfry/slatted grille '+str(side+1)+'-'+str(idx+1))
            element(b,side,box(u-.239,shutter_top-.018,u+.239,shutter_top+.031),-.205,-.118,FLASH,'Belfry/shutter head')
        element(b,side,box(-OUTER-.025,SILL-.083,OUTER+.025,SILL-.014),-.02,.081,STONE,'Belfry/triple sill '+str(side+1))
        # The February 2011 river photograph retains both descending rows through bare branches.
        if side in (0,3):
            for i in range(3):
                u,z=SLITS[i*2:i*2+2];holes.append(little_window(b,side,u,z,.195,.96))
        element(b,side,outline.difference(unary_union(holes)),-.178,0,WALL,'Tapered roughcast shaft/face '+str(side+1))
    w=TOP/2
    tier(b,[(H-.03,w+.011,.024),(H+.035,w+.085,.027),(H+.105,w+.105,.03)],STONE,'Cornice/stone bed')
    tier(b,[(H+.106,w+.106,.03),(H+.19,w+.199,.038),(H+.26,w+.226,.041)],FLASH,'Cornice/splayed fascia')
    tier(b,[(H+.261,w+.215,.04),(H+.307,w+.238,.04),(H+.35,w+.239,.04),(H+.418,w+.02,.03)],FLASH,'Cornice/drip and sloped coping')
    def crown(level):
        return H+.418+(level-.418)*(CAP_RISE-.418)/(1.51-.418)
    cut=.52;lantern=1.11
    tier(b,[(H+.415,lantern,cut),(crown(1.06),lantern-.023,cut)],UPPER,'Lantern/short canted drum')
    tier(b,[(crown(1.057),lantern-.02,cut),(crown(1.089),lantern+.07,cut),(crown(1.168),lantern+.078,cut)],FLASH,'Lantern/eaves and drip')
    tier(b,[(crown(1.169),lantern+.075,cut),(crown(1.35),.77,.33),(crown(1.48),.30,.13),(crown(1.51),.115,.05)],FLASH,'Lantern/faceted cap')
    b.tube([(0,0,crown(1.507)),(0,0,H+CROSS_RISE)],.041 if lod else .036,IRON,7 if lod else 12,'Lantern/iron cross post')
    b.tube([(0,-.42,H+CAP_RISE+.64*(CROSS_RISE-CAP_RISE)),(0,.42,H+CAP_RISE+.64*(CROSS_RISE-CAP_RISE))],.032,IRON,7 if lod else 12,'Lantern/iron cross arms')
    # The separate dark memorial at the front has stepped feet, shouldered head and a stone cross.
    front=-BASE/2-.18
    for z,w0,depth,h in [(.047,.98,.53,.094),(.151,.90,.44,.105)]:
        b.box((0,front,z),(w0,depth,h),MEMORIAL,label='Forecourt memorial/stone step')
    plate=Polygon([(-.351,.205),(.351,.205),(.351,1.065),(.299,1.11),(.278,1.18),(.19,1.219),(.087,1.228),(.059,1.267),(-.059,1.267),(-.087,1.228),(-.19,1.219),(-.278,1.18),(-.299,1.11),(-.351,1.065)])
    b.prism(plate,.0,.148,lambda u,z,d:(u,front+.069-d,z),MEMORIAL,'Forecourt memorial/shouldered tablet')
    b.box((0,front-.004,1.344),(.048,.056,.160),MEMORIAL,label='Forecourt memorial/cross post')
    b.box((0,front-.004,1.36),(.152,.050,.043),MEMORIAL,label='Forecourt memorial/cross arms')
    return b
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',required=True,type=Path);cli.add_argument('--lod',action='store_true');a=cli.parse_args()
    model=add_building(Builder(PALETTE),a.lod);report=model.save(a.output,META)
    print(json.dumps(dict(sha256=report['sha256'],closed_parts=len(model.parts),triangles=sum(len(v['triangles'])for v in model.parts))))
