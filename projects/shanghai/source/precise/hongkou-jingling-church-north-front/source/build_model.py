"""Build the documented 2025 Kunshan Road gable and restored leaded window."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from north_front import PALETTE,add_north_front
ID='hongkou-jingling-church-north-front'
SCOPE='昆山路135号景灵堂北面三座连山墙、2025年验收的通高铅条玻璃花窗、十二瓣玫瑰与两侧圆花、三叶拱饰和门廊台阶。'
META=dict(id=ID,name='景灵堂昆山路北门山墙与修复花窗',scope=SCOPE,model_scope_zh=SCOPE,
          viewer_page='jingling-church-north-front.html',status='documented-post-2025-north-front',
          estimated='主窗高10.56米、宽5.44米据修缮记录，其他构件由验收照、旧照与建筑足迹按比例估算；彩绘玻璃以原创几何表现色块和铅条。',
          interiors_modeled=False,source_register=f'source/precise/{ID}/reference-review.json',
          coordinate_convention='GLB +Z faces the street, +X runs westward from the middle of the north front, +Y is up.',
          copyright='Original model MIT. Source photographs and historic drawings retain their respective rights.')
if __name__=='__main__':build(SOURCE,META,PALETTE,add_north_front)
