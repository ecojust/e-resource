"""Reconstruct the 1908 published view of the Zi-ka-wei observatory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as RepeatingTextureBuilder
from photo_architecture import Facade
from historic_masonry import MASONRY,TEXTURE,map_bricks
from elevation import (BASE,DARK,FRAME,GLASS,IVORY,JOINT,RED,ROOF,STONE,
                       hip,window_wall)
from clock_tower import CLOCK,METAL,WALL,build_tower

ID='xuhui-zikawei-observatory-1908'
META=dict(id=ID,name='徐家汇观象台1908年钟塔与两翼',heritage_group='4D047',
          viewer_page='zikawei-observatory-1908.html',
          scope='以1908年出版图的封闭式砖木测风塔为准，复原钟塔、两翼、双向台阶和院侧返面。')


class AggregateBuilder(RepeatingTextureBuilder):
    """Keep the optional authoring summary in step with the finalized sampler."""
    def save(self,path,metadata=None):
        super().save(path,metadata)
        path=Path(path)
        report=path.with_suffix('.geometry.json')
        if report.exists():
            state=json.loads(report.read_bytes())
            with path.open('rb') as stream:
                state['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            report.write_text(json.dumps(state,ensure_ascii=False,separators=(',',':'))+'\n')


def pigment(v,roughness=.81,metal=0.):
    rgb=np.array(v,dtype=float)/255.
    return dict(color=np.where(rgb<.04045,rgb/12.92,((rgb+.055)/1.055)**2.4).tolist(),
                roughness=roughness,metallic=metal)


PALETTE={
    MASONRY:dict(color=[1.,1.,1.],roughness=.9,texture=str(TEXTURE)),
    RED:pigment([157,86,67]),STONE:pigment([161,147,128]),
    IVORY:pigment([209,197,174]),GLASS:pigment([80,92,96],.29,.13),
    FRAME:pigment([86,73,63]),JOINT:pigment([103,73,65]),
    BASE:pigment([103,100,96]),ROOF:pigment([92,84,81]),
    DARK:pigment([53,51,48]),CLOCK:pigment([217,207,179],.68),
    METAL:pigment([68,70,64],.47,.25),WALL:pigment([185,163,136])}

# Widths were recovered from the shaded building symbol on the 1920 plan and
# scaled to the measured end-to-end roof span. The later schematic includes a short eastern
# extension. The 1908 plate shows the pavilion ending in open sky at that
# position. Only the five evidenced volumes are included in this period model.
SECTIONS=[
    ('West end pavilion',-22.60,-13.00,0.,18.0,11.77,13.65),
    ('West connecting wing',-13.00,-3.80,3.40,14.10,11.41,12.64),
    ('Clock tower base',-3.80,3.90,-1.52,17.98,11.84,12.08),
    ('East connecting wing',3.90,13.10,3.40,13.70,11.41,12.64),
    ('East end pavilion',13.10,23.80,0.,17.6,11.77,13.65)]


def wall_stub(b,a,c,label,eave,lod):
    face=Facade(b,a,c,label)
    face.wall(.06,eave,(),.35,MASONRY)
    face.beam(2.40,.18,.10,STONE,label='Plinth course')
    face.beam(eave-.12,.24,.21,STONE,label='Eave projection')


def pavilion(b,idx,section,lod):
    name,x0,x1,y0,y1,eave,ridge=section;width=x1-x0
    separation=.25 if idx==0 else .207 if idx==4 else .23
    shift=.14 if idx==0 else .45 if idx==4 else 0.
    bays=[shift-width*separation,shift+width*separation]
    window_wall(b,(x0,y0),(x1,y0),name+' / front',eave,bays,lod,True,idx in (1,3))
    window_wall(b,(x1,y1),(x0,y1),name+' / rear',eave,bays,lod,False)
    for hand,x in [(-1,x0),(1,x1)]:
        other=idx+hand
        if other<0 or other==len(SECTIONS):
            limits=[(y0,y1)]
        else:
            o=SECTIONS[other]
            limits=[(y0,min(y1,o[3])),(max(y0,o[4]),y1)]
        for a,c in limits:
            if c-a<.30:continue
            fr,to=((x,c),(x,a)) if hand<0 else ((x,a),(x,c))
            if c-a>=7:
                window_wall(b,fr,to,name+' / end',eave,[0.],lod,True)
            else:wall_stub(b,fr,to,name+' / wing return',eave,lod)
    hip(b,x0,x1,y0,y1,eave,ridge,name)
    b.box(((x0+x1)/2,(y0+y1)/2,.055),(width,y1-y0,.11),BASE,label=name+' / footprint')


def add_building(b,lod):
    for idx,section in enumerate(SECTIONS):
        if idx==2:build_tower(b,*section[1:5],lod)
        else:pavilion(b,idx,section,lod)
    map_bricks(b)


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('unexpected raw export arguments: '+' '.join(rest))
        builder=AggregateBuilder(PALETTE)
        add_building(builder,args.lod);builder.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['ZIKAWEI_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder
        pack.build(SOURCE,META,PALETTE,add_building)
