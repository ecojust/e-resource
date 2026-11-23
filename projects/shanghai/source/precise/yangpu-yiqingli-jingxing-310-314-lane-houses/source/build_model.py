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

ID='yangpu-yiqingli-jingxing-310-314-lane-houses'
SLUG='yiqingli-jingxing-310-314-lane-houses'
PALETTE=dict(street314.PALETTE)
META={'id':ID,'name':'颐庆里住宅，景星路街面','address':'上海市杨浦区景星路310、314弄',
      'heritage_group':'5G014','period':'2015年4月街面','geometry_license':'MIT',
      'texture_license':'MIT','photos_embedded':False,'photo_author':'Fayhoo',
      'photo_source':'https://commons.wikimedia.org/wiki/File:Jingxinglu_314_Long_Zhuzhai.JPG',
      'url':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
      'viewer_page':SLUG+'.html','copyright':'Original architecture and procedural materials: MIT. Photographs: Fayhoo, CC BY-SA 3.0; not embedded.'}

def add_building(b,lod=False):
    street314.add_front(b,lod)
    layout=json.loads((SOURCE/'facade314-layout.json').read_bytes())
    gateways314.add_gateways(street314.Front(b,layout),lod)

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
