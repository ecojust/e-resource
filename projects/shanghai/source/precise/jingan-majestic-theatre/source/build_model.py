"""Build the Majestic Theatre's 2017 street exterior, including its rounded lobby."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from majestic_geometry import PALETTE, add_theatre

ID = 'jingan-majestic-theatre'
SCOPE = '以2017年修缮后日、夜照片为准的圆弧门厅、两条临街外墙及屋顶概略体量；窗格、饰带、招牌字形、色泽与高度均为近似。'
METADATA = {
    'id':ID,'name':'美琪大戏院（圆弧门厅、临街外墙与屋顶体量）',
    'status':'original-photo-informed-exterior','viewer_page':'majestic-theatre.html',
    'scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,
    'coordinate_convention':'Blender X east, Y north, Z up. GLB X east, Y up, Z south. Origin at registered footprint centroid.',
    'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json',
    'lettering':{'text':['MAJESTIC','美琪大戏院','MAJESTIC THEATRE'],'font':'Majestic Sign Subset Bold','font_license':'SIL OFL 1.1','traced':False},
    'copyright':'Original geometry MIT. Renamed sign font subset under SIL OFL 1.1. No photo pixels embedded.',
}

if __name__ == '__main__':
    build(SOURCE,METADATA,PALETTE,add_theatre)
