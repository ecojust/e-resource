"""Build the Guiren Li street gateway at the northwest mouth of Kangding East Road Lane 3."""
import argparse
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()), None)
if PROJECT is None:
    PROJECT = Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(SOURCE))
from repeat_materials import RepeatingBuilder
import gable_relief
import lane_iron_gate
import gate_masonry
import guiren_window_sashes

META = dict(id='jingan-guiren-li-kangding-lane-gate', name='归仁里康定东路过街楼、镜心山花与相邻街窗',
    viewer_page='guiren-li-kangding-lane-gate.html', heritage_group='5B053',
    scope='康定东路3弄西北过街楼和两侧紧邻街面开间。街门、窗扇、镜心石饰、砖腰线和敞开穿堂前段按实照重建。其余弄内楼栋及过街楼后部未收录。',
    photo_author='高参88、YOCO、张渊源及百度地图分期公开街景。',
    photo_source='https://m.thepaper.cn/newsDetail_forward_14165880',
    license_url='https://opensource.org/license/mit', geometry_license='MIT',
    texture_license='MIT (original procedural brick, glazing and redrawn address plate)',
    photos_embedded=False,
    attribution='上海第五批优秀历史建筑5B053。高参88实拍2016-07-02、2015/2020/2021分期街面和YOCO弄额近照。三站独立定位与原图1797及康定东路走势交叉核验。',
    copyright='Original model, drawings and textures licensed under MIT. Reference photographs retain their own rights.')
PALETTE={**gate_masonry.PALETTE,**gable_relief.PALETTE,**guiren_window_sashes.PALETTE,**lane_iron_gate.PALETTE}

def add_building(builder,lod=False):
    gate_masonry.add_street_masonry(builder,lod)
    lane_iron_gate.add_lane_gate(builder,lod)
    gable_relief.add_gable_relief(builder,lod)
    guiren_window_sashes.add_windows(builder,lod)

def main():
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unrecognized mesh options')
        builder=RepeatingBuilder(PALETTE)
        add_building(builder,args.lod)
        builder.save(args.output,META)
        return
    if args.lod:parser.error('--lod requires --output')
    from asset_rights import licensed_writer,retain_metadata
    os.environ['GUIREN_GATE_BLENDER']=args.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
    pack.Builder=RepeatingBuilder
    pack.retain_metadata=retain_metadata
    pack.write_json=licensed_writer(pack.write_json,META)
    pack.build(SOURCE,META,PALETTE,add_building)

if __name__=='__main__':main()
