"""Generate the garden house at 1055 Yuyuan Road in local metres."""
import argparse
import json
import os
import sys
from pathlib import Path

SOURCE=Path(__file__).absolute().parent
roots=[SOURCE,*SOURCE.parents]
if os.getenv('E_RESOURCE_SHANGHAI'):
    roots.append(Path(os.environ['E_RESOURCE_SHANGHAI']))
PROJECT=next(root for root in roots if (root/'tools/package_architectural_model.py').is_file())
for relative in ['source/precise/hongkou-general-post-office/source/common','source/precise/hongkou-tanggu-road-apartment-dated-crown/source']:
    sys.path.insert(0,str(PROJECT/relative))
from crown_builder import CrownBuilder
from house_fabric import PALETTE as WALLS
from garden_shell import add_shell
import huang_roof

Builder=CrownBuilder
PALETTE={**WALLS,**huang_roof.PALETTE}
ID='changning-yuyuan-1055-huang-family-garden-residence'
SLUG='yuyuan-1055-huang-family-garden-residence'
LAYOUT=json.loads((SOURCE/'garden-layout.json').read_bytes())
META=dict(id=ID,name='愚园路1055号黄家花园住宅',address='上海市长宁区愚园路1055号',viewer_page=SLUG+'.html',heritage_group='5M014',period='2016',
    scope='花园宅东侧三折窗弧形阳台、方柱入口、南端花格女儿墙日光室及主屋。',dimensions='旧地籍图南边约13.5米。拟合主檐高7.45米。拟合值与初始地籍配准均有误差。',
    photo_author='高参88；黄氏家族相册；上海长宁',photo_source='https://blog.sina.com.cn/s/blog_5d1bdf480102zefw.html',
    url='https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',photos_embedded=False,
    attribution='按高参88院内实拍、门口照片、黄氏家族旧照及地籍示意图重建。历史资料与拍摄者详见独立页。',
    geometry_license='MIT',texture_license='MIT',license_url='https://opensource.org/license/mit',
    copyright='Original reconstructed geometry and two procedural finishes: MIT. Research photographs remain with their respective creators.',
    camera_views=json.loads((SOURCE/'cameras.json').read_bytes()))
def add_building(b,lod=False):
    add_shell(b,lod,LAYOUT)
    huang_roof.add_roof(b,lod,LAYOUT)
def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output',type=Path,required=True);cli.add_argument('--lod',action='store_true')
    args=cli.parse_args()
    b=Builder(PALETTE)
    add_building(b,args.lod)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    report=b.save(args.output,META)
    print({k:report[k] for k in ('triangles','parts','bytes','sha256')})
if __name__=='__main__':main()
