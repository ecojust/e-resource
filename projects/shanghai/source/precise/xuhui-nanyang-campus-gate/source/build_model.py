"""Reconstruct the palace-style 1935 gate of Jiaotong University on Huashan Road."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from palace_gate import PALETTE, make_gate

ID='xuhui-nanyang-campus-gate'
SCOPE='华山路1954号徐汇校区的1935年老校门。正面朱墙、绿琉璃屋面、石狮、交通大学竖牌和校园侧窗列按2010至2021年影像，取中央门扇开启的实见状态。两侧围墙、桥头灯柱及校园其他单体另计。'
META=dict(id=ID,name='交通大学徐汇校区老校门（南洋公学旧址）',status='original-photo-informed-exterior',
          scope=SCOPE,model_scope_zh=SCOPE,viewer_page='nanyang-campus-gate.html',
          estimated='屋脊、飞檐、门洞和狮像的尺寸按照片估计，彩画、兽像及竖牌字形采用简化几何。',
          coordinate_convention='GLB +X points north along the Huashan Road facade, +Y is up and +Z faces out to the street.',
          source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,
          copyright='Original geometry MIT. Renamed Chinese lettering subset SIL OFL 1.1. Photographs documented separately.')
if __name__=='__main__':
    from final_preview import finish
    build(SOURCE,META,PALETTE,make_gate)
    finish()
