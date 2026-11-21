"""Construct the northeast street front of the 1927 Yingyuan Villa at 2365 North Sichuan Road."""
import argparse,hashlib,json,math,os,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union

SOURCE=Path(__file__).absolute().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as RepeatBuilder
from photo_architecture import Facade,opening
from mineral_render import CAST,TEXTURE,apply_metric_uv
from villa_joinery import (BRICK,LIGHT_BRICK,MORTAR,LIMESTONE,DARK,WOOD,DOOR,BRASS,GLASS,SECOND,RED,STONE,MILK,IRON,
                          pediment,sash,entrance)
from projecting_bays import turret,projecting_window,TILE,WORN_TILE,EAVE,floor_slab
from villa_roof import roof

ID='hongkou-yingyuan-villa-pedimented-entrance'
META=dict(id=ID,name='樱苑别墅东北立面三角窗楣与题名门廊',heritage_group='4F019',
          viewer_page='yingyuan-villa-pedimented-entrance.html',
          scope='四川北路2365号东北沿街立面、圆形凸窗、题名门廊和凸窗上方的山墙。按2014、2020年照片与2021年街景制作。')
DIM=json.loads((SOURCE/'dimensions.json').read_bytes())


class AggregateBuilder(RepeatBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        file=Path(path);receipt=file.with_suffix('.geometry.json')
        if receipt.is_file():
            data=json.loads(receipt.read_bytes())
            with file.open('rb') as stream:data['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            data['bytes']=file.stat().st_size
            receipt.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')


def pigment(rgb,rough=.82,metal=0.):
    v=np.array(rgb)/255.;return dict(color=np.where(v<.04045,v/12.92,((v+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)


PALETTE={CAST:dict(color=[1.,1.,1.],texture=str(TEXTURE),roughness=.93),BRICK:pigment([139,71,55]),LIGHT_BRICK:pigment([161,91,66]),
         MORTAR:pigment([142,118,97]),LIMESTONE:pigment([202,191,164]),DARK:pigment([44,40,36]),WOOD:pigment([84,64,54],.63),
         DOOR:pigment([130,93,55],.58),BRASS:pigment([151,123,67],.41,.43),GLASS:pigment([87,99,91],.24,.22),
         SECOND:pigment([69,76,77],.28,.17),RED:pigment([167,42,43],.55),STONE:pigment([129,123,113]),
         MILK:pigment([229,220,198],.37),IRON:pigment([72,68,58],.49,.26),TILE:pigment([118,72,58]),WORN_TILE:pigment([129,80,65]),
         EAVE:pigment([76,56,47]),'Darker cut granite':pigment([116,110,104]),'Dormant wall shadows':pigment([143,125,102])}


def add_building(b,lod):
    d=DIM;u=d['measured_u'];left=-7.57;right=u['right_wall_under_front_eave']
    whole=Facade(b,(-.5,0),(.5,0),'Northeast front')
    flat=[u[k]for k in ['first_flat_upper_window_center_at_sill','second_flat_upper_window_center_at_sill','third_flat_upper_window_center_at_sill','rightmost_upper_window_center_at_sill']]
    pwidth=[1.57,1.63,1.72,1.36];lower=[(flat[0],1.50),(flat[1],1.52),(flat[3],1.28)]
    arch_cx=u['right_paired_projection_center_at_sill'];portal=(u['door_portal_left_outer_at_header']+u['door_portal_right_outer_at_header'])/2
    ridge=4.05
    face=Polygon([(left,0),(right,0),(right,7.00),(ridge,d['cross_gable_ridge']-.09),(.85,7.53),(left,d['flat_eave']-.12)])
    holes=[box(x-w/2,d['upper_sill'],x+w/2,d['upper_sash_head'])for x,w in zip(flat,pwidth)]
    holes += [box(x-w/2,d['lower_sill'],x+w/2,d['lower_sash_head'])for x,w in lower]
    holes += [box(portal-d['portal_outer_width']/2,0,portal+d['portal_outer_width']/2,d['portal_soffit']),
              box(arch_cx-.82,d['oriel_sill'],arch_cx+.82,d['oriel_head']),opening(arch_cx,.61,.76,.92,.265,14 if lod else 32),
              opening(ridge,7.78,1.28,.54,.50,20 if lod else 46)]
    area=face.difference(unary_union(holes));whole.prism(area,-.365,0,CAST,'Perforated street wall')
    # The dark setback in the stair bay is visible behind the mullions.
    whole.box(arch_cx,(d['oriel_sill']+d['oriel_head'])/2,1.76,d['oriel_head']-d['oriel_sill']+.08,.12,-.47,DARK,'Stair oriel/interior shadow')
    for j,(x,width)in enumerate(zip(flat,pwidth)):
        sash(whole,x,d['upper_sill'],width,d['upper_sash_head']-d['upper_sill'],lod,'Upper sash '+str(j+1),blind=j==3)
        pediment(whole,x,d['upper_sash_head']+.035,width+.47,d['upper_pediment_apex']-d['upper_sash_head']-.135,lod,'Upper pediment '+str(j+1))
    for j,(x,width)in enumerate(lower):
        sash(whole,x,d['lower_sill'],width,d['lower_sash_head']-d['lower_sill'],lod,'Lower sash '+str(j+1))
        pediment(whole,x,d['lower_sash_head']+.025,width+.51,d['lower_pediment_apex']-d['lower_sash_head']-.125,lod,'Lower pediment '+str(j+1))
    # Jointed stone skirt runs only through the exterior masonry left after cutting the openings.
    for j,(lo,hi)in enumerate([(0,.285),(.285,.565),(.565,.866)]):
        step=.74 if not lod else 1.12
        x=left-step*(.37 if j%2 else 0)
        while x<right:
            x0=max(left,x+.008);x1=min(right,x+step-.010)
            if x1>x0:
                shape=box(x0,lo+.008,x1,hi-.009).intersection(area)
                if not shape.is_empty and shape.area>.003:whole.prism(shape,.006,.069,STONE if (int(5*x)+j)%4 else 'Darker cut granite','Cut granite plinth')
            x+=step
    for z,ww,th,dd in [(7.40,.0,.10,.12),(7.50,.18,.10,.20),(7.59,.15,.08,.26)]:
        length=.92-left;whole.box((left+.92)/2,z,length+ww,th,dd,.047,LIMESTONE,'Flat eave/rendered moulding')
    rightface=Facade(b,(right,0),(right,d['section_depth_m']),'Northwest return')
    rightface.wall(0,6.94,(),.265,CAST)
    leftface=Facade(b,(left,d['section_depth_m']),(left,0),'Southeast return')
    leftface.wall(0,d['flat_eave']-.13,(),.265,CAST)
    link_wall=Facade(b,(d['measured_u']['turret_finial'],2.83),(left,2.83),'Tower junction')
    link_wall.wall(0,d['flat_eave']-.14,(),.22,CAST)
    floor_slab(b,box(left,.04,right,d['section_depth_m']),0,.115,STONE,'Section/exposed floor cut')
    floor_slab(b,box(left,.31,right,d['section_depth_m']),4.34,4.51,'Dormant wall shadows','Section/upper floor cut')
    entrance(whole,d,lod);projecting_window(b,whole,arch_cx,d,lod);turret(b,d,lod);roof(b,d,lod,whole)
    rot=np.array([[d['frontage_tangent_enu'][0],-d['frontage_tangent_enu'][1]],[d['frontage_tangent_enu'][1],d['frontage_tangent_enu'][0]]])
    for part in b.parts:
        xyz=np.asarray(part['vertices']);xyz[:,:2]=xyz[:,:2]@rot.T;part['vertices']=xyz.tolist()
    apply_metric_uv(b)


if __name__=='__main__':
    pa=argparse.ArgumentParser(add_help=False)
    pa.add_argument('--output',type=Path);pa.add_argument('--lod',action='store_true');pa.add_argument('--blender',default='blender')
    args,rest=pa.parse_known_args()
    if args.output:
        if rest:pa.error('Unrecognised raw-export options')
        model=AggregateBuilder(PALETTE);add_building(model,args.lod);model.save(args.output,META)
    else:
        if args.lod:pa.error('--lod requires --output')
        os.environ['YINGYUAN_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)

