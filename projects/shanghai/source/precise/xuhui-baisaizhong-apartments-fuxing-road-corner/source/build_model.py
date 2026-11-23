"""The Boissezon Apartments, placed from their historical ground plan and dated street photographs."""
import argparse,json,os,sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
paths=list(SOURCE.parents)
if os.environ.get('E_RESOURCE_SHANGHAI'):paths.append(Path(os.environ['E_RESOURCE_SHANGHAI']))
PROJECT=next(p for p in paths if (p/'tools/package_architectural_model.py').is_file())
PRECISE=PROJECT/'source/precise'
for lib in ['hongkou-general-post-office/source/common','hongkou-tanggu-road-apartment-dated-crown/source']:
    sys.path.insert(0,str(PRECISE/lib))
from crown_builder import CrownBuilder as Builder
import materials,corner,construction,street_wings,stair_hall,roof_storey
ID='xuhui-baisaizhong-apartments-fuxing-road-corner'
SLUG='baisaizhong-apartments-fuxing-road-corner'
PALETTE=materials.PALETTE|corner.PALETTE
META={'id':ID,'name':'白赛仲公寓','address':'上海市徐汇区复兴西路26、28号','heritage_group':'5D007','period':'1930年代形制，依2015–2023年影像登记的街角与住宅','camera_views':json.loads((SOURCE/'cameras.json').read_bytes()),'photo_author':'Fayhoo','license_url':'https://creativecommons.org/licenses/by-sa/3.0/','geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'source':'https://m.thepaper.cn/newsDetail_forward_22555305','photo_source':'https://commons.wikimedia.org/wiki/File:Baisaizhong_Gongyu.JPG','viewer_page':SLUG+'.html'}
def add_building(b,lod=False):
    construction.add_floors(b,lod)
    construction.add_back(b,lod)
    stair_hall.add_stairs(b,lod)
    street_wings.add_wings(b,lod)
    corner.add_corner(b,lod)
    roof_storey.add_roof(b,lod)

def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',type=Path,required=True);cli.add_argument('--lod',action='store_true');a=cli.parse_args()
    b=Builder(PALETTE);add_building(b,a.lod);a.output.parent.mkdir(exist_ok=True,parents=True)
    r=b.save(a.output,META);print(json.dumps({k:r[k] for k in ('sha256','triangles','parts','bytes')}))
if __name__=='__main__':main()
