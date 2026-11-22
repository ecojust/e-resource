"""Construct the photographed exterior of the former Postal Supply Department at Jiaozhou Road."""
import argparse
import os
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(SOURCE))
from repeat_materials import RepeatingBuilder
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
import west_masonry as walls
import postal_window_sashes as glazing
import south_bay_frieze as frieze
import main_porch as porch

META=dict(id='jingan-postal-supply-office-jiaozhou-road',name='交通部邮政总局驻沪办事处胶州路西立面与南端檐窗',
    viewer_page='postal-supply-office-jiaozhou-road.html',heritage_group='5B057',
    scope='胶州路现322号院内临街楼的西立面、入口雨篷、南端三列檐窗及女儿墙。北侧上层和南端低层按可见范围截取。市名录胶州路320号未列各楼，历史地址与当前楼栋外观分别核对。',
    photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,
    texture_license=TEXTURE_LICENSE,photos_embedded=False,
    historical_source='https://archive.org/details/1941-shanghai-desk-hong-list-july-edition/page/n253/mode/1up',
    attribution='上海第五批优秀历史建筑5B057，交通部邮政总局驻沪办事处；1941、1942年名录列驻沪供应处322号，2015至2021年分期街景用于建筑形体与窗侧实读。',
    copyright='Original geometry, schematic drawings and procedural material textures, MIT. Reference photographs are not embedded.')
PALETTE={**walls.PALETTE,**glazing.PALETTE,**frieze.PALETTE,**porch.PALETTE}
def add_sash(builder,lod,op,end=False):
    idx=len(builder.parts)
    options={k:op[k]for k in ('upper_rows','lower_rows')if k in op}
    finish='sky'if op['storey']==4 else 'shaded' if op['storey']==1 else 'grey'
    glazing.add_window(builder,lod,('South end 'if end else'West ')+op['id'],op['x0'],op['x1'],op['z0'],op['z1'],op['glass_y'],family=op['family'],glass_finish=finish,**options)
    if end:
        for p in builder.parts[idx:]:
            p['vertices']=[(walls.SOUTH-depth,u,z)for u,depth,z in p['vertices']]
def add_building(builder,lod=False):
    walls.add_masonry(builder,lod)
    porch.add_main_porch(builder,lod)
    frieze.add_south_bay_frieze(builder,lod,head_z=4.144)
    for op in walls.OPENINGS:add_sash(builder,lod,op)
    for op in walls.LAYOUT['south_windows']:add_sash(builder,lod,op,True)
def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender');args,extra=parser.parse_known_args()
    if args.output:
        if extra:parser.error('Unknown model arguments: '+' '.join(extra))
        b=RepeatingBuilder(PALETTE);add_building(b,args.lod);b.save(args.output,META);return
    if args.lod:parser.error('--lod requires --output')
    from asset_rights import retain_metadata,licensed_writer
    os.environ['POSTAL_SUPPLY_BLENDER']=args.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'build_blender_source.py')]
    pack.Builder=RepeatingBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
    pack.build(SOURCE,META,PALETTE,add_building)
if __name__=='__main__':main()
