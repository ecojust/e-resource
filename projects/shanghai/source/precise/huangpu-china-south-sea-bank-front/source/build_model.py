from pathlib import Path
import sys
import os
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from hankou_front import PALETTE,facade
META = {'id': 'huangpu-china-south-sea-bank-front',
 'name': '中南银行大楼汉口路南立面中央柱列',
 'viewer_page': 'china-south-sea-bank-front.html',
 'status': 'original-photo-informed-exterior',
 'scope': '汉口路南面中央三开间，底层三门与四对塔司干柱，以及二至四层九窗与四根多立克巨柱。',
 'model_scope_zh': '二至四层早期巨柱列及1997年改成三开间的门廊，按2023年修缮项目近照制作。',
 'estimated': '依据地块南侧凹口宽度、历史图件及正面实照估计门柱半径、门深、层高和墙饰。',
 'source_register': 'source/precise/huangpu-china-south-sea-bank-front/reference-review.json',
 'interiors_modeled': False,
 'coordinate_convention': 'Local X along Hankou Road eastward, positive Y into the southern wall, Z '
                          'upward in metres.',
 'copyright': 'Original geometry; the modern inscription uses an OFL font subset.'}

if __name__ == '__main__':
    if '--blender' in sys.argv:
        index=sys.argv.index('--blender')+1
        os.environ['HANKOU_BANK_BLENDER']=sys.argv[index]
        sys.argv[index]=str(HERE/'blender_bank.py')
    else:
        sys.argv.extend(['--blender',str(HERE/'blender_bank.py')])
    build(HERE,META,PALETTE,facade)
