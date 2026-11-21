"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from curved_cornice import PALETTE,add_building
META={'id': 'hongkou-little-pearce-apartments-curved-cornice', 'name': '小浦西公寓塘沽路圆角檐带与齿饰', 'viewer_page': 'little-pearce-curved-cornice.html', 'status': 'photo-informed-architectural-component', 'scope': '塘沽路一侧圆角立面上，最高两层以下的外挑石色腰檐。选取中间一枚曲形承托、两边十枚方托和下一道小齿饰。', 'model_scope_zh': '塘沽路一侧圆角立面上，最高两层以下的外挑石色腰檐。选取中间一枚曲形承托、两边十枚方托和下一道小齿饰。', 'interiors_modeled': False, 'source_register': 'source/precise/hongkou-little-pearce-apartments-curved-cornice/reference-review.json', 'estimated': 'The photos constrain the ordering, relative size and spacing of courses. Radius, profile offsets and repeated dentil pitch have no survey measurement; count covers this cropped model section only.', 'coordinate_convention': 'Horizontal x, curved facade towards -y, vertical z. Zero marks the brick section below the string course.', 'copyright': 'Original model and materials under MIT.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
