"""Second-storey curved brick bay and set-back balcony at No. 8 Gongyuan Fang."""
import math
import json
from pathlib import Path
import numpy as np
FIT=json.loads((Path(__file__).resolve().parents[1]/'measurements/bay-camera-fit.json').read_bytes())
P=FIT['parameters']
JOINT='Recessed warm lime mortar'
BRICK=['Brick | orange','Brick | russet','Brick | light fired','Brick | plum']
STONE='Warm cast concrete and sill';OLD='Rose-toned underside';STEEL='Oxide-red sash';IRON='Painted dark metal';DARK='Rebate shadow';GLASS='Window glass | muted daylight';BACK='Retired balcony sash';PLASTER='Light sand render';EAVE='Weathered fascia'
def profile(c,rough=.8):return dict(color=c,roughness=rough)
PALETTE={JOINT:profile([.385,.307,.237]),STONE:profile([.725,.645,.49]),OLD:profile([.38,.176,.133]),
 STEEL:profile([.124,.059,.053],.65),IRON:profile([.045,.042,.045],.60),DARK:profile([.040,.032,.032]),
 GLASS:profile([.28,.39,.42],.31),BACK:profile([.18,.21,.22],.55),PLASTER:profile([.61,.55,.43]),EAVE:profile([.069,.041,.060])}
PALETTE.update({m:profile(c)for m,c in zip(BRICK,[[.53,.237,.130],[.46,.186,.105],[.61,.313,.174],[.42,.17,.116]])})
PALETTE[GLASS]['alpha']=.82
R=P['radius'];HALF=P['wall_half_span'];GAP=P['opening_arc_width'];PITCH=P['bay_axis_pitch'];HEAD=P['head']
BOX=[[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]
def curved(s,depth,z):
    a=s/R
    return [(R-depth)*math.sin(a),R-(R-depth)*math.cos(a),z]
def add_bay(b,lod=False,layout=None):
    """Build in local metres with Z zero at the photographed second-floor sill."""
    lod=lod is True or lod=='lod'; b.palette.update(PALETTE);layout=layout or {}
    shift=np.asarray(layout.get('origin',(0,0,0)));scale=float(layout.get('course_height',.063))/.063
    def mesh(v,f,m,label):b.add((np.array(v)*scale+shift).tolist(),f,m,label)
    def cube(x0,x1,y0,y1,z0,z1,m,lab):
        v=[[x,y,z]for z in (z0,z1)for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]
        mesh(v,BOX,m,lab)
    def prism(s0,s1,z0,z1,d0,d1,segments=1):
        v=[];f=[]
        for n in range(segments+1):
            s=s0+(s1-s0)*n/segments
            v.extend([curved(s,d,z) for d,z in [(d0,z0),(d1,z0),(d1,z1),(d0,z1)]])
            if n:
                l=(n-1)*4
                for j in range(4):
                    k=(j+1)%4;f.append([l+j,l+k,l+4+k,l+4+j])
        f.extend([[3,2,1,0],[segments*4+j for j in (0,1,2,3)]])
        return v,f
    def band(s0,s1,z0,z1,d0,d1,m,label,count=None):
        v,f=prism(s0,s1,z0,z1,d0,d1,count or max(1,math.ceil((s1-s0)/(.37 if lod else .14))))
        mesh(v,f,m,label)
    def tube(points,radius,material,label,sides=None):
        sides=sides or (5 if lod else 9);v=[];f=[]; pts=np.array(points)
        for i,pt in enumerate(pts):
            t=pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)];t/=np.linalg.norm(t)
            v1=np.cross(np.array([0.,1.,0.]),t)
            if np.linalg.norm(v1)<.01:v1=np.cross(np.array([1.,0.,0.]),t)
            v1/=np.linalg.norm(v1);v2=np.cross(t,v1)
            for j in range(sides):
                a=2*math.pi*j/sides;v.append(pt+radius*(math.cos(a)*v1+math.sin(a)*v2))
            if i:
                q=(i-1)*sides
                for j in range(sides):k=(j+1)%sides;f.append([q+j,q+k,q+sides+k,q+sides+j])
        f.extend([list(range(sides))[::-1],list(range(len(v)-sides,len(v)))])
        mesh(v,f,material,label)
    # Front and jamb returns. The three openings are left clear in the brickwork.
    centers=[-PITCH,0,PITCH]; gaps=[(s-GAP/2,s+GAP/2)for s in centers]
    width=P['wall_half_span']; head=HEAD; slab=P['slab_base'];top=P['slab_top']
    def solid_runs(lo,hi,z0,z1):
        if z0>=head or z1<=0:return [(lo,hi)]
        cuts=[lo]
        for left,right in gaps:
            if lo<left<hi:cuts.append(left)
            if lo<right<hi:cuts.append(right)
        cuts.append(hi)
        return [(a,c)for a,c in zip(cuts,cuts[1:])if not any(l<(a+c)/2<r for l,r in gaps)]
    for n,(l,r)in enumerate(solid_runs(-width,width,0,head)):
        band(l,r,0,head,.009,.22,JOINT,f'Visible reveal | pier {n+1}')
    band(-width,width,-.23,0,.009,.22,JOINT,'Brick breast below windows')
    band(-width,width,head,slab,.009,.22,JOINT,'Brick spandrel over three apertures')
    bricks={m:([],[])for m in BRICK}
    for row in range(-4,math.ceil(slab/.063)):
        bottom=max(row*.063+.002,-.23);upper=min((row+1)*.063-.002,slab)
        if upper<=bottom:continue
        # Split the single course intersecting the opening head before trimming the run.
        levels=[bottom]+([head] if bottom<head<upper else [])+[upper]
        for z0,z1 in zip(levels,levels[1:]):
            for j in range(-12,13):
                s0=j*.226+(row%2)*.113+.002;s1=s0+.222
                for a,c in solid_runs(max(-width,s0),min(width,s1),z0,z1):
                    if c-a<.009:continue
                    if any(z0>=head and z1<=head+P['lintel_height'] and a>l-.025 and c<r+.025 for l,r in gaps):continue
                    mat=BRICK[(row*19+j*7+j*row)%len(BRICK)];v,f=prism(a,c,z0,z1,-.004,.009);vs,fs=bricks[mat];o=len(vs);vs+=v;fs.extend([[o+k for k in face]for face in f])
    for m,(v,f)in bricks.items():mesh(v,f,m,'Running bond | '+m)
    for j,(l,r)in enumerate(gaps):
        label=['Left','Centre','Right'][j]+' curved bay'
        band(l-.02,r+.02,head,head+P['lintel_height'],-.067,.075,STONE,label+' | cast lintel')
        band(l-.043,r+.043,-.031,.020,-.075,.13,STONE,label+' | projected sill')
        # Each sash is planar within its splayed radial opening.
        a=np.array(curved(l,.115,0));c=np.array(curved(r,.115,0));u=c-a;w=np.linalg.norm(u);u/=w
        n=np.array([-u[1],u[0],0]);k=np.array([0.,0.,1.])
        def winbox(t0,t1,y0,y1,z0,z1,mat,part):
            ctr=a+u*(t0+t1)/2+n*(y0+y1)/2+k*(z0+z1)/2
            b.box(ctr*scale+shift,((t1-t0)*scale,(y1-y0)*scale,(z1-z0)*scale),mat,basis=[u,n,k],label=label+' | '+part)
        frame=.044
        for x0,x1 in [(0,frame),(w-frame,w)]:winbox(x0,x1,0,.065,0,head,STEEL,'rebated side stile')
        for z0,z1 in [(0,.045),(head-.05,head)]:winbox(frame,w-frame,0,.065,z0,z1,STEEL,'head or foot stile')
        mid=head*P['meeting_rail_ratio'];winbox(frame,w-frame,-.012,.060,mid-.033,mid+.033,STEEL,'meeting rail')
        for low,high in [(.045,mid-.033),(mid+.033,head-.05)]:
            winbox(w*.5-.013,w*.5+.013,.014,.047,low,high,STEEL,'vertical glazing bar')
            for x0,x1 in [(frame,w*.5-.013),(w*.5+.013,w-frame)]:winbox(x0,x1,.045,.055,low,high,GLASS,'daylight pane')
    # Moulding profile traces the visible curved light edge and its reddish lower return.
    profile=[(0,.030),(.13,-.049),(.23,-.105),(.28,-.074),(.38,-.028),(.66,-.025),(.76,-.092),(.87,-.115),(1.,-.095)]
    if lod:profile=[profile[i]for i in (0,1,2,4,6,8)]
    for j,((t0,ext0),(t1,ext1))in enumerate(zip(profile,profile[1:])):
        left0,right0=-HALF,HALF
        left1,right1=-HALF,HALF
        v=[];f=[];N=14 if lod else 32
        for i in range(N+1):
            q=i/N;lo=left0*(1-q)+right0*q;hi=left1*(1-q)+right1*q
            v+= [curved(lo,ext0,slab+(top-slab)*t0),curved(lo,.65,slab+(top-slab)*t0),curved(hi,.65,slab+(top-slab)*t1),curved(hi,ext1,slab+(top-slab)*t1)]
            if i:
                o=(i-1)*4
                for a in range(4):c=(a+1)%4;f.append([o+a,o+c,o+c+4,o+a+4])
        f += [[3,2,1,0],[N*4+k for k in range(4)]]
        mesh(v,f,OLD if .27<t0<.74 else STONE,'Balcony | curved cornice profile '+str(j+1))
    span=P['rail_half_span'];dep=P['rail_recess'];rh=P['rail_height'];zt=top+rh
    # The railing has a broad top, two intermediate horizontal belts, narrow
    # uprights, and three groups of opposed scallops. Intervals behind hanging poles are interpolated.
    SAMP=14 if lod else 35
    for off,thick in [(0,.016),(-.20,.017),(-.32,.019),(-.47,.012)]:
        pts=[curved(x,dep,zt+off) for x in np.linspace(-span,span,SAMP)];tube(pts,thick,IRON,'Balcony | continuous curved rail '+str(off))
    for i,s in enumerate(np.linspace(-span,span,17)):
        tube([curved(s,dep,top+.009),curved(s,dep,zt-(0 if i%4==0 else .20))],.016 if i%4==0 else .010,IRON,'Balcony | upright '+str(i+1))
    for n,s in enumerate([-span*.72,0,span*.72]):
        for level in ([.22,.40] if lod else [.14,.33,.52]):
            for sg in [-1,1]:
                angles=np.linspace(0,math.pi/2,4 if lod else 7)
                pts=[curved(s+sg*.20*(1-math.cos(t)),dep-.012,top+level+.105*math.sin(t)) for t in angles]
                tube(pts,.009,IRON,'Balcony | paired scallop '+str(n+1))
    # Exposed glazed enclosure behind the railing, with its straight roof edge.
    y=P['glazing_y'];bw=P['glazing_half_width'];z0=top+.04;z1=P['glazing_head'];tr=P['glazing_transom']
    # The section ends at the two photographed side cheeks. Lower glazing edges are hidden by railing.
    for i in range(4):
        x0=-bw+i*bw/2;x1=x0+bw/2
        for a,c in [(z0,tr),(tr+.032,z1)]:
            cube(x0+.022,x1-.022,y+.028,y+.040,a+.016,c-.016,GLASS,'Retreat | pane '+str(i+1))
    for i in range(5):
        x=-bw+i*bw/2;cube(x-.022,x+.022,y-.006,y+.045,z0,z1,BACK,'Retreat | vertical glazing frame')
    for z in [z0,tr,z1]:
        cube(-bw,bw,y-.008,y+.045,z-.025,z+.025,BACK,'Retreat | horizontal glazing frame')
    for side in [-1,1]:
        x=side*(bw+.14);cube(x-.14,x+.14,y-.04,y+.24,z0,z1,PLASTER,'Retreat | visible rendered cheek')
    eave=FIT['roof_edge']; fy=eave['front_y']; tz=eave['top_z']
    # Two roof–sky lines constrain the lip independently of the glazing head.
    # The right tip is visible at x≈548/382 in the two images. The left is occluded.
    cube(-bw-.22,bw+1.00,fy,fy+.34,tz-.17,tz,EAVE,'Retreat | dark roof edge')
    cube(-bw-.25,bw+.28,y+.02,y+.28,z1+.02,tz-.17,PLASTER,'Retreat | rendered head below fascia')
    cube(-bw-.20,bw+.98,fy+.01,y+.29,tz-.18,tz-.144,EAVE,'Retreat | exposed dark soffit')
