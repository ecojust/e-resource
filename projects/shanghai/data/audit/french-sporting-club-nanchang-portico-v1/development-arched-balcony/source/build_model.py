"""Rebuild the measured street entrance of the French Sporting Club."""
from pathlib import Path
import sys
source = Path(__file__).resolve().parent
project = next(root for root in source.parents if (root / 'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(source))
sys.path.insert(0, str(project / 'tools'))
from package_architectural_model import build
from sports_club_portico import MATERIALS as PALETTE,add_building
ID='huangpu-french-sporting-club-nanchang-portico'
scope='依据有日期的南昌路实景和门侧市牌，制作法国体育总会门廊两根有槽圆柱、红筒瓦短棚、双开铁门、展馆题额和上层穿花栏板后的半圆券窗。'
META=dict(id=ID,name='法国体育总会南昌路门廊与券窗阳台',viewer_page='french-sporting-club-nanchang-portico.html',status='photo-informed-exterior-study',
          scope=scope,model_scope_zh=scope,reference_height_m=8.91,estimated='南昌路侧两柱的位置与尺度由2023年四个机位交会估计。柱头到旧墙的进深、檐口高度和花格孔径按公开实照校正。',
          source_register='source/precise/'+ID+'/reference-review.json',coordinate_convention='Metres. Positive X points southwest, positive Y into the house and Z upward. Zero is midway between street column axes.',
          interiors_modeled=False,copyright='Original geometry. No photographic imagery is included.')
if __name__=='__main__':
    build(source,META,PALETTE,add_building)
