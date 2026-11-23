"""Build an editable local study of the old, open Yangtszepoo tower crown."""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder

SLUG='yangpu-yangshupu-fire-brigade-historic-tower-crown'
META=dict(id=SLUG,name='杨树浦救火会旧望塔圆眼与敞亭塔冠',viewer_page='yangshupu-fire-brigade-historic-tower-crown.html',
          heritage_group='5G010',address='上海市杨浦区杨树浦路1307号',period='杨浦区融媒体中心所刊历史照片中的旧塔冠，原照摄期未载。',
          dimensions='塔身宽取一个展示单位；截取两层装饰带至敞亭帽的局部。',photos_embedded=False,
          photo_author='历史图由杨途供稿；年代对照照片由Fayhoo拍摄。',photo_source='https://m.thepaper.cn/newsDetail_forward_19513921',
          geometry_license='MIT, original reconstruction',texture_license='MIT, original generated mineral finish',
          copyright='Original reconstructed geometry and generated material under the MIT license. No third-party image is embedded.')
def tone(rgb,rough=.8):
    return {'color':[(c/255)**2.2 for c in rgb],'roughness':rough}
WALL='Historic crown | pale mineral face';SILL='Historic crown | cornice and moulding';EDGE='Historic crown | pale rim'
PANEL='Historic crown | lower rectangular panel';GLASS='Historic crown | dark roundel';BAR='Historic crown | roundel crosspiece'
INNER='Historic crown | shadowed reveal';ROOF='Historic crown | pavilion sheet roof';FLOOR='Historic crown | cornice weathering'
PALETTE={WALL:{'color':[.86,.86,.86],'roughness':.92,'texture':str(SOURCE/'mineral-render.png')},
  SILL:tone((175,174,168)),EDGE:tone((196,194,185)),PANEL:tone((135,134,129)),
  GLASS:tone((56,59,57),.44),BAR:tone((104,104,96),.58),INNER:tone((91,91,86)),ROOF:{'color':[1,1,1],'roughness':.67,'texture':str(SOURCE/'sheet-finish.png')},FLOOR:tone((153,154,146))}
SURVEY=json.loads((SOURCE.parent/'measurements/historical-crown-camera.json').read_bytes())

def make_texture():
    # A non-photographic, seamless fine mineral grain; no brick bond is visible.
    rng=np.random.default_rng(724)
    face=rng.normal(0,3.2,(128,128))
    coarse=rng.normal(0,1.7,(16,16)).repeat(8,0).repeat(8,1)
    coarse=sum(np.roll(np.roll(coarse,i,0),j,1) for i in range(5)for j in range(5))/25
    rgb=np.clip(np.array([184,184,178])+np.round(face+coarse)[:,:,None],0,255).astype(np.uint8)
    Image.fromarray(rgb).save(SOURCE/'mineral-render.png',optimize=True)
    sheet=np.clip(np.array([99,100,98])+np.rint(face*.47+coarse*.34)[:,:,None],0,255).astype(np.uint8)
    Image.fromarray(sheet).save(SOURCE/'sheet-finish.png',optimize=True)

def mapper(face):
    if face=='front':return lambda u,z,d:(u,-.5-d,z)
    return lambda u,z,d:(.5+d,u,z)

def axis_values(points):
    # Opposite sides of a circle each give independent limits in the registered plane.
    left,right,top,bottom=points
    return (left[0]+right[0])*.5,(bottom[1]+top[1])*.5,((right[0]-left[0])+(top[1]-bottom[1]))*.25

def decorated_face(b,face,lod):
    m=mapper(face);a=SURVEY['plane_readings'][face]
    cx,cz,r=axis_values(a['eye']);n=8 if lod else 20
    def circle(rad):return Point(cx,cz).buffer(rad,quad_segs=n)
    def extrude(poly,z0,z1,mat,label):b.prism(poly,z0,z1,m,mat,face+' '+label)
    fl,fr,br,bl=a['field']
    left=(fl[0]+bl[0])/2;right=(fr[0]+br[0])/2
    base=(br[1]+bl[1])/2;top=(fl[1]+fr[1])/2
    field=box(left,base,right,top)
    # The front skin occupies the first .055 of the return. Butt the two solids
    # at its inside edge to avoid coincident exterior faces at the photographed corner.
    skin_start=-.445 if face=='return' else -.5
    skin=box(skin_start,-.26,.5,1.70)
    extrude(skin.difference(unary_union([field,circle(r)])),-.055,0,WALL,'shaft wall around the recessed panels')
    extrude(field,-.055,-.017,PANEL,'rectangular recessed mineral panel')
    extrude(circle(r),-.055,-.037,GLASS,'dark circular face')
    extrude(circle(r+.024).difference(circle(r)),.0004,.013,SILL,'roundel outside moulding')
    if face=='front':
        cross=unary_union([box(cx-.008,cz-r,cx+.008,cz+r),box(cx-r,cz-.006,cx+r,cz+.006)]).intersection(circle(r))
        extrude(cross,-.023,-.012,BAR,'two photographed roundel crosspieces')
    # Small stepped blind panels immediately around/under each circular eye.
    feet=a['stepped_foot'];bottom=np.median([p[1]for p in feet[:2]])
    u0=min(p[0]for p in a['upper_moulding']);u1=max(p[0] for p in a['upper_moulding']+feet)
    if u1-u0<2*r+.07:u1=u0+2*r+.07
    ax=(u0+u1)/2; half=(u1-u0)/2;spring=cz+.008;rise=max(p[1] for p in a['upper_moulding'])-spring
    arch=[(ax+half*math.cos(t),spring+rise*math.sin(t)) for t in np.linspace(0,math.pi,14 if lod else 32)]
    blind=Polygon([(u0,bottom),(u1-.034,bottom),(u1-.034,bottom+.058),(u1,bottom+.086),*arch,(u0,bottom)])
    edge=blind.difference(blind.buffer(-.013,join_style='mitre')).difference(circle(r+.026))
    extrude(edge,.0005,.010,EDGE,'arched blind frame and stepped foot')
    # Shaft face remains plain where the archive print is washed out.
    extrude(box(-.484,1.52,.484,1.548),.0005,.006,SILL,'fine band below the cornice')
    extrude(box(-.5,-.238,.5,-.212),.0005,.009,SILL,'lower horizontal edge of study')

def square_loft(b,rings,mat,label):
    sides=4;angles=np.radians([45,135,225,315]);loft(b,rings,mat,label,sides,angles,math.sqrt(2))

def loft(b,rings,mat,label,n=8,angles=None,multiplier=1):
    theta=angles if angles is not None else np.arange(n)*2*math.pi/n+math.pi/8
    v=[];faces=[]
    for r,z in rings:v.extend([(r*multiplier*math.cos(t),r*multiplier*math.sin(t),z)for t in theta])
    faces.append(tuple(reversed(range(n))))
    for i in range(len(rings)-1):
        for j in range(n):
            k=(j+1)%n;j0=i*n+j;k0=i*n+k
            faces.append((j0,k0,k0+n,j0+n))
    faces.append(tuple((len(rings)-1)*n+j for j in range(n)))
    b.add(v,faces,mat,label)

def build(lod=False):
    b=CrownBuilder(PALETTE)
    for face in ('front','return'):decorated_face(b,face,lod)
    # These two plain closure faces meet the decorated skins at their inside edge.
    b.box((-.4725,.0275,.72),(.055,.945,1.96),WALL,label='plain cutback rear edge, left')
    b.box((-.0275,.4725,.72),(.945,.055,1.96),WALL,label='plain cutback rear edge, right')
    b.box((0,0,-.24),(.89,.89,.04),INNER,label='lower section closure')
    square_loft(b,[(.498,1.699),(.507,1.708),(.529,1.729),(.529,1.743)],SILL,'square cornice recessed undercut')
    square_loft(b,[(.526,1.743),(.553,1.76),(.553,1.80)],ROOF,'dark squared drip at eaves')
    square_loft(b,[(.553,1.80),(.535,1.811),(.30,1.837)],FLOOR,'shallow weathering surface of square cornice')
    # The printed silhouette establishes a faceted pavilion. Its unseen half
    # uses eight-fold symmetry, a documented modelling convention.
    loft(b,[(.251,1.83),(.279,1.885),(.276,2.245)],WALL,'faceted solid lantern apron')
    loft(b,[(.28,2.245),(.283,2.258)],SILL,'pavilion sill')
    angles=np.arange(8)*math.pi/4+math.pi/8
    radius=.266
    for i,t in enumerate(angles):
        p=(radius*math.cos(t),radius*math.sin(t))
        b.box((*p,2.43),(.047,.047,.345),WALL,basis=[(math.cos(t),math.sin(t),0),(-math.sin(t),math.cos(t),0),(0,0,1)],label=f'open lantern pier {i+1}')
    loft(b,[(.278,2.602),(.278,2.606)],INNER,'dark recessed underside behind the lantern lights')
    loft(b,[(.279,2.606),(.299,2.620),(.299,2.632)],ROOF,'lantern head band below the dark cap')
    loft(b,[(.312,2.632),(.352,2.642),(.352,2.664)],ROOF,'polygonal roof drip and underside')
    loft(b,[(.352,2.664),(.273,2.72),(.225,2.738)],ROOF,'low hipped cap without a finial')
    return b

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--lod',action='store_true')
    args=ap.parse_args();report=build(args.lod).save(args.output,META);print(report['sha256'],report['parts'],report['triangles'])
if __name__=='__main__':
    if not all((SOURCE/f).exists() for f in ('mineral-render.png','sheet-finish.png')):make_texture()
    main()
