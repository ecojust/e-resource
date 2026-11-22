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
from riverside_wall import ID, PALETTE, add_building, texture

scope='陈永年在《春节走进陈云故里练塘古镇》中点出前进街77号陆家米行的高围墙和石库门。紧随题注的沿河照片可读出白灰墙、偏右的矩形大门、门边较矮的横孔和左端较高的方孔。青浦区发改委2026年6月的修缮批复写明同一门牌，并列出各立面、院落格局、木质结构、门窗及走廊栏杆等修缮项目。本件仅取照片中白墙中段。'
META=dict(id=ID,name='练塘陆家米行旧址沿河院墙与石框门洞',scope=scope,model_scope_zh=scope,viewer_page='liantang-lu-rice-house-riverside-gate.html',reference_height_m=4.25,all_dimensions_estimated=True,estimated='署名图像为600×394，近树和垂枝挡住门头及中段上缘。仅取读得清的矩形灰框、凹口和墙顶暗压线，暗部深度依比例估计。河埠、相邻楼房、院内各间与墙上未能逐件辨清的构件保持在本次观察范围之外。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
