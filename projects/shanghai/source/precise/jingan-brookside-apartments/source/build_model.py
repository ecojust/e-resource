"""Export the protected apartment block in the garden of 731 Huashan Road."""
import argparse
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from brookside_geometry import PALETTE, add_building

ID = 'jingan-brookside-apartments'
SCOPE = '依据2019年无人机航拍和2023年花园正照，重建华山路731号公寓七层折翼、中央屋顶透空券列、两侧凸窗与南入口。华山路沿街细部参考2020和2021实景；树后窗列、屋顶隐蔽构件和层高分配为估算。两座独立院门和地下室另计。'
META = {'id': ID, 'name': '枕流公寓', 'viewer_page': 'brookside-apartments.html',
        'status': 'original-photo-informed-exterior', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False,
        'coordinate_convention': 'Metres, Z up. Local X follows the middle garden facade east-northeast; negative local Y faces the southern garden.',
        'copyright': 'Original architectural geometry, MIT. External photographs and plans are reference material; no third-party image is embedded.'}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['BROOKSIDE_APARTMENTS_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
