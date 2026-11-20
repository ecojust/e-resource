"""Build the two public street elevations of the Chekiang First Commercial Bank."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from frontage import PALETTE, add_frontage

ID = 'huangpu-chekiang-first-commercial-bank'
SCOPE = '江西中路西面七排水平窗、凹入式营业厅门、截角六排转折窗、汉口路北面的通高竖窗与办公门，以及低一段的临街窗墙。'
META = dict(id=ID, name='浙江第一商业银行大楼（江西中路与汉口路街面）',
            viewer_page='chekiang-first-bank.html',
            status='original-exterior-informed-by-archival-and-2019-photography',
            scope=SCOPE, model_scope_zh=SCOPE,
            estimated='街面三段按OSM定位，约44.04米、15.77米和21.06米。靠外侧主檐据2019年单幅照片近似35米，后段按同图折算。高度和窗格为估计。',
            coordinate_convention='GLB +Z looks out to the northwest street corner. The authoring survey tracks the western Jiangxi frontage, rotated 32 degrees when packaging. GLB +Y is up.',
            interiors_modeled=False, source_register=f'source/precise/{ID}/reference-review.json',
            copyright='Original geometry MIT. No photographic textures or scanned drawings embedded.')
if __name__ == '__main__':
    build(SOURCE, META, PALETTE, add_frontage)
