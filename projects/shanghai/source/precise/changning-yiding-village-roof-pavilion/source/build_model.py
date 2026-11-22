"""Photographed upper room at Edinburgh Terrace, Lane 495 Jiangsu Road."""
import argparse,hashlib,json,os,sys
from pathlib import Path
import numpy as np
from shapely.geometry import box

SOURCE=Path(__file__).absolute().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as MetricBuilder
from photo_architecture import Facade

from roughcast import CAST,TEXTURE,apply_metric_uv
from frontage import RED,PALE,BROWN,CREAM,SAND,STEEL,BLACK,GLASS,GLASS2,SIDE,EDGE,double_cornice,steel_front,return_sash
from roof_details import TILE,TILE2,DARK_TILE,PIPE,IRON,UNIT,FAN,tile_slope,external_fittings
META=dict(id='changning-yiding-village-roof-pavilion',name='忆定村江苏路495弄住宅屋顶方间与双道红砖檐带',heritage_group='4M008',
    viewer_page='yiding-village-roof-pavilion.html',scope='2014年沿街照片里屋顶方间的两个可见面、错格钢窗与相接的低瓦屋面。')
D=json.loads((SOURCE/'dimensions.json').read_bytes())
M=SOURCE.parent/'measurements'
GRID=json.loads((M/'steel-window-pattern.json').read_bytes());BANDS=json.loads((M/'double-cornice-rhythm.json').read_bytes())['front_rows']
CUT='Neutral cut in plaster';ROOF='Muted flat roof';GLINT='Reflected light'
def pigment(rgb,rough=.82,metal=0):
    c=np.asarray(rgb)/255;return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={CAST:dict(color=[1,1,1],roughness=.93,texture=str(TEXTURE)),CUT:pigment([172,161,143]),ROOF:pigment([151,142,127]),
    RED:pigment([151,86,67]),PALE:pigment([196,147,107]),BROWN:pigment([125,80,68]),CREAM:pigment([190,183,162]),
    SAND:pigment([220,204,168]),STEEL:pigment([80,79,66],.59,.16),BLACK:pigment([49,47,40]),
    GLASS:pigment([222,213,190],.43,.10),GLASS2:pigment([211,204,180],.44,.11),GLINT:pigment([231,224,205],.46,.08),
    SIDE:pigment([68,66,63]),EDGE:pigment([125,122,115],.59,.18),'Dusty side glazing':pigment([100,98,94],.43,.14),
    'Muted glass reflection':pigment([143,141,133],.48,.11),TILE:pigment([143,100,79]),TILE2:pigment([157,109,86]),
    DARK_TILE:pigment([98,76,69]),PIPE:pigment([196,190,174]),IRON:pigment([71,69,67],.61,.28),UNIT:pigment([182,178,163],.68,.18),
    FAN:pigment([89,84,77],.66,.12),'Weathered fan ring':pigment([134,128,116],.68,.19)}
class AggregateBuilder(MetricBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        p=Path(path);f=p.with_suffix('.geometry.json')
        if f.is_file():
            r=json.loads(f.read_bytes())
            with p.open('rb')as stream:r['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            r['bytes']=p.stat().st_size;f.write_text(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')


def add_building(builder,lod):
    front=Facade(builder,(-.5,0),(.5,0),'Front')
    side=Facade(builder,(0,-.5),(0,.5),'Return')
    l=-D['front_width'];deep=D['return_depth'];h=D['roof_level'];band=D['cornice_height'];floor=-.72
    a=D['front_window_left'];c=a+D['front_window_width']
    win=(a,0,c,1.55)
    sw=(D['return_window_near'],D['return_window_bottom'],D['return_window_far'],D['return_window_top'])
    front.prism(box(l,floor,0,h).difference(box(*win)),-.19,0,CAST,'roughcast pierced wall')
    side.prism(box(.19,floor,deep,h).difference(box(*sw)),-.19,0,CAST,'roughcast pierced wall')
    # The tree-concealed and rear limits are simple study cuts, capped against open light.
    builder.box((l+.075,deep/2,floor+(h-floor)/2),(.15,deep,h-floor),CUT,label='Upper room/left study cut')
    builder.box(((l+.15)/2,deep-.075,floor+(h-floor)/2),(-l-.15,.15,h-floor),CUT,label='Upper room/rear study cut')
    builder.plan_prism(box(l,.00,0,deep),h-.032,h+.006,ROOF,'Upper room/roof surface')
    builder.plan_prism(box(l,0,0,deep),floor-.025,floor+.004,CUT,'Upper room/base cut')
    steel_front(front,win,GRID,lod);return_sash(builder,side,sw,lod)
    double_cornice(front,l,0,h,band,BANDS)
    double_cornice(side,0,deep,h,band,BANDS,True)
    # The low adjoining parapet has a photographed red/pale double band at the front.
    lower=Facade(builder,(-.5,.01),(.5,.01),'Lower frontage')
    lower.prism(box(.0,floor,3.38,-.02),-.22,.0,CAST,'adjoining wall')
    ext=[]
    for r in BANDS:
        period=r['median_period_m']
        ext.append({**r,'visible_pale_centres_m':np.arange(.023,3.38,period).tolist()})
    double_cornice(lower,0,3.38,-.012,.31,ext)
    tile_slope(builder,lod);external_fittings(builder,side,lod)
    apply_metric_uv(builder)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for a raw mesh')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['YIDING_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
