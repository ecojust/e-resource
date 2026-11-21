"""Package the garden entrance, gables and south return of Wangdetang."""
import argparse
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from frontage import PALETTE, frontage

ID = 'jingan-wangdetang-augustinian-office'
SCOPE = ('北京西路1220弄2号望德堂院内入口立面与南侧临街转角，按2016年公开实照及2017年照片制作门廊、石阶、'
         '曲线山墙、圆窗、铁栏和拱窗。既有民居后部、办事处其余房屋、内部祈祷室和院墙另列。')
META = dict(id=ID, name='望德堂院内门廊与曲线山墙', status='original-photo-informed-partial-exterior',
            viewer_page='wangdetang.html', scope=SCOPE, model_scope_zh=SCOPE,
            interiors_modeled=False, source_register=f'source/precise/{ID}/reference-review.json',
            estimated='根据786号冻结轮廓校准西侧12.55米短面。墙体厚度、山墙转折、窗高和檐部进深由照片估算。',
            coordinate_convention='Local +X follows the western entrance wall toward SSE; +Y enters the building toward ENE; +Z is up.',
            copyright='Original MIT geometric work and procedural materials. Photos and maps are cited by URL.')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['WANGDETANG_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,frontage)
