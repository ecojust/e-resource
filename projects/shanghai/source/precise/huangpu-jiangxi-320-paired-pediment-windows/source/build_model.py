"""The two adjacent pedimented windows at 320 Jiangxi Middle Road."""
import argparse,hashlib,json,os,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

SOURCE=Path(__file__).absolute().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:
    PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as TexturedBuilder

from shapely.geometry import box
from photo_architecture import Facade
from window_details import (BAYS,STONE,LIGHT,SHADE,FIELD,JOINT,REVEAL,SILL,WOOD,GLAZING,
    BLUE,OCHRE,HEM,LINING,METAL,shape,panelled_stone,sash,cloth)
from paint import TEXTURE,apply_metric_uv
from asset_rights import licensed_writer,retain_metadata,visible_canvas_surfaces
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id='huangpu-jiangxi-320-paired-pediment-windows',name='道达大楼江西中路立面双三角窗楣与托座',
    heritage_group='5A004',viewer_page='jiangxi-320-paired-pediment-windows.html',
    scope='江西中路320号临街正立面照片右侧一对三角窗楣、分层檐线、中央凸楔、竖窗及2015年条纹布篷。',
    source_period='Antigng摄于2015年7月20日',geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,
    photos_embedded=False,photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
    copyright='Model geometry CC BY-SA 4.0. Photographic reference: Antigng, 20 July 2015, '+PHOTO_SOURCE+' . '+LICENSE_URL,
    attribution='Interpreted from Antigng’s photograph of the Doeda Building. Geometry CC BY-SA 4.0. Original procedural texture and code MIT.')
def pigment(rgb,rough=.82,metal=0):
    c=np.asarray(rgb)/255.
    return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={STONE:pigment([203,198,185]),LIGHT:pigment([218,210,195]),SHADE:pigment([165,158,143]),
    FIELD:dict(color=[1.,1.,1.],texture=str(TEXTURE),roughness=.93),JOINT:pigment([151,144,129]),
    REVEAL:pigment([176,172,160]),SILL:pigment([190,186,174]),WOOD:pigment([58,61,65],.6),
    GLAZING[0]:pigment([56,62,67],.32,.16),GLAZING[1]:pigment([79,96,106],.38,.13),
    GLAZING[2]:pigment([91,89,85],.37,.1),BLUE:pigment([91,125,148]),OCHRE:pigment([187,169,126]),
    HEM:pigment([87,95,102]),LINING:pigment([183,174,155]),METAL:pigment([68,71,70],.52,.4)}

def add_building(builder,lod):
    f=Facade(builder,(-2.4,0),(2.4,0),'Street')
    holes=unary_union([shape(bay['opening'],.015) for bay in BAYS])
    # Cut through the window apertures; build the wall body only inside the study limits.
    outline=box(-2.10,-.36,2.10,4.04)
    wall=outline.difference(holes)
    f.prism(wall,-.365,-.009,JOINT,'continuous recessed opening reveals')
    for i,(level,top) in enumerate(zip([-.36,0,.41,.85,1.28,1.73,2.16,2.60,3.04,3.48,3.89],[0,.41,.85,1.28,1.73,2.16,2.60,3.04,3.48,3.89,4.04])):
        for j,(l,r) in enumerate([(-2.10,-1.46+(i%2)*.55),(-1.46+(i%2)*.55,.10+(i%2)*.63),(.10+(i%2)*.63,1.50+(i%2)*.27),(1.50+(i%2)*.27,2.10)]):
            segment=wall.intersection(box(l+.002,level+.003,r-.002,top-.003))
            if segment.area>1e-5:f.prism(segment,-.009,.001,FIELD,'masonry course '+str(i+1)+' stone '+str(j+1))
    for bay in BAYS:
        panelled_stone(f,bay);sash(f,bay);cloth(builder,bay,lod)
    apply_metric_uv(builder)
class AggregateBuilder(TexturedBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        visible_canvas_surfaces(Path(path), {BLUE,OCHRE,HEM})
        p=Path(path);side=p.with_suffix('.geometry.json')
        if side.is_file():
            record=json.loads(side.read_bytes())
            with p.open('rb') as file:record['sha256']=hashlib.file_digest(file,'sha256').hexdigest()
            record['bytes']=p.stat().st_size;side.write_text(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['DOEDA_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder
        pack.retain_metadata=retain_metadata
        pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
