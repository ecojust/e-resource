"""The two independently observed tiled canopies in the Changle Road courtyard.

X follows the front towards photographic right, Y enters the house, Z is up.
The front triangular hip rises toward the separate high windowed wall. The
unseen back slope is cut at the wall; the red roof across the lane opening
and the high windowed storey's own cap belong to other surfaces.
"""
from math import ceil, cos, pi, sin
import numpy as np

TILES = ("Changle roof | weathered umber tile", "Changle roof | muted grey brown tile",
         "Changle roof | dark fired clay")
CAP = "Changle roof | rounded hip cap"
DRIP = "Changle roof | weather-darkened drip edge"
WOOD = "Changle roof | dark red eaves timber"
BOARD = "Changle roof | shaded boarded soffit"
PALETTE = {
    # glTF baseColorFactor values are linear reflectances. Colour samples and
    # same-view daylight/adjacent-wall comparisons are in the measurement set.
    TILES[0]: {"color":[.245,.218,.198],"roughness":.85},
    TILES[1]: {"color":[.219,.201,.187],"roughness":.86},
    TILES[2]: {"color":[.181,.162,.150],"roughness":.85},
    CAP: {"color":[.283,.207,.179],"roughness":.81},
    DRIP: {"color":[.069,.061,.055],"roughness":.79},
    WOOD: {"color":[.130,.084,.065],"roughness":.83},
    BOARD: {"color":[.074,.064,.055],"roughness":.90},
}
# Heights describe the tile bed at the projecting fascia's upper edge. The
# cap noses have their own radius above this datum. Depths behind the screen
# of trees are approximate. Full photographic controls accompany the source.
MAIN = ((-2.20,-.67,5.285),(4.71,-.57,5.43),(1.23,3.00,7.92),4.51)
WING = ((5.40,1.55,5.73),(11.64,1.50,6.005),(7.75,4.10,7.65),5.12)

def _closed(b,points,faces,material,label):
    verts=np.array(points,dtype=float)
    tris=[]
    for face in faces:
        tris.extend((face[0],face[i],face[i+1]) for i in range(1,len(face)-1))
    base=verts-verts[0]
    area3=base[np.array(tris)]
    if np.einsum('ij,ij->',area3[:,0],np.cross(area3[:,1],area3[:,2]))<0:
        tris=[(c,b_,a) for a,b_,c in tris]
    b.add(verts.tolist(),tris,material,label)

def _prism(b,polygon,offset,material,name):
    low=np.array(polygon,dtype=float);high=low+np.array(offset)
    n=len(low);faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n))
    _closed(b,np.vstack((low,high)),faces,material,name)

def _beam(b,a,c,half_width,depth,material,label):
    a,c=np.array(a),np.array(c);e=c[:2]-a[:2];e/=np.linalg.norm(e)
    n=half_width*np.r_[-e[1],e[0],0.]
    _prism(b,[a-n,c-n,c+n,a+n],[0,0,-depth],material,label)

def _caps(b,a,c,lod,label):
    a,c=np.array(a),np.array(c);vec=c-a;length=np.linalg.norm(vec)
    direction=vec/length; cross=np.cross(direction,(0,0,1.));cross/=np.linalg.norm(cross)
    up=np.cross(cross,direction)
    steps=7 if not lod else 4
    count=max(1,round(length/(.36 if not lod else .71)))
    for j in range(count):
        t0=j/count;t1=min(1.,(j+1)/count+.014/length)
        rings=[]
        for t,rad in ((t0,.109),(t1,.089)):
            center=a+t*vec
            arc=[center+rad*(cos(i*pi/steps)*cross+sin(i*pi/steps)*up) for i in range(steps+1)]
            rings.append(arc+[center-.030*up])
        n=len(rings[0]);faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
        faces.extend((i,(i+1)%n,n+(i+1)%n,n+i)for i in range(n))
        _closed(b,rings[0]+rings[1],faces,CAP,label+' | lapped hip cap')

def _clip(polygon,axis,bound,greater):
    kept=[]
    for a,c in zip(polygon[-1:]+polygon[:-1],polygon):
        va=(a[axis]-bound) if greater else (bound-a[axis])
        vc=(c[axis]-bound) if greater else (bound-c[axis])
        if (va>0)!=(vc>0):
            t=va/(va-vc);kept.append(tuple(x+t*(y-x) for x,y in zip(a,c)))
        if vc>0:kept.append(c)
    return kept

def _tile(b,poly,a,axis,run,width,wave,phase,lower,upper,lod,material,name):
    """Closed solid of one lapping tile or a continuous LOD course with the same edge."""
    if len(poly)<3:return
    first=min(p[0] for p in poly);last=max(p[0] for p in poly)
    if last-first<.001:return
    pitch=(wave/3 if lower<.001 else wave*2) if lod else wave/4
    knots=[first,*[k*pitch for k in range(int(np.floor(first/pitch))+1,int(np.ceil(last/pitch))) if first+.0001<k*pitch<last-.0001],last]
    top=[];index={};tri=[];edges={}
    for l,r in zip(knots,knots[1:]):
        cell=_clip(_clip(poly,0,l-1e-9,True),0,r+1e-9,False)
        ids=[]
        for x,t in cell:
            key=(round(x,6),round(t,6))
            if key not in index:
                index[key]=len(top)
                ripple=.022*(1+cos(2*pi*(x/wave+phase)))/2
                # The downhill nose sits proud of the next lower course.
                height=.029*(1-(t-lower)/(upper-lower))+ripple
                top.append(a+x*axis+t*run+np.array([0,0,height]))
            i=index[key]
            if not ids or ids[-1]!=i:ids.append(i)
        if len(ids)>1 and ids[0]==ids[-1]:ids.pop()
        for i in range(1,len(ids)-1):
            group=(ids[0],ids[i],ids[i+1])
            if len(set(group))<3:continue
            tri.append(group)
            for m,n in zip(group,group[1:]+group[:1]):
                if (n,m) in edges:del edges[(n,m)]
                else:edges[(m,n)]=True
    if not tri:return
    n=len(top);bottom=[]
    for x,t in index:bottom.append(a+x*axis+t*run+np.array([0,0,-.019]))
    sides=[(v,u,u+n,v+n) for u,v in edges]
    _closed(b,top+bottom,tri+[(k+n,j+n,i+n)for i,j,k in tri]+sides,material,name)

def _slope(b,left,right,up_left,up_right,lod,label):
    a,z,ul,ur=map(lambda v:np.array(v,dtype=float),[left,right,up_left,up_right])
    axis=z-a;width=np.linalg.norm(axis[:2]);axis/=width
    shift_l=np.dot((ul-a)[:2],axis[:2]);run=ul-a-shift_l*axis
    shift_r=np.dot((ur-a)[:2],axis[:2])
    footprint=[(0.,0.),(width,0.),(shift_r,1.)]
    if abs(shift_r-shift_l)>.001:footprint.append((shift_l,1.))
    else:ur=ul
    _prism(b,[a+x*axis+t*run+np.array([0.,0.,-.031])for x,t in footprint],[0.,0.,-.11],BOARD,label+' | boarded underside')
    count=max(2,round(np.linalg.norm(run)/.245))
    wave=.105
    cols=ceil(width/(2*wave))
    for row in range(count):
        t0=row/count;t1=min(1.,(row+1)/count+.014/max(np.linalg.norm(run),.1))
        strip=_clip(_clip(footprint,1,t0-1e-9,True),1,t1+1e-9,False)
        if lod:
            _tile(b,strip,a,axis,run,width,wave,0.,t0,t1,True,TILES[(row//3)%3],label+' | fluted tile course')
            continue
        for col in range(cols):
            l=col*2*wave+.0007 if col else -.00001
            r=(col+1)*2*wave-.0007
            tile=_clip(_clip(strip,0,l,True),0,r,False)
            mat=TILES[(col*23+row*7+(col//3))%3]
            _tile(b,tile,a,axis,run,width,wave,0.,t0,t1,False,mat,label+' | lapped pantile')
    _beam(b,a,z,.037,.115,DRIP,label+' | projecting drip')
    # Rafter end blocks project out from the eaves. Use the inboard
    # normal of this slope; this leaves the shadow line between the blocks.
    inside=run.copy();inside[2]=0;inside/=np.linalg.norm(inside)
    n=max(2,round(width/.405))
    for i in range(n):
        f=(i+.5)/n
        edge=a+(z-a)*f+np.array([0,0,-.130])
        _beam(b,edge+.075*inside,edge+.55*inside,.052,.135,WOOD,label+' | exposed rafter tail')
    _beam(b,a+.05*inside+np.array([0,0,-.122]),z+.05*inside+np.array([0,0,-.122]),.031,.083,WOOD,label+' | timber fascia')

def _hip(b,shape,lod,label):
    left,right,peak,back=shape
    left=np.array(left,dtype=float);right=np.array(right,dtype=float);peak=np.array(peak)
    bl=left.copy();bl[1]=back;br=right.copy();br[1]=back;back_peak=peak.copy();back_peak[1]=back
    _slope(b,left,right,peak,peak,lod,label+' front')
    _slope(b,bl,left,back_peak,peak,lod,label+' minus-X return')
    _slope(b,right,br,peak,back_peak,lod,label+' plus-X return')
    _caps(b,left,peak,lod,label+' left');_caps(b,right,peak,lod,label+' right')
    _caps(b,peak,back_peak,lod,label+' ridge')

WING_WALL_SEATS = ((5.40,3.10), (10.10,3.10), (11.075,3.94), (11.55,3.94))


def _wing_soffit(b,left,right,back,wall_seats):
    """Join the continuous front and end soffits to the stepped return wall."""
    x0,y0,z0=left
    x1,y1,z1=right
    seats=[(x,y+.004,5.58) for x,y in wall_seats]
    if len(seats)<2 or any(a[0]>=c[0] for a,c in zip(seats,seats[1:])):
        raise ValueError('The wall seat must follow the eave from east to west')
    # The front lining continues above the rafter tails and behind the wall
    # face. The oblique segment meets the set-back narrow window bay.
    face=[]
    for i,(x,_,_) in enumerate(seats):
        xx=x0 if i==0 else x1-.063 if i==len(seats)-1 else x
        f=(xx-x0)/(x1-x0)
        face.append((xx,y0+f*(y1-y0)+.078,z0+f*(z1-z0)-.170))
    for i in range(len(seats)-1):
        panel=[face[i],face[i+1],seats[i+1],seats[i]]
        _prism(b,panel,[0.,0.,.075],BOARD,'setback wing lining | under outer eaves '+str(i+1))
    west=seats[-1]
    _prism(b,[face[-1],(face[-1][0],back,face[-1][2]),(west[0],back,west[2]),west],
           [0.,0.,.075],BOARD,'setback wing lining | west eaves to wall plate')


def add_roofs(builder,lod=False,wing_wall_seats=WING_WALL_SEATS):
    _hip(builder,MAIN,lod,'central projecting roof')
    # Winter photographs show a short upper ridge entering the high wall on
    # the left. Its awning continues beneath the hidden joint; its near face
    # has a horizontal upper edge before it slopes to the exposed right hip.
    left,right,tip,back=WING
    _wing_soffit(builder,left,right,back,wing_wall_seats)
    ridge_left=(left[0],tip[1],tip[2]-.044)
    _slope(builder,left,right,ridge_left,tip,lod,'setback wing roof front')
    left=np.asarray(left);right=np.asarray(right);tip=np.asarray(tip)
    br=right.copy();br[1]=back;end=tip.copy();end[1]=back
    _slope(builder,right,br,tip,end,lod,'setback wing roof outer return')
    _caps(builder,right,tip,lod,'setback wing right hip')
    _caps(builder,ridge_left,tip,lod,'setback wing wall ridge')
    _caps(builder,tip,end,lod,'setback wing short depth ridge')
