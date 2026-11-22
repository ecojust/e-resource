"""Register the three upper bands visible in Livelikerw's 2019 street photograph against the 2022 entrance."""
from pathlib import Path
import json
import numpy as np
p=Path(__file__).resolve().parent
# The crop occupies 2143,484 to 4153,2746 in the 4912×3264 original.
def original(p):return [(u+.5)*2010/480-.5+2143 if i==0 else (u+.5)*2262/540-.5+484 for i,u in enumerate(p)]
def source_2022(uv):
    m=json.loads((p/'2022-entrance-registration.json').read_bytes())
    v=np.linalg.solve(m['street_plane_homography'],[*uv,1])
    return v[:2]/v[2]
# Arch spring, crown, joint under the stone sign and the upper-window sill.
controls=[([170.2,371.5],[2134.18,2046.66]),([288.8,372.3],[3758.36,2008.26]),
          ([230.0,318.8],[2975.98,1265.7]),([171.8,415.3],[(279.9+.5)*7296/980-.5,(352+.5)*5472/735-.5]),
          ([289.5,416.5],[(500.4+.5)*7296/980-.5,(351+.5)*5472/735-.5]),
          ([163.0,278.0],[(281+.5)*7296/980-.5,(96+.5)*5472/735-.5]),([291.5,278.2],[(514+.5)*7296/980-.5,(85+.5)*5472/735-.5])]
def fit(pairs):
    rows=[];b=[]
    for a,uv in pairs:
        u,v=a;x,z=source_2022(uv)
        rows.extend([[u,v,1,0,0,0,-u*x,-v*x],[0,0,0,u,v,1,-u*z,-v*z]]);b.extend([x,z])
    return np.r_[np.linalg.lstsq(rows,b,rcond=None)[0],1].reshape((3,3))
H=fit(controls)
def world(u,v):
    a=H@[u,v,1];return (a[:2]/a[2]).round(5).tolist()
geometry=[]
for floor,sill,top,sides in [('first',276.,230.,[(174,197),(216,239),(256,279)]),
                             ('second',193.,153.,[(173,197),(214,237),(254,276)]),
                             ('attic',98.,35.,[(170,195),(208,233),(247,273)])]:
    for i,(l,r) in enumerate(sides,1):
        points=[[l,sill],[r,sill+.6],[r,top+.6],[l,top]]
        geometry.append(dict(floor=floor,column=i,original_pixels=[original(pt) for pt in points],xz=[world(*a)for a in points]))
report=dict(source='https://commons.wikimedia.org/wiki/File:355_Middle_Sichuan_Road_Shanghai.jpg',photographer='Livelikerw',capture='2019-07-11 12:47:57',
    source_sha256='89ee9f5f14e7ed742a4a305cc372bf7cb67c624c6c35354edad9f653e62c0ae3',size=[4912,3264],crop=[2143,484,4153,2746],working_size=[480,540],
    registration='Different photographs of the same chamfer. Matched stationary stone and arch points. The inscribed names and commercial screens changed and were excluded.',
    control_points=[dict(photo_2019=original(c),photo_2022=b)for c,b in controls],photo_2019_crop_to_world=H.tolist(),windows=geometry,
    stone_levels=[dict(feature=n,original_pixels=original([230,y]),elevation_m=world(230,y)[1])for n,y in [('first sill',279),('first base of parapet',299),('first cornice',220),('first lip',205),('second sill',199),('upper fascia',147),('large cornice lower bed',132),('large cornice outer lip',113),('attic sill',102),('attic top in central crop',2)]])
(p/'2019-upper-frontage.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':print([(x['feature'],round(x['elevation_m'],2))for x in report['stone_levels']])
