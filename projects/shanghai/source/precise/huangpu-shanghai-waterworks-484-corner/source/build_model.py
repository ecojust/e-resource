"""Export the photographed southwest cut corner of the Shanghai Waterworks Company."""
from argparse import ArgumentParser
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from waterworks_corner import PALETTE, add_building

ID = 'huangpu-shanghai-waterworks-484-corner'
SCOPE = '江西中路484号与香港路相接处的斜角上段。依据2019年俯拍校对赤色坡檐与檐口，结合两组街照刻画矩窗下的束带花环和凸框素板。切角宽度来自底图，层高、浮雕深度与色彩据照片估算。两街长翼、底层和屋顶加建保留原城。'
META = {'id': ID, 'name': '英商自来水公司大楼（自来大楼）西南转角花饰', 'viewer_page': 'shanghai-waterworks-484-corner.html',
        'status': 'photo-informed-public-street-elevation', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False, 'coordinate_convention': 'Metres, Z up. The corner street elevation faces local negative Y. X runs from the Jiangxi Middle Road end to the Hongkong Road end. The ground floor lies below the model.',
        'copyright': 'Original geometry under MIT. Source photographs remain with their credited photographers.'}
if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['WATERWORKS_CORNER_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
