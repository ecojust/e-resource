"""Build the northeast plaza elevation and its short street returns."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from plaza import PALETTE, add_plaza

ID = 'huangpu-development-building'
SCOPE = '福州路与江西中路交会处西南角的内凹街面，包括中央黑花岗岩门、十六排三列高窗、较低侧塔、两端八排窗肩部及临街短返面。'
META = dict(id=ID, name='建设大楼（福州路口凹入塔面）', viewer_page='development-building.html',
            scope=SCOPE, model_scope_zh=SCOPE, status='original-exterior-informed-by-street-photography-and-conservation-report',
            estimated='地上总高67.97米据市住建委及市历保中心，地图弧边25.48米。各窗、退阶和门框按2013至2025摄影近似。',
            coordinate_convention='GLB +Z faces northeast across the intersection; +X northwest; +Y up.',
            interiors_modeled=False, source_register=f'source/precise/{ID}/reference-review.json',
            copyright='Original mesh MIT; no photographic textures or third-party meshes embedded.')
if __name__ == '__main__':
    build(SOURCE, META, PALETTE, add_plaza)
