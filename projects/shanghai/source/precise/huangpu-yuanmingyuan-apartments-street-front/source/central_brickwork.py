"""The two actual masonry arches, recessed central windows, gables and wing spandrels of 115 Yuanmingyuan Road."""
from functools import lru_cache
import json
from pathlib import Path

import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import LineString,Polygon,box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

from east_photo_plane import on_wall
from gable_dedications import PALETTE as INSCRIPTIONS,add_gable_dedications
from material_names import MATERIAL as BRICK,TEXTURE

HERE=Path(__file__).resolve().parents[1]/'measurements'
PLASTER='Weathered grey lime render'
STONE='Grey coping and string courses'
JOINT='Recessed warm mortar of the radiating arches'
TIMBER='Dark red brown painted timber casements'
GLASS='Blue grey glazing behind the central brick arches'
SHADOW='Unlit timber reveals behind arched windows'
PALE='Pale inset stone above the centre entrance'
TILES=['Arch brick warm red','Arch brick muted rose','Arch brick pale red','Arch brick deep red']
COURSES=['Upper wall rose brick','Upper wall muted brick','Upper wall light brick','Upper wall dark brick','Upper wall warm brick']
BED='Weathered upper-wall mortar'
PALETTE={**INSCRIPTIONS,PLASTER:dict(color=[.60,.56,.53],roughness=.95),STONE:dict(color=[.365,.345,.31],roughness=.85),
         JOINT:dict(color=[.35,.268,.225],roughness=.96),TIMBER:dict(color=[.202,.12,.105],roughness=.63),
         GLASS:dict(color=[.142,.208,.27],roughness=.30,metallic=.08),SHADOW:dict(color=[.105,.078,.068],roughness=.92),
         PALE:dict(color=[.69,.61,.50],roughness=.9),BRICK:dict(color=[1.,1.,1.],roughness=.92,texture=str(TEXTURE))}
def srgb(rgb):
    v=np.asarray(rgb)/255.
    return np.where(v>.04045,((v+.055)/1.055)**2.4,v/12.92).tolist()


# The 2014 and 2016 exposures show the upper masonry lighter and less saturated
# than the ground-floor brick. The arch is only slightly lighter than that wall.
for name,rgb in zip(COURSES,[[184,142,125],[177,134,120],[196,153,137],[171,131,115],[189,144,129]]):
    PALETTE[name]=dict(color=srgb(rgb),roughness=.94)
for name,rgb in zip(TILES,[[186,145,131],[192,150,136],[201,159,143],[178,137,121]]):
    PALETTE[name]=dict(color=srgb(rgb),roughness=.90)
PALETTE[BED]=dict(color=srgb([153,125,115]),roughness=.96)
PALETTE[JOINT]=dict(color=srgb([147,109,100]),roughness=.97)


@lru_cache(maxsize=1)
def measurements():return json.loads((HERE/'east-brickwork-features.json').read_bytes())


def solid(b,shape,front,back,mat,name):
    if not shape.is_empty and shape.area>1.e-8:
        b.prism(shape,-back,-front,lambda x,z,d:(x,-d,z),mat,name)


def study(x,y,depth):
    return on_wall(480.+x/1.75,y/1.75,depth,camera='2016_front')[[0,2]]


def guide(x,y,depth):
    return on_wall(x/.75,y/.75,depth,camera='2016_front')[[0,2]]


@lru_cache(maxsize=1)
def detail_to_front():
    register=json.loads((HERE/'central-arch-close-registration.json').read_bytes())
    return np.linalg.inv(register['front_to_detail_matrix'])


def from_detail(u,v,depth):
    # Close-study points refer to the 850-pixel-wide guide of the native 1200
    # image. Its 551 shared masonry points register both exposures.
    target=detail_to_front()@np.array([u*1200./850.,v*1200./850.,1.])
    return on_wall(*(target[:2]/target[2]),depth,camera='2016_front')[[0,2]]


def ring_rails(tt,depth,round_window):
    if round_window:
        x0=443.6+150.*np.cos(tt);x1=443.6+221.8*np.cos(tt)
        y0=251.-120.*np.sin(tt);y1=251.-181.*np.sin(tt)
    else:
        x0=448.+171.*tt;x1=448.+195.*tt
        y0=511.+13.*tt*tt;y1=446.+33.*tt*tt
    return [np.array([from_detail(x,y,depth)for x,y in zip(xs,ys)]) for xs,ys in [(x0,y0),(x1,y1)]]


def profile_shape(xz,width):
    return LineString(xz).buffer(width/2,cap_style='flat',join_style='mitre')


def ledge(b,x0,x1,z,depth,label):
    for i,(dz,h,reach) in enumerate([(-.105,.105,.06),(0.,.065,.115),(.065,.048,.155)]):
        extra=reach*.38
        solid(b,box(x0-extra,z+dz,x1+extra,z+dz+h),depth-reach,depth+.03,STONE,f'{label} moulding {i+1}')


def ring(b,row,is_round,depth,lod):
    ends=(0.,np.pi) if is_round else (-1.,1.)
    kind='Semi-circular radial brick' if is_round else 'Segmental window head'
    mapped=measurements()['upper_radial_joints' if is_round else 'lower_wedge_joints'];field='angle_rad' if is_round else 'parameter'
    joints=np.r_[ends[0],[r[field]for r in mapped],ends[1]]
    # Register at the face of the projecting stones, where the dark radial
    # joints were measured. The backing is set inside this edge.
    def surface(low,high,samples,observed_plane=None):
        plane=depth-.122 if observed_plane is None else observed_plane
        inner,outer=ring_rails(samples,plane,is_round)
        return Polygon([*(inner+(outer-inner)*low),*(inner+(outer-inner)*high)[::-1]])
    continuous=np.linspace(*ends,81 if lod else 141)
    bed=depth-(.107 if is_round else .092)
    solid(b,surface(0.,1.,continuous),bed,depth+.10,JOINT,kind+' continuous mortar bed')
    # These thin voussoirs have separate, visible side planes. A narrow joint
    # exposes the recessed mortar bed all the way up the arch.
    for i,(a,z) in enumerate(zip(joints,joints[1:]),1):
        gap=min(.003 if is_round else .004,(z-a)*.23)
        if z-a<.002:continue
        left=a+gap;right=z-gap
        if is_round:
            left=mapped[i-2]['dark_joint_edges_rad'][1] if i>1 else a
            right=mapped[i-1]['dark_joint_edges_rad'][0] if i<=len(mapped) else z
            if right<=left:continue
        tt=np.linspace(left,right,3 if not lod else 2)
        front=depth-(.121+.002*np.sin(i*.93))
        solid(b,surface(.105,.86,tt,front),front,bed+.009,TILES[(i*13+i//5)%4],f'{kind} voussoir {i:03d}')
    for j,(lo,hi,reach)in enumerate([(0.,.033,.150),(.033,.068,.129),(.068,.105,.105),(.86,.895,.116),(.895,.954,.151),(.954,1.,.170)]):
        solid(b,surface(lo,hi,continuous),depth-reach,depth-.064,TILES[3 if j in [0,5] else 0],f'{kind} rolled edge {j+1}')
    if is_round:
        for name,sign in [('south',-1),('north',1)]:
            xx=row['outer_left'] if sign<0 else row['outer_right'];c=study(xx,row['spring'],depth)
            solid(b,box(c[0]-.17,c[1]-.074,c[0]+.17,c[1]+.05),depth-.19,depth+.025,TILES[3],name+' arch impost')


def glazing(b,shape,name,depth,bars,lod):
    solid(b,shape,depth+.065,depth+.115,GLASS,name+' recessed glass')
    casing=shape.difference(shape.buffer(-.080,join_style='mitre'))
    solid(b,casing,depth-.070,depth+.071,TIMBER,name+' perimeter frame')
    for tag,path,width in bars:
        strip=profile_shape(path,width).intersection(shape)
        solid(b,strip,depth-(.025 if width>.059 else 0.),depth+.072,TIMBER,name+' '+tag)


def opening_outline(row,round_window,depth,at_frame=False):
    t=np.linspace(0.,np.pi,97) if round_window else np.linspace(1.,-1.,65)
    if round_window and at_frame:
        curve=np.array([from_detail(443.+143.*np.cos(a),250.-109.*np.sin(a),depth)for a in t])
    else:
        curve=ring_rails(t,depth,round_window)[0]
    bottom_left=study(row['left'],row['sill'],depth)
    bottom_right=study(row['right'],row['sill'],depth)
    return np.vstack((bottom_left,bottom_right,curve))


def splayed_reveal(b,row,round_window,depth,frame):
    front=opening_outline(row,round_window,depth)
    rear=opening_outline(row,round_window,frame,True)
    vertices=[];faces=[]
    for face,plane in [(front,depth),(rear,frame)]:
        centroid=face.mean(axis=0)
        for index in range(2):
            unit=face-centroid
            unit/=np.linalg.norm(unit,axis=1)[:,None]
            contour=face+unit*.082*index
            vertices.extend((x,plane,z)for x,z in contour)
    n=len(front)
    for j in range(n):
        k=(j+1)%n
        faces.extend([(j,k,2*n+k,2*n+j),(n+j,3*n+j,3*n+k,n+k),
                      (n+j,n+k,k,j),(2*n+j,2*n+k,3*n+k,3*n+j)])
    name='Arched' if round_window else 'Segmental'
    b.add(vertices,faces,SHADOW,name+' splayed inner lining')
    shadow=Polygon(rear).union(Polygon(front)).buffer(.18)
    solid(b,shadow,frame+.17,frame+.23,SHADOW,name+' backing behind the glazing')


def study_casements(b,row,round_window,lod):
    # The shutter grid is measured in the near-axial exposure. It sits further
    # inside the building than the outward-facing brick opening.
    d=measurements()['arch_window_depth_m'];shape=Polygon(opening_outline(row,round_window,d,True))
    bars=[]
    def mark(label,coords,width):bars.append((label,[study(x,z,d)for x,z in coords],width))
    if round_window:
        for i,x in enumerate([136,176,216,257,300]):mark(f'main upright {i+1}',[(x,232),(x,119)],.079 if i!=2 else .112)
        for y,left,right,width in [(119,136,301,.079),(162,104,333,.083),(205,104,333,.041)]:mark(f'rail at source row {y}',[(left,y),(right,y)],width)
        for i,x in enumerate([175,216,257]):mark(f'fanlight bar {i+1}',[(x,119),(x,60)],.052)
    else:
        # The glass is rectangular behind the shallow brick vault. Leave dark
        # timber in the upper reveal between its head and the actual brick arch.
        limit=study(215,422,d)[1]
        solid(b,shape.intersection(box(-8,limit,8,28)),d+.015,d+.10,SHADOW,'Segmental head dark recessed soffit')
        shape=shape.intersection(box(-8.,0.,8.,limit))
        for i,x in enumerate([157,213,271]):mark(f'tall casement joint {i+1}',[(x,608),(x,420)],.093)
        for y,width in [(480,.086),(454,.050),(544,.044)]:mark(f'casement rail at row {y}',[(98,y),(333,y)],width)
        for i,x in enumerate([129,185,241,302]):mark(f'pair of transom lights {i+1}',[(x,477),(x,422)],.050)
    glazing(b,shape,'Arched upper sash' if round_window else 'Lower four-part sash',d,bars,lod)
    limits=[136,176,216,257,300] if round_window else [100,157,213,271,332]
    levels=[119,162,232] if round_window else [422,480,606]
    for j,(left,right) in enumerate(zip(limits,limits[1:]),1):
        for k,(top,bottom) in enumerate(zip(levels,levels[1:]),1):
            rectangle=guided_box((left,top,right,bottom),study,d)
            # Paired leaves have individual stepped joinery around each pane.
            outer=rectangle.buffer(-.029,join_style='mitre')
            inner=rectangle.buffer(-.070,join_style='mitre')
            solid(b,outer.difference(inner).intersection(shape),d-.049,d+.012,TIMBER,
                  f'{"Arched" if round_window else "Lower"} window leaf {j}.{k} raised bead')


def add_brick_courses(builder,face,front):
    # Keep each stretcher an individual closed solid, batched in horizontal
    # courses and colours. Clipped bricks follow the actual curves of the holes.
    pitch=.232;height=.065
    faces_box=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    batches={}
    def store(poly,y0,y1,key,rectangular):
        vertices,faces=batches.setdefault(key,([],[]));start=len(vertices)
        if rectangular:
            a,z,b,t=poly.bounds
            xy=[(a,z),(b,z),(b,t),(a,t)]
            vertices.extend((x,y,h)for y in (y0,y1) for x,h in xy)
            faces.extend(tuple(start+n for n in v)for v in faces_box);return
        poly=orient(poly,sign=1.);coords=list(poly.exterior.coords)[:-1];nn=len(coords)
        ids={p:i for i,p in enumerate(coords)}
        vertices.extend((x,y,h)for y in (y0,y1) for x,h in coords)
        for tri in constrained_delaunay_triangles(poly).geoms:
            a,b,c=[ids[p] for p in list(orient(tri,sign=1.).exterior.coords)[:3]]
            faces.extend([(start+a,start+b,start+c),(start+nn+c,start+nn+b,start+nn+a)])
        for i in range(nn):
            j=(i+1)%nn;faces.append((start+i,start+nn+i,start+nn+j,start+j))
    xmin,zmin,xmax,zmax=face.bounds
    for row in range(int(np.floor(zmin/height)),int(np.ceil(zmax/height))):
        bottom=max(zmin,row*height+.0026);top=min(zmax,(row+1)*height-.0026)
        if top<=bottom:continue
        for ix in range(-15,15):
            left=max(xmin,pitch*(ix+(row%2)*.5)+.003)
            right=min(xmax,pitch*(ix+1+(row%2)*.5)-.003)
            if right<=left:continue
            cell=box(left,bottom,right,top)
            tone=(ix*41+row*13+((ix+3)*row)%11)%len(COURSES)
            y0=front-.006-.003*(.5+.5*np.sin(ix*13.7+row*2.2))
            key=(row//16,tone)
            if face.covers(cell):store(cell,y0,front+.007,key,True);continue
            clipped=face.intersection(cell)
            parts=[clipped] if isinstance(clipped,Polygon) else getattr(clipped,'geoms',[])
            for poly in parts:
                if isinstance(poly,Polygon) and poly.area>1.e-7:store(poly,y0,front+.007,key,False)
    for (block,tone),(vertices,faces) in sorted(batches.items()):
        builder.add(vertices,faces,COURSES[tone],f'East centre hand-laid brick courses {block}.{tone+1}')


def guided_box(corners,fn,depth):
    x0,y0,x1,y1=corners
    return Polygon([fn(x0,y0,depth),fn(x1,y0,depth),fn(x1,y1,depth),fn(x0,y1,depth)])


def central_spandrel(b,depth):
    for i,(a,z) in enumerate([(102,122),(204,229),(314,336)]):
        solid(b,guided_box((a,239,z,319),study,depth),depth-.10,depth+.02,BRICK,f'Central spandrel brick pier {i+1}')
    # The two groups each have a larger pale centre and four shorter corner blocks.
    for i,x in enumerate([162,271]):
        for j,(dx,dy,w,h) in enumerate([(0,0,22,26),(-19,-17,13,13),(18,-17,13,13),(-19,17,13,13),(18,17,13,13)]):
            xx=x+dx;yy=281+dy
            solid(b,guided_box((xx-w/2,yy-h/2,xx+w/2,yy+h/2),study,depth),depth-.057,depth+.018,PALE,f'Five-stone group {i+1} block {j+1}')
    for y,xa,xb,label in [(233,92,343,'Upper arch sill'),(320,88,343,'Stone below the two square motifs'),(609,85,345,'Lower rectangular window sill')]:
        a=study(xa,y,depth);z=study(xb,y,depth);ledge(b,a[0],z[0],(a[1]+z[1])/2,depth,label)


def upper_attic(b,depth,lod):
    from east_photo_plane import pixel
    def registered(x,z,d):
        image=pixel([x/100.-3.2,.85,22.5-z/100.]);return on_wall(*image,d)[[0,2]]
    def band(coords,d):return guided_box(coords,registered,d)
    total=box(-2.83,17.13,2.77,22.07);outer=band((143,285,478,427),depth)
    solid(b,total.difference(outer),depth,1.71,PLASTER,'Recessed rendered attic with a genuine six-light opening')
    glass_depth=1.39;shape=box(outer.bounds[0]-.025,outer.bounds[1]-.025,outer.bounds[2]+.025,outer.bounds[3]+.025)
    glass_clip=band((137,315,449,430),glass_depth)
    solid(b,shape.difference(glass_clip),glass_depth-.055,glass_depth+.068,SHADOW,'Recessed attic window head and reveals')
    bars=[]
    for i,x in enumerate([175,225,283,337,391]):
        bars.append((f'vertical light divider {i+1}',[registered(x,318,glass_depth),registered(x,429,glass_depth)],.089 if i in [1,3]else .059))
    for i,y in enumerate([370,412]):bars.append((f'lower rail {i+1}',[registered(138,y,glass_depth),registered(445,y,glass_depth)],.05))
    glazing(b,glass_clip.intersection(shape),'Recessed attic ribbon window',glass_depth,bars,lod)
    sill=band((139,429,512,437),depth);ledge(b,sill.bounds[0],sill.bounds[2],sill.centroid.y,depth,'Attic sill')
    # Some brick is exposed in the original rendered apron, including the
    # narrow central pier. Model its whole section and the return under the sill.
    outline=[(145,439),(496,439),(495,472),(468,472),(457,461),(446,462),(428,479),(414,476),(412,515),(216,515),(202,482),(191,468),(176,468),(169,489),(151,490)]
    solid(b,Polygon([registered(u,v,depth)for u,v in outline]),depth-.055,depth+.040,BRICK,'Exposed brick infill below the attic sill')
    pillar=band((293,443,328,513),depth);solid(b,pillar,depth-.122,depth+.017,BRICK,'Short vertical brick pier below attic')
    for y,h,mat,name in [(51,17,STONE,'Attic upper coping'),(72,52,BRICK,'Exposed attic crown fascia'),(133,11,TILES[3],'Attic upper stepped cordon'),(211,12,BRICK,'High brick line above attic sash'),(530,13,STONE,'Continuous moulding between arch and attic')]:
        z=registered(320,y,depth)[1];thick=abs(registered(320,y+h,depth)[1]-z)
        solid(b,box(-2.83,z-thick,2.77,z),depth-.113,depth+.035,mat,name)
    for y in [58,68,129,143,219,532,549]:
        z=registered(320,y,depth)[1];solid(b,box(-2.83,z-.033,2.77,z),depth-.15,depth+.005,STONE if y<70 or y>510 else TILES[3],f'Attic masonry edge at reference row {y}')


def wing_spandrels(b,lod):
    for j,c in enumerate([175.,285.,616.,725.],1):
        def pos(x,y,depth=0.):return guide(c+x,y,depth)
        def motif(poly,front,back,mat,label):solid(b,Polygon([pos(x,y)for x,y in poly]),front,back,mat,f'Wing spandrel {j} {label}')
        motif([(-27,86),(27,86),(26.5,141),(-27,141)],-.061,.036,BRICK,'brick panel')
        for side in [-1,1]:
            x=side*23
            motif([(x-3.1,88),(x+3.1,88),(x+3.1,141),(x-3.1,141)],-.119,.012,BRICK,'pilaster left' if side<0 else 'pilaster right')
        # A square raised brick frame, two shorter returns and a triangular
        # pendant form the repeated panel visible beneath each second-storey sill.
        outer=guided_box((c-12.5,96,c+12.5,124),guide,0.)
        inner=guided_box((c-10.0,99,c+10.0,120),guide,0.)
        solid(b,outer.difference(inner),-.133,-.050,TILES[3],f'Wing spandrel {j} recessed square outline')
        for side in [-1,1]:
            x=side*7.1
            motif([(x-1.5,119),(x+1.5,119),(x+1.5,127),(x-1.5,127)],-.146,-.052,TILES[0],'paired pendant stroke')
        tri=Polygon([pos(-7.8,139),pos(0,123.6),pos(7.8,139)])
        solid(b,tri.difference(tri.buffer(-.052,join_style='mitre')),-.172,-.051,TILES[3],f'Wing spandrel {j} pointed pendant')
        # The flat arch is wider at its top and formed of distinct radiating bricks.
        n=17;marks=np.linspace(-1.,1.,n+1)
        def strip(t0,t1):return [(32.3*t0,142), (32.3*t1,142), (25.7*t1,163.7), (25.7*t0,163.7)]
        motif(strip(-1.,1.),-.08,.025,JOINT,'flat arch backing')
        for k,(a,z) in enumerate(zip(marks,marks[1:])):
            motif(strip(a+.005,z-.005),-.127-(.012 if k==n//2 else 0.),-.064,TILES[(j+3*k)%4],f'flat voussoir {k+1}')
        a,z=pos(-33.5,141),pos(33.5,141)
        ledge(b,a[0],z[0],(a[1]+z[1])/2,-.012,f'Wing spandrel {j} head')


def gables(b,lod):
    records=measurements()['gable_edges']
    for side,west,east,basewest,baseeast in [('south',-11.729,-2.83,22.31,22.46),('north',2.77,11.729,22.48,22.67)]:
        pairs=[]
        for suffix in ['left','right']:
            pts=[on_wall(*p,-.073)[[0,2]]for p in records[side+'-'+suffix]['native_edge_points']]
            X,Z=np.asarray(pts).T;pairs.append(np.polyfit(X,Z,1))
        a,b0=pairs[0];c,d=pairs[1];mid=(d-b0)/(a-c);crest=a*mid+b0
        pitch=(baseeast-basewest)/(east-west);intercept=basewest-pitch*west
        l=(intercept-b0)/(a-pitch);r=(intercept-d)/(c-pitch)
        # Cap the shoulders at the original straight wall's endpoints; the
        # field survey describes the slight asymmetry in the north/south cut.
        l=np.clip(l,west+.08,mid-.12);r=np.clip(r,mid+.12,east-.08)
        rim=[(west,basewest),(l,pitch*l+intercept),(mid,crest),(r,pitch*r+intercept),(east,baseeast)]
        shell=Polygon([(west,basewest-.21),(east,baseeast-.21),*rim[::-1]])
        solid(b,shell,-.014,.64,PLASTER,side+' rendered triangular gable and shoulders')
        cap=Polygon([*rim,*[(x,z-.065)for x,z in rim[::-1]]])
        solid(b,cap,-.073,.68,STONE,side+' thin coping on the gable skyline')
        centre_line=[(l,pitch*l+intercept-.055),(r,pitch*r+intercept-.055)]
        solid(b,profile_shape(centre_line,.117),-.052,.006,BRICK,side+' exposed red brick gable band')


def add_central_brickwork(b,lod):
    survey=measurements();depth=survey['front_face_depth_m'];rows=survey['central_window_guides']
    holes=[Polygon(opening_outline(rows[key],round_window,depth)) for key,round_window in [('arched',True),('segmental',False)]]
    face=box(-2.83,6.23,2.77,17.18).difference(unary_union(holes))
    solid(b,face,depth,depth+.050,BED,'Recessed central brick pavilion with two real arch openings')
    add_brick_courses(b,face,depth)
    for key,round_window in [('arched',True),('segmental',False)]:
        row=rows[key];ring(b,row,round_window,depth,lod)
        splayed_reveal(b,row,round_window,depth+.024,survey['arch_window_depth_m']+.04)
        study_casements(b,row,round_window,lod)
    central_spandrel(b,depth);upper_attic(b,depth,lod);wing_spandrels(b,lod);gables(b,lod)
    add_gable_dedications(b,lod)
