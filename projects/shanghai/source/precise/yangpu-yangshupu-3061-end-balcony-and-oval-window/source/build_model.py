"""Model the photographed terminal bay of the residences in Lane 3061, Yangshupu Road."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import Polygon, box

SOURCE=Path(__file__).absolute().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as MetricBuilder
from photo_architecture import Facade
from limewash import CAST,TEXTURE,apply_metric_uv
from oval_surround import BRICK,LIGHT,MORTAR,RED,oval_window
from roof_corner import EAVE,TILE,TILE_LIGHT,roof
from window_joinery import WOOD,EDGE,BLUE,GREY,IRON,CREAM,SHADOW,upper_frames,lower_frames,railing

ID='yangpu-yangshupu-3061-end-balcony-and-oval-window'
META=dict(id=ID,name='杨树浦路3061弄住宅端部阳台与椭圆砖窗',heritage_group='4G004',viewer_page='yangshupu-3061-end-balcony-and-oval-window.html',
          scope='2013年署名照片中右端的一开间及其侧墙。三扇底层窗、四扇二楼格窗、弧形铁栏、坡面窗及侧面的竖长砖饰窗。')
DIM=json.loads((SOURCE/'dimensions.json').read_bytes())


def pigment(rgb,roughness=.83,metallic=0.):
    a=np.array(rgb)/255.
    return dict(color=np.where(a<.04045,a/12.92,((a+.055)/1.055)**2.4).tolist(),roughness=roughness,metallic=metallic)


PALETTE={CAST:dict(color=[1.,1.,1.],roughness=.95,texture=str(TEXTURE)),WOOD:pigment([103,44,49],.65),EDGE:pigment([132,66,59]),
         BLUE:pigment([126,151,148],.28,.20),GREY:pigment([87,90,100],.30,.17),IRON:pigment([46,46,49],.54,.48),
         CREAM:pigment([214,207,184]),SHADOW:pigment([49,45,44]),BRICK:pigment([165,112,103]),LIGHT:pigment([183,134,122]),
         MORTAR:pigment([208,190,164]),RED:pigment([126,58,56]),TILE:pigment([109,59,57]),TILE_LIGHT:pigment([136,78,67]),
         EAVE:pigment([102,58,53]),'Pale gutter metal':pigment([166,163,146],.58,.28),
         'Rough pink stone':pigment([176,156,139]),'Stone joint':pigment([123,111,99]),
         'Section core':pigment([126,117,102]),'Lime cornice':pigment([196,186,162])}


class AggregateBuilder(MetricBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        raw=Path(path);receipt=raw.with_suffix('.geometry.json')
        if receipt.is_file():
            record=json.loads(receipt.read_bytes())
            with raw.open('rb')as stream:record['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            record['bytes']=raw.stat().st_size
            receipt.write_text(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n')


def lower_bow(builder,d,lod):
    fronts=[];extended=[]
    for pair in d['ground_jamb_xy']:
        a,b=np.asarray(pair);axis=(b-a)/np.linalg.norm(b-a)
        a=a-axis*.14;b=b+axis*.14
        fronts.append(Facade(builder,a,b,'Bow opening '+str(len(fronts)+1)));extended.extend([a,b])
    perimeter=[(d['left_cut'],0),*extended,(d['corner_x'],0)]
    z0=d['cut_base'];top=d['ground_cornice']
    for i,face in enumerate(fronts):
        width=np.linalg.norm(np.diff(np.array(d['ground_jamb_xy'][i]),axis=0))
        win=box(-width/2,d['ground_sill'],width/2,d['ground_window_top'])
        body=box(-face.length/2,z0,face.length/2,top).difference(win)
        face.prism(body,-.19,0,CAST,'plastered piers and window seats')
        lower_frames(face,d,lod,i+1)
    for i in [0,2,4,6]:
        face=Facade(builder,perimeter[i],perimeter[i+1],'Bow pier '+str(i//2+1))
        face.prism(box(-face.length/2,z0,face.length/2,top),-.19,0,CAST,'solid angled return')
    outline=Polygon([*perimeter,(d['corner_x'],.22),(d['left_cut'],.22)])
    for name,z,h,projection,mat in [('sill plate',z0,.080,.025,'Section core'),('storey fascia',top,.14,.055,CREAM),
                                    ('cornice groove',top+.14,.055,.095,'Lime cornice'),('upper drip',top+.195,.072,.128,CREAM)]:
        builder.plan_prism(outline.buffer(projection,join_style=2),z,z+h,mat,'Bow/'+name)
    # Slender curved balcony curb and open ironwork at the photographed edge.
    xs=np.linspace(d['rail_left'],d['rail_right'],24);span=xs[-1]-xs[0]
    line=[(x,-.39-.29*(1-(2*(x-xs[0])/span-1)**2))for x in xs]
    cap=Polygon([*line,(xs[-1],.012),(xs[0],.012)])
    builder.plan_prism(cap,top+.262,d['rail_base'],CAST,'Balcony/curved plaster base')
    builder.plan_prism(cap.buffer(.021,join_style=2),d['rail_base']-.039,d['rail_base']+.004,CREAM,'Balcony/edge coping')
    railing(builder,d,lod)


def side_wall(builder,d,lod):
    x=d['corner_x'];edge=Facade(builder,(x,-.5),(x,.5),'Side return')
    oval=oval_window(builder,edge,d,lod)
    lower=d['ground_cornice'];top=d['eave']-.028;depth=d['side_cut'];z0=d['cut_base']
    # Separately cut and filled to avoid a hidden wall behind the opening leaf.
    edge.prism(box(0,lower+.18,depth,top).difference(oval),-.21,0,CAST,'ivory plaster around oval')
    edge.prism(box(0,z0,depth,lower+.18),-.19,0,'Stone joint','ground-storey rubble backing')
    rows=6;course=(lower+.14-z0)/rows
    for k in range(rows):
        width=.64;start=-width/2 if k%2 else 0.
        while start<depth:
            left=max(0.,start+.007);right=min(depth,start+width-.007)
            if right-left>.02:
                edge.box((left+right)/2,z0+(k+.5)*course,right-left,course-.018,.032,.010,'Rough pink stone','staggered rustication')
            start+=width
    for z,high,prot,mat in [(lower+.09,.105,.06,'Lime cornice'),(lower+.166,.047,.115,CREAM),(lower+.216,.046,.092,'Lime cornice')]:
        edge.box(depth/2,z,depth,high,prot+.046,prot/2,mat,'floor string return')


def add_building(builder,lod):
    d=DIM;left=d['left_cut'];right=d['corner_x'];e=d['eave']
    face=Facade(builder,(-.5,0),(.5,0),'Front wall')
    width=d['upper_width'];sill=d['upper_sill'];head=sill+d['upper_height']
    window=box(0,sill,width,head)
    wall=box(left,d['ground_cornice']+.2,right,e-.040).difference(window)
    face.prism(wall,-.19,0,CAST,'limewashed wall enclosing the balcony doors')
    upper_frames(face,d,lod);lower_bow(builder,d,lod);side_wall(builder,d,lod)
    for face,z,width,cx in [(face,e-.100,right-left,(right+left)/2),(Facade(builder,(right,-.5),(right,.5),'Side eaves'),e-.100,d['side_cut'],d['side_cut']/2)]:
        face.box(cx,z,width,.100,.12,.017,'Lime cornice','eaves band')
    builder.plan_prism(box(left,.01,right,d['side_cut']),d['cut_base'],d['cut_base']+.07,'Section core','Section/base')
    roof(builder,d,lod);apply_metric_uv(builder)


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for a raw mesh')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['YANGSHUPU3061_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
