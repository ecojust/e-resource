"""Build the detached bell tower of Holy Trinity Cathedral."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT / 'tools'))
from package_architectural_model import build
sys.path.insert(0, str(PROJECT / 'source/precise/huangpu-holy-trinity-cathedral/source'))
from tower import PALETTE, add_tower

ID = 'huangpu-holy-trinity-bell-tower'
SCOPE = '主堂北侧的独立方塔、重建的尖顶及连接主堂北廊的短廊。'
META = dict(id=ID, name='圣三一基督教堂（独立钟塔与连接短廊）', status='original-photo-informed-exterior',
    scope=SCOPE, model_scope_zh=SCOPE, viewer_page='holy-trinity-bell-tower.html',
    estimated='塔尖沿用建筑名录公布的48米高度；塔基、各层标高、喇叭口和构件进深按照片估计。',
    coordinate_convention='Local glTF +X NNW, +Y up, +Z toward the garden on Jiangxi Road. Origin at bell tower base center.',
    source_register='source/precise/'+ID+'/reference-review.json',interiors_modeled=False,
    copyright='Original geometry MIT. No photographs, scans or third-party models embedded.')

if __name__ == '__main__':
    build(SOURCE, META, PALETTE, add_tower)
