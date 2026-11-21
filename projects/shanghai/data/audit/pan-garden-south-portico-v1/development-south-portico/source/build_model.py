"""Rebuild the documented south entrance front of Pan Garden Residence."""
from pathlib import Path
import sys
source = Path(__file__).resolve().parent
project = next(root for root in source.parents if (root / 'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(source))
sys.path.insert(0, str(project / 'tools'))
from package_architectural_model import build
from south_portico import MATERIALS, add_building
PALETTE = MATERIALS
ID = 'jingan-pan-garden-south-portico'
scope = '依据2008年、2014年署名外景与2013年刊载的南院立面、弧阶近照，制作南楼双柱门廊、二层石栏、倒角凸窗、退层檐口和弧形台阶。'
META = dict(id=ID, name='潘氏花园住宅南楼柱廊立面',viewer_page='pan-garden-south-portico.html',
            status='photo-informed-exterior-study',scope=scope,model_scope_zh=scope,reference_height_m=11.8,
            estimated='南面21.9米、整座主楼檐高11.8米见2013年建筑记述。窗轴、柱径与台阶进深按照片比例估算。模型截于前檐后的第一段屋坡。',
            source_register='source/precise/'+ID+'/reference-review.json',coordinate_convention='Metres. X increases to the right of the south courtyard front, Y toward the retained house, Z up.',
            interiors_modeled=False,copyright='Original geometry. No photographic pixels embedded.')
if __name__=='__main__':
    build(source,META,PALETTE,add_building)
