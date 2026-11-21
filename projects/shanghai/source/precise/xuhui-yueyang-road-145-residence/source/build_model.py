"""Build the original garden facade and mansard roof of the documented 145 residence."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from residence import PALETTE,add_residence

ID='xuhui-yueyang-road-145-residence'
SCOPE='岳阳路145号主宅的花园南立面、连续露台、首层玻璃窗墙、双前凸山墙、中央老虎窗与主楼折檐红瓦屋顶。北侧附楼和东邻永嘉路501号圆塔住宅各自保留。'
META=dict(id=ID,name='岳阳路145号花园住宅南立面与折檐红瓦屋顶',viewer_page='yueyang-road-145-residence.html',
          scope=SCOPE,model_scope_zh=SCOPE,status='documented-garden-facade-and-roof',
          estimated='尺度综合1948年行号图、冻结地块、航片与公开照片估算，隐蔽侧后墙采用简化体量。模型表现2021、2023年刊载照片中的可见外观。',
          coordinate_convention='Local +X runs eastward along the garden facade, local +Y points northwards into the house, and Z is up. In glTF +Z faces the garden and +Y is up.',
          interiors_modeled=False,source_register=f'source/precise/{ID}/reference-review.json',
          copyright='Original building geometry MIT. Photographs remain with their authors and are not embedded.')
if __name__=='__main__':build(SOURCE,META,PALETTE,add_residence)
