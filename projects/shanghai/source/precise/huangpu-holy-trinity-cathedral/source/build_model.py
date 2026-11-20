"""Produce the independent Holy Trinity Cathedral main church."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from cathedral import PALETTE,add_cathedral

ID='huangpu-holy-trinity-cathedral'
SCOPE='临江西中路花园的主堂、东入口门廊、两侧柱廊、横翼与西端圣所外部。独立钟塔、学校办公楼和室内另列。'
META={'id':ID,'name':'圣三一基督教堂（主堂与花园门廊）','status':'original-photo-informed-exterior',
      'scope':SCOPE,'model_scope_zh':SCOPE,'viewer_page':'holy-trinity-cathedral.html',
      'estimated':'层高、屋面、走廊深度、窗格、石材、后端与遮挡部分按比照估计。',
      'coordinate_convention':'GLB +X toward NNW, +Y up, +Z toward the garden on Jiangxi Road.',
      'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
      'copyright':'Original geometry MIT. No photographs, scans or third-party models embedded.'}

if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_cathedral)
