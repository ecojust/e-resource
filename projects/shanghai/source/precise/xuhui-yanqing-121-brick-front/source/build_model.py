"""Reconstruct the photographed street front at 121 Yanqing Road from its registered openings."""
import argparse,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in [*HERE.parents,Path(os.getenv('E_RESOURCE_SHANGHAI','.'))] if (p/'tools/package_architectural_model.py').is_file())
for folder in ['hongkou-general-post-office/source/common','hongkou-tanggu-road-apartment-dated-crown/source','xuhui-gaoan-77-curved-veranda/source']:
    sys.path.append(str(PROJECT/'source/precise'/folder))
from crown_builder import CrownBuilder
from placement import Facade
from brick_finishes import REPEAT_METRES
from brick_front import add_front
from materials import PALETTE
from western_bay import add_western_bay
ID='xuhui-yanqing-121-brick-front';SLUG='yanqing-121-brick-front'
META={'id':ID,'name':'延庆路121号住宅砖砌街面与木筋凸窗','address':'上海市徐汇区延庆路121号','heritage_group':'5D043','geometry_license':'MIT','texture_license':'MIT','photo_author':'Antigng','photo_reference_date':'2018-02-07','photo_reference_page':'https://commons.wikimedia.org/wiki/File:延庆路121号住宅.jpg','photo_reference_license':'CC BY-SA 4.0','photos_embedded':False,'scope':'清水砖临街墙、五樘上窗和券口上方的木筋凸窗。'}
class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in REPEAT_METRES:
            sx,sz=REPEAT_METRES[material];p=self.parts[-1]
            p['texcoords']=[(u/(.78*sx),v/(.78*sz)) for u,v in p['texcoords']]
def add_building(b,lod=False):
    add_front(Facade(b,label='Yanqing 121'),lod)
    add_western_bay(b,lod)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--lod',action='store_true');args=ap.parse_args();b=Builder(PALETTE);add_building(b,args.lod);r=b.save(args.output,META);print(r['sha256'],r['triangles'])
