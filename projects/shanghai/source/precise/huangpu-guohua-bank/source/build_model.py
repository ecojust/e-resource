"""Build the restored southeast entrance and Art Deco tower of the former China State Bank."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from corner import PALETTE,add_corner
ID='huangpu-guohua-bank'
SCOPE='北京东路342号东南临街转角，包括中央三列窗塔段、两侧各三列的弧形窗墙、花岗石拱券、扇形铁格、恢复后的國華大樓门额及入口石阶。'
META=dict(id=ID,name='国华银行大楼（东南转角与弧形窗墙）',viewer_page='guohua-bank.html',status='original-exterior-informed-by-historical-drawing-and-restoration-photographs',scope=SCOPE,model_scope_zh=SCOPE,
 estimated='沿地图两处外侧凸点的弦长约9.14米。入口约两层高、全楼约50米的文献尺与历史图、2014年及2023年外景约束各段；逐窗及曲率为估计。',coordinate_convention='GLB +Z faces the street corner; +X along the diagonal frontage northeast; +Y up.',interiors_modeled=False,source_register=f'source/precise/{ID}/reference-review.json',copyright='Original geometry MIT. No photo or scanned drawing textures embedded.')
if __name__=='__main__':build(SOURCE,META,PALETTE,add_corner)
