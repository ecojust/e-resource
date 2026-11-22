"""Rebuild the surviving four-storey Changzhi Road and Nanxun Road corner residence."""
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
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from changzhi_builder import StreetBuilder as CrownBuilder
sys.path.insert(0,str(SOURCE))
import changzhi_walls,changzhi_sashes,changzhi_entrances,changzhi_roof_crown,changzhi_roofs
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
ID='hongkou-st-lukes-hospital-changzhi-nanxun-corner'
META=dict(id=ID,name='同仁医院旧址长治路、南浔路转角住宅',viewer_page='st-lukes-hospital-changzhi-nanxun-corner.html',
          heritage_group='5F034 / HK-J-034-V',address='上海市虹口区长治路155至159号（单号）、南浔路193号',
          scope='四层转角住宅的两条街面、三折角、临街拱口、南浔路五段封合浅凹、山花圆眼及窄窗塔。红瓦斜屋面采用三期航片复核的平面边界与脊线。后墙、屋脊高度和凹面深度保留估计。',
          dimensions='街景多站与原始底图给出两条街边的方向与大致长度。窗、山花和塔按具名原照反算。未作实地测绘。',
          photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,
          texture_license=TEXTURE_LICENSE,photos_embedded=False,url=PHOTO_SOURCE,
          attribution='上海市房屋管理局5F034。同仁医院旧址，登记年代为1920年代。Fayhoo 2016、老房子爱好者2021刊、上海虹口2023年照片仅供形制核对。',
          copyright='Original architectural detail and procedural mineral render under MIT. Documentary images are cited and are not embedded. See SOURCES-LICENSE.md for underlying footprint attribution.')
PALETTE={**changzhi_roofs.PALETTE,**changzhi_walls.PALETTE,**changzhi_sashes.PALETTE,**changzhi_entrances.PALETTE,**changzhi_roof_crown.PALETTE}
def layout():
    return json.loads((SOURCE/'street-layout.json').read_bytes())

def add_building(b,lod=False):
    data=layout()
    changzhi_walls.add_walls(b,lod,data)
    changzhi_sashes.add_sashes(b,lod,data)
    changzhi_entrances.add_entrances(b,lod,data)
    changzhi_roofs.add_roof(b,lod,data)
    changzhi_roof_crown.add_crown(b,lod,data)
    # Blender stores 63 UTF-8 bytes per editable object name. Keep the unique
    # face and window identifiers while removing the repeated building name.
    for part in b.parts:
        part['label']=part['label'].replace('St Luke windows / ','Window ').replace('Changzhi entrances / ','Entry | ')

def main():
    args=argparse.ArgumentParser(add_help=False)
    args.add_argument('--output',type=Path)
    args.add_argument('--lod',action='store_true')
    args.add_argument('--blender',default='blender')
    opt,extra=args.parse_known_args()
    if opt.output:
        if extra:args.error('Unexpected arguments '+str(extra))
        b=CrownBuilder(PALETTE)
        add_building(b,opt.lod)
        b.save(opt.output,META)
        return
    if opt.lod:args.error('--lod requires --output')
    from asset_rights import retain_metadata,licensed_writer
    os.environ['ST_LUKES_CORNER_BLENDER']=opt.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'build_blender_source.py')]
    pack.Builder=CrownBuilder
    pack.retain_metadata=retain_metadata
    pack.write_json=licensed_writer(pack.write_json,META)
    pack.build(SOURCE,META,PALETTE,add_building)

if __name__=='__main__':main()
