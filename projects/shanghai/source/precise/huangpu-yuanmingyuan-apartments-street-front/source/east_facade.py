"""White wings, chamfered brick loggias and the recessed apartment entrance."""
import json
from math import cos, pi, sin
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from east_photo_plane import on_wall
from material_names import MATERIAL
from street_entrance import (DAMP, FANGLASS, GRANITE, INNER, METAL, STONE, WOOD,
                             dressed_column, plate, rect, tier)
from wing_casements import GLASS, PAINT, PALETTE as SASH, add_casement, finish, openings

MEASURES = Path(__file__).resolve().parents[1] / "measurements"
PLASTER = "Warm lime render of the eastern wings"
CORNICE = "Grey green east frontage sill stone"
TERRA = "Oxide red moulded terracotta frieze"
BED = "Shadowed bed behind terracotta carving"
OAK = "Red brown varnish of the entrance oak"
BRONZE = "Bronze capital edge and external letters"
PALETTE = {PLASTER: finish([193, 184, 168], .92),
           CORNICE: finish([135, 136, 124], .86),
           TERRA: finish([165, 103, 78], .84),
           BED: finish([105, 66, 54], .9),
           OAK: finish([79, 39, 34], .54),
           BRONZE: finish([82, 69, 53], .62, .24), **SASH}


def add_wings(b, lod=False):
    for side, l, r, low, high in [('South', -11.729,-2.83,22.31,22.46),
                                  ('North', 2.77,11.729,22.48,22.67)]:
        shell = Polygon([(l,6.23),(r,6.23),(r,high),(l,low)])
        holes = [box(w['left'], w['bottom'], w['right'], w['top'])
                 for w in openings() if l < w['left'] < r]
        plate(b, shell.difference(unary_union(holes)), 0., .78, PLASTER, side+' six-opening rendered wing')
        for z, material, front, h in [(6.23,DAMP,-.19,.07),(6.30,CORNICE,-.13,.077),
                                        (16.05,MATERIAL,-.025,.53),(16.58,TERRA,-.084,.093),
                                        (16.674,MATERIAL,-.108,.18),(16.854,DAMP,-.107,.047),
                                        (16.901,CORNICE,-.179,.105),(17.006,CORNICE,-.219,.071)]:
            plate(b,box(l,z,r,z+h),front,.12,material,side+f' principal horizontal course {z:g}')
        outer=l+.09 if side=='South' else r-.09
        inner=r-.056 if side=='South' else l+.056
        for tag,x in [('outer',outer),('inner',inner)]:
            b.tube([[x,-.085,.06],[x,-.085,5.89],[x,-.185,6.14],[x,-.17,6.39],
                    [x,-.071,6.48],[x,-.071,16.88],[x,-.146,17.15],[x,-.097,21.81]],
                   .054,METAL,8 if lod else 16,side+' '+tag+' rainwater downpipe')
        for j,x in enumerate(np.linspace(l+.52,r-.42,3),1):
            b.box([x,-.08,6.50],[.18,.15,.055],DAMP,label=f'{side} ledge light {j} foot')
            b.box([x,-.125,6.58],[.22,.18,.14],METAL,label=f'{side} ledge light {j}')


def add_recessed_entrance(b,lod=False):
    ref=json.loads((MEASURES/'entrance-lower-front-2016.json').read_bytes())
    cam=ref['camera']
    # The 2014 view is too dark beyond the portico to recover the rear wall
    # metrically. The recess behind the measured capital is interpreted from
    # the three steps, deep ceiling and door jambs in the two register views.
    depth=2.78
    opening=rect(ref['door_opening_px'],cam,.745)
    l,z0,r,z1=opening.bounds
    crown=[on_wall(u,v,depth,cam)[[0,2]] for u,v in ref['back_door_arch_px']]
    observed=np.array(crown)
    x=np.linspace(observed[0,0],observed[-1,0],37 if lod else 85)
    crown=np.c_[x,PchipInterpolator(observed[:,0],observed[:,1])(x)]
    xleft,xright=crown[0][0],crown[-1][0]
    left,bot,right,spring=rect(ref['back_door_outer_rect_px'],cam,depth).bounds
    spring=np.mean([crown[0][1],crown[-1][1]])
    arched=Polygon([(xleft,bot),*crown,(xright,bot)])
    side=[box(l+.15,.91,xleft-.095,z1-.19),box(xright+.095,.91,r-.15,z1-.19)]
    whole=box(l-.03,0,r+.03,z1+.025)
    plate(b,whole.difference(unary_union([arched,*side])),depth,depth+.22,MATERIAL,'Recess back wall under oak fanlight')
    # The side walls and ceiling enclose the photographed vestibule, with
    # their visible faces directly behind the paired column pedestals.
    for k,(a,d) in enumerate([(l-.09,l+.001),(r-.001,r+.09)],1):
        b.box([(a+d)/2,(depth+.04)/2,z1/2],[d-a,depth-.04,z1],MATERIAL,label=f'Entrance {k} deep side return')
    b.box([(l+r)/2,(depth+1.30)/2,z1+.037],[r-l,depth-1.30,.075],STONE,label='Sheltered vestibule ceiling')
    for j,g in enumerate(side,1):
        a,h,c,d=g.bounds; label=f'Recess side light {j}'
        plate(b,g,depth+.11,depth+.128,FANGLASS,label+' glass')
        plate(b,g.difference(g.buffer(-.062,join_style=2)),depth-.021,depth+.085,OAK,label+' oak casing')
        for q in np.linspace(a,c,4)[1:-1]:plate(b,box(q-.022,h,q+.022,d),depth+.006,depth+.098,OAK,label+' mullion')
        plate(b,box(a,d-.473,c,d-.384),depth-.010,depth+.10,OAK,label+' transom')
        plate(b,box(a,h-.05,c,h+.021),depth-.111,depth+.14,OAK,label+' sill')
    plate(b,arched.difference(arched.buffer(-.085,join_style=1)),depth-.075,depth+.13,OAK,'Oak arched entrance architrave')
    arch_ring=LineString(crown).buffer(.033,cap_style=2,join_style=1)
    plate(b,arch_ring,depth-.114,depth-.047,WOOD,'Fanlight projecting outer bead')
    upper=arched.intersection(box(xleft-1,spring,xright+1,z1+.25))
    plate(b,upper,depth+.093,depth+.112,FANGLASS,'Fanlight glazing')
    mid=(xleft+xright)/2
    for j,x in enumerate([mid],1):
        plate(b,upper.intersection(box(x-.043,spring,x+.043,z1+.4)),depth+.014,depth+.093,OAK,f'Fanlight central stile {j}')
    plate(b,box(xleft,spring-.06,xright,spring+.066),depth-.069,depth+.11,OAK,'Broad oak fanlight spring rail')
    for j in range(11 if not lod else 7):
        p=LineString(crown).interpolate((j+.5)/(11 if not lod else 7),normalized=True)
        plate(b,Point(p).buffer(.029,quad_segs=4 if lod else 7),depth-.135,depth-.10,BRONZE,'Fanlight studded arch')
    # The daylight view shows one ajar leaf with panelling in the shaded opening.
    plate(b,box(xleft,bot,xright,spring),depth+1.33,depth+1.42,INNER,'Shaded passage visible through open leaf')
    for j,(base,sign,angle) in enumerate([(xleft+.084,1,.94),(xright-.084,-1,1.30)],1):
        width=(xright-xleft)*.48
        t=np.array([sign*np.cos(angle),np.sin(angle)])
        origin=np.array([base,depth+.06]);n=np.array([-t[1],t[0]])
        def leaf_point(u,z,y):return [*(origin+t*u-n*y),z]
        def leaf(shape,y0,y1,mat,label):
            b.prism(shape,y0,y1,leaf_point,mat,label)
        leaf(box(0,bot+.035,width,spring-.082),-.036,.036,OAK,f'Open panelled entrance door {j}')
        for k,(a,c) in enumerate([(bot+.22,bot+.68),(bot+.76,spring-.33)],1):
            if c<=a:continue
            p=box(.11,a,width-.09,c);leaf(p.difference(p.buffer(-.029,join_style=2)),.037,.057,WOOD,f'Entrance door {j} raised panel {k}')
    b.box([(l+r)/2,3.26,.164],[r-l-.024,2.55,.328],GRANITE,label='Stone threshold and inner vestibule floor')
    b.box([(l+r)/2,2.18,.187],[r-l-.026,1.39,.374],GRANITE,label='Upper landing behind the three treads')


def transform_corner(b,first,side):
    # Side pieces are built in a local (street distance, inward depth, up)
    # frame, then brought onto either photographed chamfer.
    origin=np.array([side*11.729,0.])
    tangent=np.array([side*5.24,5.0]);tangent/=np.linalg.norm(tangent)
    inward=np.array([-side*tangent[1],abs(tangent[0])])
    rotation=np.column_stack((tangent,inward))
    for part in b.parts[first:]:
        vertices=np.asarray(part['vertices'],dtype=float);vertices[:,:2]=vertices[:,:2]@rotation.T+origin
        part['vertices']=vertices.tolist()
        if np.linalg.det(rotation)<0:
            part['triangles']=np.asarray(part['triangles'])[:,[0,2,1]].tolist()


def curve_point(t,reach=0.):
    theta=t*1.35
    rad=2.20+reach
    return np.array([2.22+rad*np.sin(theta),.48-rad*np.cos(theta)])


def curved_strip(b,lod,lower,upper,reach,thickness,mat,name,solid=False):
    angles=np.linspace(-1,1,35 if lod else 73)
    ring=[curve_point(t,reach)for t in angles]
    if solid:
        ring.extend([[ring[-1][0],.77],[ring[0][0],.77]])
    else:
        ring.extend(curve_point(t,reach-thickness) for t in angles[::-1])
    shape=Polygon(ring)
    b.prism(shape,lower,upper,lambda x,y,z:(x,y,z),mat,name)


def cornice_ornament(b,lod,tag):
    curved_strip(b,lod,5.44,5.94,.035,.192,BED,tag+' red terracotta frieze bed')
    for i,t in enumerate(np.linspace(-.94,.94,17),1):
        theta=t*1.35; normal=np.array([sin(theta),-cos(theta)])
        tangent=np.array([cos(theta),sin(theta)])
        c=curve_point(t,.051)
        def xyz(u,z,offset):return [*(c+tangent*u+normal*offset),z]
        # Each photograph shows suspended pointed leaves alternating with pairs
        # of moulded scrolls. These are modelled in shallow physical relief.
        edge=[(-.113,5.905),(.111,5.905),(.095,5.824),(.054,5.745),(0,5.675),(-.057,5.744),(-.095,5.814)]
        vv=[xyz(x,z,.008)for x,z in edge]+[xyz(x,z,.052)for x,z in edge]+[xyz(0,5.81,.09)]
        n=len(edge);faces=[tuple(range(n-1,-1,-1))]
        for j in range(n):
            k=(j+1)%n;faces.extend([(j,k,n+k,n+j),(n+j,n+k,2*n)])
        b.add(vv,[face[::-1] for face in faces],TERRA,f'{tag} frieze leaf {i}')
        for sign in [-1,1]:
            u=np.linspace(0,pi*1.70,13 if lod else 27);rr=np.linspace(.081,.009,len(u))
            pts=[xyz(sign*(.081+radius*cos(a)),5.589+radius*sin(a),.053)for a,radius in zip(u,rr)]
            b.tube(pts,.020,TERRA,5 if lod else 8,f'{tag} scroll {i}')
        b.tube([xyz(0,5.65,.047),xyz(0,5.708,.074),xyz(0,5.857,.093)],.014,TERRA,5 if lod else 8,f'{tag} leaf centre {i}')


def corner_level(b,lod,tag,l,r,z0,z1,level):
    w=dict(label=tag+' '+level,level='attic' if level=='attic' else 'upper',wing='near',left=l,right=r,bottom=z0,top=z1)
    add_casement(b,w,lod,.26 if level=='attic' else .32)
    plate(b,box(l-.13,z0-.15,r+.13,z0),-.17,.08,CORNICE,tag+' '+level+' sill')
    if level=='lower':
        for i in range(13):
            u=i/13;v=(i+1)/13
            a=l+(r-l)*u;c=l+(r-l)*v;spread=(r-l)*.105
            q=Polygon([(a+.008,z1),(c-.008,z1),(c+(2*v-1)*spread-.008,z1+.31),(a+(2*u-1)*spread+.008,z1+.31)])
            plate(b,q,-.053,.012,TERRA,tag+f' flat brick arch {i+1}')
    else:
        plate(b,box(l-.07,z1,r+.07,z1+.17),-.073,.02,CORNICE,tag+' '+level+' stone lintel')


def add_side_loggias(b,lod=False):
    for side,tag in [(-1,'South corner'),(1,'North corner')]:
        first=len(b.parts)
        # The 2014 southwest view supplies the measured near return. The
        # opposite return is supported by the north 2016 register views.
        profile=[(0,6.24),(4.84,6.24),(4.84,20.61),(3.27,20.61),(3.27,21.59),
                 (2.61,21.59),(2.61,22.08),(1.05,22.31),(1.05,21.87),(.34,21.87),(.34,21.60),(0,21.61)]
        frames=[(1.16,2.58,7.53,9.96,'lower'),(1.07,2.85,12.12,14.97,'middle'),(1.06,2.32,17.13,18.49,'attic')]
        wall=Polygon(profile).difference(unary_union([box(l,z0,r,z1) for l,r,z0,z1,_ in frames]))
        plate(b,wall,0,.63,MATERIAL,tag+' brick tower with three true openings')
        # Short grey outside returns close the edge of the view supplied by
        # the oblique photos. The hidden side and the rear remain unmodelled.
        plate(b,box(4.84,6.23,5.50,20.60),0,.62,PLASTER,tag+' rendered end return')
        for l,r,z0,z1,label in frames:corner_level(b,lod,tag,l,r,z0,z1,label)
        # Each return is framed by stepped brick piers, with a recessed
        # central apron above the second-storey flat arch. The street views
        # resolve the projecting pier faces and individual splayed arch joints.
        for j,(a,d) in enumerate([(.18,.75),(3.20,3.77)],1):
            for k,(lo,hi,face) in enumerate([(6.23,10.97,-.08),(11.24,16.21,-.105),(16.95,20.65,-.085)]):
                plate(b,box(a,lo,d,hi),face,.017,MATERIAL,f'{tag} brick pier {j} level {k+1}')
            for h in [10.86,15.0,18.49]:
                plate(b,box(a-.02,h-.03,d+.02,h+.06),-.13,.025,TERRA,f'{tag} pier ledge {j} {h}')
        for j,(lo,hi,p) in enumerate([(10.52,10.84,-.046),(11.26,11.81,-.040),(15.26,16.12,-.048),(18.72,20.37,-.052)],1):
            plate(b,box(.80,lo,3.17,hi),p,.028,MATERIAL,f'{tag} brick apron {j}')
            plate(b,box(.81,lo,3.16,lo+.054),p-.038,.01,TERRA,f'{tag} brick apron bead {j}')

        for z,reach,height in [(10.85,.076,.19),(11.04,.12,.09),(11.13,.165,.105),
                               (16.20,.06,.44),(16.64,.102,.16),(16.80,.172,.098),(16.90,.227,.086)]:
            plate(b,box(-.02,z,4.87,z+height),-reach,.08,CORNICE if reach>.12 else MATERIAL,tag+f' stepped band {z}')
        for j,(l,r,z) in enumerate([(1.05,2.61,22.21),(.34,1.05,21.87),(2.61,3.27,21.59)],1):
            plate(b,box(l-.045,z-.01,r+.045,z+.095),-.10,.51,CORNICE,tag+f' parapet coping {j}')
            cx=(l+r)/2;rad=.185 if j==1 else .14
            b.lathe([cx,.13],[(z+.089,rad*.70),(z+.139,rad*.80),(z+.145,rad*.52),
                (z+.153,rad*.50),(z+.21,rad*.89),(z+.279,rad),(z+.338,rad*.80),
                (z+.39,rad*.38),(z+.401,.009)],CORNICE,12 if lod else 24,tag+f' stone finial {j}')
        for s0,s1 in [(0,.52),(3.77,4.88)]:
            plate(b,box(s0,-.01,s1,5.22),.04,1.43,MATERIAL,tag+' ground brick return jamb')
        rear=box(.1,.01,4.75,5.42);door=box(.70,.19,3.68,4.42)
        plate(b,rear.difference(door),.99,1.36,MATERIAL,tag+' entrance at back of loggia')
        plate(b,door,1.12,1.16,INNER,tag+' glazed entrance door field')
        for s in [1.02,1.46,2.20,2.94,3.38]:
            plate(b,box(s-.033,.23,s+.033,4.34),1.051,1.129,OAK,tag+' glazed entrance upright')
        for z in [.27,1.09,3.41,4.26]:
            plate(b,box(.73,z,3.63,z+.073),1.045,1.16,OAK,tag+' glazed entrance transom')
        for j,t in enumerate([-.92,-.56,.81],1):
            p=curve_point(t,-.18);x,y=p
            b.box([x,y,.80],[.79,.83,1.60],MATERIAL,label=tag+f' column {j} brick pedestal')
            b.box([x,y,1.63],[.88,.9,.10],CORNICE,label=tag+f' column {j} stone base')
            dressed_column(b,x,y,1.68,4.87,.225,lod,tag+f' brick pillar {j}',True)
        # The curved front course has a continuous soffit and a physical
        # parapet. Its balcony floor does not occupy the open first-floor bay.
        curved_strip(b,lod,4.85,5.45,0,.30,STONE,tag+' curved loggia architrave',True)
        cornice_ornament(b,lod,tag)
        for j,(lower,upper,reach,mat) in enumerate([(5.94,6.002,.085,TERRA),(6.002,6.095,.151,CORNICE),
            (6.095,6.161,.191,DAMP),(6.161,6.24,.139,CORNICE),(6.24,7.38,.026,MATERIAL),(7.38,7.47,.062,CORNICE)],1):
            curved_strip(b,lod,lower,upper,reach,.19,mat,tag+f' curved balcony course {j}')
        curved_strip(b,lod,6.08,6.21,.035,.2,GRANITE,tag+' balcony floor',True)
        transform_corner(b,first,side)
