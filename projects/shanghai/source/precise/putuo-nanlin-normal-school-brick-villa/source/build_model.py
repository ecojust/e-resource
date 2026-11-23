"""Build the photographically registered window wall of the Nanlin school."""
import argparse
from pathlib import Path
from fabric import NanlinBuilder, PALETTE as FINISHES
from window_wall import PALETTE as WINDOW, add_window_wall

ID='putuo-nanlin-normal-school-brick-villa'
META=dict(id=ID,name='原南林师范学校旧址',address='上海市普陀区凯旋北路1555弄',
          source='https://commons.wikimedia.org/wiki/File:Nanlinshifanxuexiao_Jiuzhi.JPG',
          scope='2016年实拍的排窗立面、双挑台、山花、瓶栏和修复后的两层券廊。',
          dimensions='照片中的砖皮、窗口和柱间距用于估算建筑尺度。')


def build(lod=False):
    from nanlin_ornaments import PALETTE as ORNAMENT, add_ornaments
    from fabric import metric, LAYOUT
    from nanlin_arcade import PALETTE as ARCADE, add_arcade
    b=NanlinBuilder({**FINISHES,**WINDOW,**ORNAMENT,**ARCADE})
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
    return b


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path);parser.add_argument('--lod',action='store_true')
    args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    b=build(args.lod);info=b.save(args.output,META)
    print(info['triangles'],len(b.parts),info['sha256'])
