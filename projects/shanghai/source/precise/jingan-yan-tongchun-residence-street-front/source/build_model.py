"""Build the documented street-facing bays of the eastern Yan family house."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from street_front import PALETTE, make_front

ID='jingan-yan-tongchun-residence-street-front'
SCOPE='816号东宅现沿街面三段门窗、浅砖柱、木扇与金属窗下墙，取自2022年7月街景。'
META=dict(id=ID,name='延安中路816号严同春宅东宅街面',status='original-photo-informed-exterior',
          scope=SCOPE,model_scope_zh=SCOPE,viewer_page='yan-tongchun-residence.html',
          estimated='严氏宅院由林瑞骥设计，1933年建；原沿街第一进于1998年拆除。现街面构件日期、部分受遮挡门扇及尺度待实测。',
          coordinate_convention='In the author frame +X follows the street frontage and +Y is inward. glTF +Y is up.',
          source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,
          copyright='Original MIT geometry. Sources are cited without embedding photography.')
if __name__=='__main__':build(SOURCE,META,PALETTE,make_front)
