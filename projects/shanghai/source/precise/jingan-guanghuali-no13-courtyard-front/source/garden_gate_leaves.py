"""Visible double gate at No. 13, Lane 786 Julu Road, from the 2016 and 2018 courtyard photographs."""
import json
import math
from pathlib import Path

DATA = json.loads((Path(__file__).resolve().parents[1] / 'measurements/no13-gate-details.json').read_text())
SKIN = 'No.13 gate | deep brown-black leaf'
EDGE = 'No.13 gate | folded dark frame'
IRON = 'No.13 gate | dark cast-iron grille'
GLASS = 'No.13 gate | desaturated glazed light'
SCREEN = 'No.13 gate | fine grey screen behind glass'
LOCK = 'No.13 gate | pale round lock face'
BOSS = 'No.13 gate | dark enamel pull'
SLOT = 'No.13 gate | letter opening'
STONE = 'No.13 gate | worn grey threshold'

def finish(rgb, roughness, metallic=0.):
    rgb = [c/255. for c in rgb]
    return dict(color=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb],
                roughness=roughness, metallic=metallic)

PALETTE = {SKIN:finish((49,38,38),.67,.15), EDGE:finish((55,47,47),.48,.38),
           IRON:finish((47,44,43),.59,.36), GLASS:finish((139,141,133),.38,.1),
           SCREEN:finish((114,113,106),.8), LOCK:finish((176,161,145),.35,.66),
           BOSS:finish((48,46,43),.26,.55), SLOT:finish((22,19,18),.87),
           STONE:finish((161,161,149),.90)}

def box(b, x1,x2,y1,y2,z1,z2, mat, label):
    b.box(((x1+x2)/2,(y1+y2)/2,(z1+z2)/2),
          (x2-x1,y2-y1,z2-z1),mat,label=label)

def pierced_sheet(b, bounds, holes, y, rear, label):
    """One closed sheet with through-holes and shared edges at every junction."""
    left,bottom,right,top=bounds
    xs=sorted({left,right,*[v for h in holes for v in (h[0],h[2])]})
    zs=sorted({bottom,top,*[v for h in holes for v in (h[1],h[3])]})
    cells=set()
    for i,(x1,x2) in enumerate(zip(xs,xs[1:])):
        for j,(z1,z2) in enumerate(zip(zs,zs[1:])):
            if not any(l<(.5*(x1+x2))<r and low<(.5*(z1+z2))<high for l,low,r,high in holes):
                cells.add((i,j))
    vertices=[];lookup={};faces=[]
    def vertex(i,j,k):
        key=(i,j,k)
        if key not in lookup:
            lookup[key]=len(vertices);vertices.append((xs[i],(y,rear)[k],zs[j]))
        return lookup[key]
    for i,j in sorted(cells):
        coords=((i,j),(i+1,j),(i+1,j+1),(i,j+1));front=[vertex(a,c,0)for a,c in coords];back=[vertex(a,c,1)for a,c in coords]
        faces.extend((front,back[::-1]))
        for s,neighbor in enumerate(((i,j-1),(i+1,j),(i,j+1),(i-1,j))):
            if neighbor not in cells:
                k=(s+1)%4;faces.append((front[k],front[s],back[s],back[k]))
    b.add(vertices,faces,SKIN,label)

def lock_disc(b,x,z,profile,mat,label,n):
    vertices=[];faces=[]
    for y,r in profile:
        for i in range(n):
            a=i*2*math.pi/n
            vertices.append((x+r*math.cos(a),y,z+r*math.sin(a)))
    faces.append(tuple(range(n)))
    for j in range(len(profile)-1):
        for i in range(n):
            k=(i+1)%n;a=j*n
            faces.append((a+k,a+i,a+n+i,a+n+k))
    faces.append(tuple(range(len(vertices)-1,len(vertices)-n-1,-1)))
    b.add(vertices,faces,mat,label)

def build_grille(b, name, aperture, far):
    l,lo,r,hi=aperture;w=r-l;h=hi-lo
    def xx(px):return l+(px-25.)*w/182.
    def zz(px):return hi-(px-66.)*h/287.
    def rod(x1,x2,z1,z2,label):
        box(b,x1,x2,.295,.304,z1,z2,IRON,name+' | '+label)
    trim=.010
    for x,side in ((l,'left'),(r,'right')):
        box(b,x-trim*.53,x+trim*.53,.298,.329,lo-.010,hi+.010,EDGE,name+' | '+side+' folded jamb')
    for z,side in ((lo,'bottom'),(hi,'top')):
        box(b,l+.005,r-.005,.299,.330,z-.007,z+.007,EDGE,name+' | '+side+' folded rail')
    box(b,l-.015,r+.015,.268,.316,hi+.006,hi+.014,EDGE,name+' | projecting drip hood')
    box(b,l-.001,r+.001,.334,.340,lo-.002,hi+.002,GLASS,name+' | inset rectangular light')
    for i,px in enumerate((76,160),1):
        x=xx(px);rod(x-.0030,x+.0030,lo,hi,'continuous upright '+str(i))
    for i,py in enumerate((132,287),1):
        z=zz(py);rod(l,r,z-.0028,z+.0028,'continuous tie '+str(i))
    for i,py in enumerate((115,149,208,270,304),1):
        z=zz(py)
        for a,c,s in ((l,xx(93),'left'),(xx(144),r,'right')):
            rod(a,c,z-.0025,z+.0025,s+' short cross tie '+str(i))
    for upper,lower,label in ((115,149,'upper'),(270,304,'lower')):
        for px,side in ((53,'left'),(182,'right')):
            x=xx(px);rod(x-.0025,x+.0025,zz(lower),zz(upper),side+' '+label+' return')
    if not far:
        for j in range(1,31):
            z=lo+h*j/31
            box(b,l+.005,r-.005,.331,.333,z-.00085,z+.00085,SCREEN,name+' | inner screen stripe '+str(j))

def add_gate_leaves(b, lod=False):
    far=lod is True or lod in ('lod','low','distant')
    holes=DATA['clear_openings'];slot=DATA['review_locks_and_slot']['slot_xz']
    left,right=DATA['leaf_edges'];gap=DATA['leaf_joint_gap']
    for index,row in enumerate(holes):
        name='No.13 '+row['leaf']+' gate leaf';a,d=(left,-gap/2) if index==0 else (gap/2,right)
        cut=[row['clear_opening_xz']]
        if index==0:cut.append(slot)
        pierced_sheet(b,(a,DATA['leaf_bottom'],d,DATA['leaf_top']),cut,.31,.356,name+' | pierced face and returned cut edges')
        build_grille(b,name,row['clear_opening_xz'],far)
    l,bottom,r,top=slot
    box(b,l-.002,r+.002,.343,.348,bottom-.002,top+.002,SLOT,'No.13 left leaf | dark letter slot inner flap')
    box(b,l-.006,r+.006,.295,.319,top-.002,top+.006,EDGE,'No.13 left leaf | letter slot brow')
    box(b,left-.006,right+.009,.285,.355,1.946,1.983,EDGE,'No.13 double gate | shallow head flashing')
    for key,mat,profile,label in (
        ('upper_lock_xz',LOCK,[(.284,.020),(.288,.024),(.311,.025)],'brushed circular escutcheon'),
        ('lower_spindle_xz',BOSS,[(.244,.012),(.248,.022),(.264,.027),(.28,.022),(.298,.014),(.31,.021)],'projecting dark door pull')):
        x,z=DATA['review_locks_and_slot'][key];lock_disc(b,x,z,profile,mat,'No.13 left leaf | '+label,12 if far else 24)
    sill=DATA['threshold'];half=sill['width']/2
    box(b,-half,half,sill['front_y'],sill['rear_y'],sill['underside_z'],sill['top_z'],STONE,'No.13 | single light stone threshold between plinths')
