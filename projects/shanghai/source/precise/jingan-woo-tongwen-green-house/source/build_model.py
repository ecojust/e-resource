"""Package the documented Tongren Road garden residence."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from residence import PALETTE,add_residence

ID='jingan-woo-tongwen-green-house'
SCOPE='铜仁路333号吴同文住宅主楼，含花园立面的三层圆端窗、错层露台、西南露天弧梯、底层车道及北侧楼梯窗。门房、院墙、车库与南侧独立楼栋另行保留。'
META=dict(id=ID,name='吴同文住宅（绿房子）',viewer_page='woo-green-house.html',scope=SCOPE,model_scope_zh=SCOPE,
          status='documented-garden-residence-exterior',estimated='据四层平面、修缮现场与园侧照片及两期航片拟合。尺寸非实测；屋顶附属、树后和服务区按可见轮廓简化。',
          coordinate_convention='Local X follows the garden towards the east drum at bearing 68.5 degrees. Y points into the house at 338.5 degrees, and Z is up. glTF +Z faces the garden.',
          model_period='2013年修缮后、2016年花园现场照所见外观',interiors_modeled=False,
          source_register=f'source/precise/{ID}/reference-review.json',
          copyright='Original model geometry MIT. Reference images remain with their respective owners and are not embedded.')
if __name__=='__main__':build(SOURCE,META,PALETTE,add_residence)
