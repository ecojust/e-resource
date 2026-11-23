"""The three documented dormers facing the service courtyard."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon, box

from service_materials import EDGE, FRAME, GLASS, PALETTE, PLASTER, TILE

MEASURE = Path(__file__).resolve().parents[1] / 'measurements'
PREFIX = 'Eves garden roof / '


def dormer_layout(frame):
    obs = json.loads((MEASURE/'front-dormer-controls.json').read_bytes())['window_points']
    pitch = (frame.ridge-frame.eave)/(frame.depth/2)
    forms = []
    for name, item in obs.items():
        uv = np.array(item['design'])
        # On the two flanking windows the bottom rail terminates in the climbing roof.
        # The central face continues down to the courtyard portal.
        bottom_uv = uv[2:].mean(axis=0)
        y = frame.design.plane(bottom_uv,[0,0,frame.eave],[0,-pitch,1])[1] if name!='center' else 0.
        corners = np.array([frame.design.wall(pt,y) for pt in uv])
        l,r = corners[[0,3],0].mean(),corners[[1,2],0].mean()
        base,top = corners[2:,2].mean(),corners[:2,2].mean()
        mid = (l+r)/2
        scale=frame.width/14.8
        apex = frame.design.plane(item['cap']['design'],[mid,0,0],[1,0,0])
        front=y-.080*scale
        eave=top+.065*scale
        if name=='center':
            shoulder_points=[frame.design.wall(pt,front) for pt in item['timber_envelope_design'][1:3]]
            apron=np.mean([p[2] for p in shoulder_points])
            # The reference shows a short hip above a flat-topped plaster gable.
            hs=(r-l)*(apex[2]-apron)/(2*(apex[2]-eave))
            hip_depth=max(.24*scale,2*hs*.77)
            hip=front+hip_depth*(apex[2]-eave)/(apex[2]-apron)
            # The central white gable is vertical; its roof is clipped only at the upper tip.
            clipped_z=apron
        else:
            hip=max(front+.22*scale,apex[1])
            clipped_z=eave
        forms.append(dict(name=name,l=l,r=r,y=y,z0=base,z1=top,scale=scale,mid=mid,
                          front=front,eave=eave,tip=float(apex[2]),hip=hip,
                          clipped_z=clipped_z,pitch=pitch,observation=item))
    return forms


def limits(frame,item):
    pitch=item['pitch']
    return ((item['eave']-frame.eave)/pitch,(item['tip']-frame.eave)/pitch)


def roof_apertures(frame):
    """Three XY Polygons just inside the cheeks, ready for the main slope subtraction."""
    rings=[]
    for m in dormer_layout(frame):
        eave_y,ridge_y=limits(frame,m)
        inside=.028*m['scale']
        l,r,y=m['l']+inside,m['r']-inside,m['y']+inside
        rings.append(Polygon([(l,y),(r,y),(r,eave_y-inside),(m['mid'],ridge_y-inside),(l,eave_y-inside)]))
    return rings


def xz(b,outline,y0,y1,mat,label):
    if not outline.is_empty:
        b.prism(outline,-y1,-y0,lambda x,z,d:(x,-d,z),mat,label)


def plate(b,xyz,dz,material,label):
    # Each plate consists of one convex polygon extruded down the vertical axis.
    xyz=np.asarray(xyz,float)
    if len(xyz)<3:return
    keep=[0]
    for i in range(1,len(xyz)):
        if np.linalg.norm(xyz[i]-xyz[keep[-1]])>1e-6:keep.append(i)
    xyz=xyz[keep]
    if len(xyz)>2 and np.linalg.norm(xyz[-1]-xyz[0])<1e-6:xyz=xyz[:-1]
    n=len(xyz)
    if n<3:return
    a=xyz[:,:2];area=np.sum(a[:,0]*np.roll(a[:,1],-1)-a[:,1]*np.roll(a[:,0],-1))
    if abs(area)<1e-7:return
    if area<0:xyz=xyz[::-1]
    low=xyz-[0,0,dz]
    verts=[*low,*xyz]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    b.add(verts,faces,material,label)


def clipped(poly,normal,offset):
    if not len(poly):return []
    out=[]
    for a,b in zip(poly,[*poly[1:],poly[0]]):
        aa=np.dot(normal,a)-offset;bb=np.dot(normal,b)-offset
        if aa>=-1.e-9:out.append(a)
        if (aa>1.e-9 and bb< -1.e-9) or (aa< -1.e-9 and bb>1.e-9):
            out.append(a+aa/(aa-bb)*(b-a))
    return out


def faces(frame,m):
    ll,rr=m['l'],m['r'];cx=m['mid'];s=m['scale']
    y=m['front']; e=m['eave']; tip=m['tip'];hy=m['hip'];far=limits(frame,m)[1]+.05*s
    left,right=ll-.064*s,rr+.064*s
    front_l=np.array([left,y,e]);front_r=np.array([right,y,e])
    if m['name']=='center':
        front_l[2]=front_r[2]=m['clipped_z']
        ratio=(tip-m['clipped_z'])/(tip-e)
        front_l[0]=cx-(cx-left)*ratio;front_r[0]=cx+(right-cx)*ratio
        # Only the small end of the ridge hips down to this shoulder. The
        # main triangular cheeks of its steep gable reach the full eave.
        hy=y+.25*s
    apex=np.array([cx,hy,tip]);back=np.array([cx,far,tip])
    front=[front_l,front_r,apex]
    origin=frame.eave-.014*s
    result=[]
    for side,x,p in [('left',left,front_l),('right',right,front_r)]:
        outer=np.array([x,y,e]);backedge=np.array([x,far,e])
        corners=[outer,backedge,back,apex,p] if m['name']=='center' else [outer,backedge,back,apex]
        result.append((side,clipped(corners,[0,-m['pitch'],1],origin),1))
    result.append(('hip',front,0))
    return result


def tiles(b,polygon,axis,scale,lod,name):
    if not len(polygon):return
    plate(b,polygon,.066*scale,TILE,name+' roof plane')
    zmin=min(p[2]for p in polygon);zmax=max(p[2]for p in polygon)
    pitch=.125*scale
    n=max(2,round((zmax-zmin)/pitch))
    # Small joint widths and lap depths are working dimensions read from
    # repeated rows in the design. The album confirms the three cap contours.
    dz=(zmax-zmin)/n
    for k in range(n):
        z=zmin+k*dz
        if lod and k%2:continue
        strip=clipped(clipped(polygon,[0,0,1],z+.002*scale),[0,0,-1],-z-(dz*.14 if lod else dz))
        if not strip:continue
        normal=np.eye(3)[axis]
        t0,t1=min(p[axis]for p in strip),max(p[axis]for p in strip)
        pitch=.231*scale
        first=np.floor(t0/pitch-k*.5)*pitch+k*.5*pitch
        stops=[(t0,t1)] if lod else [(v+.006*scale,v+pitch-.006*scale)for v in np.arange(first,t1,pitch)]
        for a,c in stops:
            piece=clipped(clipped(strip,normal,a),-normal,-c)
            if len(piece)<3:continue
            lifts=np.array([[0,0,.007*scale+.013*scale*(1-(p[2]-z)/dz)] for p in piece])
            plate(b,np.array(piece)+lifts,.018*scale,TILE,name+' visible tile course')


def add_dormers(b,frame,lod=False):
    for m in dormer_layout(frame):
        name=m['name'];pre=PREFIX+name+' / ';s=m['scale']
        y,l,r,z,h=m['y'],m['l'],m['r'],m['z0'],m['z1']
        eye=m['observation'];eave_y,_=limits(frame,m)
        j=.055*s
        def panel(shape,d0,d1,mat,label):
            xz(b,shape,y+d0*s,y+d1*s,mat,pre+label)
        if name=='center':
            panel(box(l,frame.eave-.032*s,r,z),.004,.13,PLASTER,'plaster panel over the entry')
            for xx in np.linspace(l,r,5):
                panel(box(xx-j/2,frame.eave-.03*s,xx+j/2,z),-.038,.03,FRAME,'oak under the sill')
            gable=Polygon([(l,h),(r,h),
              *[(p[0],p[2])for p in [frame.design.wall(uv,y) for uv in reversed(eye['timber_envelope_design'][1:3])]]])
            panel(gable,.014,.13,PLASTER,'plaster gable')
            for i,points in enumerate(eye['mouldings_design']):
                arr=[frame.design.wall(uv,y)[[0,2]] for uv in points]
                curve=LineString(arr).buffer(.032*s,cap_style=2,join_style=1).intersection(gable)
                panel(curve,-.043,.025,FRAME,'bowed oak '+str(i+1))
            path=LineString([gable.exterior.coords[i] for i in [1,2,3,0]]).buffer(.037*s,cap_style=2,join_style=2)
            panel(path,-.035,.042,FRAME,'raked gable fascia')
        low=frame.roof_level(y)-.035*s
        # With the front skin cut by the host, solid cheek boards meet its slope.
        for i,x in enumerate((l,r)):
            section=Polygon([(y,low),(y,h+.055*s),(eave_y+.012*s,h+.055*s)])
            b.prism(section,x-.035*s,x+.035*s,lambda depth,height,offset:(offset,depth,height),
                    EDGE,pre+'boarded cheek '+str(i+1))
        casement=box(l,z,r,h)
        span=r-l
        us=eye['mullions_design_at_y'][1]
        scaled=[l+(u-us[0])/(us[-1]-us[0])*span for u in us]
        openings=[]
        for i,(a,c) in enumerate(zip(scaled,scaled[1:])):
            opening=box(a+j,z+.061*s,c-j,h-.067*s)
            openings.append(opening)
            panel(opening.buffer(.004*s,join_style=2),.045,.058,GLASS,'light '+str(i+1))
            for fraction in (.34,.66):
                hh=z+(h-z)*fraction
                panel(box(a+j,hh-.009*s,c-j,hh+.009*s),.013,.048,FRAME,'fine horizontal glazing bar')
            if not lod:
                mid=(a+c)/2
                panel(box(mid-.008*s,z+.061*s,mid+.008*s,h-.067*s),.015,.049,FRAME,'fine vertical glazing bar')
        for opening in openings:casement=casement.difference(opening)
        panel(casement,-.037,.073,FRAME,'four-light frame')
        panel(box(l-.037*s,z-.039*s,r+.037*s,z+.017*s),-.065,.078,FRAME,'projecting sill')
        for side,polygon,axis in faces(frame,m):
            tiles(b,polygon,axis,s,lod,pre+side)
