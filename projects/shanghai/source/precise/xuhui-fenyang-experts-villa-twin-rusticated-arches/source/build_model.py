"""Rebuild the paired garden-side masonry arches of the former consular residence."""
from pathlib import Path
import os, sys
SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT', SOURCE.parents[3])) / 'tools'))
from package_architectural_model import build
from veranda import PALETTE, build_veranda
ID = 'xuhui-fenyang-experts-villa-twin-rusticated-arches'
SCOPE = '花园侧底层廊角连续两券和共墩，包括凿面灰石端块、三块冠石、起拱层与顶部水平檐线。'
META = dict(id=ID, name='上海音乐学院专家楼底层双券与毛石拱饰',
            viewer_page='fenyang-experts-villa-twin-arches.html',
            scope=SCOPE, model_scope_zh=SCOPE,
            source_register='source/precise/' + ID + '/reference-review.json',
            interiors_modeled=False, status='Measured photographic proportions; garden-side masonry only',
            estimated='每券净跨取约2.32米为比例尺。原照无尺寸标记，厚度与墙脚标高为制作估计。',
            coordinate_convention='X follows the garden wall to the right in the front photograph, Y goes inside, Z points up.',
            copyright='Original model of the masonry. Documentary photographs are credited separately.')
if __name__ == '__main__':
    wrapper = SOURCE/'native_blender.py'
    if '--blender' in sys.argv:
        argument = sys.argv.index('--blender') + 1
        os.environ['FENYANG_BLENDER'] = sys.argv[argument]
        sys.argv[argument] = str(wrapper)
    else:
        sys.argv.extend(['--blender', str(wrapper)])
    build(SOURCE, META, PALETTE, build_veranda)
