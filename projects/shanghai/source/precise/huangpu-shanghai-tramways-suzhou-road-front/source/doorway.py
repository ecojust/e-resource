"""Compose the three photographed stone shafts, Ionic scrolls and jointed entrance arch."""
import json
from pathlib import Path

import numpy as np
from photo_plane import pixel, position

DATA = Path(__file__).resolve().parents[1] / 'measurements/entrance.json'
SHAFT = 'Entrance pale limestone'
CUT = 'Recessed arch masonry'
CAPITAL = 'Russet column capitals'
BAND = 'Capital moulding edges'
KEY = 'Russet arch key'

def pigment(rgb):
    s = np.array(rgb, dtype=float) / 255
    return dict(color=np.where(s <= .04045, s / 12.92, ((s+.055)/1.055)**2.4).tolist(),
                roughness=.86, metallic=0.)

PALETTE = {SHAFT:pigment([173,162,133]), CUT:pigment([147,139,117]),
           CAPITAL:pigment([126,81,65]), BAND:pigment([154,108,86]), KEY:pigment([116,76,59])}

def surface(builder, vertices, faces, material, label):
    v=np.asarray(vertices,dtype=float)
    # A closed polyhedron has positive signed volume for outward face winding.
    volume=sum(np.dot(v[f[0]],np.cross(v[f[i]],v[f[i+1]]))
               for f in faces for i in range(1,len(f)-1))
    builder.add(v,[list(reversed(f)) for f in faces] if volume<0 else faces,material,label)

def rings(builder, axis, profile, n, material, label):
    vertices=[]
    for z,r in profile:
        for a in np.arange(n)*2*np.pi/n:
            vertices.append([axis[0]+r*np.cos(a),axis[1]+r*np.sin(a),z])
    faces=[list(reversed(range(n)))]
    for k in range(len(profile)-1):
        for i in range(n):
            j=(i+1)%n
            faces.append([k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i])
    faces.append(list(range((len(profile)-1)*n,len(profile)*n)))
    surface(builder,vertices,faces,material,label)

def prism(builder,outline,front,back,material,label):
    # The same X/Z outline continues through the arch thickness.
    coords=np.asarray(outline)
    vertices=[[x,y,z] for y in [front,back] for x,z in coords]
    n=len(coords)
    faces=[list(range(n)),list(reversed(range(n,2*n)))]
    faces.extend([[i,n+i,n+(i+1)%n,(i+1)%n]for i in range(n)])
    surface(builder,vertices,faces,material,label)

def xz(uv,depth):return position(*uv,depth)[[0,2]]

def shaft_radius(axis, z, u1, u2):
    angles=np.arange(72)*2*np.pi/72
    low,high=.06,.48
    for _ in range(12):
        radius=(low+high)*.5
        values=[pixel((axis[0]+radius*np.cos(t),axis[1]+radius*np.sin(t),z))[0]for t in angles]
        if max(values)-min(values)<u2-u1:low=radius
        else: high=radius
    return (low+high)*.5

def make_column(b,c,lod):
    k=c['id']; depth=c['axis_y_estimate_m']
    left,right=c['shaft_edges'];centre=(np.array(left)+right)*.5
    cx,_,zh=position(*centre,depth)
    radius=shaft_radius([cx,depth],zh,left[0],right[0])
    _,_,top=position(*c['neck'],depth)
    _,_,base=position(*c['visible_base'],depth)
    n=16 if lod else 32
    rings(b,[cx,depth],[(base,radius*1.04),(base+.055,radius*1.10),(base+.09,radius),
                        (top-.12,radius*.90),(top-.07,radius*.93),(top-.018,radius*.94),
                        (top,radius*.92)],n,SHAFT,f'{k} smooth limestone shaft and basal arris')
    cz=top+.13
    rings(b,[cx,depth],[(top-.012,radius*.97),(top+.02,radius*1.03),
                        (top+.045,radius*.99),(cz,radius*1.11),(cz+.10,radius*1.30),
                        (cz+.14,radius*1.32)],n,CAPITAL,f'{k} capital bell and stepped neck')
    dims=radius*1.37
    block=[[cx-dims,cz+.122],[cx+dims,cz+.122],[cx+dims,cz+.174],[cx-dims,cz+.174]]
    prism(b,block,depth-dims,depth+dims,CAPITAL,f'{k} raised abacus')
    for index,(u,v,rpx) in enumerate(c['volute_centres_and_upright_radii']):
        d=depth-radius*1.08
        vx,vz=xz([u,v],d)
        delta=xz([u+rpx,v],d)-xz([u-rpx,v],d)
        r=.5*np.linalg.norm(delta)
        path=[]
        for i,t in enumerate(np.linspace(0,2*np.pi*1.28,15 if lod else 31)):
            # A high outer return turns inwards to the raised central eye.
            rr=r*(1-.83*i/(14 if lod else 30))
            path.append([vx+(-1 if index else 1)*rr*np.cos(t+.8),d-.014,vz+rr*np.sin(t+.8)])
        b.tube(path,max(.009,.155*r),BAND,5 if lod else 8,f'{k} volute {index+1} raised spiral')


def add_bearing_and_corbels(b,lod,d):
    rows=d['bearing_header_and_corbels']
    def solid(points,front,back,material,label):
        prism(b,[xz(q,front)for q in points],front,back,material,label)
    front=rows['front_depth_estimates_m']['header']
    solid(rows['header_outer'],front,.045,SHAFT,'Upper limestone bearing across all three Ionic capitals')
    solid(rows['upper_step'],front-.035,front+.018,SHAFT,'Upper bearing outer moulded arris')
    solid(rows['lower_shadow_line'],front-.018,front+.016,CUT,'Lower edge of projecting entrance bearing')
    outer=rows['panel_outer']
    inner=rows['panel_inner']
    for i in range(4):
        k=(i+1)%4
        solid([outer[i],outer[k],inner[k],inner[i]],-.46,front+.004,SHAFT,'Raised margin to blank inset limestone panel')
    # Solid stone cores close the light visible behind the photographed spirals.
    # They reach the underside of the entrance bearing from each existing capital.
    edges=np.array([xz(point,front)for point in rows['header_outer']])
    left,right=edges[3],edges[2]
    for col in d['columns']:
        depth=col['axis_y_estimate_m']
        mid=np.mean(col['shaft_edges'],axis=0)
        cx,_,zz=position(*mid,depth)
        rad=shaft_radius((cx,depth),zz,*[edge[0] for edge in col['shaft_edges']])
        neck=position(*col['neck'],depth)[2]
        volute_plane=depth-rad*1.08
        vus=[(xz([u,v],volute_plane),.5*np.linalg.norm(xz([u+r,v],volute_plane)-xz([u-r,v],volute_plane))) for u,v,r in col['volute_centres_and_upright_radii']]
        lo=min(q[0][0]-q[1]*.92 for q in vus)
        hi=max(q[0][0]+q[1]*.92 for q in vus)
        top_at=lambda x:left[1]+(right[1]-left[1])*(x-left[0])/(right[0]-left[0])+.008
        z0=min(q[0][1]-.58*q[1]for q in vus)
        core=[(cx-.98*rad,neck+.11),(cx+.98*rad,neck+.11),(hi,z0),(hi,top_at(hi)),(lo,top_at(lo)),(lo,z0)]
        prism(b,core,volute_plane+.025,depth+.96*rad,CAPITAL,col['id']+' solid carved capital body')
        strip=[(lo-.012,top_at(lo)-.050),(hi+.012,top_at(hi)-.050),(hi+.018,top_at(hi)),(lo-.018,top_at(lo))]
        prism(b,strip,volute_plane-.019,depth+1.02*rad,BAND,col['id']+' square bearing moulding')
        for k,(center,r) in enumerate(vus):
            count=12 if lod else 26
            poly=[[center[0]+r*.91*np.cos(a),center[1]+r*.91*np.sin(a)]for a in np.arange(count)*2*np.pi/count]
            prism(b,poly,volute_plane+.004,volute_plane+.065,CAPITAL,col['id']+f' stone backing for volute {k+1}')
    for row in rows['end_blocks']:
        name=row['name']
        solid(row['outline'],-.273,.035,CAPITAL,name+' upright russet end console')
        solid(row['far_arris'],-.301,-.266,CAPITAL,name+' turned outer edge of console')
        for key,rkey,direction in [('top_eye','upper_radius_px',1),('lower_eye','lower_radius_px',-1)]:
            u,v=row[key];rpx=row[rkey];fixed=-.303
            x,z=xz((u,v),fixed);r=np.linalg.norm(xz((u+rpx,v),fixed)-xz((u-rpx,v),fixed))*.5
            count=12 if lod else 26
            core=[(x+r*np.cos(a),z+r*np.sin(a))for a in np.arange(count)*2*np.pi/count]
            prism(b,core,fixed,-.258,CAPITAL,name+' '+key+' stone eye')
            path=[]
            for i,t in enumerate(np.linspace(0,2*np.pi*1.34,count)):
                rr=r*(1-.83*i/(count-1))
                path.append([x+rr*np.cos(t*.98+.5)*direction,fixed-.013,z+rr*np.sin(t*.98+.5)])
            b.tube(path,.014 if lod else .017,BAND,5 if lod else 8,name+' '+key+' curved return')

def add_doorway(b,lod):
    d=json.loads(DATA.read_text())
    for c in d['columns']:make_column(b,c,bool(lod))
    add_bearing_and_corbels(b,bool(lod),d)
    front=d['front_arch_face_y_m']
    back=d['visible_arch_return_y_m']
    inner=np.array([xz(q,front)for q in d['arch_inner']])
    outer=np.array([xz(q,front)for q in d['arch_outer']])
    for i in range(len(inner)-1):
        if i in (5,6):continue  # concealed by the russet projecting keystone
        gap=.019
        qa=inner[i]*(1-gap)+inner[i+1]*gap; qb=inner[i]*gap+inner[i+1]*(1-gap)
        ra=outer[i]*(1-gap)+outer[i+1]*gap; rb=outer[i]*gap+outer[i+1]*(1-gap)
        prism(b,[qa,qb,rb,ra],front,front+.09,SHAFT,f'arch face voussoir {i+1}')
        # Deep actual soffit courses extend from the inner lip to the inset door surround.
        rqa=qa*.94+ra*.06;rqb=qb*.94+rb*.06
        prism(b,[qa,qb,rqb,rqa],front+.09,back,CUT,f'voussoir {i+1} soffit return')
    outline=[xz(q,front-.085)for q in d['keystone_face']]
    prism(b,outline,front-.085,front+.16,KEY,'central projecting russet keystone')

    # The left jamb shows three horizontal joints, visible beyond the shaft.
    # At the far right the column hides their ends, leaving a plain, short reveal.
    xleft, spring_left = inner[0]
    lower = [xz(q, front)[1] for q in d['front_jamb_left']]
    left_courses=[spring_left]+lower+[.60]
    for i,(top,bottom) in enumerate(zip(left_courses,left_courses[1:])):
        if bottom>=top:continue
        outline=[[xleft-.14,bottom+.008],[xleft,bottom+.008],
                 [xleft,top-.008],[xleft-.14,top-.008]]
        prism(b,outline,front,back,CUT,f'left door jamb course {i+1} and return')
    prism(b,[(xleft-.14,.045),(xleft,.045),(xleft,.605),(xleft-.14,.605)],front,back,CUT,'Plain jamb extended to threshold below visible course')
    xright, spring_right = inner[-1]
    outline=[[xright,.045],[xright+.08,.045],[xright+.08,spring_right],[xright,spring_right]]
    prism(b,outline,front,back,CUT,'narrow right jamb return screened by column')
