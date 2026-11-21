"""Build the measured principal house and its attached northern wing at 315 Xinhua Road."""
import argparse
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from garden_house import PALETTE, house

ID = 'changning-xinhua-road-315-garden-house'
SCOPE = ('新华路315号花园住宅主屋及相连北翼。南面按2024年10月发布的花园实照，北面按两期庭院照片，'
         '平面和屋顶按两层公开平面图及航片配准。门房、院墙、花园其他建筑、室内及未经实测的隐蔽构造另列。')
META = dict(id=ID, name='新华路315号花园住宅', status='original-photo-informed-exterior',
            viewer_page='xinhua-road-315.html', scope=SCOPE, model_scope_zh=SCOPE,
            interiors_modeled=False, source_register=f'source/precise/{ID}/reference-review.json',
            estimated='建筑平面、街线和坡向有独立图像依据。跨度按冻结地块尺度校准，高度、各房间退进及材料色值按照片估计。',
            coordinate_convention='Local +X runs east-southeast along the garden facade, +Y enters the house toward Xinhua Road, and +Z is up.',
            copyright='Original model geometry and materials, MIT. External photographs and plans are referenced by source.')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['XINHUA315_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,house)
