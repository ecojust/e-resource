"""Model the open galleries and stairs of the historic residential court on Longchang Road."""
import argparse
import json
import os
from pathlib import Path
import sys
SOURCE=Path(__file__).absolute().parent
roots=[SOURCE,*SOURCE.parents]
if os.getenv('E_RESOURCE_SHANGHAI'):roots.append(Path(os.environ['E_RESOURCE_SHANGHAI']))
PROJECT=next(r for r in roots if (r/'tools/package_architectural_model.py').is_file())
for sub in ['hongkou-general-post-office/source/common','hongkou-tanggu-road-apartment-dated-crown/source','changning-yuyuan-1055-huang-family-garden-residence/source']:
    sys.path.append(str(PROJECT/'source/precise'/sub))
from crown_builder import CrownBuilder as Builder

import numpy as np
import courtyard
import street_facade
import west_entrance
ID='yangpu-longchang-apartments-grant-road-barracks-courtyard'
SLUG='longchang-apartments-grant-road-barracks-courtyard'
LAYOUT=json.loads((SOURCE/'courtyard-layout.json').read_bytes())
PALETTE={**courtyard.PALETTE, **street_facade.PALETTE, **west_entrance.PALETTE}
META=dict(id=ID,name='隆昌公寓——北院四面外廊与梯塔',address='上海市杨浦区隆昌路362号',heritage_group='5G002',period='2012–2019',viewer_page=SLUG+'.html',scope='具名北院五层住宅、四翼闭合外廊及伸向庭院的混凝土梯塔。',dimensions='2019年有日期航片拟合斜四边院，2012年院内照片拟合层高。',photo_author='Antigng、sunny sunday、Han Lei Photo、henrie；人民网文化频道、上观新闻。',photo_source='https://www.flickr.com/photos/jch-00/8300128448/',url='https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',geometry_license='MIT',texture_license='MIT',license_url='https://opensource.org/license/mit',copyright='Original architectural model and procedural textures: MIT. All reference photographs remain with their creators.',photos_embedded=False,camera_views=json.loads((SOURCE/'cameras.json').read_bytes()))
def add_building(b,lod=False):
    courtyard.add_court(b,lod,LAYOUT)
    street_facade.add_street(b,lod,LAYOUT)
    entry=LAYOUT['public_entrance']
    x=entry['outer_x']
    gate=Builder(PALETTE)
    west_entrance.add_entrance(gate,lod,{'gate_clear_width':entry['width'],'gate_clear_height':entry['height']})
    for part in gate.parts:
        part['vertices']=(np.asarray(part['vertices'])+[x,0.0,0.0]).tolist()
    b.parts.extend(gate.parts)
    # A short, plain exhibition section connects two intentionally aligned apertures.
    # It is not a survey of the occupied ground storey.
    face=courtyard.frame(b,LAYOUT,0)
    ends=[face.pt(s,-LAYOUT['gallery_depth']-.295,0) for s in entry['inner_s']]
    left,right=x-entry['width']/2,x+entry['width']/2
    start=.18
    shape=courtyard.Polygon([(left,start),(right,start),(right,ends[1][1]),(left,ends[0][1])])
    b.plan_prism(shape,-.095,.008,courtyard.SL,'362 exhibition section | paving')
    b.plan_prism(shape,entry['height'],entry['height']+.13,courtyard.C,'362 exhibition section | soffit')
    for edge,stop,sign in ((left,ends[0][1],-1),(right,ends[1][1],1)):
        b.box([edge+sign*.065,(start+stop)/2,entry['height']/2],[.13,stop-start,entry['height']],courtyard.C,label='362 exhibition section | jamb lining')

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true')
    a=p.parse_args();b=Builder(PALETTE);add_building(b,a.lod);a.output.parent.mkdir(parents=True,exist_ok=True)
    report=b.save(a.output,META);print({k:report[k]for k in ('parts','triangles','bytes','sha256')})
if __name__=='__main__':main()
