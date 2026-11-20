"""Build the south-facing arcade of the 1913/1923 teaching block at Guangming Middle School."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT / 'tools'))
from package_architectural_model import build
from school_geometry import PALETTE, make_school

ID = 'huangpu-sino-french-school-teaching-building'
SCOPE = '中法学堂和今光明中学操场北侧的三层教学楼。1913年先建西段，1923年向东扩建。三处南伸翼楼围合两处开敞廊前空间，西端面向西藏南路。'
META = dict(
    id=ID, name='光明中学教学楼（原中法学堂）', status='original-photo-informed-exterior',
    scope=SCOPE, model_scope_zh=SCOPE, viewer_page='sino-french-school.html',
    estimated='各层高度、开廊深度与栏杆细部按历史和近年照片估计。屋顶设备房按公开影像概括。教室内部未复原。',
    coordinate_convention='Local glTF +X points east-northeast along the court. +Y is up. +Z faces the playing court.',
    source_register=f'source/precise/{ID}/reference-review.json', interiors_modeled=False,
    copyright='Original geometry MIT. Renamed school-plaque lettering subset SIL OFL 1.1. Source photographs remain external.',
)

if __name__ == '__main__':
    build(SOURCE, META, PALETTE, make_school)
