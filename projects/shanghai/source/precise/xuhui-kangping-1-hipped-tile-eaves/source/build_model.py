"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from hip_tiles import PALETTE,add_building
META={'id': 'xuhui-kangping-1-hipped-tile-eaves', 'name': '康平路1号花园住宅街角红瓦檐', 'viewer_page': 'kangping-1-hipped-tile-eaves.html', 'status': 'photo-informed-architectural-component', 'scope': '2013年临高安路与康平路街角的底层两面转折瓦檐，保留开口筒瓦、凹面底瓦、成排檐端、搭接的圆弧斜脊、深色檐沟及檐下局部砂浆墙。', 'model_scope_zh': '2013年临高安路与康平路街角的底层两面转折瓦檐，保留开口筒瓦、凹面底瓦、成排檐端、搭接的圆弧斜脊、深色檐沟及檐下局部砂浆墙。', 'interiors_modeled': False, 'source_register': 'source/precise/xuhui-kangping-1-hipped-tile-eaves/reference-review.json', 'estimated': '在街角低屋檐的放大片中，斜脊有圆筒形端口，檐线两侧重复的筒瓦之间有凹槽。原照有透视且局部落叶遮挡。选择转角两侧各16条瓦垄，按0.192米估算中心距，得到各3.072米的展示段。屋面坡度、进深、瓦片搭接及墙面厚度均为比例复原估值。', 'coordinate_convention': 'Local x and y run along the two eaves, meeting at the outer corner. Z is vertical.', 'copyright': 'Original geometry and materials under MIT. Photograph credited to Livelikerw, CC BY-SA 4.0.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
