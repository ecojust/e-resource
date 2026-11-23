"""Build the central inscribed balcony at Lane 553, Middle Fuxing Road."""
from argparse import ArgumentParser
from pathlib import Path
import json, os, sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from balcony import PALETTE,add_balcony
ID='huangpu-fuxing-fang-553-inscribed-balcony'
SCOPE='复兴中路553弄跨弄过街楼二层中央题名阳台：三折面灰色石框和红色「復興坊」题名、出挑板与可见底托、后方中央成对木百叶及两旁窄砖垛；东西两排楼、店面、门柱、三楼、连续遮篷及院内1至21号另列。'
META=dict(id=ID,name='辣斐坊复兴中路553弄过街楼题名阳台',viewer_page='fuxing-fang-553-inscribed-balcony.html',status='photo-informed-surveyed-inscribed-balcony',scope=SCOPE,model_scope_zh=SCOPE,source_register='source/precise/'+ID+'/reference-review.json',interiors_modeled=False,estimated='2021年1月7日三台街面相机交会，正面长1.69米；阳台正板底高约4.0米、压顶约5.0米；地理高程约±0.4米，端部挑宽与背面构造为照片估尺。',coordinate_convention='Metres. Local X follows the street from northeast to southwest. Y points south-southeast into the house. Z is height above the lane.',geometry_license='MIT AND CC-BY-SA-4.0',copyright='Architectural geometry under MIT. The three red painted-character meshes are perspective-corrected tracings of Fu-Xing Fang Shanghai.JPG, by Livelikerw, 27 January 2015, under CC BY-SA 4.0. Source https://commons.wikimedia.org/wiki/File:Fu-Xing_Fang_Shanghai.JPG. Licence https://creativecommons.org/licenses/by-sa/4.0/.')
if __name__=='__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    parser.add_argument('--out', type=Path, required=True)
    options, remaining = parser.parse_known_args()
    os.environ['FUXING_BALCONY_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--out', str(options.out), '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_balcony)
    # The shared exporter defaults to MIT for original building geometry.
    # Preserve the separately attributed licence on the three traced meshes.
    file = options.out/'manifest.json'
    manifest = json.loads(file.read_bytes())
    assert manifest['id'] == ID and manifest['copyright'] == META['copyright']
    manifest['geometry_license'] = META['geometry_license']
    pending = file.with_suffix('.tmp')
    pending.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    pending.replace(file)
