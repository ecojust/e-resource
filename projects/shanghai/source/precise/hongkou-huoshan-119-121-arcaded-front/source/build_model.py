"""Document the arcaded street front at 119–121 Huoshan Road from 2015, 2020 and 2026 observations."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union

SOURCE=Path(__file__).absolute().parent
PROJECT=next(parent for parent in SOURCE.parents if (parent/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as MetricBuilder
from photo_architecture import Facade,opening

from brick_facing import CAST,TEXTURE,apply_metric_uv
from arcade import RED,SECOND,JOINT,BUFF,GREY,WOOD,GLASS,REFLECT,FAN,METAL,DARK,PANEL,wing
from parapet import plate
from roof_section import TILE,SUN_TILE,EAVE,roof

ID='hongkou-huoshan-119-121-arcaded-front'
META=dict(id=ID,name='霍山路119–121号住宅双拱窗与砖砌女儿墙',heritage_group='4F027',viewer_page='huoshan-119-121-arcaded-front.html',
          scope='住宅组中霍山路119–121号的临街上部、左右双拱窗、两座屋面窗和中央起伏的砖女儿墙。参考2015、2026年两张署名照片及2020年四处街景。')
DIM=json.loads((SOURCE/'dimensions.json').read_bytes())


def colour(rgb,rough=.83,metal=0):
    v=np.array(rgb)/255.
    return dict(color=np.where(v<.04045,v/12.92,((v+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)


PALETTE={CAST:dict(color=[1.,1.,1.],roughness=.96,texture=str(TEXTURE)),RED:colour([137,71,55]),SECOND:colour([110,57,48]),
         JOINT:colour([116,108,94]),BUFF:colour([201,192,170]),GREY:colour([131,125,112]),WOOD:colour([79,62,55],.66),
         GLASS:colour([86,88,86],.29,.21),REFLECT:colour([108,116,114],.29,.17),FAN:colour([119,78,66],.83),
         METAL:colour([60,58,53],.48,.22),DARK:colour([50,45,42]),PANEL:colour([127,112,91]),
         'Grey painted joinery':colour([98,96,88]),TILE:colour([114,72,62]),SUN_TILE:colour([137,88,68]),
         EAVE:colour([67,61,57]),'Dark dormer cheeks':colour([82,70,61]),'Section cut':colour([127,115,101])}


class AggregateBuilder(MetricBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        raw=Path(path);receipt=raw.with_suffix('.geometry.json')
        if receipt.is_file():
            rec=json.loads(receipt.read_bytes())
            with raw.open('rb') as stream:rec['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            rec['bytes']=raw.stat().st_size
            receipt.write_text(json.dumps(rec,ensure_ascii=False,separators=(',',':'))+'\n')


def street_arcades(builder,d,lod):
    front=Facade(builder,(-.5,0),(.5,0),'Arcades')
    for index,(left,right,axes) in enumerate([(0,d['middle_left'],d['gallery_axes'][:2]),
                                              (d['middle_right'],d['cornice_width'],d['gallery_axes'][2:])]):
        title='Near pair' if index==0 else 'Far pair'
        holes=[]
        for level in ('middle','upper'):
            val=d['gallery_levels'][level]
            for n,x in enumerate(axes):
                holes.append(opening(x,val['apron_bottom'],d['gallery_span'],val['peak']-val['apron_bottom'],val['rise'],23 if lod else 52))
                wing(front,x,d,level,lod,title+' '+level+' '+str(n+1),red_panel=(index==0 and level=='upper'),internal_side=1 if n==0 else -1)
            # The cream enclosure and its narrow centre support continue between both openings.
            radius=d['gallery_span']/2
            inner_left=axes[0]+radius;inner_right=axes[1]-radius;mid=(inner_left+inner_right)/2
            holes.append(box(inner_left-.002,val['apron_bottom'],inner_right+.002,val['spring']-.073))
            panel_width=inner_right-inner_left
            base=val['apron_bottom'];top=val['spring']-.12
            front.box(mid,(base+top)/2,panel_width,top-base,.14,-.245,BUFF,title+' '+level+'/continuous cream enclosure')
            front.box(mid,(base+top)/2,panel_width*.55,top-base,.117,-.119,BUFF,title+' '+level+'/central engaged jamb')
            for dz,h,fac,mat in [(-.098,.11,.71,SECOND),(-.007,.091,.91,RED),(.076,.071,1.08,SECOND)]:
                front.box(mid,val['spring']+dz,panel_width*fac,h,.198,.036,mat,title+' '+level+'/stepped central impost')
            if not lod:
                for k in (-1,0,1):
                    front.box(mid+k*panel_width*.19,val['spring']-.092,.041,.054,.047,.147,GREY,title+' '+level+'/impost detail')
        face=box(left,2.71,right,d['cornice_z']-.078).difference(unary_union(holes))
        front.prism(face,-.355,0,CAST,title+'/perforated grey brick wall')
        for z,w,h,depth,material in [(2.755,.004,.068,.14,RED),(2.825,.044,.088,.21,GREY),
                                      (6.876,.005,.086,.161,RED),(6.96,.012,.069,.21,GREY),
                                      (d['cornice_z']-.178,.046,.089,.144,RED),(d['cornice_z']-.081,.112,.128,.236,GREY),
                                      (d['cornice_z']+.009,.184,.079,.295,BUFF)]:
            front.box((left+right)/2,z,right-left+w,h,depth,.018,material,title+'/horizontal string')
        if not lod:
            count=round((right-left)/.171)
            for n in range(count):
                front.box(left+(n+.5)*(right-left)/count,2.982,.089,.111,.067,.045,SECOND,title+'/plinth brick dentils')


def add_building(builder,lod):
    d=DIM;w=d['cornice_width'];depth=d['section_depth'];street_arcades(builder,d,lod)
    center=Facade(builder,(-.5,-.178),(.5,-.178),'Central bays');plate(center,d,lod)
    for x in [d['middle_left'],d['middle_right']]:
        center.box(x,6.83,.232,8.24,.349,-.059,RED,'Pilaster/street junction')
    # The first arched opening on the southwest return is visible in both sources.
    left=Facade(builder,(0,depth),(0,0),'West return');ax=depth/2-1.17
    data=d['gallery_levels']['upper'];side=opening(ax,data['apron_bottom'],d['gallery_span'],data['peak']-data['apron_bottom'],data['rise'],23 if lod else 52)
    outline=box(-depth/2,2.71,depth/2-.358,d['cornice_z']-.012)
    left.prism(outline.difference(side),-.265,0,CAST,'brick side wall')
    wing(left,ax,d,'upper',lod,'side upper opening')
    right=Facade(builder,(w,0),(w,depth),'East return')
    right.prism(box(-depth/2+.358,2.71,depth/2,d['cornice_z']-.012),-.265,0,CAST,'plain wall at cut')
    for lo,hi in [(0,d['middle_left']),(d['middle_left'],d['middle_right']),(d['middle_right'],w)]:
        builder.plan_prism(box(lo,.36,hi,depth),2.71,2.815,'Section cut','Section/base cut')
    roof(builder,d,lod)
    tx,ty=d['tangent_enu'];rotation=np.array([[tx,-ty],[ty,tx]])
    for part in builder.parts:
        vertices=np.asarray(part['vertices']);vertices[:,0]-=w/2
        vertices[:,:2]=vertices[:,:2]@rotation.T;part['vertices']=vertices.tolist()
    apply_metric_uv(builder)


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for raw output')
        b=AggregateBuilder(PALETTE);add_building(b,args.lod);b.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['HUOSHAN_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
