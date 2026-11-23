"""Stand-alone No. 20 plaque. Its position on the main facade is unmeasured."""
from pathlib import Path
import json,argparse
from shapely.geometry import box,Polygon,Point
from build_model import CrownBuilder,front
HERE=Path(__file__).absolute().parent
GREEN='number enamel | deep teal';WHITE='number enamel | ivory lettering';EDGE='number enamel | weathered rim';SCREW='number enamel | fixing'
def build():
    b=CrownBuilder({GREEN:{'color':[.018,.19,.155],'roughness':.40},WHITE:{'color':[.83,.83,.70],'roughness':.51},EDGE:{'color':[.16,.29,.22],'roughness':.64},SCREW:{'color':[.15,.17,.14],'roughness':.66}})
    data=json.loads((HERE.parent/'measurements/enamel-letter-contours.json').read_bytes())
    w,h=.29,.21
    plate=box(.009,.009,w-.009,h-.009).buffer(.009,quad_segs=8);front(b,plate,0,.004,GREEN,'plate substrate')
    outer=plate.buffer(-.008,join_style='round');inner=outer.buffer(-.0015);front(b,outer.difference(inner),-.00045,-.00008,EDGE,'thin rim')
    uv=lambda a:[(w*x,h*z)for x,z in a]
    for i,g in enumerate(data['rings']):
        front(b,Polygon(uv(g['exterior']),[uv(p) for p in g['holes']]).buffer(0),-.0006,-.0001,WHITE,'enamel / '+str(i+1))
    for x,z in [(0.017,.019),(.273,.020),(.018,.194),(.273,.193)]:
        front(b,Point(x,z).buffer(.0022,quad_segs=6),-.0017,-.0001,SCREW,'small mounting')
    return b
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);a=p.parse_args()
    build().save(a.out,{'name':'愚园路1112弄20号门牌','extent':'独立近摄局部，未确定在临弄立面的安装位置','photographic_reference':'41629625'})
