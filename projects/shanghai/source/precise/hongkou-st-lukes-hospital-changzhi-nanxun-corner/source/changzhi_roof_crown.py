"""The three street faces of the corner lantern and the Changzhi Road oculus pediment.

Along-face distances, height and streetward offsets are in metres. Three historical overhead images establish the rear cap silhouette.
"""
import json
from math import atan2, cos, hypot, pi, sin
from pathlib import Path

PLASTER = 'Crown | pale warm roughcast'
CAP = 'Crown | limestone cap and rake'
SOFFIT = 'Crown | stone soffit'
REVEAL = 'Crown | recessed mineral render'
SASH = 'Crown | dark green window frame'
PANE = 'Crown | slate green glazing'
INSIDE = 'Crown | shaded rear cut'

def finish(rgb, rough, metal=0.0):
    return dict(color=[((c / 255 + .055) / 1.055) ** 2.4 for c in rgb],
                roughness=rough, metallic=metal)

PALETTE = {PLASTER:finish((193,184,165),.88),CAP:finish((199,192,176),.86),
           SOFFIT:finish((151,147,134),.94),REVEAL:finish((143,139,128),.89),
           SASH:finish((59,67,63),.64),PANE:finish((85,108,112),.35,.14),
           INSIDE:finish((85,81,74),.96)}

def solid(b, vertices, faces, material, label):
    """Set outward winding after the local sections have been lifted onto a street face."""
    v6=0.
    for face in faces:
        a=vertices[face[0]]
        for k in range(1,len(face)-1):
            v=vertices[face[k]]; w=vertices[face[k+1]]
            v6+=a[0]*(v[1]*w[2]-v[2]*w[1])+a[1]*(v[2]*w[0]-v[0]*w[2])+a[2]*(v[0]*w[1]-v[1]*w[0])
    if abs(v6)<1e-10:
        raise ValueError(label+' has zero volume')
    if v6<0:
        faces=[tuple(reversed(f)) for f in faces]
    b.add(vertices,faces,material,label)

def face_basis(face):
    a, end=face['a'],face['b']
    dx,dy=end[0]-a[0],end[1]-a[1]
    length=hypot(dx,dy); tx,ty=dx/length,dy/length
    nx,ny=face['out']
    def point(s,z,offset):
        return a[0]+tx*s+nx*offset,a[1]+ty*s+ny*offset,z
    return length,point

def face_prism(b,point,shape,rear,front,mat,name):
    bottom=[point(s,z,rear) for s,z in shape]
    top=[point(s,z,front) for s,z in shape]
    n=len(shape)
    f=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    f += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    solid(b,bottom+top,f,mat,name)

def box_on_face(b,point,s0,s1,z0,z1,back,front,mat,name):
    face_prism(b,point,[(s0,z0),(s1,z0),(s1,z1),(s0,z1)],back,front,mat,name)

def flat_prism(b,xy,z0,z1,mat,tag):
    n=len(xy);verts=[(x,y,z) for z in (z0,z1) for x,y in xy]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces+=[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    solid(b,verts,faces,mat,tag)

def ring_section(b,point,outer,inner,rear,front,mat,tag):
    n=len(outer)
    verts=[point(s,z,d) for d in (rear,front) for line in (outer,inner) for s,z in line]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,i+n,j+n,j),(i+2*n,j+2*n,j+3*n,i+3*n),
                      (i,j,j+2*n,i+2*n),(i+n,i+3*n,j+3*n,j+n)])
    solid(b,verts,faces,mat,tag)

def gable(b,face,row,lod):
    _,pt=face_basis(face)
    left,peak,right=row['triangle'];cx,cz,r=row['oculus']
    back,front=row['face_offset']-.29,row['face_offset']
    steps=40 if lod else 80
    corner_angles=[atan2(z-cz,s-cx)%(2*pi) for s,z in (left,peak,right)]
    angles=sorted({round(a,10) for a in corner_angles+[2*pi*i/steps for i in range(steps)]})
    outer=[];inner=[]
    for a in angles:
        dx,dz=cos(a),sin(a);hits=[]
        for p,q in ((left,peak),(peak,right),(right,left)):
            vx,vz=q[0]-p[0],q[1]-p[1];det=dx*vz-dz*vx
            if abs(det)<1e-10:continue
            t=((p[0]-cx)*vz-(p[1]-cz)*vx)/det
            frac=((p[0]-cx)*dz-(p[1]-cz)*dx)/det
            if t>0 and -.000001<=frac<=1.000001:hits.append(t)
        t=min(hits);outer.append((cx+t*dx,cz+t*dz));inner.append((cx+r*dx,cz+r*dz))
    ring_section(b,pt,outer,inner,back,front,PLASTER,'Pediment | perforated tympanum')
    def circle(rad):
        return [(cx+rad*cos(a),cz+rad*sin(a)) for a in angles]
    ring_section(b,pt,circle(r+.045),circle(r-.018),front-.155,front+.017,CAP,'Pediment | inner stone arris')
    ring_section(b,pt,circle(r-.018),circle(r-.054),front-.197,front-.148,SASH,'Pediment | recessed round frame')
    face_prism(b,pt,circle(r-.052),front-.218,front-.198,PANE,'Pediment | round glazing')
    # The upper lip stands forward of the oculus plane. The recessed grey panel
    # casts a broad raking shadow visible from the other end of Changzhi Road.
    width=row['rake_width']; projection=row['rake_projection']
    profile=[(0,.90),(.15,1.),(.30,1.),(.31,.76),(.54,.72),(.63,.43),(.83,.42),(1.,.12)]
    for side,(a,bp) in enumerate(((left,peak),(peak,right)),1):
        for k,((drop0,depth0),(drop1,depth1)) in enumerate(zip(profile,profile[1:]),1):
            shape=[(a[0],a[1]-width*drop0),(bp[0],bp[1]-width*drop0),
                   (bp[0],bp[1]-width*drop1),(a[0],a[1]-width*drop1)]
            verts=[pt(x,z,front-.012) for x,z in shape]
            verts.extend(pt(x,z,front+projection*d) for (x,z),d in zip(shape,(depth0,depth0,depth1,depth1)))
            faces=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
            solid(b,verts,faces,CAP if k not in (4,6) else SOFFIT,f'Pediment | rake {side} course {k}')
    key_w=r*.27; low=cz+r-.020
    face_prism(b,pt,[(cx-key_w*.65,low),(cx+key_w*.65,low),(cx+key_w,low+r*.36),(cx-key_w,low+r*.36)],front-.02,front+.045,CAP,'Pediment | oculus keystone')

def offset_vertices(faces,distance):
    out=[]
    for i in range(len(faces)+1):
        f=faces[min(i,len(faces)-1)]
        p=f['a'] if i<len(faces) else f['b']
        n=f['out'];m=faces[max(0,i-1)]['out']
        den=1+n[0]*m[0]+n[1]*m[1]
        out.append((p[0]+distance*(n[0]+m[0])/den,p[1]+distance*(n[1]+m[1])/den))
    return out

def expand_polygon(vertices, distance):
    """Offset the documented eight-sided crown, intersecting adjacent cap edges."""
    normals=[]
    for i,a in enumerate(vertices):
        b=vertices[(i+1)%len(vertices)]
        dx,dy=b[0]-a[0],b[1]-a[1]
        length=hypot(dx,dy)
        normals.append((dy/length,-dx/length))
    result=[]
    for i,(x,y) in enumerate(vertices):
        n,m=normals[i-1],normals[i]
        step=distance/(1+n[0]*m[0]+n[1]*m[1])
        result.append((x+step*(n[0]+m[0]),y+step*(n[1]+m[1])))
    return result


def small_sash(b,point,length,window,base,head,offset,index):
    u0,u1,z0,z1=window
    u0*=length;u1*=length
    tag='Lantern | '+('Changzhi' if index==0 else 'Nanxun')
    # Dark frame edges lie 4–5 pixels inside the measured mouths in the district photograph.
    t=.051; back=offset-.155; front=offset-.12
    for label,ds,de,dz,dh in [('left jamb',u0,u0+t,z0,z1),('right jamb',u1-t,u1,z0,z1),('lower rail',u0+t,u1-t,z0,z0+t),('upper rail',u0+t,u1-t,z1-t,z1)]:
        box_on_face(b,point,ds,de,dz,dh,back,front,SASH,tag+' '+label)
    box_on_face(b,point,u0+t,u1-t,z0+t,z1-t,back-.017,back-.004,PANE,tag+' recessed light')
    if index==2:
        x=(u0+u1)/2
        box_on_face(b,point,x-.016,x+.016,z0+t,z1-t,back+.005,front-.013,SASH,tag+' centre mullion')
        for k in (1,2):
            z=z0+(z1-z0)*k/3
            box_on_face(b,point,u0+t,u1-t,z-.014,z+.014,front-.014,front-.006,SASH,tag+' glazing bar '+str(k))
    box_on_face(b,point,u0-.085,u1+.085,z0-.080,z0-.014,offset-.023,offset+.066,CAP,tag+' small sill')

def add_crown(b,lod,layout):
    for name,value in PALETTE.items():b.palette.setdefault(name,value)
    config=layout.get('roof_crown')
    if config is None:
        config=json.loads((Path(__file__).resolve().parents[1]/'measurements/roof-crown-geometry.json').read_text())
    by_id={f['id']:f for f in layout['faces']}
    gable(b,by_id['changzhi'],config['gable'],lod)
    fs=[by_id['corner-changzhi'],by_id['corner-center'],by_id['corner-nanxun']]
    t=config['lantern']; offset=t['face_offset']; z0=t['foot_z']; z1=t['head_z']
    if 'face_vertices' in t:
        # The upstairs drum has its own narrower side faces and deeper front,
        # measured against the three lower piers in two separate photographs.
        upper=[]
        for f,a,end in zip(fs,t['face_vertices'],t['face_vertices'][1:]):
            dx=end[0]-a[0];dy=end[1]-a[1];length=hypot(dx,dy)
            n=[dy/length,-dx/length]
            if n[0]*f['out'][0]+n[1]*f['out'][1]<0:n=[-n[0],-n[1]]
            upper.append(dict(id=f['id'],a=a,b=end,out=n))
        fs=upper
    pts=offset_vertices(fs,offset)
    for i,face in enumerate(fs):
        f={**face,'a':pts[i],'b':pts[i+1]};length,pt=face_basis(f)
        mat=PLASTER; dep=-.28
        if i==1:
            box_on_face(b,pt,0,length,z0,z1,dep,0,mat,'Lantern | plain centre facet')
            continue
        win=t['openings'][f['id']];u0,u1,lo,hi=win
        for part,x,y,z,h in [('pier left',0,u0*length,z0,z1),('pier right',u1*length,length,z0,z1),('sill panel',u0*length,u1*length,z0,lo),('head panel',u0*length,u1*length,hi,z1)]:
            box_on_face(b,pt,x,y,z,h,dep,0,mat,'Lantern | side %d %s'%(i+1,part))
        small_sash(b,pt,length,win,z0,z1,0,i)
    # The three vertical street faces fix the front outline in two photographs.
    # Independent 2019, 2021 and 2025 overhead views bound the rear cap edges.
    # Back face fittings cannot be distinguished at this sampling distance.
    outline=list(pts)+t['roofward_vertices']
    for j in range(3,len(outline)):
        a=outline[j];end=outline[(j+1)%len(outline)]
        dx,dy=end[0]-a[0],end[1]-a[1]
        length=hypot(dx,dy)
        face={'a':a,'b':end,'out':[dy/length,-dx/length]}
        _,point=face_basis(face)
        box_on_face(b,point,0,length,z0,z1,-.11,0,PLASTER,'Lantern | rear facet '+str(j-2))
    flat_prism(b,expand_polygon(outline,.024),z0-.082,z0+.001,SOFFIT,'Lantern | bed on pierced lower drum')
    for name,step,low,high,mat in [('lower drip',.065,-.105,-.053,SOFFIT),('stepped fascia',.100,-.053,.042,CAP),('top weathering',.122,.042,.105,CAP)]:
        flat_prism(b,expand_polygon(outline,step),z1+low,z1+high,mat,'Lantern | '+name)



def gable_street_span(layout=None):
    """Along Changzhi Road return the two verge feet, base height and oculus."""
    geom=(layout or {}).get('roof_crown')
    if geom is None:
        geom=json.loads((Path(__file__).resolve().parents[1]/'measurements/roof-crown-geometry.json').read_text())
    g=geom['gable']; left,_,right=g['triangle']
    return dict(s0=left[0],s1=right[0],base_z=min(left[1],right[1]),oculus=g['oculus'])
