"""Photographically registered upper facade, terrace and entry passage at Lane 212."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
from huanlong_photo_plane import on_wall
from upper_casements import openings
from material_names import MATERIAL

MEASUREMENTS=Path(__file__).resolve().parents[1]/'measurements'
E=json.loads((MEASUREMENTS/'fabric-observations.json').read_bytes())
R=json.loads((MEASUREMENTS/'terrace-rail-edges.json').read_bytes())['uprights']
WHITE='212 terrace | light-grey painted concrete'
GREY='212 terrace | darker fascia and horizontal reveals'
RAIL='212 terrace | painted narrow balusters'
STEEL='212 roof shade | painted framing'
GREEN='212 roof shade | turquoise front edge and fabric fold'
GSCREEN='212 terrace | weathered green fabric side screen'
BLIND='212 terrace | pale roll-up blind slats'
SHADOW='212 terrace | recessed glazing'
PAVING='212 entrance | lightly mottled grey passage surface'

def srgb(rgb,rough=.88,metal=0.):
    c=np.asarray(rgb)/255.
    return dict(color=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)

PALETTE={WHITE:srgb([188,186,183]),GREY:srgb([134,132,124]),RAIL:srgb([183,181,179]),STEEL:srgb([67,71,62],.70,.14),GREEN:srgb([62,127,111],.61),GSCREEN:srgb([74,123,104],.85),BLIND:srgb([178,182,177],.83),SHADOW:srgb([72,75,68]),PAVING:srgb([149,146,139])}

def slab(b,shape,y0,y1,mat,label):
    b.prism(shape,-y1,-y0,lambda x,z,d:(x,-d,z),mat,label)

def from_photo(points,y,camera='commons_2015'):
    return Polygon([(x,z) for x,_,z in (on_wall(*a,y,camera) for a in points)])

def bounds(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)

def front(b):
    x0,x1=-2.83,2.67
    wall=Polygon([(x0,.010),(x1,.010),(x1,8.08),(x0,7.99)])
    for row in openings():
        wall=wall.difference(box(row['left'],row['bottom'],row['right'],row['top']))
    # The opening below the photographed timber windows remains clear through the building section.
    wall=wall.difference(box(-2.55,-.02,.73,3.62))
    slab(b,wall,0.,.31,MATERIAL,'Upper plaster wall, three actual openings and deep jambs')
    bounds(b,x0,-2.55,.30,1.34,.009,3.63,MATERIAL,'West passage side return')
    bounds(b,.73,.86,.30,1.34,.009,3.63,MATERIAL,'East passage side return')
    bounds(b,-2.55,.73,.30,1.34,3.62,3.73,GREY,'Recessed passage ceiling')
    for k,y0,y1,mat,label in [('lower_cornice',-.165,.025,WHITE,'Projecting string course beneath timber windows'),('underside_drip',-.180,-.145,GREY,'Shadow moulding below the string course')]:
        slab(b,from_photo(E[k],y0),y0,y1,mat,label)
    for i,line in enumerate(E['rainwater_downpipes']):
        pts=[on_wall(*a,-.091)for a in line]
        b.tube(pts,.036,WHITE,sides=12,label='Rainwater downpipe '+str(i+1))
        for j in (1,len(pts)-2):
            x,y,z=pts[j];bounds(b,x-.049,x+.049,y-.041,.012,z-.018,z+.018,GREY,f'Downpipe {i+1} collar {j}')
    mouth=np.array([[-2.90960,-2.95719,.371],[2.08765,-2.79132,.284]])
    rear=np.array([[-2.55,1.37,.003],[.73,1.37,.003]])
    upper=np.array([mouth[0],mouth[1],rear[1],rear[0]])
    p=np.vstack([upper,upper-[0,0,.060]])
    b.add(p,[(0,1,2),(0,2,3),(4,6,5),(4,7,6),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],PAVING,'Graded paving to the passage')
    # Deep lining under the lintel and behind the visible jambs intercepts oblique rays.
    # Dimensions follow the real opening. There is no invented room plan.
    for row in openings():
        l,r,h0,h1=[row[k] for k in ('left','right','bottom','top')]
        bounds(b,l-.019,l,.303,1.22,h0,h1,SHADOW,row['key']+' inner jamb — west')
        bounds(b,r,r+.019,.303,1.22,h0,h1,SHADOW,row['key']+' inner jamb — east')
        bounds(b,l,r,.303,1.22,h1,h1+.025,SHADOW,row['key']+' upper reveal inside the room')
        bounds(b,l,r,.303,1.22,h0-.027,h0,SHADOW,row['key']+' inner sill return')
        bounds(b,l-.032,r+.032,1.168,1.196,h0-.035,h1+.035,SHADOW,row['key']+' dark lining behind the casements')

def terrace(b,lod):
    y=E['terrace_face_y']
    slab(b,from_photo(E['deck_fascia'],y),y+.012,.62,WHITE,'Deck slab and eave over the two open window bays')
    for i,row in enumerate(R):
        p=from_photo([row[k] for k in ('upper_left','upper_right','lower_right','lower_left')],y)
        slab(b,p,y,y+.074,RAIL,f'Terrace painted baluster {i+1:02d}')
    for name,depth in [('balustrade_cap',.115),('balustrade_base',.137)]:
        slab(b,from_photo(E[name],y-.007),y-.007,y+depth,WHITE,name.replace('_',' ').title())
    # Only continue the terrace floor to the observed back wall. Its top is below the open guard.
    face=from_photo(E['balustrade_base'],y)
    z0=face.bounds[1]-.045
    bounds(b,-2.69,2.48,-.066,1.19,z0-.071,z0,GREY,'Grey terrace walking surface')
    for end in (-2.749,2.54):
        bounds(b,end,end+.065,-.130,1.15,z0-.03,8.78 if end<0 else 8.95,WHITE,'Solid returning terrace cheek')
    cam=E['roof_station'];rear=1.15
    wall=from_photo(E['penthouse_visible_outline'],rear,cam)
    # The upper and lower edge of this house section are captured in different photographs.
    # Extend only to the terrace floor and subtract the glazing actually visible behind the awning.
    a,c,d,e=wall.bounds
    opening=from_photo(E['back_frame_rect'],rear,cam)
    wall=wall.union(box(a+.076,z0,d-.080,c+.34)).difference(opening)
    slab(b,wall,rear,rear+.21,MATERIAL,'Setback upper room and street-facing parapet silhouette')
    slab(b,opening,rear+.153,rear+.191,SHADOW,'Dark upper glazing behind the folding blind')
    x0,z0,x1,z1=opening.bounds
    for i in range(5):
        x=x0+(x1-x0)*i/4
        strip=opening.intersection(box(x-.020,z0-.01,x+.020,z1+.03))
        slab(b,strip,rear+.09,rear+.158,STEEL,f'Upper room mullion {i+1}')
    lip=from_photo(E['roof_lip'],rear-.12,cam)
    slab(b,lip,rear-.12,rear+.202,GREY,'Overhanging dark coping of the rear upper room')
    # January and September views give the outer green edge and steel stays. The wallward depth is an estimate.
    a,bp=[np.asarray(on_wall(*p,.46,cam))for p in E['rolled_awning']['visible_edge']]
    run=bp-a;v=run/np.linalg.norm(run)
    for i in range(7 if not lod else 4):
        f=i/(6 if not lod else 3)
        q=a+f*run
        b.tube([q+[0.,-.016,.012],q+[0.,.61,.094]],.013,STEEL,sides=8,label=f'Awning steel rafter {i+1}')
    b.tube([a,bp],.024,GREEN,sides=10,label='Green folding shade front rail')
    h=np.array([0.,.61,.090]);n=np.cross(run,h);n=n/np.linalg.norm(n)
    pts=np.array([a,bp,bp+h,a+h]);q=np.vstack((pts,pts-.015*n))
    b.add(q,[(0,1,2,3),(7,6,5,4),(4,5,1,0),(5,6,2,1),(6,7,3,2),(7,4,0,3)],GREEN,'Green narrow folding canopy at the back of the terrace')
    # The left fabric wing is recorded directly on the summer photograph.
    # Its cropped triangular corner is still visible beneath the trees.
    shade=from_photo([[3524,488],[3734,391],[3923,626],[3594,755],[3537,768]],.44)
    slab(b,shade,.44,.459,GSCREEN,'Western green wind screen with visible angled corner')
    blind_y=rear-.091
    blind=from_photo(E['painted_blind_corners_commons'],blind_y)
    bx,bz,bx1,bz1=blind.bounds
    for i,pos in enumerate((bx,bx1)):
        bounds(b,pos-.019,pos+.019,blind_y-.016,rear+.095,bz-.025,bz1+.045,STEEL,f'Blind hanging guide {i+1}')
    upper_edge=list(blind.exterior.coords)[:2]
    b.tube([[x,blind_y-.016,z+.017]for x,z in upper_edge],.027,STEEL,sides=12,label='Blind head roller')
    slab(b,blind,blind_y,blind_y+.022,BLIND,'Partly lowered light blind behind the canopy')
    if not lod:
        lx,lz,rx,rz=blind.bounds
        for i,z in enumerate(np.arange(lz+.014,rz,.020)):
            slab(b,blind.intersection(box(lx,z,rx,z+.003)),blind_y-.004,blind_y+.002,GREY,f'Original blind slat {i+1:02d}')

AIRER='212 photograph | folding clothes rack, dull aluminium'
PALETTE[AIRER]=srgb([164,168,169],.47,.39)

def clothes_rails(b,lod):
    from scipy.optimize import brentq
    data=json.loads((MEASUREMENTS/'retractable-airer.json').read_bytes())
    rods=[]
    for j,l in enumerate(data['rails']):
        uv=np.array(l['observed'])
        witness=uv[uv[:,0]==3850][0]
        z=on_wall(3850,1466,-data['central_rail_projection_from_wall_m'])[2]
        y=brentq(lambda depth:on_wall(*witness,depth)[2]-z,-1.3,0.)
        line=[np.array(on_wall(*p,y)) for p in l['ends_xy']]
        rods.append((y,line))
        b.tube(line,.0115,AIRER,sides=10 if lod else 18,label=f'2015 folding clothes line | rail {j+1}')
    for k,u in enumerate(data['scissor_arm_attachments_u']):
        y,line=rods[1]
        r=data['rails'][1];p=np.array(on_wall(u,r['line_y_per_u']*u+r['line_intercept'],y))
        x,_,z=p
        bounds(b,x-.036,x+.036,-.045,.005,z-.245,z+.015,STEEL,f'Folding bracket {k+1} wall mounting')
        y0=-.046;y1=rods[0][0]
        for j in range(3):
            ya=y0+(y1-y0)*j/3;yb=y0+(y1-y0)*(j+1)/3
            for a,c in ((z,z-.15),(z-.15,z)):
                b.tube([[x-.008,ya,a],[x+.008,yb,c]],.009,AIRER,sides=8 if lod else 12,label=f'Folding bracket {k+1} links {j+1}')
        b.tube([[x,y0,z],[x,y1,z]],.012,AIRER,sides=10,label=f'Folding bracket {k+1} top bar')

def add_212_fabric(builder,lod=False):
    front(builder)
    clothes_rails(builder,lod)
    terrace(builder,lod)
