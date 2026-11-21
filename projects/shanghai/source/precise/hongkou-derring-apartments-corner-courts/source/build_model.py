"""Make the two documented street wings and two roofed courts of Derring Apartments."""
import argparse,hashlib,json,os,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as RepeatingTextureBuilder
from photo_architecture import Facade
from taishan_bricks import BRICK,TEXTURE,apply_metric_uv
from street_elevation import (BASE,CAP,COVER,FRAME,GLASS,GLAZED,METAL,PANEL,ROOF,ROUGH,
                              SHADOW,SHUTTER,street_wall,walk_level)
from corner_crown import southwest_crown,projecting_balcony
from roof_landscape import roof_houses

ID='hongkou-derring-apartments-corner-courts'
META=dict(id=ID,name='德邻公寓街角与双天井',heritage_group='4F003',viewer_page='derring-apartments-corner-courts.html',
          scope='以2019至2022年修缮前实照复原江西北路和崇明路沿街部分、三个转角和两个有覆顶的院井。')
PLAN=json.loads((SOURCE/'plan.json').read_bytes())
LEVELS=dict(base=4.87,sill=[4.95,7.74,10.74,13.69,18.19],head=[6.48,9.18,12.27,15.33,19.38],
            sixth=16.76,body=16.18,regular_top=21.90)


class AggregateBuilder(RepeatingTextureBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata);p=Path(path);side=p.with_suffix('.geometry.json')
        if side.is_file():
            doc=json.loads(side.read_bytes())
            with p.open('rb')as stream:doc['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            side.write_text(json.dumps(doc,ensure_ascii=False,separators=(',',':'))+'\n')


def pigment(color,roughness=.84,metallic=0):
    v=np.array(color)/255.
    return dict(color=np.where(v<.04045,v/12.92,((v+.055)/1.055)**2.4).tolist(),roughness=roughness,metallic=metallic)


PALETTE={BRICK:dict(color=[1.,1.,1.],texture=str(TEXTURE),roughness=.91),
         BASE:pigment([183,175,164]),ROUGH:pigment([171,153,129]),PANEL:pigment([201,183,151]),
         FRAME:pigment([58,54,49],.63,.14),GLASS:pigment([71,85,90],.34,.13),
         GLAZED:pigment([73,97,82],.39),CAP:pigment([163,146,123]),METAL:pigment([113,118,113],.53,.18),
         SHADOW:pigment([52,54,53]),SHUTTER:pigment([130,130,124],.71),
         ROOF:pigment([109,104,95]),COVER:pigment([134,153,143],.73)}


def positions(length,kind):
    # Corner bays are distinct from the rectilinear middle fields on either street.
    if kind in ('east-cut','southwest'):return [-.84,.84],[(-length/2,length/2)]
    if kind=='northwest':return [-2.24,0.,2.24],[(-length/2,length/2)]
    centres=np.linspace(-length/2+1.64,length/2-1.64,19 if kind=='west' else 18)
    reach=centres[1]-centres[0]
    runs=[(-length/2,centres[3]+reach*.53),(centres[-5]-reach*.53,length/2)]
    return centres.tolist(),runs


def opaque_return(b,a,c,label,lod):
    f=Facade(b,a,c,label)
    f.wall(.05,LEVELS['base'],(),.34,BASE)
    f.wall(LEVELS['base'],LEVELS['regular_top'],(),.31,ROUGH)
    f.beam(LEVELS['regular_top']-.12,.22,.13,CAP,label='Return coping')


def street(b,a,c,kind,lod):
    labels={'west':'Jiangxi North Road','south':'Chongming Road','southwest':'Southwest corner',
            'northwest':'Northwest cut','east-cut':'Southeast cut'}
    f=Facade(b,a,c,labels[kind]+' / base')
    bays,runs=positions(f.length,kind)
    lower=np.linspace(-f.length/2+f.length/16,f.length/2-f.length/16,8).tolist() if kind=='south' else []
    walk_level(f,kind,lower,LEVELS['base'],lod)
    up=street_wall(b,a,c,labels[kind]+' / upper',kind,bays,runs,LEVELS,lod)
    if kind=='southwest':southwest_crown(up,LEVELS,lod)
    if kind=='west':
        for idx in (7,11):projecting_balcony(up,bays[idx],LEVELS['sill'][3]-.12,lod)
    if kind in ('west','south'):
        # The pale middle is interrupted by isolated narrow brown vertical piers.
        for x in (bays[6]-.91,bays[10]-.91):
            up.box(x,(LEVELS['base']+LEVELS['regular_top'])/2,.42,LEVELS['regular_top']-LEVELS['base'],.19,.061,BRICK,'Narrow brick piers in roughcast')


def roof_and_courts(b,plan,holes,lod):
    deck=plan.difference(unary_union(holes));z=LEVELS['regular_top']-.49
    b.plan_prism(deck,z-.24,z,ROOF,'Ring roof and cross wing')
    b.plan_prism(plan,.012,.103,BASE,'Foundation and court floors')
    roof_houses(b,plan,holes,z,lod)
    for k,poly in enumerate(holes,1):
        label='West' if k==1 else 'East'
        outline=orient(poly,sign=-1.)
        for j,(a,c)in enumerate(zip(outline.exterior.coords,list(outline.exterior.coords)[1:])):
            f=Facade(b,a,c,label+' court')
            f.wall(.10,z,(),.21,ROUGH)
        # 2021 overhead imagery shows opaque pale-green fields. The height of
        # these sheltered courts below the surrounding parapet is approximate.
        zz=z-3.15
        b.plan_prism(poly,zz-.12,zz,COVER,label+' court / pre-renovation cover')
        b.plan_prism(poly.difference(poly.buffer(-.15,join_style=2)),zz,zz+.105,METAL,label+' court / roof edge')


def add_building(b,lod):
    pts=PLAN['outline_m'];plan=orient(Polygon(pts),sign=1.)
    holes=[Polygon(x) for x in PLAN['covered_courts_m']]
    assert plan.is_valid and all(plan.contains(h) for h in holes)
    for a,c,kind in [(9,10,'west'),(10,0,'southwest'),(0,1,'south'),(1,2,'east-cut'),(8,9,'northwest')]:
        street(b,pts[a],pts[c],kind,lod)
    for i in range(2,8):
        opaque_return(b,pts[i],pts[i+1],'Attached back range '+str(i),lod)
    roof_and_courts(b,plan,holes,lod)
    apply_metric_uv(b)


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('unexpected raw export arguments: '+' '.join(rest))
        b=AggregateBuilder(PALETTE);add_building(b,args.lod);b.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['DERRING_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
