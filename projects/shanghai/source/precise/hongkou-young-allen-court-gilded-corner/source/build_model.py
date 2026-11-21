"""Model the gold corner turret and the two photographed street fronts of Young Allen Court."""
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
from grey_brick import BRICK,TEXTURE,apply_metric_uv
from frontage import (RED,BRIGHT,STONE,SASH,GLASS,SHADOW,SLATE,TILE,CLAY,METAL,PLASTER,GILT,SEAM,frontage)
from gilded_tower import tower,octagon
from pitched_roofs import pitched_roof
from zhapu_bays import west_front
from corner_shop import CLOTH,CREAM,WOOD,corner_shop
from shapely.geometry import box
from shapely.geometry.polygon import orient

ID='hongkou-young-allen-court-gilded-corner'
META=dict(id=ID,name='乍浦路260号金顶角楼与老虎窗',heritage_group='4F007',viewer_page='young-allen-court-gilded-corner.html',
          scope='乍浦路与昆山路东南街角，按修缮前照片复原北、西两面、八角塔与金色曲顶。')
PLAN=json.loads((SOURCE/'plan.json').read_bytes())

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


PALETTE={CLOTH:pigment([170,123,113]),CREAM:pigment([202,195,177]),WOOD:pigment([157,100,64]),BRICK:dict(color=[1.,1.,1.],texture=str(TEXTURE),roughness=.91),
 RED:pigment([155,91,69]),BRIGHT:pigment([175,115,82]),STONE:pigment([163,151,128]),
 SASH:pigment([117,59,46],.64),GLASS:pigment([72,85,87],.29,.12),SHADOW:pigment([49,48,46]),
 SLATE:pigment([73,74,68]),TILE:pigment([155,94,73]),CLAY:pigment([180,115,81]),METAL:pigment([94,92,82],.61,.22),
 PLASTER:pigment([212,199,171]),GILT:pigment([215,171,86],.37,.47),SEAM:pigment([230,189,107],.39,.44)}


def add_building(b,lod):
    p=PLAN;radius=p['tower_radius'];s=p['shell']
    body=box(s['west'],s['south'],s['east'],s['north'])
    octa=Polygon(octagon(radius))
    union=orient(body.union(octa),sign=1.)
    b.plan_prism(union,.024,.15,STONE,'Foundation / street corner house')
    ring=list(union.exterior.coords)
    front=[]
    for a,c in zip(ring,ring[1:]):
        a=np.array(a);c=np.array(c);v=c-a
        if v[0]<-8 and abs(v[1])<1e-5:
            front.append(('Kunshan',a,c))
        elif v[1]<-6 and abs(v[0])<1e-5:
            front.append(('Zhapu',a,c))
        elif max(abs(a[0]),abs(c[0]))>5 or max(abs(a[1]),abs(c[1]))>5:
            f=Facade(b,a,c,'Attached return');f.wall(.13,p['eave'],(),.29,BRICK)
    assert len(front)==2
    for name,a,c in front:
        facade=Facade(b,a,c,name)
        if name=='Zhapu':west_front(facade,p,lod)
        else:frontage(facade,name,p,lod)
    tower(b,p,lod,body)
    corner_shop(b,p,lod)
    pitched_roof(b,p,front,lod)
    # Local x follows Kunshan Road. Position native meshes and the web export
    # in the same east/north/up basis before computing brick coordinates.
    angle=np.deg2rad(p['east_axis_bearing_from_east_deg'])
    matrix=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    for part in b.parts:
        vv=np.asarray(part['vertices']);vv[:,:2]=vv[:,:2]@matrix.T
        part['vertices']=vv.tolist()
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
        os.environ['YOUNG_ALLEN_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
