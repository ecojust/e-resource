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
from gate_panels import ID, PALETTE, add_building, texture

scope='市表5W039登记为吴氏民居。Fayhoo于2019年8月18日拍摄的同址街照题为“凌梦周宅 大洪村吴家宅19号”。本件取正门的白色门额，三块下部灰饰排成一列，上方另有一道长灰饰，最下为两端收折的石梁。'
META=dict(id=ID,name='大洪村吴家宅19号正门的四块灰饰与层叠门额',scope=scope,model_scope_zh=scope,viewer_page='wujiazhai-no19-four-gate-panels.html',reference_height_m=2.33,all_dimensions_estimated=True,estimated='名录与照片均写大洪村吴家宅19号，名称随各自来源记载。现有资料不足以说明吴氏与凌梦周的权属或居住关系。远照可辨灰饰数量、宽窄和边框，中心纹样仅表现灰面；不猜题字、图案和具体石种。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
