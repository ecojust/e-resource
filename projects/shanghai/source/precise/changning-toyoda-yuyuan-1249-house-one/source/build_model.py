"""Model the two documented exterior elevations of the Toyota spinning mill's house No. 1."""
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
import house_one
import three_arches
ID='changning-toyoda-yuyuan-1249-house-one'
SLUG='toyoda-yuyuan-1249-house-one'
LAYOUT=json.loads((SOURCE/'house-layout.json').read_bytes())
PALETTE={**house_one.PALETTE,**three_arches.PALETTE}
META=dict(id=ID,name='丰田纱厂干部住宅（愚园路1249弄1号）',address='上海市长宁区愚园路1249弄1号',heritage_group='5M022',period='2018',viewer_page=SLUG+'.html',scope='两向实见院面、上层联券、侧面三小券与门廊及屋面。',dimensions='三小窗净宽按砖皮暂取0.66米，长墙尺度由转角照片推算。被遮挡面收口为近似。',photo_author='Antigng；高参88',photo_source='https://commons.wikimedia.org/wiki/File:愚园路1249弄1号住宅.jpg',url='https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',geometry_license='MIT',texture_license='MIT',license_url='https://opensource.org/license/mit',copyright='Original reconstructed geometry and procedural finishes: MIT. Source photographs remain with their creators.',photos_embedded=False,camera_views=json.loads((SOURCE/'cameras.json').read_bytes()))
def add_building(b,lod=False):
    house_one.add_building(b,lod,LAYOUT)
    three_arches.add_three_arches(b,lod,LAYOUT)
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true')
    a=p.parse_args();b=Builder(PALETTE);add_building(b,a.lod);a.output.parent.mkdir(parents=True,exist_ok=True)
    report=b.save(a.output,META);print({k:report[k]for k in ('parts','triangles','bytes','sha256')})
if __name__=='__main__':main()
