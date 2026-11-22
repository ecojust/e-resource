"""Build the surviving 1914 service block of Shanghai General Hospital (municipal listing 5F030)."""
import argparse
import json
import os
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(SOURCE))
from hospital_builder import HospitalBuilder
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
import hospital_walls,hospital_court,hospital_roof,hospital_sashes,hospital_tablet

ID='hongkou-general-hospital-1914-kitchen-block'
META=dict(id=ID,name='公济医院旧楼东部（1914年后勤楼）',viewer_page='general-hospital-1914-kitchen-block.html',
    heritage_group='5F030',address='上海市虹口区北苏州路190号，天潼路、乍浦路转角',
    scope='保留至今的五层红砖后勤楼，包含临街北立面、乍浦路东侧退进、朝院一面可见的窗列、悬挑阳台和屋顶轮廓。西端与后建酒店交接处作封边。',
    photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,
    texture_license=TEXTURE_LICENSE,photos_embedded=False,url=PHOTO_SOURCE,
    dimensions='街景交会估计北面两端相距44.62米，东部南侧外角约为(1.14,11.33)米，主檐顶约23.7米。绝对尺寸和被遮盖的西侧收口为建模估算。',
    attribution='上海市优秀历史建筑5F030；乔争月引用1914年12月的《北华捷报》（North-China Herald），戴邹君另摄庭院。',
    copyright='Original geometry and procedurally generated red brickwork under MIT. Reference photographs retain their original rights and are not embedded.')
PALETTE={**hospital_roof.PALETTE,**hospital_tablet.PALETTE,**hospital_sashes.PALETTE,**hospital_walls.PALETTE}

def layout():
    report=json.loads((SOURCE/'sash-layout.json').read_bytes())
    return dict(width=44.62,depth=11.33,eaves=23.69,short_return_x=1.14,short_return_depth=4.95,
                faces=report['faces'],ground=json.loads((SOURCE/'ground-layout.json').read_bytes()))

def add_building(b,lod=False):
    data=layout()
    hospital_walls.add_walls(b,data,lod)
    for face in ('north','court'):
        hospital_sashes.add_panel_links(b,face,data['faces'][face],data,lod=lod)
    hospital_court.add_balcony(b,lod=lod,layout=data)
    hospital_tablet.add_tablet(b,lod=lod,layout=data)
    hospital_roof.add_roof(b,lod=lod,layout=data)

def main():
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    options,extra=parser.parse_known_args()
    if options.output:
        if extra:parser.error('Unexpected model options '+str(extra))
        model=HospitalBuilder(PALETTE);add_building(model,options.lod);model.save(options.output,META)
        return
    if options.lod:parser.error('--lod needs --output')
    from asset_rights import retain_metadata,licensed_writer
    os.environ['GONGJI_1914_BLENDER']=options.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'build_blender_source.py')]
    pack.Builder=HospitalBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
    pack.build(SOURCE,META,PALETTE,add_building)

if __name__=='__main__':main()
