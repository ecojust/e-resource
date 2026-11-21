"""Measure the signed GLB through the façade plane, vestibule, two projecting bays and roof slopes."""
import argparse,json,math,runpy
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon

HERE=Path(__file__).absolute().parent
SOURCE=HERE.parents[2]/'source/precise/hongkou-yingyuan-villa-pedimented-entrance/source'
DIM=json.loads((SOURCE/'dimensions.json').read_bytes())
BASE=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
PLASTER='Yingyuan ochre render';BRICK=['Baked cherry brick','Sunlit brick header','Recessed lime joints']
WOOD='Walnut casements';GLASS='Glass reflecting the park';SHADE='Shaded glazing';STONE='Warm sill limestone'
TILES=['Dark red clay tile','Weathered clay tile','Painted dark eaves']
tx,ty=DIM['frontage_tangent_enu'];rot=np.array([[tx,-ty],[ty,tx]])


def cases():
    checks=[];d=DIM;u=d['measured_u']
    def probe(name,xy,z,direction,mat=None,iv=None,length=4.0):
        p=rot@xy;v=rot@direction[:2]
        checks.append(dict(name=name,origin=[*p,z],direction=[*v,direction[2]],length=length,allowed=[mat]if isinstance(mat,str)else mat,range_m=iv))
    def front(name,x,z,mat,iv,length=4.0):probe(name,[x,-2.],z,[0.,1.,0.],mat,iv,length)
    def vertical(name,x,y,expected_z,mat,err_low=.12,err_high=.12):
        probe(name,[x,y],14.,[0.,0.,-1.],mat,[14.-expected_z-err_high,14.-expected_z+err_low],13.)
    flat=[u[k]for k in ['first_flat_upper_window_center_at_sill','second_flat_upper_window_center_at_sill','third_flat_upper_window_center_at_sill','rightmost_upper_window_center_at_sill']]
    for upper in (False,True):
        windows=list(zip(flat,[1.57,1.63,1.72,1.36]))if upper else [(flat[0],1.50),(flat[1],1.52),(flat[3],1.28)]
        sill=d['upper_sill']if upper else d['lower_sill'];head=d['upper_sash_head']if upper else d['lower_sash_head']
        for i,(x,w)in enumerate(windows):
            name=('upper'if upper else 'lower')+' casement '+str(i+1)
            for sign in (-1,1):
                for fraction in (.22,.46,.76):
                    z=sill+(head-sill)*fraction
                    front(f'{name} glazed leaf {sign} at {fraction}',x+sign*w*.23,z,SHADE if upper and i==3 else GLASS,[2.208,2.214])
                front(f'{name} brick jamb {sign}',x+sign*(w/2+.067),sill+.44*(head-sill),BRICK,[1.870,1.909])
            front(name+' meeting stile',x,sill+.38*(head-sill),WOOD,[2.060,2.073])
            front(name+' middle sill moulding',x+w*.26,sill-.070,STONE,[1.778,1.798])
            front(name+' vertical brick lintel',x+w*.17,head+.105,BRICK,[1.743,1.82])
            front(name+' recessed triangular tympanum',x+.021,head+.237,PLASTER,[1.875,1.885])
    for j,x in enumerate([-6.82,-4.02,-1.31,1.36,4.70,6.80]):
        front('flat rendered interbay '+str(j),x,5.72,PLASTER,[1.995,2.005])
    front('outer brick jamb beside the name',.96,5.72,BRICK,[1.870,1.909])
    centre=(u['door_portal_left_outer_at_header']+u['door_portal_right_outer_at_header'])/2;leaf=d['door_leaf_total']/2
    for sign in (-1,1):
        cp=centre+sign*(leaf/2+.008)
        for i in range(4):
            z=d['entry_landing']+.315+i*(d['door_height']-.575)/3.
            front(f'octagonal entrance glass {sign} row {i+1}',cp+.047,z+.038,SHADE,[3.084,3.096])
            front(f'oak stile outside pane {sign} row {i+1}',cp+leaf*.376,z,'Varnished entrance oak',[3.038,3.050])
        for z in (1.28,2.33,3.22):
            front('open volume forward of door '+str((sign,z)),centre+sign*.62,z,None,None,2.62)
        front('portal brick edge '+str(sign),centre+sign*(d['portal_outer_width']/2-.074),1.80,'Baked cherry brick',[1.829,1.846])
    for j,x in enumerate(np.linspace(-1.49,1.49,7)):
        front('top of projecting doorway canopy '+str(j),centre+x,d['portal_top']-.02,'Baked cherry brick',[1.627,1.643])
    for k in range(4):
        reach=1.42-.31*k
        top=d['entry_landing']*(k+1)/4
        probe('granite threshold tread '+str(k+1),[centre+.32,-reach+.14],1.10,[0.,0.,-1.],'Grey cut stair granite',[1.10-top-.009,1.10-top+.009],1.19)
    front('pendant opal glass',centre,d['portal_soffit']-.568,'Pendant frosted glass',[2.300,2.313])
    shapes=json.loads((SOURCE/'sign-outlines.json').read_bytes())['name']
    for i,piece in enumerate(shapes):
        poly=Polygon(piece[0],piece[1:]);q=poly.representative_point()
        front('name relief component '+str(i),centre+q.x,4.12+q.y,'Vermilion raised name',[1.923,1.936])
    cx=u['right_paired_projection_center_at_sill'];sill=d['oriel_sill'];h=d['oriel_head']-sill
    profile=[(-.945,.023),(-.835,-.22),(-.205,-.531),(.205,-.531),(.835,-.22),(.945,.023)]
    for z in [sill+.13,sill+.77,sill+1.47,sill+2.18,sill+2.93,sill+h-.11]:
        front('cream pier between paired stair sashes at '+str(z),cx,z,PLASTER,[1.445,1.458])
    for j in (1,3):
        a=np.array(profile[j])+[cx,0.];c=np.array(profile[j+1])+[cx,0.];mid=(a+c)/2;t=(c-a)/np.linalg.norm(c-a);n=np.array([t[1],-t[0]])
        for sign in (-1,1):
            for fz in (.14,.40,.68,.91):
                probe(f'oriel facet {j} pane {sign} elevation {fz}',mid+sign*.16*t+1.45*n,sill+fz*h,[*-n,0.],SHADE if j==3 else GLASS,[1.553,1.571])
        probe(f'oriel facet {j} tall mullion',mid+1.45*n,sill+.37*h,[*-n,0.],WOOD,[1.493,1.508])
    front('low arched subwindow',cx+.055,1.0,'Shadow at timber reveal',[2.202,2.220])
    for j,(yy,rad) in enumerate([(sill-.482,.31),(sill-.315,.64),(sill-.138,.92)]):
        front('underside stair corbel level '+str(j),cx,yy,STONE,[2.-.531*rad-.010,2.-.531*rad+.010])
    for j,x in enumerate([-6.81,-5.41,-2.41,.27]):
        for k,y in enumerate([.28,2.60,4.24]):
            if abs(x+.32)<.82 or abs(x+3.82)<.84:continue
            v=(y+.23)/(d['section_depth_m']+.23);z=d['flat_eave']+(d['main_section_ridge']-d['flat_eave'])*v
            vertical(f'front roof tile {j},{k}',x,y,z,TILES)
    ridge=4.05
    for j,x in enumerate([1.93,3.42,4.91,5.98,7.06]):
        edge,z0=(.85,7.60)if x<ridge else(u['right_wall_under_front_eave']+.42,6.82)
        z=z0+(d['cross_gable_ridge']-z0)*(x-edge)/(ridge-edge)
        for i,y in enumerate([.10,1.23,3.23]):
            if x<ridge and d['flat_eave']+(d['main_section_ridge']-d['flat_eave'])*(y+.23)/(d['section_depth_m']+.23)>z-.14:continue
            vertical(f'pitched cross gable tile {j},{i}',x,y,z,TILES)
    tower=u['turret_finial'];cy=2.587
    for i,ang in enumerate([-153,-106,-79,-40]):
        for k,r in enumerate([.54,1.08,1.70,2.16]):
            t=math.radians(ang);z=d['turret_cone_top']-(d['turret_cone_top']-d['turret_eave'])*(r-.039)/(2.41-.039)
            vertical(f'turret radial roof tile {i},{k}',tower+r*math.cos(t),cy+r*math.sin(t),z,TILES,.15,.18)
    for j,(lo,hi)in enumerate([(-173,-123),(-115,-65),(-57,-7)]):
        uv=lambda a:np.array([tower,cy])+d['frontage_outer_radius_m']*np.array([math.cos(math.radians(a)),math.sin(math.radians(a))])
        a=uv(lo);c=uv(hi);mid=(a+c)/2;t=(c-a)/np.linalg.norm(c-a);n=np.array([t[1],-t[0]])
        for k,z in enumerate([1.35,2.21,5.12,6.03]):
            for sign in(-1,1):
                # The building return screens the outer pane of the end sash from
                # its long oblique sightline. Probe the surface inside that recess too.
                dist=.12 if j==2 and sign==1 else .55
                probe(f'corner tower sash {j} height {k} pane {sign}',mid+sign*.26*t+dist*n,z,[*-n,0.],SHADE if j==2 else GLASS,[dist+.098,dist+.116])
                if j==2 and sign==1:
                    probe(f'wall screening the oblique tower view {k}',mid+sign*.26*t+.55*n,z,[*-n,0.],PLASTER,[.180,.198])
    return checks


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('raw','full','lod','output'):parser.add_argument(key,type=Path)
    args=parser.parse_args();records={k:BASE(getattr(args,k),cases())for k in ('raw','full','lod')}
    args.output.write_text(json.dumps(records,ensure_ascii=False,separators=(',',':'))+'\n')
    for k,r in records.items():print(k,len(r['cases']),[(c['name'],c['first_hit']) for c in r['cases']if not c['passed']][:18])
    raise SystemExit(int(not all(r['passed']for r in records.values())))

