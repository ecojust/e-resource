"""Append carved limestone to the southern of the three principal river-facing arches."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
DOORS=HERE.parents[2]/'bund17/revisions/street-wing-doors'
sys.path.insert(0,str(DOORS))
from build_wing_doors import Parts,chunks,glb

STONE='Carved limestone and capitals'
FRAME=json.loads((HERE/'facade-frame.json').read_bytes())


def ovoid(parts,center,radii,lod,tilt=0.,rings=None):
    """Closed ellipsoid with separate poles and a slight lean in the elevation plane."""
    sides,latitudes=(9,5) if lod else (15,8)
    if rings:sides,latitudes=rings
    rx,rz,rd=radii
    co,si=math.cos(tilt),math.sin(tilt)
    def v(x,z,d):return (center[0]+co*x-si*z,center[1]+si*x+co*z,center[2]+d)
    pts=[v(0,0,rd)];faces=[]
    for j in range(1,latitudes):
        b=math.pi*j/latitudes
        for i in range(sides):
            a=math.tau*i/sides
            pts.append(v(rx*math.sin(b)*math.cos(a),rz*math.sin(b)*math.sin(a),rd*math.cos(b)))
    pts.append(v(0,0,-rd));last=len(pts)-1
    for i in range(sides):
        t=(i+1)%sides
        faces.extend([(0,1+i,1+t),(last,last-sides+t,last-sides+i)])
    for j in range(latitudes-2):
        for i in range(sides):
            a=1+j*sides+i;b=1+j*sides+(i+1)%sides
            faces.extend([(a,a+sides,b),(b,a+sides,b+sides)])
    parts.surface(STONE,pts,faces)


def p(px,py,depth):
    # The reference photograph is oblique. Its ratios are fitted between the
    # existing 4.15 m arch and its frieze, not used to change the bank's wall.
    return np.array([(px-331.)*.0121,11.11-(py-135.)*.0093,depth])


def limb(parts,a,b,diam,lod):
    delta=b-a;length=math.hypot(delta[0],delta[1])
    angle=math.atan2(-delta[0],delta[1])
    ovoid(parts,(a+b)/2,(diam/2,length/2+.03,diam*.49),lod,angle)


def curled_line(parts,coords,radius,lod):
    points=[p(*row) for row in coords]
    parts.tube(STONE,points,radius,6 if lod else 9)


def feather(parts,root,tip,width,lod):
    delta=tip-root;length=math.hypot(delta[0],delta[1]);angle=math.atan2(-delta[0],delta[1])
    ovoid(parts,(root+tip)/2,(width/2,length/2,.044 if lod else .053),lod,angle)
    if not lod:
        parts.tube(STONE,[root+[0,0,.033],(root+tip)/2+[0,0,.046],tip],.012,6)


def cherub(lod):
    b=Parts()
    # A shallow stone back joins the cheek, torso, bent legs and feather fan to
    # the original masonry. The forms stand proud of the original scrollwork.
    ovoid(b,p(151,187,-.075),(.31,.45,.28),lod,-.37)
    ovoid(b,p(158,176,.14),(.17,.235,.14),lod,-.33)
    ovoid(b,p(143,194,.18),(.189,.151,.145),lod,-.42)
    ovoid(b,p(133,205,.16),(.177,.145,.14),lod,-.37)
    # The outside leg drops beside the arch. The nearer knee folds in front.
    for a,d,limit in [((136,205,.21),(121,221,.22),.19),
                      ((121,221,.22),(107,241,.22),.135),
                      ((141,199,.20),(127,211,.27),.19),
                      ((127,211,.27),(120,223,.27),.135)]:
        limb(b,p(*a),p(*d),limit,lod)
    for px,py,dep in [(120,222,.23),(127,211,.28)]:ovoid(b,p(px,py,dep),(.083,.083,.075),lod)
    ovoid(b,p(103,243,.24),(.092,.059,.065),lod,-.50)
    ovoid(b,p(118,226,.27),(.078,.052,.061),lod,-.40)
    # Shoulders, crossed forearms and a separate small hand near the archivolt.
    for coords in [((154,167,.18),(165,183,.32),.151),
                   ((165,183,.32),(181,200,.34),.127),
                   ((173,170,.14),(166,190,.21),.126)]:
        a,end,d=coords;limb(b,p(*a),p(*end),d,lod)
    ovoid(b,p(184,201,.35),(.076,.056,.063),lod,.27)
    ovoid(b,p(160,162,.20),(.095,.117,.112),lod)
    # The oval cranium, two cheeks, projecting nose, lips, chin and curls are
    # all limestone. The sheltered recesses produce the facial shadows.
    ovoid(b,p(162,148,.265),(.183,.195,.15),lod,-.07)
    for hand in [-1,1]:
        ovoid(b,p(162+hand*8,151,.371),(.071,.061,.043),lod)
        ovoid(b,p(162+hand*6.5,146,.383),(.052,.019,.024),lod,hand*.11)
        ovoid(b,p(162+hand*16,149,.25),(.036,.056,.051),lod)
        if not lod:ovoid(b,p(162+hand*6.0,147.0,.396),(.025,.014,.015),False)
    ovoid(b,p(162.3,149.0,.409),(.031,.063,.045),lod,-.09)
    ovoid(b,p(162.6,154.4,.401),(.039,.018,.025),lod)
    ovoid(b,p(162.5,157.2,.365),(.059,.040,.029),lod)
    # Hair follows the head contour; it is not a circumferential ring across the face.
    for i in range(7 if lod else 13):
        count=7 if lod else 13;a=.06+math.pi*.93*i/(count-1)
        ovoid(b,p(162+14.2*math.cos(a),147-14.7*math.sin(a),.29+.036*math.sin(a)),(.049,.051,.050),lod)
    # Two folded wing lobes, overlapping feathers and a darker groove between rows.
    for wing,count in [(0,4 if lod else 7),(1,3 if lod else 5)]:
        for i in range(count):
            t=i/(count-1)
            start=p(150-3*t,164+10*t,.10+wing*.03)
            tip=p(110+12*t+wing*6,145+30*t+wing*7,.125+wing*.025)
            feather(b,start,tip,.11 if not wing else .085,lod)
    return b.data()


def acanthus_lobe(parts,index,lod):
    """A broad lobed blade encloses one earlier symbolic diagonal stroke."""
    knots=np.array([[-(.94+index*.23),10.50,.20],
                    [-(1.50+index*.22),10.93,.32],
                    [-(1.86+index*.16),11.12,.20]])
    steps=12 if lod else 21
    sides=6 if lod else 10
    ring=[];faces=[]
    for i in range(steps+1):
        u=i/steps
        # Passing through the original high point leaves its three append-only
        # guide strokes embedded along the deeply modelled central leaves.
        knot=min(1,int(u*2));t=u*2-knot
        pos=knots[knot]*(1-t)+knots[knot+1]*t
        tangent=knots[knot+1,:2]-knots[knot,:2]
        tangent/=np.linalg.norm(tangent)
        normal=np.array([-tangent[1],tangent[0]])
        fullness=math.sin(math.pi*u)**.57
        lobe=.82+.18*math.cos(u*math.pi*10)
        half=.041+.103*fullness*lobe
        for j in range(sides):
            a=math.tau*j/sides
            cross=math.cos(a);off=normal*cross*half
            surface=pos[2]+.075+(.045+.070*fullness)*math.sin(a)
            ring.append((pos[0]+off[0],pos[1]+off[1],surface))
        if i:
            for j in range(sides):
                a=(i-1)*sides+j;b=(i-1)*sides+(j+1)%sides
                faces.extend([(a,b,a+sides),(b,b+sides,a+sides)])
    ring.append(tuple([*knots[0,:2],knots[0,2]+.075]));lo=len(ring)-1
    ring.append(tuple([*knots[-1,:2],knots[-1,2]+.075]));hi=len(ring)-1
    for j in range(sides):
        faces.extend([(lo,(j+1)%sides,j),(hi,steps*sides+j,steps*sides+(j+1)%sides)])
    parts.surface(STONE,ring,faces)

def foliage(lod):
    b=Parts()
    for index in range(3):acanthus_lobe(b,index,lod)
    # The pair of horn-shaped stems turn in toward the keystone. Smaller
    # acanthus leaves overlap the original symbolic line in the upper spandrel.
    for row in [
        [(178,169,.09),(193,160,.13),(215,153,.17),(231,146,.18),(238,147,.18),(239,153,.18),(234,156,.18),(230,151,.16)],
        [(182,175,.03),(199,168,.09),(219,165,.12),(241,158,.13),(258,151,.12),(267,143,.07)],
        [(130,188,.06),(117,201,.09),(110,220,.10),(109,246,.12),(117,264,.14),(124,267,.15),(129,259,.16),(124,255,.16)]]:
        curled_line(b,row,.047 if lod else .054,lod)
    for i,(a,end,w) in enumerate([((199,161),(188,150),.13),((204,160),(205,143),.135),
                                    ((216,158),(226,141),.12),((225,160),(246,148),.13),
                                    ((234,155),(258,142),.12),((246,153),(267,140),.115),
                                    ((113,241),(104,252),.12),((115,252),(122,270),.10)]):
        if lod and i in (1,4):continue
        feather(b,p(*a,.09),p(*end,.14),w,lod)
    return b.data()


def beast(lod):
    b=Parts()
    # The central plaque in the old mesh is a plain keystone. Its carved
    # animal mask has a forehead, paired ears, protruding muzzle and open jaw.
    def m(x,z,d):return np.array([x,z,d])
    ovoid(b,m(0,10.95,.202),(.204,.26,.18),lod)
    ovoid(b,m(0,11.07,.328),(.167,.149,.083),lod)
    for hand in [-1,1]:
        ovoid(b,m(hand*.117,11.035,.369),(.072,.039,.038),lod,hand*.18)
        ovoid(b,m(hand*.108,10.984,.344),(.050,.032,.026),lod)
        ovoid(b,m(hand*.145,11.159,.289),(.062,.099,.063),lod,hand*-.49)
        for i in range(3 if lod else 5):
            z=11.03-i*.060
            a=m(hand*(.15+i*.009),z,.244);end=m(hand*(.237+i*.006),z-.102,.299)
            feather(b,a,end,.066,lod)
        ovoid(b,m(hand*.066,10.87,.429),(.075,.052,.070),lod)
        if not lod:ovoid(b,m(hand*.060,10.916,.494),(.018,.010,.010),False)
    ovoid(b,m(0,10.966,.392),(.063,.102,.087),lod)
    ovoid(b,m(0,10.922,.450),(.081,.042,.064),lod)
    # A hollow between the two jaws retains the shadow of the baseline keystone.
    points=[m(.111*math.cos(t),10.777+.095*math.sin(t),.343)
            for t in np.linspace(-math.pi*.95,math.pi*.95,12 if lod else 19)]
    b.tube(STONE,points,.035,6 if lod else 9)
    ovoid(b,m(0,10.680,.301),(.09,.041,.049),lod)
    return b.data()


def instances(lod):
    tangent=np.array(FRAME['world_basis_u']);inward=np.array(FRAME['world_basis_v'])
    u,v=FRAME['front_center'];mid=tangent*(u+FRAME['left_bay_center_u_m'])+inward*v
    for label,source,mirror in [('Southern acanthus',foliage,-1),('Northern acanthus',foliage,1),
                                ('Southern winged figure',cherub,-1),('Northern winged figure',cherub,1),
                                ('Central animal keystone',beast,0)]:
        transformed={}
        for mat,(points,normals,faces)in source(lod).items():
            values=points.copy();vectors=normals.copy()
            if mirror==1:
                values[:,0]*=-1;vectors[:,0]*=-1;faces=faces[:,::-1].copy()
            def gltf(array,origin):
                en=origin+array[:,0:1]*tangent-array[:,2:3]*inward
                return np.column_stack((en[:,0],array[:,1],-en[:,1])).astype('<f4')
            transformed[mat]=(gltf(values,mid),gltf(vectors,np.zeros(2)),faces)
        yield label,transformed


def augment(original,binary,lod):
    doc=deepcopy(original);blob=bytearray(binary)
    material=next(i for i,m in enumerate(doc['materials'])if m.get('name')==STONE)
    def add(array,target,kind,component,bounds=False):
        blob.extend(b'\0'*(-len(blob)%4));view=len(doc['bufferViews']);payload=array.tobytes()
        doc['bufferViews'].append({'buffer':0,'byteOffset':len(blob),'byteLength':len(payload),'target':target})
        blob.extend(payload);acc={'bufferView':view,'componentType':component,'type':kind,'count':len(array)}
        if bounds:acc.update(min=array.min(axis=0).tolist(),max=array.max(axis=0).tolist())
        doc['accessors'].append(acc);return len(doc['accessors'])-1
    scene=doc['scenes'][doc.get('scene',0)];count=0
    for name,groups in instances(lod):
        points,normals,faces=groups[STONE]
        pos=add(points,34962,'VEC3',5126,True);normal=add(normals,34962,'VEC3',5126)
        ind=add(faces.ravel(),34963,'SCALAR',5123)
        index=len(doc['meshes']);doc['meshes'].append({'name':name,'primitives':[{'attributes':{'POSITION':pos,'NORMAL':normal},'indices':ind,'material':material}]})
        scene['nodes'].append(len(doc['nodes']));doc['nodes'].append({'name':name,'mesh':index});count+=len(faces)
    doc['buffers'][0]['byteLength']=len(blob)
    return doc,bytes(blob),count


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prior',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();args.output.mkdir(exist_ok=True,parents=True)
    baseline=json.loads((HERE/'baseline.json').read_bytes());results={}
    for role in ['raw','web','lod']:
        src=args.prior/(role+'.glb');assert sha256(src.read_bytes()).hexdigest()==baseline['assets'][role]['sha256']
        doc,bin_data=chunks(src);new,buf,count=augment(doc,bin_data,role=='lod');dst=args.output/(role+'.glb')
        glb(dst,new,buf);results[role]={'sha256':sha256(dst.read_bytes()).hexdigest(),'added_triangles':count,'bytes':dst.stat().st_size}
    print(json.dumps(results,indent=2))
