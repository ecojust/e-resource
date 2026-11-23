"""Reconstruct the documented garden-side service wing of the Sassoon estate, Shanghai."""
import argparse
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path[:0]=[str(HERE),str(HERE.parent/'measurements'),str(PROJECT/'source/precise/hongkou-general-post-office/source/common'),str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source')]
from crown_builder import CrownBuilder
from photo_architecture import Builder as ArchitectureBuilder
from wing_frame import WingFrame
from service_materials import PALETTE as BASE_PALETTE
import wing_finishes
PALETTE={**BASE_PALETTE,**wing_finishes.PALETTE}
from court_frame import add_courtyard
from covered_link import add_link
from pitched_roof import add_roof
from roof_dormers import add_dormers,roof_apertures
from side_return import add_side,side_roof_apertures

ID='changning-sassoon-villa-service-wing'
SLUG='sassoon-villa-service-wing'
META={'id':ID,'name':'沙逊别墅辅楼院面木构与老虎窗','address':'上海市长宁区虹桥路2409号','heritage_id':'sh-historic-b1-030',
      'source':'https://www.jianweigroup.com/site/10/category0051/b1216655955211e89cd6408d5c6f7eaa.html',
      'photo_source':'https://digitalcollections.smu.edu/digital/collection/vsp/id/52',
      'camera_views':json.loads((HERE/'cameras.json').read_bytes()),'geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'viewer_page':SLUG+'.html'}
class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in wing_finishes.STEMS:wing_finishes.metric_uv(self.parts[-1])
    def save(self,path,metadata=None):
        ArchitectureBuilder.save(self,path,metadata)
        return wing_finishes.writer.embed_normals(path)
def add_building(b,lod=False):
    frame=WingFrame()
    add_courtyard(b,frame,lod)
    add_roof(b,frame,lod,roof_apertures(frame),side_roof_apertures(frame))
    add_dormers(b,frame,lod)
    add_side(b,frame,lod)
    add_link(b,frame,lod)
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',type=Path,required=True);cli.add_argument('--lod',action='store_true')
    args=cli.parse_args();b=Builder(PALETTE);add_building(b,args.lod);print(b.save(args.output,META)['sha256'])
