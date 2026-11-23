"""Changle Road courtyard porch: measured overlapping terracotta cover and pan tiles."""
import json
from pathlib import Path
import numpy as np

DATA=json.loads((Path(__file__).resolve().parent.parent/'measurements/porch-tile-observations.json').read_bytes())
CLAY='Changle 325 | curved fired terracotta'
PALE='Changle 325 | sun-worn terracotta'
DARK='Changle 325 | red-brown fired clay'
PAN='Changle 325 | concave red pan tile'
END='Changle 325 | deep red fired eave end'
FASCIA='Changle 325 | charcoal eave board'
TRIM='Changle 325 | black eave moulding'
BRACKET='Changle 325 | ochre porch bracket'
BED='Changle 325 | shadowed roof bedding'
PALETTE={name:{'color':rgb,'roughness':rough} for name,rgb,rough in [
    (CLAY,[.445,.116,.042],.71),(PALE,[.505,.146,.055],.71),(DARK,[.330,.076,.032],.76),
    (PAN,[.372,.092,.035],.76),(END,[.290,.064,.025],.78),(FASCIA,[.025,.022,.018],.88),
    (TRIM,[.018,.017,.016],.86),(BRACKET,[.55,.435,.240],.9),(BED,[.167,.098,.058],.97)]}


class Roof:
    """Fit depth and shear from the ten matched cover axes across the roof."""
    def __init__(self,frame,front_y=-.30):
        self.frame=frame
        self.front_y=front_y
        self.front=[frame.plane((u,605),front_y) for u in DATA['front_disc_centres_u']]
        upper=DATA['upper_cover_centres_u']
        a=np.array([frame.plane((u,449),0)[0] for u in upper])
        slope=np.array([frame.plane((u,449),1)[0] for u in upper])-a
        yf,dx=np.linalg.lstsq(np.c_[slope,-np.ones(len(a))],np.array(self.front[:len(a)])[:,0]-a,rcond=None)[0]
        self.rear_y=float(yf);self.shear=float(dx)
        self.pitch=float(np.median(np.diff(np.array(self.front)[:,0])))
        self.z0=float(np.mean(np.array(self.front)[:10,1]))
        self.z1=float(np.mean([frame.plane((u,449),yf)[1] for u in upper]))
        self.upper_u=np.polyfit(np.arange(len(upper)),upper,1)
        self.x0=np.array(self.front)[:,0].tolist()
        self.zaxis=np.array(self.front)[:,1].tolist()
        self.rear_top=self.station(444,4.5)
    def interp(self,seq,i):
        if i<0:return seq[0]+i*(seq[1]-seq[0])
        if i>len(seq)-1:return seq[-1]+(i+1-len(seq))*(seq[-1]-seq[-2])
        return float(np.interp(i,np.arange(len(seq)),seq))
    def image_u(self,v,i):
        a=self.interp(DATA['front_disc_centres_u'],i)
        b=float(np.polyval(self.upper_u,i))
        return a+(605-v)*(b-a)/156
    def station(self,v,i):
        uv=(self.image_u(v,i),v)
        z0=self.frame.plane(uv,self.front_y)[1];z1=self.frame.plane(uv,self.rear_y)[1]
        base=self.interp(self.zaxis,i)
        return float((z0-base)/(self.z1-self.z0-(z1-z0)))
    def xyz(self,i,t,dx,dz):
        x=self.interp(self.x0,i)+self.shear*t+dx
        z=self.interp(self.zaxis,i)+(self.z1-self.z0)*t+dz
        return self.frame.xyz(x,self.front_y+t*(self.rear_y-self.front_y),z)
    def last(self,i):
        limits=np.array(DATA['visible_right_limit_v_u'])
        for v in np.arange(605,442,-.5):
            if self.image_u(v,i)>np.interp(v,limits[:,0],limits[:,1])+2:
                return self.station(v,i)
        return self.rear_top


def solid(b,verts,faces,material,label):
    p=np.asarray(verts,dtype=float);r=p-p[0]
    vol=sum(np.dot(r[a[0]],np.cross(r[a[k]],r[a[k+1]])) for a in faces for k in range(1,len(a)-1))
    if vol<0:faces=[tuple(reversed(a)) for a in faces]
    b.add(p,faces,material,'Changle 325 / porch roof / '+label)


def tile(b,roof,i,lo,hi,kind,index,lod):
    is_cover=kind=='cover'
    n=(7 if lod else 14) if is_cover else (4 if lod else 8)
    theta=np.linspace(-.31*np.pi,1.31*np.pi,n+1)
    p=roof.pitch;pts=[]
    for t,taper in ((lo,1.),(hi,.88)):
        for dep in (0.,.039*p):
            for j,angle in enumerate(theta):
                if is_cover:
                    dx=(.352*p*taper-dep)*np.cos(angle)
                    dz=(.285*p*taper-dep)*np.sin(angle)
                else:
                    k=2*j/n-1
                    dx=.529*p*k
                    dz=p*(-.238+.192*k*k)-dep+(1-taper)*(-.26*p)
                pts.append(roof.xyz(i,t,dx,dz))
    w=n+1;faces=[]
    for j in range(n):
        faces.extend([(j,j+1,2*w+j+1,2*w+j),(w+j,3*w+j,3*w+j+1,w+j+1),
                      (j,w+j,w+j+1,j+1),(2*w+j,2*w+j+1,3*w+j+1,3*w+j)])
    faces.extend([(0,2*w,3*w,w),(n,n+w,n+3*w,n+2*w)])
    tone=(CLAY,CLAY,PALE,CLAY,DARK,CLAY)[(int(i)*7+index*11)%6] if is_cover else PAN
    solid(b,pts,faces,tone,f'{kind} {i:g} course {index+1:02d}')


def inset_end(b,roof,i,lod):
    # Small inset ceramic closure, leaving the modelled barrel wall and rim exposed.
    p=roof.pitch;n=10 if lod else 18
    ring=np.linspace(0,2*np.pi,n,endpoint=False)
    pts=[roof.xyz(i,t,.298*p*np.cos(a),.236*p*np.sin(a)-.014*p) for t in (.005,.024) for a in ring]
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    faces+= [(j,j+n,(j+1)%n+n,(j+1)%n) for j in range(n)]
    solid(b,pts,faces,END,f'recessed ceramic nose {i+1:02d}')


def block(b,frame,front,back,material,name):
    n=len(front)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    solid(b,[frame.xyz(*v) for v in [*front,*back]],faces,material,name)


def add_porch_roof(b,frame,lod=False):
    roof=Roof(frame);p=roof.pitch
    for is_cover in (False,True):
        indices=range(17) if is_cover else range(16)
        image_rows=DATA['cover_lap_rows_v'] if is_cover else DATA['pan_lap_rows_v']
        # Each modeled course has a distinct lower nose and a tapering overlapping heel.
        for track in indices:
            i=track if is_cover else track+.5
            stations=[0.,*[roof.station(v,i) for v in image_rows],roof.rear_top]
            last=roof.last(i)
            for j,(a,h) in enumerate(zip(stations,stations[1:])):
                stop=min(h+.11*(h-a),last)
                if stop-a>.002:tile(b,roof,i,a,stop,'cover' if is_cover else 'pan',j,lod)
            if is_cover and i<16:inset_end(b,roof,i,lod)
    # The narrow backing follows the photographed roof footprint. Its right edge
    # passes just under the nearer wing where the picture stops showing tile.
    edge=[-.34,*range(17),16.13]
    for j,(left,right) in enumerate(zip(edge,edge[1:])):
        last_left=max(0.,roof.last(left));last_right=max(0.,roof.last(right))
        if min(last_left,last_right)<.002:continue
        plan=[(left,.013),(right,.013),(right,last_right),(left,last_left)]
        corners=[roof.xyz(i,t,0.,z*p) for z in (-.55,-.303) for i,t in plan]
        faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        solid(b,corners,faces,BED,f'roof backing segment {j+1:02d}')
    # A dark continuous ledge and its narrow beads are visible below the tubular noses.
    for v0,v1,y0,y1,name,mat in [(612,625,-.31,-.10,'wide fascia',FASCIA),(610,614,-.342,-.16,'upper rolled bead',TRIM),(624,629,-.306,-.12,'fascia lower lip',TRIM)]:
        section=[]
        for u,v in ((434,v0),(869,v0-2),(869,v1-2),(436,v1)):
            x,z=frame.plane((u,v),y0);section.append((x,y0,z))
        block(b,frame,section,[(x,y1,z)for x,y,z in section],mat,name)
    # Each bracket is cut back towards the front. Its side makes the visible hollow curve.
    for n,uu in enumerate([(449,490),(866,899)]):
        xs=[frame.plane((u,659),0.)[0] for u in uu]
        nose=-.235;upper=frame.plane((uu[0],628),nose)[1];lower=frame.plane((uu[0]+13,719),0.)[1]
        yz=[(nose,upper),(.125,upper),(.125,lower),(.016,lower),(-.018,lower+.035),
            (-.024,lower+.15),(-.06,lower+.28),(-.14,upper-.22),(-.209,upper-.1)]
        faces=[[(x,y,z) for y,z in yz] for x in xs]
        block(b,frame,*faces,BRACKET,('left' if n==0 else 'right')+' ochre eaves bracket')
