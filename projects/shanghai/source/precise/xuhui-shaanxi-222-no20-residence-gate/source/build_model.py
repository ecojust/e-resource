"""Build the double-leaf residence gate at 20, Lane 222 South Shaanxi Road."""
import argparse
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.append(str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
from residence_gate import PALETTE as ENTRY, add_entry
from gate_frieze import PALETTE as FRIEZE, add_frieze
from gate_hardware import PALETTE as HARDWARE, add_hardware
ID='xuhui-shaanxi-222-no20-residence-gate'
SLUG='shaanxi-222-no20-residence-gate'
PALETTE={**ENTRY,**FRIEZE,**HARDWARE}
META={'id':ID,'name':'陕西南路222弄20号住宅院门','address':'上海市徐汇区陕西南路222弄20号','heritage_group':'5D063',
      'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
      'photo_source':'https://blog.sina.com.cn/s/blog_5d1bdf480102whoy.html','photo_author':'高参88',
      'reference_publication_date':'2016-02-02','photos_embedded':False,'geometry_license':'MIT','texture_license':'MIT',
      'scope':'20号临弄院门，含灰色门柱、退进的连饰檐口、圆角门洞、兽面双环和号码牌。'}
def add_building(b,lod=False):
    add_entry(b,lod)
    add_frieze(b,lod)
    add_hardware(b,lod)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true')
    a=p.parse_args();b=Builder(PALETTE);add_building(b,a.lod);print(b.save(a.output,META)['sha256'])
