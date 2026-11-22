"""Street and courtyard elevations of the stepped grey-brick residence at 310 Changde Road."""
from pathlib import Path
import json
import math
import numpy as np
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
import paired_tower_windows as tower

HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE.parent/'measurements/residence-wall-sections.json').read_text())
GREY='Residence | grey facing brick'
RED='Residence | red brick'
BRIGHT='Residence | terracotta arch mouldings'
SHADOW='Residence | shaded soffit'
STONE='Residence | pale stone'
IRON='Residence | iron rail'
WOOD='Residence | painted sash'
PALE='Residence | pale green casements'
GLASS='Residence | muted daylight on glass'
DARK='Residence | dark reflection'
LIGHT='Residence | pale sky reflection'
CLAY='Residence | red-orange clay tiles'
GROOVE='Residence | tile rolls'
FASCIA='Residence | deep eaves'
LEAF='Residence | painted louvre'
ORNAMENT='Residence | terracotta acanthus'
PALETTE={name:tower.finish(rgb,r,m) for name,rgb,r,m in [
 (GREY,(247,247,247),.93,0),(RED,(148,81,67),.93,0),(BRIGHT,(176,103,79),.86,0),
 (SHADOW,(97,69,59),.91,0),(STONE,(174,173,155),.88,0),(IRON,(120,123,118),.61,.34),
 (WOOD,(135,62,49),.67,0),(PALE,(124,139,123),.67,.03),(GLASS,(109,129,118),.33,.13),
 (DARK,(72,78,76),.38,.11),(LIGHT,(167,174,160),.36,.09),(CLAY,(157,86,72),.84,0),
 (GROOVE,(174,103,83),.84,0),(FASCIA,(96,67,58),.86,0),(LEAF,(100,79,67),.76,0),(ORNAMENT,(169,116,88),.85,0)]}
PALETTE[GREY].update(texture=str(HERE/'changde-grey-brick.png'),color=[1.,1.,1.])

def arch(l,r,bottom,spring,top,steps=36):
    mid=(l+r)/2
    return Polygon([(l,bottom),(r,bottom),*[(mid+(r-l)/2*math.cos(a),spring+(top-spring)*math.sin(a)) for a in np.linspace(0,math.pi,steps+1)]])

def aperture(row):
    return arch(*[row[k] for k in ('left','right','bottom','spring','top')])

class Wall:
    """A wall-face coordinate system with positive depth toward the building."""
    def __init__(self,b,origin,along,name):
        self.b=b;self.origin=np.asarray(origin,float)
        self.u=np.asarray(along,float);self.u/=np.linalg.norm(self.u)
        self.n=np.array([-self.u[1],self.u[0]]);self.name=name
    def point(self,u,z,y):
        p=self.origin+u*self.u+y*self.n
        return float(p[0]),float(p[1]),z
    def skin(self,shape,front,back,material,label):
        parts=[shape] if shape.geom_type=='Polygon' else list(getattr(shape,'geoms',[]))
        for p in parts:
            if p.geom_type=='Polygon' and p.area>1e-8:
                self.b.prism(orient(p,sign=1),-back,-front,lambda u,z,t:self.point(u,z,-t),material,self.name+' | '+label)
    def strip(self,l,r,z,t,y,d,material,label):
        if r>l and t>z:self.skin(box(l,z,r,t),y,d,material,label)
    def rod(self,points,radius,material,label,sides=8):
        self.b.tube([self.point(*p) for p in points],radius,material,sides,self.name+' | '+label)

def trim_window(w,row,lod):
    l,r,b,s,t=[row[k] for k in ('left','right','bottom','spring','top')]
    c=(r+l)/2;rx=(r-l)/2;rz=t-s;n=row['columns'];kind=row['profile'];tag=row['key'];zspan=s-b
    shape=aperture(row);wing=tag.startswith(('bay','outer bay'))
    frame=PALE if wing else WOOD;front=.164 if wing else .181
    if kind=='casement':front=.13
    w.skin(shape,front+.076,front+.099,DARK,tag+' | glazing in the recess')
    if kind=='shuttered':
        for j in range(2):
            left=l+.063+j*(r-l-.126)/2;right=left+(r-l-.126)/2
            for h in np.arange(b+.115,s-.05,.11):
                # The blind blades are closed. Their cut ends are set behind the stiles.
                w.strip(left,right,h,h+.091,front,front+.047,LEAF,tag+' | louvre blade')
        w.skin(shape.intersection(box(l,s,r,t+.02)),front+.022,front+.073,SHADOW,tag+' | dark fan above shutters')
    else:
        for col in range(n):
            a=l+(r-l)*col/n;d=l+(r-l)*(col+1)/n
            for j in range(row['rows']):
                lo=b+zspan*j/row['rows'];hi=b+zspan*(j+1)/row['rows']
                mat=(DARK if 'lower' in tag else GLASS) if wing else (LIGHT if 'upper' in tag and col==3 else GLASS)
                w.strip(a+.021,d-.021,lo+.016,hi-.016,front+.063,front+.075,mat,tag+' | individual rectangular light')
        if kind=='tympanum':
            w.skin(shape.intersection(box(l,s,r,t+.01)),.022,.142,STONE,tag+' | decorated tympanum')
            for k in range(14):
                a=math.pi*(k+.5)/14
                x=c+rx*.73*math.cos(a);z=s+rz*.72*math.sin(a)
                off=.049;w.rod([(x-off,z-.046,-.002),(x,z+.046,-.010),(x+off,z-.035,-.002)],.014,ORNAMENT,tag+' | raised terracotta leaves',5)
            for ii in range(8):
                a=ii*math.tau/8;poly=[]
                for j in range(16):
                    v=j*math.tau/16
                    radial=.085+.089*math.cos(v);cross=.041*math.sin(v)
                    poly.append((c+math.cos(a)*radial-math.sin(a)*cross,s+.62*rz+math.sin(a)*radial+math.cos(a)*cross))
                w.skin(Polygon(poly),-.035,-.001,ORNAMENT,tag+' | central rosette petal')
            w.skin(arch(l+.06,r-.06,s-.08,s-.01,s+.19),-.068,.07,RED,tag+' | shallow inner arch under relief')
        elif t>s+.06:
            fan=shape.intersection(box(l,s,r,t+.01))
            w.skin(fan,front+.061,front+.075,LIGHT if wing else GLASS,tag+' | arched fanlight')
            for x in np.linspace(l,r,6 if n==4 else 4)[1:-1]:
                hi=s+rz*math.sqrt(max(0,1-((x-c)/rx)**2))
                w.strip(x-.015,x+.015,s,hi,front+.007,front+.043,frame,tag+' | fanlight glazing bar')
        for j in range(1,row['rows']):
            z=b+zspan*j/row['rows'];h=.019 if row['rows']>=4 else .027
            w.strip(l+.023,r-.023,z-h,z+h,front+.001,front+.05,frame,tag+' | sash transom')
    for j in range(n+1):
        x=l+(r-l)*j/n
        width=.059 if j in (0,n) or j==n/2 else .032
        w.strip(max(l,x-width/2),min(r,x+width/2),b,s+.03,front-.009,front+.059,frame,tag+' | vertical stile')
    for z,h in ((s,.037),(b+.025,.025)):w.strip(l,r,z-h,z+h,front-.012,front+.071,frame,tag+' | meeting rail')
    outer=arch(l-.26,r+.26,b,s,t+.27);middle=arch(l-.165,r+.165,b,s,t+.186)
    low=box(l-.5,s-1e-5,r+.5,t+.53)
    w.skin(outer.difference(shape).intersection(low),-.057,.145,RED,tag+' | brick archivolt')
    w.skin(outer.difference(middle).intersection(low),-.091,-.055,BRIGHT,tag+' | raised outer arch moulding')
    inner=arch(l-.053,r+.053,b,s,t+.062)
    w.skin(inner.difference(shape).intersection(low),-.111,front+.043,BRIGHT,tag+' | rolled intrados and reveal')
    for sign in [-1,1]:
        center=c+sign*(rx+.11)
        for dz,dw in [(0,.34),(-.07,.28),(-.13,.19)]:
            w.strip(center-dw/2,center+dw/2,s+dz-.05,s+dz+.016,-.11,.03,BRIGHT,tag+' | spring impost')
    for k in range(10 if lod else 22):
        a=math.pi*(k+.5)/(10 if lod else 22);radial=np.array([math.cos(a),math.sin(a)])
        pt=np.array([c+rx*radial[0],s+rz*radial[1]])
        w.rod([(*(pt+radial*.080),-.063),(*(pt+radial*.165),-.063)],.0054,SHADOW,tag+' | radial mortar joint',4)
    if kind not in ('shuttered','shallow'):
        w.skin(Polygon([(c-.077,t+.022),(c+.077,t+.022),(c+.119,t+.344),(c-.119,t+.344)]),-.141,-.058,BRIGHT,tag+' | key in arch crown')
    w.strip(l-.085,r+.085,b-.11,b+.003,-.13,.16,STONE,tag+' | sill')
    if 'great' in tag:
        w.strip(l+.05,r-.05,b-.71,b-.162,-.025,.018,STONE,tag+' | pale apron under window')
        for x in (l+.16,r-.16):
            w.skin(Polygon([(x-.066,b-.145),(x+.066,b-.145),(x+.046,b-.37),(x,b-.45),(x-.046,b-.37)]),-.119,-.008,BRIGHT,tag+' | brick console beneath sill')

def grey_uv(part):
    points=np.asarray(part['vertices']);verts=[];coords=[];faces=[];lookup={}
    for tri in part['triangles']:
        p=points[list(tri)];k=int(np.argmax(abs(np.cross(p[1]-p[0],p[2]-p[0]))))
        uv=((1,2),(0,2),(0,1))[k];face=[]
        for i in tri:
            if (k,i) not in lookup:
                lookup[k,i]=len(verts);verts.append(tuple(points[i]));coords.append((points[i,uv[0]]/1.38,points[i,uv[1]]/1.56))
            face.append(lookup[k,i])
        faces.append(tuple(face))
    part.update(vertices=verts,texcoords=coords,triangles=faces)

def face(w,l,r,bottom,top,rows,lod,additional=(),dentil=True,belts=True):
    holes=[aperture(v)for v in rows]+list(additional)
    void=unary_union(holes)
    w.skin(box(l,bottom,r,top).difference(void),0,.37,GREY,'grey brickwork and the cut returns')
    if belts:
        for z,th,y in [(4.19,.085,-.019),(4.34,.11,-.065),(8.84,.10,-.038),(9.02,.185,-.10),(9.22,.065,-.043)]:
            if bottom<z<top:
                w.skin(box(l,z,r,z+th).difference(void),y,.010,RED,'continuous string course')
        for z in [s for s in (7.43,11.80,16.80) if bottom<s<top-.4]:
            w.skin(box(l,z,r,z+.092).difference(void),-.019,.010,RED,'red spring course')
    if dentil:
        for depth,h in [(.05,.12),(.17,.105),(.27,.075)]:
            w.strip(l,r,top+.02-h-depth*.39,top+.02-depth*.39,-depth,.15,RED,'stepped brick cornice')
        for x in np.arange(l+.12,r-.04,.29):
            w.strip(x-.060,x+.060,top-.30,top-.09,-.170,.005,BRIGHT,'projecting cornice dentil')
    for row in rows:trim_window(w,row,lod)

def hip(b,rect,z,top,ridge,m,lod,text):
    l,y,r,v=rect;cx,cy=(l+r)/2,(y+v)/2
    if ridge=='x':a=(cx-max(0,(r-l-(v-y))*.47),cy,top);d=(2*cx-a[0],cy,top)
    else:a=(cx,cy-max(0,(v-y-(r-l))*.47),top);d=(cx,2*cy-a[1],top)
    fs=[(l,y,z),(r,y,z),(r,v,z),(l,v,z)];faces=[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)]
    if ridge=='y':faces=[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5)]
    vertices=[*fs,a,d];base=z-.087
    b.add([*vertices,*[(x,y,base)for x,y,_ in fs]],[*faces,(9,8,7,6),(0,6,7,1),(1,7,8,2),(2,8,9,3),(3,9,6,0)],m,text+' | hipped tile skin')
    for i,face_ids in enumerate(faces):
        f=[np.array(vertices[j],float)for j in dict.fromkeys(face_ids)]
        a1=f[0];a2=f[1];p0=f[-1];p1=f[2]
        span=max(2,int(np.linalg.norm(a2-a1)/(.23 if lod else .16)))
        for k in range(1,span):
            t=k/span;lo=a1*(1-t)+a2*t;hi=p0*(1-t)+p1*t
            b.tube([lo,hi],.015 if lod else .021,GROOVE,4 if lod else 6,text+' | downslope roll')
        for j in range(1,8 if lod else 15):
            t=j/(8 if lod else 15);lo=a1*(1-t)+p0*t;hi=a2*(1-t)+p1*t
            if np.linalg.norm(hi-lo)>.08:b.tube([lo,hi],.009,SHADOW,4,text+' | tile course')
    for x,y1 in [(0,4),(1,5 if ridge=='x' else 4),(2,5),(3,4 if ridge=='x' else 5),(4,5)]:
        if np.linalg.norm(np.subtract(vertices[x],vertices[y1]))>.05:b.tube([vertices[x],vertices[y1]],.051,CLAY,8,text+' | ridge and hips')

def add_fabric(b,lod=False):
    start=len(b.parts);rows=DATA['windows'];q=DATA['portal']
    # The portal has a thick brick outer arch. Its crown keystone is carried by the separate porch.
    opening=arch(q['centre_x']-q['outer_radius_x'],q['centre_x']+q['outer_radius_x'],-.50,q['spring'],q['spring']+q['outer_radius_z'],64)
    front=Wall(b,(0,0),(1,0),'Street front');holes=[aperture(v).buffer(.012,quad_segs=5) for v in tower.openings()]
    opening=opening.union(box(-2.53,-.50,2.40,1.86))
    face(front,-9.83,2.80,-.48,13.59,[v for v in rows if v['face']=='front' and v['plane_m']==0],lod,additional=[opening,*holes])
    face(front,-2.75,2.80,13.59,18.07,[],lod,[*holes],belts=False)
    side=Wall(b,(2.80,0),(0,1),'Tower return');turn=[v for v in rows if v['key'].startswith('tower return')]
    face(side,0,2.50,-.47,13.59,turn[1:],lod);face(side,0,5.84,13.59,18.07,turn[:1],lod,belts=False)
    # Two small steel maintenance platforms are visible on the tower return in the Nina photographs.
    for a in turn[1:]:
        l=a['left']-.13;r=a['right']+.14;z=a['bottom']+.018
        side.strip(l,r,z-.08,z,-.66,-.004,IRON,'small iron platform')
        for x in np.linspace(l,r,7):side.strip(x-.013,x+.013,z,z+.75,-.65,-.624,IRON,'platform upright')
        for h in [0.14,.39,.62,.75]:
            side.strip(l,r,z+h-.012,z+h+.012,-.65,-.625,IRON,'platform horizontal rail')
            for x in [l,r]:side.strip(x-.011,x+.011,z+h-.013,z+h+.013,-.64,-.012,IRON,'platform rail return')
    for x,y,right in [(2.80,2.50,8.03),(8.70,4.00,12.67)]:
        wing=Wall(b,(0,y),(1,0),'South wing')
        chosen=[v for v in rows if v['face']=='front' and v['plane_m']==y]
        face(wing,x,right,-.47,13.39 if y<3 else 13.46,chosen,lod)
    # A canted side of the projecting bay has a narrow sash on each floor.
    v=np.array([.67,1.50]);length=np.linalg.norm(v);canted=Wall(b,(8.03,2.50),v,'Canted bay return')
    cut=[]
    for key,B,E,T in [('lower',4.91,7.09,7.32),('upper',9.62,11.75,11.99)]:
        cut.append(dict(key='Canted return '+key,left=.39,right=length-.33,bottom=B,spring=E,top=T,profile='shallow',columns=2,rows=3))
    face(canted,0,length,-.47,13.39,cut,lod)
    sections=[((-9.83,0),(0,-1),-9.10,0,13.59),((12.67,4),(0,1),0,5.1,13.46),
              ((0,9.10),(-1,0),-12.67,9.83,13.39),((-2.75,0),(0,-1),-5.84,0,18.07),
              ((0,5.84),(-1,0),-2.80,2.75,18.07)]
    for i,(origin,d,l,r,z) in enumerate(sections):
        face(Wall(b,origin,d,'Outline return '+str(i+1)),l,r,13.5 if i>=3 else -.47,z,[],lod,belts=i<2)
    hip(b,(-10.28,-.46,3.22,9.49),13.69,16.38,'x',CLAY,lod,'North roof')
    hip(b,(-3.12,-.37,3.16,6.25),18.17,20.33,'y',CLAY,lod,'Tower roof')
    hip(b,(2.47,2.19,8.42,9.42),13.52,15.89,'y',CLAY,lod,'South projecting roof')
    hip(b,(8.41,3.68,13.04,9.46),13.58,15.57,'y',CLAY,lod,'South rear roof')
    for i,(x,y,z) in enumerate([(-8.25,5.45,15.62),(-2.16,6.68,16.11)]):
        for extent,lo,hi,material in [(0.65,z-.64,z+1.01,GREY),(.76,z+.98,z+1.13,RED),(.71,z+1.13,z+1.32,GREY),(.83,z+1.32,z+1.43,RED)]:
            b.box((x,y,(lo+hi)/2),(extent,extent*.89,hi-lo),material,label='Chimney '+str(i+1)+' | shaft and corbelled cap')
    # Two small front-facing dormers occur in Gao 01, one above the broad north arches, one above the south bay.
    for i,(x,y,z) in enumerate([(-4.60,1.01,14.55),(6.40,3.55,14.11)]):
        front=Wall(b,(0,y),(1,0),'Dormer '+str(i+1));outline=Polygon([(x-.64,z),(x+.64,z),(x+.64,z+.78),(x,z+1.41),(x-.64,z+.78)])
        void=box(x-.37,z+.05,x+.37,z+.77);front.skin(outline.difference(void),-.015,.85,GREY,'brick gable and cheeks')
        front.skin(void,.11,.17,DARK,'shadowed sash');front.strip(x-.025,x+.025,z+.05,z+.78,.065,.12,WOOD,'central mullion')
        for k in range(3):front.strip(x-.36,x+.36,z+.12+k*.29,z+.143+k*.29,.067,.11,WOOD,'sash rail')
        for sign in (-1,1):
            top=(x,z+1.44);edge=(x+sign*.73,z+.73)
            poly=Polygon([top,edge,(edge[0],edge[1]-.10),(x,top[1]-.10)])
            front.skin(poly,-.115,.98,CLAY,'sloping tile cap')
    for part in b.parts[start:]:
        if part['material']==GREY:grey_uv(part)
