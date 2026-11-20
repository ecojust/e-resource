"""Build the street-visible two bays and private iron gate of Yicun House 2."""
import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from photo_architecture import Facade

P = json.loads((HERE / 'parameters.json').read_bytes())
MATERIALS = {
    'warm cream stucco': (.80,.761,.664), 'pale raised plaster': (.86,.811,.708),
    'worn stone slip': (.63,.588,.512), 'deep window reveal': (.18,.159,.134),
    'blue gray inner glass': (.23,.304,.316), 'dark bronze sash': (.193,.186,.157),
    'aged cream turned stone': (.759,.718,.614), 'shaded eave timber': (.255,.174,.126),
    'umber roof tile': (.46,.204,.127), 'weathered terracotta': (.585,.300,.193),
    'ridge terracotta': (.631,.351,.228), 'dark rainwater pipe': (.185,.170,.146),
    'bronze black iron': (.151,.154,.133), 'weathered bronze trim': (.355,.311,.207),
    'wired lamp glass': (.710,.701,.517), 'gate pier plinth': (.512,.495,.442),
}
PALETTE = {k:dict(color=list(v),roughness=.35 if 'glass' in k else .76,
                  metallic=.42 if any(w in k for w in ('iron','bronze','pipe')) else .015)
           for k,v in MATERIALS.items()}
META = {
 'id':P['id'],'name':'逸村2号淮海中路园侧立面','status':'photo-informed-exterior',
 'viewer_page':'yicun-no2-street-front.html','audit_directory':'data/audit/yicun-no2-street-front-v1/',
 'scope':'Garden-side elevation of Yicun No. 2, cross-gabled red roof and its own iron gate. Front architectural details follow the 2015 photograph and public road panoramas. Rear elevations are a simplified envelope.',
 'model_scope_zh':'逸村2号朝淮海中路的园侧三层窗墙、前山墙浅弧、圆窗、螺旋窗柱、分段红瓦屋面与本户花铁门。约1942年建造，模型依据2013、2015及2020年所见外观。屋后与侧墙上未见的细部简化。公共弄门、对面1号及内侧其他单体分列。',
 'coordinate_convention':'Local glTF X follows the garden front northeast at 53.5 degrees true, Y up and +Z faces southeast.',
 'map_reference_license':'OpenStreetMap and Overture Maps, ODbL-1.0. Reconstructed local geometry from the published footprint and multiple visual references.',
 'interiors_modeled':False,
}
RING = np.array(P['source_local_outline_m'])
EAVE = P['estimated_main_eave_z_m']


def twisted_shaft(face,u,z0,z1,radius,lod,label):
    """A twisted column with three continuous helical flutes and square capital."""
    sides=12 if lod else 22
    levels=19 if lod else 42
    verts=[]
    for i in range(levels+1):
        v=i/levels
        for j in range(sides):
            ang=math.tau*j/sides
            rad=radius*(1+.145*math.cos(3*ang-v*math.tau*2.5))
            verts.append(face.point(u+rad*math.cos(ang),z0+(z1-z0)*v,-.025+rad*math.sin(ang)))
    faces=[tuple(range(sides)),tuple(reversed(range(levels*sides,(levels+1)*sides)))]
    for i in range(levels):
        for j in range(sides):
            j2=(j+1)%sides
            faces.append((i*sides+j,(i+1)*sides+j,(i+1)*sides+j2,i*sides+j2))
    face.builder.add(verts,faces,'aged cream turned stone',face.label+'/'+label+' spiral stone')
    for z,w,h in [(z0+.033,radius*2.52,.065),(z1-.045,radius*2.64,.090)]:
        face.box(u,z,w,h,.26,-.035,'pale raised plaster',label+' capital and foot')


def lights(face,u,z0,z1,w,count,lod,label,shafts=True):
    outline=box(u-w/2,z0,u+w/2,z1)
    face.prism(outline,-.24,-.22,'blue gray inner glass',label+' glazing')
    inner=outline.buffer(-.055,join_style=2)
    bars=[box(u-w/2,z0+(z1-z0)*.74,u+w/2,z0+(z1-z0)*.74+.032)]
    step=w/count
    for i in range(count):
        x=u-w/2+(i+.50)*step
        if not lod:bars.append(box(x-.014,z0,x+.014,z1))
        if i:
            x=u-w/2+i*step
            bars.append(box(x-.030,z0,x+.030,z1))
            if shafts:twisted_shaft(face,x,z0+.06,z1-.055,.090 if w>1.6 else .064,lod,label)
    face.prism(outline.difference(inner.difference(unary_union(bars))),-.16,-.105,'dark bronze sash',label+' sash')
    face.box(u,z0-.055,w+.17,.11,.285,.018,'worn stone slip',label+' sill')


def semi_recess(face,u,z,rad,lod):
    # The visible plaster half-round is filled with stucco above the separate window.
    steps=16 if lod else 44
    arc=np.linspace(math.pi,0,steps+1)
    pts=[(u+rad*math.cos(t),z+rad*math.sin(t))for t in arc]
    inner=Polygon([(u-rad,z-.008),*pts,(u+rad,z-.008)]).buffer(0)
    face.prism(inner,-.085,-.065,'warm cream stucco','shallow half-round backing')
    face.builder.tube([face.point(x,zz,.013)for x,zz in pts],.034,'pale raised plaster',5 if lod else 9,face.label+'/half-round moulding')
    return inner


def tile_canopy(face,u,base,width,span,lod):
    z=base+.06
    # Cap and little individual cover tiles project over the iron balcony.
    face.prism(box(u-width/2,z-.16,u+width/2,z-.10),-.02,.34,'shaded eave timber','canopy underside')
    n=max(5,round(width/(.19 if lod else .115)))
    for v in np.linspace(u-width/2+.05,u+width/2-.05,n):
        face.builder.tube([face.point(v,z,-.04),face.point(v,z-.12,span)],.059,'ridge terracotta',6 if lod else 10,face.label+'/canopy tile rolls')


def balcony(face,u,z,width,lod):
    face.box(u,z-.075,width,.17,.63,.24,'pale raised plaster','garden balcony slab')
    for level in (z+.17,z+.86):
        face.line((u-width/2,level,.50),(u+width/2,level,.50),.023,'bronze black iron',5 if lod else 8,'balcony rails')
    for x in np.linspace(u-width/2,u+width/2,10):
        face.line((x,z+.035,.50),(x,z+.86,.50),.015,'bronze black iron',5 if lod else 7,'balcony upright')
    for end in (-1,1):
        for level in (z+.17,z+.86):
            x=u+end*width/2;face.line((x,level,.02),(x,level,.50),.019,'bronze black iron',5 if lod else 7,'balcony ends')
    if not lod:
        for v in np.linspace(u-width*.39,u+width*.39,4):
            arc=np.linspace(0,math.tau,21)
            face.builder.tube([face.point(v+.125*math.cos(t),z+.34+.12*math.sin(t),.498)for t in arc],.012,'bronze black iron',5,face.label+'/balcony loops')


def facade_pair(b,lod):
    gable=Facade(b,RING[2],RING[1],'Street gable')
    half=gable.length/2;top=P['front_gable_crown_m'];c=0
    contour=Polygon([(-half,.16),(half,.16),(half,EAVE),(0,top),(-half,EAVE)])
    opening_rows=[(1.13,3.28,2.24),(4.69,6.29,2.35),(8.29,9.82,2.18)]
    holes=[box(c-w/2,z0,c+w/2,z1)for z0,z1,w in opening_rows]
    small=box(-.058,11.06,.058,11.30)
    arc=semi_recess(gable,c,9.88,1.04,lod)
    gable.wall(.16,top,[*holes,small,arc],.22,'warm cream stucco',contour)
    gable.prism(small,-.19,-.14,'deep window reveal','attic vent')
    for i,(z0,z1,w)in enumerate(opening_rows):
        lights(gable,c,z0,z1,w,3,lod,'triplet '+str(i+1))
    for z,w,h,depth in [(4.57,2.78,.135,.46),(4.45,2.61,.12,.375),(4.34,2.41,.11,.275),(4.26,2.21,.085,.21)]:
        gable.box(0,z,w,h,depth,.07,'worn stone slip','stepped projecting window stool')
    for z in (3.55,6.75,9.84):
        gable.box(0,z,gable.length,.033,.037,.005,'worn stone slip','render divider')
    for z in [6.44]:
        for u in np.linspace(-half+.11,half-.11,25):
            if abs(u)<1.21:continue
            gable.box(u,z,.11,.13,.115,.038,'pale raised plaster','small plaster dentils')
    gable.line((-half,EAVE,.02),(0,top,.02),.048,'worn stone slip',5 if lod else 8,'gable raking edge')
    gable.line((0,top,.02),(half,EAVE,.02),.048,'worn stone slip',5 if lod else 8,'gable raking edge')
    recess=Facade(b,RING[4],RING[3],'Recessed balcony bay')
    strips=[(-1.08,1.03,3.12,1.75),(-1.08,4.68,6.12,1.73),(-1.09,8.10,9.34,1.76)]
    stair=box(1.17,4.87,1.97,6.17);dial=Point(1.70,8.66).buffer(.414,quad_segs=15 if lod else 32)
    recess.wall(.16,EAVE,[*(box(u-w/2,z0,u+w/2,z1)for u,z0,z1,w in strips),stair,dial],.22,'warm cream stucco')
    for i,(u,z0,z1,w)in enumerate(strips):lights(recess,u,z0,z1,w,3,lod,'recess triplet '+str(i+1))
    lights(recess,1.57,4.87,6.17,.80,1,lod,'small stair window',False)
    recess.prism(dial,-.20,-.176,'blue gray inner glass','round window glass')
    recess.prism(dial.difference(dial.buffer(-.070)),-.135,-.072,'dark bronze sash','round bronze frame')
    recess.prism(dial.intersection(box(1.687,8.18,1.713,9.09)),-.12,-.10,'dark bronze sash','round center sash')
    tile_canopy(recess,-1.08,6.58,2.18,.43,lod)
    balcony(recess,-1.08,4.61,2.11,lod)
    for z in (3.55,6.75,9.84):
        recess.box(0,z,recess.length,.032,.035,.004,'worn stone slip','render divider')
    return gable,recess


def roof_plane(b,shape,elevation,run,lod,label):
    if shape.is_empty:
        return
    for tri in constrained_delaunay_triangles(shape).geoms:
        pts=list(tri.exterior.coords)[:-1]
        if not tri.exterior.is_ccw:pts.reverse()
        b.add([(x,y,elevation(x,y)) for x,y in pts],[(0,1,2)],'umber roof tile',label+'/continuous plane')
    xmin,ymin,xmax,ymax=shape.bounds
    major=run==0
    low,high=(xmin,xmax) if major else (ymin,ymax)
    tiles=max(3,round((high-low)/(.33 if lod else .164)))
    for idx in range(tiles):
        at=low+(idx+.5)*(high-low)/tiles
        line=LineString([(at,ymin-1),(at,ymax+1)] if major else [(xmin-1,at),(xmax+1,at)])
        kept=line.intersection(shape)
        segments=kept.geoms if kept.geom_type=='MultiLineString' else [kept]
        for seg in segments:
            if seg.geom_type!='LineString' or seg.length<.10:continue
            p0,p1=seg.coords[0],seg.coords[-1]
            points=[(x,y,elevation(x,y)+.028) for x,y in (p0,p1)]
            b.tube(points,.034 if lod else .044,'weathered terracotta' if idx%3 else 'ridge terracotta',
                   5 if lod else 7,label+'/rows of curved cover tile')
    for p,q in zip(list(shape.exterior.coords),list(shape.exterior.coords)[1:]):
        if math.dist(p,q)>.04:
            b.tube([(*p,elevation(*p)),(*q,elevation(*q))],.050,'ridge terracotta',6 if lod else 8,label+'/ridge and verge rolls')


def roofs(b,lod):
    # The photographed forward gable projects past the cross ridge of the recessed wing.
    outline=Polygon(RING).buffer(.14,join_style=2)
    join=-.22;ridge=2.43;y_ridge=.58
    east=outline.intersection(box(join,-20,20,20))
    west=outline.intersection(box(-20,-20,join,20))
    high_gable=P['front_gable_crown_m']
    east_z=lambda x,y:high_gable-abs(x-ridge)*.61
    left_z=lambda x,y:EAVE+1.54-abs(y-y_ridge)*.247
    for label,region,func,run in [
      ('Gable west slope',east.intersection(box(-20,-20,ridge,20)),east_z,1),
      ('Gable east slope',east.intersection(box(ridge,-20,20,20)),east_z,1),
      ('West wing street slope',west.intersection(box(-20,-20,20,y_ridge)),left_z,0),
      ('West wing garden slope',west.intersection(box(-20,y_ridge,20,20)),left_z,0),
    ]:roof_plane(b,region,func,run,lod,label)
    for i,(q,p) in enumerate(zip(RING,np.roll(RING,-1,axis=0))):
        if i in (1,3):continue
        a,c=p,q
        face=Facade(b,a,c,'Side and rear '+str(i))
        split=[0.,1.]
        for n,val in ((0,join),(0,ridge),(1,y_ridge)):
            if abs(c[n]-a[n])>.001:
                t=(val-a[n])/(c[n]-a[n])
                if .0001<t<.9999:split.append(t)
        split=sorted(set(split))
        for k,(t0,t1)in enumerate(zip(split,split[1:])):
            A=a+(c-a)*t0;C=a+(c-a)*t1;func=east_z if (A[0]+C[0])/2>join else left_z
            z1,z2=func(*A),func(*C)
            if min(z1,z2)<9.:raise ValueError('Unsupported eave height')
            u0=(t0-.5)*face.length;u1=(t1-.5)*face.length
            shape=Polygon([(u0,.16),(u1,.16),(u1,z2),(u0,z1)])
            face.prism(shape,-.20,0,'warm cream stucco','side or rear envelope')
    # Close the step where independently supported roof sections meet at the ridge.
    section=LineString([(join,-16),(join,18)]).intersection(outline)
    if section.geom_type=='LineString':
        y0=section.bounds[1];y1=section.bounds[3];z_e=east_z(join,0)
        pts=sorted({y0,y_ridge,y1,*[v for v in (y_ridge-(EAVE+1.54-z_e)/.247,y_ridge+(EAVE+1.54-z_e)/.247)if y0<v<y1]})
        for lo,hi in zip(pts,pts[1:]):
            b.add([(join,lo,z_e),(join,hi,z_e),(join,hi,left_z(join,hi)),(join,lo,left_z(join,lo))],[(0,1,2,3)],'warm cream stucco','Roof junction/support wall')
    # Two chimney silhouettes appear in the 2015 and 2020 photographs.
    for x,y,z,label in [(-5.63,-.10,12.49,'western chimney'),(4.14,1.97,12.78,'eastern chimney')]:
        b.box((x,y,(10.85+z)/2),(.40,.58,z-10.85),'warm cream stucco',label=label+'/shaft')
        face=Facade(b,(x-.20,y-.292),(x+.20,y-.292),label)
        small=box(-.056,z-.25,.056,z-.105)
        face.prism(small,.006,.014,'deep window reveal','dark flue opening')
        b.box((x,y,z+.038),(.47,.66,.076),'worn stone slip',label=label+'/cap')
    return outline


def scroll(face,u,z,rx,rz,hand,lod,label):
    # Forged scroll with an open tip, installed on the flat exterior of the iron leaf.
    count=12 if lod else 27
    t=np.linspace(.15,math.tau*1.11,count)
    rad=np.linspace(1,.15,count)
    pts=[face.point(u+hand*rx*rr*math.cos(a),z+rz*rr*math.sin(a),.099)for a,rr in zip(t,rad)]
    face.builder.tube(pts,.014 if lod else .019,'weathered bronze trim',5 if lod else 7,face.label+'/'+label)


def private_gate(b,lod):
    face=Facade(b,*P['private_gate_ends_m'],'No. 2 private garden gate')
    half=face.length/2
    width=.43;inside=half-width*.51
    for u in (-half,half):
        face.box(u,1.085,width,2.17,.43,0,'warm cream stucco','gateposts')
        face.box(u,.142,.47,.284,.48,0,'gate pier plinth','base blocks')
        for dz,w,h in [(2.15,.49,.08),(2.29,.57,.105),(2.369,.61,.06)]:
            face.box(u,dz,w,h,w,0,'worn stone slip','square caps')
        for k in (-1,0,1):
            face.box(u+k*.105,2.217,.052,.068,.028,.243,'deep window reveal','pier cap rectangular recesses')
        # Shallow twisted plaster moulding on the street side of both documented posts.
        if not lod:
            for q in np.linspace(.36,1.94,11):
                face.line((u-.052,q,.218),(u+.032,q+.086,.222),.014,'aged cream turned stone',6,'rope pier decoration')
        b.lathe(face.point(u,0,0)[:2],[(2.39,.09),(2.47,.054),(2.50,.082),(2.75,.123),(2.82,.085)],
                'wired lamp glass',6,label=face.label+'/lantern')
        b.lathe(face.point(u,0,0)[:2],[(2.74,.129),(2.82,.138),(2.94,.045),(2.98,.019)],
                'bronze black iron',6,label=face.label+'/lantern roof')
    def crown(u):return 2.08+.45*(1-(abs(u)/inside)**1.52)
    for hand in (-1,1):
        lo,hi=sorted([hand*.018,hand*(inside-.015)])
        xs=np.linspace(lo,hi,13 if lod else 27)
        poly=Polygon([(lo,.095),(hi,.095),*[(x,crown(x))for x in reversed(xs)]])
        face.prism(poly,-.034,.035,'bronze black iron','dark iron leaf')
        for u in np.linspace(lo+.07,hi-.07,8 if lod else 12):
            face.line((u,.16,.047),(u,crown(u)-.04,.047),.013,'weathered bronze trim',4 if lod else 7,'upright bars')
        for z in (.18,.64,1.36):
            face.box((hi+lo)/2,z,hi-lo,.031,.046,.056,'weathered bronze trim','gate horizontal bands')
        face.builder.tube([face.point(x,crown(x)+.027,.025)for x in xs],.042,'bronze black iron',6 if lod else 9,face.label+'/curved top rail')
        for u in np.linspace(lo+.17,hi-.17,4):
            scroll(face,u,.44,.14,.16,hand,lod,'lower panel scrolls')
            scroll(face,u,1.46,.135,.14,-hand,lod,'upper panel scrolls')
        for u in np.linspace(lo+.16,hi-.16,3):
            scroll(face,u,crown(u)+.105,.145,.12,hand,lod,'crest scrolls')
    for hand in (-1,1):
        scroll(face,hand*.10,2.69,.145,.16,hand,lod,'center crest')
    return face


def assemble(b,lod):
    b.plan_prism(Polygon(RING),0,.17,'gate pier plinth','House/registered footprint plinth')
    facade_pair(b,lod)
    roofs(b,lod)
    private_gate(b,lod)


if __name__=='__main__':
    from final_preview import package
    package(build,HERE,META,PALETTE,assemble)
