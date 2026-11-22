"""Build the photographed 1932 museum façade on Huqiu Road."""
import argparse
import json
import os
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from huqiu import PALETTE,add_huqiu
ID='huangpu-royal-asiatic-society-huqiu-front'
SCOPE='虎丘路20号历史西门的三道石券、两扇八卦窗、石栏阳台、四字横额、竖窗带与阶梯女儿墙。'
META=dict(id=ID,name='原亚洲文会博物院虎丘路立面',viewer_page='royal-asiatic-society.html',scope=SCOPE,model_scope_zh=SCOPE,
    source_register='source/precise/'+ID+'/reference-review.json',
    status='Historic west front shown in the museum’s 2010 photograph, checked against 2007, 2011, 2013 and 2015 views.',
    estimated='临街立面的宽度按冻结地块量得约12.28米。高度、凹进、石栏挑距和构件厚度按原片透视估计。2010年实照作为主体形制。',
    interiors_modeled=False,coordinate_convention='Local X south along Huqiu Road, Y east into the historic building, Z up. glTF +Z faces the viewer.',
    copyright='Original mesh and code MIT. No source photography redistributed as textures.')
if __name__=='__main__':
    options=argparse.ArgumentParser(add_help=False)
    options.add_argument('--blender',default='blender')
    args,remaining=options.parse_known_args()
    os.environ['HUQIU_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,add_huqiu)
    audit_path=Path(remaining[remaining.index('--audit')+1])/'geometry-native.json'
    report=json.loads(audit_path.read_bytes())
    report['render']='Cycles, 12 samples, from reopened blend. OIDN RT sRGB postfilter.'
    audit_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
