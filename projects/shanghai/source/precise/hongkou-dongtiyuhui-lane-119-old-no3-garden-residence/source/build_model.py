"""Build the garden residence identified by the Old No. 3 plate, municipal entry 5F026."""
import argparse
import json
import os
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:
    PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(SOURCE))
from old3_builder import Old3Builder
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
import old3_masonry,old3_windows,old3_balcony,old3_roof

ID='hongkou-dongtiyuhui-lane-119-old-no3-garden-residence'
META=dict(id=ID,name='东体育会路119弄老3号花园住宅',viewer_page='dongtiyuhui-lane-119-old-no3-garden-residence.html',
    heritage_group='5F026',address='上海市虹口区东体育会路119弄（老3号）',
    scope='老门牌所指花园住宅的庭院正面、巷侧、后转角、四坡红瓦屋顶与单座老虎窗。',
    photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,
    texture_license=TEXTURE_LICENSE,photos_embedded=False,url=PHOTO_SOURCE,
    dimensions='采用8.4米庭面宽为展示比例，双机联合23个庭面控制点、四个窗顶和窗台点及六道跨角实缝，进深约12.4米，估计余量约半米。绝对尺寸未经现场测量。',
    attribution='第五批优秀历史建筑5F026，高参88在2015年10月6日拍摄的四张建筑实照，以及2020年刘恩惠所摄老门牌、庭院和保护标牌。',
    copyright='Original geometry, grey render finish and clay tile texture under MIT. Photographs retain the rights of their authors and are not embedded.')
PALETTE={**old3_masonry.PALETTE,**old3_windows.PALETTE,**old3_balcony.PALETTE,**old3_roof.PALETTE}


def layout():
    front=json.loads((SOURCE/'front-layout.json').read_bytes())
    returns=json.loads((SOURCE/'return-layout.json').read_bytes())
    front.update(depth=returns['depth'],faces=returns['faces'],joint_courses=returns['joint_courses'])
    front['faces']['front']={k:front[k]for k in ['openings','columns']}
    front['faces']['east']={'openings':[],'columns':[]}
    return front


def add_building(builder,lod=False):
    measured=layout()
    for face in ['front','lane','rear','east']:
        old3_masonry.scored_face(builder,face,measured,measured['faces'][face],lod)
    old3_masonry.chimney(builder,measured,lod)
    old3_masonry.balcony_and_services(builder,measured,lod)
    old3_balcony.add_balcony_iron(builder,lod)
    old3_roof.add_roof(builder,lod=lod,layout=measured)


def main():
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender')
    args,extra=parser.parse_known_args()
    if args.output:
        if extra:parser.error('Unexpected model arguments '+str(extra))
        model=Old3Builder(PALETTE)
        add_building(model,args.lod)
        model.save(args.output,META)
        return
    if args.lod:parser.error('--lod needs --output')
    from asset_rights import retain_metadata,licensed_writer
    os.environ['OLD3_GARDEN_BLENDER']=args.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'build_blender_source.py')]
    pack.Builder=Old3Builder
    pack.retain_metadata=retain_metadata
    pack.write_json=licensed_writer(pack.write_json,META)
    pack.build(SOURCE,META,PALETTE,add_building)


if __name__=='__main__':
    main()
