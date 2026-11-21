"""Package the measured western street entrance of the Sun Garden residence."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
search=[*source.parents]
if os.environ.get('SHANGHAI_MODEL_PROJECT'):search.append(Path(os.environ['SHANGHAI_MODEL_PROJECT']))
project=next((p for p in search if (p/'tools/package_architectural_model.py').is_file()),None)
if project is None:raise RuntimeError('Set SHANGHAI_MODEL_PROJECT to the Shanghai project directory.')
sys.path.insert(0,str(project/'tools'))
from package_architectural_model import build
from sun_garden_gate import add_building,PALETTE,TOP
ID='xuhui-sun-garden-huashan-arched-gate'
SCOPE='华山路831号临街西院门、宽券与券腹、两侧六边形交叉铁花小窗、竹叶纹墙面、筒瓦门帽和831号门牌。'
META=dict(id=ID,name='华山路831号孙氏花园住宅筒瓦拱门',viewer_page='sun-garden-huashan-arched-gate.html',model_scope_zh=SCOPE,scope=SCOPE,status='photo-informed-exterior-study',reference_height_m=TOP,estimated='2015年12月实拍两站相距16.89米；门洞净宽约4.11米，券顶距地约3.13米，两侧实测洞深约1.41至1.54米。竹叶纹、瓦片间隔及侧墙截段为照片复原。',source_register='source/precise/'+ID+'/reference-review.json',coordinate_convention='Metres. The street normal points west-northwest. X goes to the right when viewed from Huashan Road, Y towards the courtyard, Z up. Origin at the midpoint between the street-side jambs.',interiors_modeled=False,copyright='Original model and procedural bamboo-patterned texture. Photographs consulted for dimensions and shape.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
