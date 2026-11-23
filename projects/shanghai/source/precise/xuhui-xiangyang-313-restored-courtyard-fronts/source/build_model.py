"""Build the observed courtyard fronts of No. 313, South Xiangyang Road, after repair."""
import argparse
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path[:0]=[str(HERE),str(HERE.parent/'measurements'),
               str(PROJECT/'source/precise/hongkou-general-post-office/source/common'),
               str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source')]
from photo_architecture import Builder
import foreground_bay
ID='xuhui-xiangyang-313-restored-courtyard-fronts'
SLUG='xiangyang-313-restored-courtyard-fronts'
PALETTE=foreground_bay.PALETTE
META={'id':ID,'name':'襄阳南路313号修缮后住宅院面','address':'上海市徐汇区襄阳南路313号',
      'heritage_id':'sh-historic-b5-xh-j-103-v','heritage_group':'5D103',
      'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
      'photo_source':'http://www.shwfjz.com/showcase/3/',
      'photo_author':'上海维方建筑装饰工程有限公司，案例3修缮后实景。原照权利归原作者。',
      'photos_embedded':False,'geometry_license':'MIT','viewer_page':SLUG+'.html',
      'local_axes':'Contractor view 1. X increases towards photographic right, Y enters the projecting wall, Z rises from the working ground level.',
      'scope':'凸墙四扇二十格大窗、退进下层百叶与上层开扇可见段。'}
def add_building(builder,lod=False):
    foreground_bay.add_foreground_bay(builder,lod)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true')
    a=p.parse_args();b=Builder(PALETTE);add_building(b,a.lod)
    print(b.save(a.output,META)['sha256'])
