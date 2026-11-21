"""Build the photographed courtyard entrance and the paired upper sashes at 6 Huayuanli."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import box

SOURCE=Path(__file__).absolute().parent
PROJECT=next(parent for parent in SOURCE.parents if (parent/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as MetricBuilder
from photo_architecture import Facade

from court_joinery import (PAINT,EDGE,DARK,GLASS,GLASS_LIGHT,PUTTY,STONE,LIME,CHIP,SHADOW,
                            FLOOR,paired_window,entry)
from roughcast import CAST,TEXTURE,apply_metric_uv
from segmented_arch import AGED,LIP,add_portal

ID='hongkou-huayuanli-six-court-arch'
META=dict(id=ID,name='花园里6号曾联松旧居院内券门与双窗',heritage_group='4F023',viewer_page='huayuanli-six-court-arch.html',
          scope='山阴路145弄6号，取2020年回访照片可见的一层券门、石阶与二层红框双窗。按单张照片估测尺寸。')
DIM=json.loads((SOURCE/'dimensions.json').read_bytes())


def pigment(rgb,roughness=.86,metallic=0):
    value=np.asarray(rgb,dtype=float)/255.
    srgb=np.where(value<.04045,value/12.92,((value+.055)/1.055)**2.4).tolist()
    return dict(color=srgb,roughness=roughness,metallic=metallic)


PALETTE={CAST:dict(texture=str(TEXTURE),color=[1.,1.,1.],roughness=.96),
         PAINT:pigment([109,56,52],.66),EDGE:pigment([145,82,67],.65),DARK:pigment([57,53,49]),
         GLASS:pigment([68,87,85],.31,.17),GLASS_LIGHT:pigment([86,101,94],.31,.16),
         PUTTY:pigment([104,82,68],.82),STONE:pigment([152,147,135]),LIME:pigment([194,180,151]),
         CHIP:pigment([213,200,177]),AGED:pigment([161,148,125]),LIP:pigment([221,210,184],.76),
         SHADOW:pigment([79,64,58]),'Study cut darkness':pigment([13,14,13]),FLOOR:pigment([119,117,110]),'Cut wall core':pigment([128,125,116])}


class AggregateBuilder(MetricBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        raw=Path(path)
        receipt=raw.with_suffix('.geometry.json')
        if receipt.is_file():
            record=json.loads(receipt.read_bytes())
            with raw.open('rb') as stream:record['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            record['bytes']=raw.stat().st_size
            receipt.write_text(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n')


def add_building(builder,lod):
    d=DIM
    half=d['width_m']/2;upper=d['upper_wall_recess'];back=d['section_back_m']
    front=Facade(builder,(-.5,0),(.5,0),'Courtyard front')
    # Bound each study at its photographic cut. Wall openings are actual mesh holes.
    head=d['threshold_height']+d['door_clear_height']
    inner_cut=box(-d['door_clear_width']/2-.091,-.001,d['door_clear_width']/2+.091,head+.094)
    wall=box(-half,-.003,half,3.095).difference(inner_cut)
    front.prism(wall,-.375,0,LIME,'Lower wall/door opening')
    wx=d['upper_center'];ww=d['upper_frame_width']
    window=box(wx-ww/2-.014,d['upper_frame_sill']-.014,wx+ww/2+.014,d['upper_frame_top']+.014)
    upper_panel=box(-half,3.095,half,d['cut_height']).difference(window)
    front.prism(upper_panel,-.40,-upper,CAST,'Upper roughcast wall')
    # The wall shows a restrained horizontal string returning under the upper storey.
    front.box(0,3.135,2*half,.053,.145,-.04,STONE,'Wall/narrow storey string')
    for side in(-1,1):
        a,b=((side*half,0),(side*half,back))if side>0 else((side*half,back),(side*half,0))
        edge=Facade(builder,a,b,'Section side '+str(side))
        start=upper+.291;length=back-start
        # Side walls beyond the photographed face are a plain section, with no inferred openings.
        edge.box((start+length/2-back/2)*side,d['cut_height']/2,length,d['cut_height'],.055,-.0275,'Cut wall core','limited return')
    builder.plan_prism(box(-half,.4,half,back),3.028,3.105,'Cut wall core','Section/upper floor cut')
    add_portal(builder,front,d,lod)
    paired_window(builder,front,d,lod)
    entry(builder,front,d,lod)
    # This separately named, removable display plane represents the photograph's
    # darkness at the limit of the known section. It supplies no interior plan.
    front.box(0,(head+d['threshold_height'])/2,d['door_clear_width']+.036,head-d['threshold_height']+.024,.012,-back+.012,'Study cut darkness','Study cut/removable dark limit')
    apply_metric_uv(builder)


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for a raw mesh')
        model=AggregateBuilder(PALETTE)
        add_building(model,args.lod)
        model.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['HUAYUANLI_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder
        pack.build(SOURCE,META,PALETTE,add_building)
