"""Build the bounded street block of the former Kincheng Banking Corporation."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from kincheng import PALETTE, add_bank

ID='huangpu-kincheng-bank'
SCOPE='江西中路200号金城银行历史大楼西侧街面与对应临街体量；后部产权、屋面设备、隐面开窗及室内另待核。'
meta={'id':ID,'name':'金城银行大楼（江西中路200号临街主楼）','status':'original-photo-informed-exterior',
      'viewer_page':'kincheng-bank.html','scope':SCOPE,'model_scope_zh':SCOPE,
      'estimated':'花岗石色调、窗格、徽章轮廓、两级顶部、层高及隐藏端墙为照片引导估计。',
      'coordinate_convention':'Local GLB +X south along street, +Y up, +Z outward toward Middle Jiangxi Road.',
      'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json',
      'copyright':'Original geometry MIT; signage uses a SIL OFL 1.1 subset; no photographs embedded.'}

if __name__=='__main__':
    build(SOURCE,meta,PALETTE,add_bank)
