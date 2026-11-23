"""Build the separately registered Jingxing Road house and the dated lane entrance."""
import argparse
from pathlib import Path
import json
import os
import sys

SOURCE=Path(__file__).resolve().parent
paths=list(SOURCE.parents)
if os.environ.get('E_RESOURCE_SHANGHAI'):
    paths.append(Path(os.environ['E_RESOURCE_SHANGHAI']))
PROJECT=next(p for p in paths if (p/'tools/package_architectural_model.py').is_file())
PRECISE=PROJECT/'source/precise'
for loc in ['hongkou-general-post-office/source/common','hongkou-tanggu-road-apartment-dated-crown/source']:
    sys.path.insert(0,str(PRECISE/loc))
from crown_builder import CrownBuilder as Builder
import street314
import gateways314
import north_return314
import roof_rows
import lane310
import housing310
import numpy as np

ID='yangpu-yiqingli-jingxing-310-314-lane-houses'
SLUG='yiqingli-jingxing-310-314-lane-houses'
PALETTE=street314.PALETTE | roof_rows.PALETTE | lane310.PALETTE
META={'id':ID,'name':'颐庆里住宅，景星路街面','address':'上海市杨浦区景星路310、314弄',
      'heritage_group':'5G014','period':'2015年4月街面','geometry_license':'MIT',
      'texture_license':'MIT','photos_embedded':False,'photo_author':'Fayhoo',
      'photo_source':'https://commons.wikimedia.org/wiki/File:Jingxinglu_314_Long_Zhuzhai.JPG',
      'url':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
      'camera_views':json.loads((SOURCE/'cameras.json').read_bytes()),
      'photo_sources':['https://commons.wikimedia.org/wiki/File:Jingxinglu_314_Long_Zhuzhai.JPG','https://commons.wikimedia.org/wiki/File:Jingxinglu_310_Long_Zhuzhai.JPG'],
      'license_url':'https://creativecommons.org/licenses/by-sa/3.0/',
      'viewer_page':SLUG+'.html','copyright':'Original architecture and procedural materials: MIT. Photographs: Fayhoo, CC BY-SA 3.0; not embedded.'}

def placed_matrix(placement):
    angle=np.radians(placement.get('rotation_degrees',0.))
    co,si=np.cos(angle),np.sin(angle)
    affine=np.eye(4)
    affine[:3,:3]=np.array([[co,-si,0],[si,co,0],[0,0,1.]])*placement.get('scale',1.)
    affine[:3,3]=placement.get('translation',[0.,0.,0.])
    return affine

def place_parts(parts, placement):
    matrix=placed_matrix(placement)
    for part in parts:
        points=np.asarray(part['vertices'])
        part['vertices']=(points@matrix[:3,:3].T+matrix[:3,3]).tolist()

def add_building(b,lod=False):
    start=len(b.parts)
    street314.add_front(b,lod)
    layout=json.loads((SOURCE/'facade314-layout.json').read_bytes())
    gateways314.add_gateways(street314.Front(b,layout),lod)
    north_return314.add_return(b,lod)
    places=json.loads((SOURCE/'house-placements.json').read_bytes())
    place_parts(b.parts[start:],places['house_314'])
    roof_rows.add_314_roof(b,lod)
    start=len(b.parts)
    lane310.add_lane310(b,lod)
    housing310.add_housing(b,lod)
    place_parts(b.parts[start:],places['house_310'])

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output',type=Path,required=True)
    cli.add_argument('--lod',action='store_true')
    args=cli.parse_args()
    builder=Builder(PALETTE)
    add_building(builder,args.lod)
    args.output.parent.mkdir(exist_ok=True,parents=True)
    info=builder.save(args.output,META)
    print(json.dumps({k:info[k] for k in ['triangles','parts','bytes','sha256']}))

if __name__=='__main__':
    main()
