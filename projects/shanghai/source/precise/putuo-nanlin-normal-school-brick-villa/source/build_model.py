"""Rebuild the four wings of the relocated Nanlin school around its open courtyard."""
import argparse
from pathlib import Path
from fabric import NanlinBuilder, PALETTE as FINISHES
from window_wall import PALETTE as WINDOW, add_window_wall

ID='putuo-nanlin-normal-school-brick-villa'
META=dict(id=ID,name='原南林师范学校旧址（陈楚湘住宅旧址）',address='上海市普陀区凯旋北路1555弄',
          viewer_page='nanlin-normal-school-brick-villa.html',heritage_group='5N001',
          period='迁后修复外观，排窗以2016年照片、四翼与天井以2021年正射影像核对。',
          scope='临河排窗、两端山花、挑台和南侧七开间双层券廊，附四翼红瓦、中央天井及实照可见的西南转角。',
          dimensions='外檐约29.5×22.3米，2021年航片可见的天井约8.3×8.6米，南廊层高约4.45米。高度、隐藏窗台与遮挡处进深均为估计。',
          photo_author='Fayhoo（2016）；南林师范学校图册，券廊拍摄者及日期未载。',
          photo_source='https://commons.wikimedia.org/wiki/File:Nanlinshifanxuexiao_Jiuzhi.JPG',
          url='https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
          source='https://shanghai.xinmin.cn/xmsq/2013/10/15/22292562.html',
          photos_embedded=False,third_party_models_embedded=False,geometry_license='MIT, original reconstruction',
          texture_license='MIT, original procedural grey brick, red brick and clay tile',
          license_url='https://opensource.org/license/mit',
          copyright='Original reconstructed geometry and procedural materials, MIT. Reference photographs retain their respective licences.')


def build(lod=False):
    from nanlin_ornaments import PALETTE as ORNAMENT, add_ornaments
    from fabric import metric, LAYOUT
    from nanlin_arcade import PALETTE as ARCADE, add_arcade
    from courtyard_roofs import PALETTE as ROOF, add_four_wings
    b=NanlinBuilder({**FINISHES,**WINDOW,**ORNAMENT,**ARCADE,**ROOF})
    add_window_wall(b,lod)
    add_ornaments(b,lod,metric)
    # Local x goes north along the river; y goes west. The cream stone
    # balustrades face the paved square to the south. Do not close their openings.
    end_south=metric(119,452)[0]
    width=LAYOUT['arcade_outer_width_m']
    span=width/(1.+.245/7.)
    inset=(width-span)/2
    add_arcade(b,lod,dict(arcade_length=span,arcade_storey=LAYOUT['arcade_storey_m'],arcade_depth=LAYOUT['arcade_recess_m']),
               point=lambda s,d,z:(end_south+d,width-inset-s,z))
    add_four_wings(b,lod)
    return b


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path);parser.add_argument('--lod',action='store_true')
    args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    b=build(args.lod);info=b.save(args.output,META)
    print(info['triangles'],len(b.parts),info['sha256'])
