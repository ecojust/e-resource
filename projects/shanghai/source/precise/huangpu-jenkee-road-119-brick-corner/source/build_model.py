"""Build the three upper corner windows recorded in the 2014 Jenkee Road street photograph."""
import os
from pathlib import Path
import sys
source = Path(__file__).resolve().parent
roots = list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):
    roots.insert(0, Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools = next(parent/'tools' for parent in roots if (parent/'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(tools))
from package_architectural_model import build
from corner import ID, PALETTE, add_building, texture

scope = '2014年Fayhoo署名照片所示四川中路与滇池路口红砖切角，三层窗洞、石砌腰线与临街窗篷。'
META = dict(id=ID, name='仁记路119号大楼红砖切角窗间',scope=scope, model_scope_zh=scope,
            viewer_page='jenkee-road-119-brick-corner.html',reference_height_m=8.69,all_dimensions_estimated=True,
            estimated='市名录以仁记路119号大楼登记，照片所题上海工业银行大楼为街角同址。进深和尺寸按照片估算。')
if __name__ == '__main__':
    texture()
    build(source,META,PALETTE,add_building)
