"""Build the central fanlight and garden stair of Sande Hall."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from garden_stair import PALETTE,add_building
META={'id': 'xuhui-jewish-hospital-garden-stair', 'name': '原犹太医院三德堂南花园石阶与半圆窗', 'viewer_page': 'jewish-hospital-garden-stair.html', 'model_scope_zh': '三德堂南花园中央石阶、左右两组折返梯、平台石栏和半层钢扇窗。', 'historical_context': '1942年三德堂，汾阳路83号10号楼。', 'copyright': 'Original garden-stair geometry, radial steelwork and material definitions: MIT. Reference photography and orthophotography remain with their authors.', 'coordinate_convention': 'Metres. X follows the long south wall from west to east. Y increases toward the building and Z points upward.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_building)
