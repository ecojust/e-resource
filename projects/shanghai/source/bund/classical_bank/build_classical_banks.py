"""Two independently researched Bund banks, with actual recessed window openings.

Run: blender -b --python build_classical_banks.py -- --building hsbc [--render]
     blender -b --python build_classical_banks.py -- --building russo [--render]

Input roof triangulation preserves the OSM courtyard. All dimensions are metres.
Architectural details are photo interpretations, not a claim of laser scanning.
No solid facade box is placed behind the window openings.
"""
import argparse, json, math, os, random, sys
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

HERE=Path(__file__).resolve().parent
R=random.Random(123)

class Builder:
    def __init__(self):
        self.verts=[];self.faces=[];self.material=[];self.smooth=[]
        self.origin=(0,0);self.u=(1,0);self.v=(0,1)
        self.window_count=0;self.opening_recesses=[]
    def frame(self,origin=(0,0),u=(1,0),v=(0,1)):
        self.origin=origin;self.u=u;self.v=v
    def point(self,p):
        x,y,z=p;return (self.origin[0]+self.u[0]*x+self.v[0]*y,self.origin[1]+self.u[1]*x+self.v[1]*y,z)
    def geom(self,verts,faces,mat=0,smooth=False):
        o=len(self.verts);self.verts.extend(self.point(p) for p in verts)
        self.faces.extend(tuple(o+i for i in f) for f in faces)
        self.material.extend([mat]*len(faces));self.smooth.extend([smooth]*len(faces))
    def box(self,x,y,z,w,d,h,mat=0):
        if min(w,d,h)<=0:return
        vs=[(x+sx*w/2,y+sy*d/2,z+sz*h/2) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        self.geom(vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    def prism(self,points,y,depth,mat=0):
        # Extruded 2D polygon in x/z. Each arch has a real curved soffit.
        n=len(points);vs=[(x,yy,z) for yy in (y,y+depth) for x,z in points]
        poly=[Vector((x,z,0)) for x,z in points]
        lookup={tuple(v):i for i,v in enumerate(poly)}
        tris=[[v if isinstance(v,int) else lookup[tuple(v)] for v in t] for t in tessellate_polygon([poly])]
        fs=[tuple(reversed(t)) for t in tris]+[tuple(n+i for i in t) for t in tris]
        fs += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        self.geom(vs,fs,mat)
    def lathe(self,x,y,profile,mat=1,segments=32,flutes=0):
        vs=[]
        for z,r in profile:
            for i in range(segments):
                a=math.tau*i/segments;rr=r-(.036*(.5+.5*math.cos(flutes*a)) if flutes else 0)
                vs.append((x+rr*math.cos(a),y+rr*math.sin(a),z))
        fs=[tuple(reversed(range(segments))),tuple((len(profile)-1)*segments+i for i in range(segments))]
        for j in range(len(profile)-1):
            for i in range(segments):fs.append((j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i))
        self.geom(vs,fs,mat,True)
    def tube(self,points,r,mat=1,sides=8):
        points=[Vector(p) for p in points];vs=[]
        for i,p in enumerate(points):
            t=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
            a=t.cross(Vector((0,1,0)))
            if a.length<.01:a=t.cross(Vector((1,0,0)))
            a.normalize();c=t.cross(a)
            for k in range(sides):vs.append(p+r*(a*math.cos(math.tau*k/sides)+c*math.sin(math.tau*k/sides)))
        fs=[]
        for i in range(len(points)-1):
            for k in range(sides):fs.append((i*sides+k,i*sides+(k+1)%sides,(i+1)*sides+(k+1)%sides,(i+1)*sides+k))
        self.geom(vs,fs,mat,True)
    def arch(self,x,y,spring,r,t,depth=.25,mat=1,segments=22):
        for i in range(segments):
            a=math.pi*i/segments+.008;c=math.pi*(i+1)/segments-.008
            pts=[(x+r*math.cos(a),spring+r*math.sin(a)),(x+(r+t)*math.cos(a),spring+(r+t)*math.sin(a)),(x+(r+t)*math.cos(c),spring+(r+t)*math.sin(c)),(x+r*math.cos(c),spring+r*math.sin(c))]
            self.prism(pts,y,depth,mat)
    def cornice(self,x,width,z,y=0,scale=1,dentils=True):
        for dz,depth,height in [(0,.32,.22),(.22,.50,.18),(.42,.82,.15),(.60,.68,.18)]:
            self.box(x,y-depth*.5,z+dz*scale,width,depth*scale,height*scale,1)
        if dentils:
            count=max(1,int(width/(.65*scale)))
            for i in range(count):self.box(x-width/2+(i+.5)*width/count,y-.23*scale,z-.20*scale,.27*scale,.44*scale,.30*scale,1)
    def pediment(self,x,y,z,w,h,mat=1):
        self.prism([(x-w/2,z),(x,z+h),(x+w/2,z)],y+.05,.30,mat)
        for off,thick in [(0,.14),(.18,.10)]:
            self.tube([(x-w/2-.12,y-off,z),(x,y-off,z+h+.10),(x+w/2+.12,y-off,z)],thick,1,6)
        self.box(x,y-.08,z-.08,w+.4,.55,.19,1)
    def scroll(self,x,y,z,scale=1,sign=1,mat=1):
        pts=[]
        for i in range(34):
            a=i/33*math.tau*1.45;r=scale*(.08+.30*i/33)
            pts.append((x+sign*r*math.cos(a),y,z+r*math.sin(a)))
        self.tube(pts,.055*scale,mat,7)
    def column(self,x,y,z0,z1,r=.65,fluted=True):
        self.box(x,y,z0+.15,2.6*r,2.6*r,.30,1)
        self.lathe(x,y,[(z0+.3,1.26*r),(z0+.44,1.30*r),(z0+.58,1.05*r),(z0+.72,r),(z1-1.0,.86*r),(z1-.83,r)],1,96 if fluted else 32,24 if fluted else 0)
        self.lathe(x,y,[(z1-.85,r),(z1-.65,1.13*r),(z1-.53,1.18*r),(z1-.37,1.05*r)],1,32)
        self.box(x,y,z1-.20,2.9*r,2.4*r,.30,1)
        for sx in [-1,1]:
            self.scroll(x+sx*.83*r,y-r-.12,z1-.51,1.2*r,sx)
            self.scroll(x+sx*.83*r,y+r+.12,z1-.51,1.2*r,sx)
    def window(self,x,y,z0,z1,w,arch=False,mullions=2,curtain=False,grille=False):
        self.window_count+=1;self.opening_recesses.append(.57)
        r=w/2;spring=z1-r if arch else z1
        if arch:poly=[(x-r,z0),(x+r,z0)]+[(x+r*math.cos(a),spring+r*math.sin(a)) for a in [math.pi*i/24 for i in range(25)]]
        else:poly=[(x-r,z0),(x+r,z0),(x+r,z1),(x-r,z1)]
        self.prism(poly,y+.57,.045,3 if not curtain else 5)
        if curtain:
            for j in range(12):
                xx=x-r+(j+.5)*w/12;top=spring if arch else z1
                self.box(xx,y+.60,z0+(top-z0)/2,w/12*.52,.04,top-z0,5 if j%3 else 6)
        # Frames stand inside the opening; reveals remain exposed on all sides.
        for xx in [x-r+.055,x+r-.055]:self.box(xx,y+.39,(z0+spring)/2,.105,.22,spring-z0,4)
        self.box(x,y+.39,z0+.055,w,.22,.11,4)
        if not arch:self.box(x,y+.39,z1-.055,w,.22,.11,4)
        else:self.arch(x,y+.30,spring,r-.11,.11,.17,4,24)
        for i in range(1,mullions+1):
            xx=x-r+w*i/(mullions+1);top=spring+math.sqrt(max(0,r*r-(xx-x)**2)) if arch else z1
            self.box(xx,y+.37,(z0+top)/2,.07,.20,top-z0,4)
        for zz in ([z0+(spring-z0)*.52,spring] if arch else [z0+(z1-z0)*.48,z0+(z1-z0)*.77]):
            self.box(x,y+.35,zz,w,.22,.07,4)
        if grille:
            for i in range(1,9):self.box(x-r+w*i/9,y+.17,(z0+spring)/2,.025,.035,spring-z0,7)
            for zz in [z0+.5,z0+1.0,spring-.4]:self.box(x,y+.16,zz,w,.04,.035,7)
    def bay(self,x,width,y,bottom,top,win_bottom,win_top,win_width,arched=False,ornate=0,curtain=False,grille=False,detailed=True):
        # Four-sided structural shell with an actually absent window aperture.
        r=win_width/2;thick=.62
        side=(width-win_width)/2
        for s in [-1,1]:self.box(x+s*(r+side/2),y+thick/2,(bottom+top)/2,side,thick,top-bottom,0)
        self.box(x,y+thick/2,(bottom+win_bottom)/2,win_width,thick,win_bottom-bottom,0)
        if arched:
            spring=win_top-r
            curve=[(x+r*math.cos(math.pi*i/24),spring+r*math.sin(math.pi*i/24)) for i in range(25)]
            self.prism([(x-r,top),(x+r,top)]+curve,y,thick,0)
        else:self.box(x,y+thick/2,(win_top+top)/2,win_width,thick,top-win_top,0)
        self.window(x,y,win_bottom,win_top,win_width,arched,2,curtain,grille)
        # Three-dimensional jamb, moulded sill and raised lintel.
        for s in [-1,1]:self.box(x+s*(r+.11),y-.07,(win_bottom+win_top-(r if arched else 0))/2,.22,.23,win_top-win_bottom-(r if arched else 0),1)
        self.box(x,y-.14,win_bottom-.10,win_width+.52,.40,.18,1)
        if arched:self.arch(x,y-.18,win_top-r,r+.02,.24,.31,1)
        else:
            self.box(x,y-.13,win_top+.10,win_width+.48,.36,.18,1)
            if ornate:self.cornice(x,win_width+.65,win_top+.25,y,.45,False)
        if ornate==2:self.pediment(x,y-.24,win_top+.45,win_width+.8,.65)
        # Individual horizontal rustication joints avoid the opening itself.
        zz=bottom+.42 if detailed else top+1
        while zz<top-.08:
            half=r if win_bottom<zz<win_top else -1
            if arched and zz>win_top-r and zz<win_top:half=math.sqrt(max(0,r*r-(zz-(win_top-r))**2))
            intervals=[(-width/2,width/2)] if half<0 else [(-width/2,-half-.15),(half+.15,width/2)]
            for a,c in intervals:
                if c>a:self.box(x+(a+c)/2,y-.007,zz,c-a,.018,.018,8)
            zz+=.55


def material(name,color,rough=.7,metal=.0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=rough;n.inputs['Metallic'].default_value=metal
    return m

def materials():
    return [material('Warm granite wall',(.58,.54,.45)),material('Carved limestone and capitals',(.69,.65,.55)),material('Dark roof coping',(.22,.24,.23)),
      material('Recessed reflecting glazing',(.075,.14,.16),.22,.40),material('Bronze window framing',(.14,.16,.14),.35,.55),material('Curtain pale fabric',(.48,.56,.53),.9),
      material('Curtain shaded folds',(.35,.43,.40),.9),material('Wrought iron gates',(.07,.075,.065),.45,.6),material('Stone joints and shadow',(.28,.26,.22)),
      material('Raised gold lettering',(.68,.44,.10),.28,.72),material('Patinated copper',(.22,.34,.29),.54,.4),material('Flag red',(.55,.018,.022))]


def roof_and_other_walls(b,data,levels,roof_extension=0):
    top=levels[-1]+roof_extension;verts=data['roof_vertices'];tri=data['roof_triangles'];b.frame()
    b.geom([(x,y,top) for x,y in verts],[tri[i:i+3] for i in range(0,len(tri),3)],2)
    fc=data['front_center'];fw=data['front_width']
    for ring_index,ring in enumerate(data['rings']):
        for j,start in enumerate(ring):
            end=ring[(j+1)%len(ring)];dx=end[0]-start[0];dy=end[1]-start[1];length=math.hypot(dx,dy)
            mid=((start[0]+end[0])/2,(start[1]+end[1])/2)
            if ring_index==0 and math.hypot(mid[0]-fc[0],mid[1]-fc[1])<.03 and abs(length-fw)<.1:continue
            u=(dx/length,dy/length);v=(-u[1],u[0]);b.frame(mid,u,v)
            count=max(1,round(length/4.4));width=length/count
            for k in range(len(levels)-1):
                lo,hi=levels[k:k+2]
                if length<2.7:b.box(0,.31,(lo+hi)/2,length,.62,hi-lo,0);continue
                for i in range(count):b.bay(-length/2+(i+.5)*width,width,0,lo,hi,lo+.9,hi-.8,min(2.1,width-.75),False,0,False,detailed=False)
            if roof_extension:b.box(0,.31,levels[-1]+roof_extension/2,length,.62,roof_extension,0)
            b.cornice(0,length,top,0,.6,False)
            b.box(0,.12,top+.8,length,.40,1.3,0);b.box(0,.10,top+1.5,length,.60,.18,1)
    b.frame()


def relief_rosette(b,x,y,z,r=.25):
    b.lathe(x,y,[(z-.1,r*.55),(z,r),(z+.12,r*.35)],1,12)
    for i in range(8):
        a=math.tau*i/8
        b.tube([(x,y,z),(x+math.cos(a)*r,y-.15,z+math.sin(a)*r)],.065,1,6)


def hsbc(b,data):
    fw=data['front_width'];half=fw/2;front=data['front_center'];levels=[0,7.2,13.0,18.6,24.1,29.1]
    roof_and_other_walls(b,data,levels);b.frame(front)
    # Five bays inside six Ionic columns; seven narrower bays in each wing.
    center_width=25.4;wing_width=(fw-center_width)/2;wing_bay=wing_width/7
    for side in [-1,1]:
        for i in range(7):
            x=side*(center_width/2+(i+.5)*wing_bay)
            for k in range(5):
                lo,hi=levels[k:k+2]
                if k==0:
                    # Current photograph shows a distinct low mezzanine row
                    # above the basement/storefront windows, not one tall pane.
                    b.bay(x,wing_bay,0,0,4.65,.60,4.08,2.2,False,1)
                    b.bay(x,wing_bay,0,4.65,7.2,5.02,6.55,1.85,False,0)
                else:
                    wb,wt={1:(8.05,12.35),2:(13.8,17.9),3:(19.6,22.7),4:(25.9,28.3)}[k]
                    winw=2.2 if k<3 else 1.95 if k==3 else 1.85
                    b.bay(x,wing_bay,0,lo,hi,wb,wt,winw,False,2 if k==1 and i in [0,6] else 1 if k<4 else 0)
            for z in [7.1,24.2]:b.cornice(x,wing_bay,z,0,.75,z>20)
        # Tall banded end and inner quoins.
        for x in [side*(half-.65),side*(center_width/2+.35)]:
            for z in [7.8+i*.64 for i in range(25)]:b.box(x,-.17,z,1.28,.32,.59,1)
        # Projecting attic window pavilions visible at both ends of each wing.
        for x in [side*(center_width/2+wing_bay*.5),side*(half-wing_bay*.5)]:
            for dx in [-1.25,1.25]:b.box(x+dx,-.20,27.35,.44,.44,3.50,1)
            b.cornice(x,3.25,29.16,-.20,.65,False)
            b.box(x,-.12,30.0,2.3,.60,1.25,0)
    # Ground level: three deep arched entryways, with genuine open reveals.
    for i in range(3):b.bay((i-1)*center_width/3,center_width/3,0,0,7.2,.45,6.2,4.2,True,0,False,True)
    # Upper centre is recessed 3.1 m behind the actual freestanding columns.
    for i in range(5):
        x=-center_width/2+(i+.5)*center_width/5
        for k in range(1,4):
            lo,hi=levels[k:k+2]
            wb,wt={1:(8.3,12.35),2:(14.0,17.9),3:(19.6,22.7)}[k]
            b.bay(x,center_width/5,3.1,lo,hi,wb,wt,2.5 if k<3 else 2.1,False,1)
        b.bay(x,center_width/5,0,24.1,29.1,25.45,28.3,2.4,False,0)
    for x in [-12,-7.2,-2.4,2.4,7.2,12]:b.column(x,-.8,7.5,24.05,.71,True)
    # Colonnade floor and coffered ceiling, not an opaque facade behind columns.
    b.box(0,1.15,7.38,center_width,4.0,.35,1);b.box(0,1.15,24.25,center_width+1,4.5,.65,1)
    for x in [-10,-5,0,5,10]:
        for yy in [.2,1.7]:b.box(x,yy,23.88,3.8,1.2,.08,8)
    for z in [7.1,24.35,29.15]:b.cornice(0,fw+.4,z,0,1 if z>20 else .9,z>20)
    # Attic parapet, short raised piers and open rail panels.
    for x in [-half+1,-13,13,half-1]:
        b.box(x,.28,30.3,2.3,.9,2.0,0);b.box(x,.20,31.35,2.6,1.05,.24,1)
    b.box(0,.33,30.0,fw,.55,1.1,0);b.box(0,.24,30.65,fw+.3,.80,.23,1)
    # Paired stone balconies and balustrades flank the column base.
    for x in [-10,10]:
        b.box(x,-1.15,8.5,4.2,.22,.18,1)
        for i in range(11):b.lathe(x-1.8+i*.36,-1.15,[(7.5,.07),(7.7,.13),(8.15,.09),(8.4,.065)],1,10)
    # Present-day raised drum: square stepped tiers, recessed windows, pediments.
    tower_front=1.1;tower_width=18.8;tower_depth=17.6
    for face in range(4):
        angle=face*math.pi/2;u=(math.cos(angle),math.sin(angle));v=(-math.sin(angle),math.cos(angle))
        cx=front[0]+math.sin(angle)*tower_depth/2;cy=front[1]+tower_front+tower_depth/2-math.cos(angle)*tower_depth/2
        b.frame((cx,cy),u,v)
        for z0,z1,ww in [(30,36.9,5.1),(36.9,41.8,5.5)]:
            b.bay(0,tower_width,0,z0,z1,z0+.9,z1-.7,ww,False,1)
            for xx in [-5.9,5.9]:b.box(xx,-.18,(z0+z1)/2,2.0,.55,z1-z0,0)
            b.cornice(0,tower_width+.5,z1,0,.75,True)
        b.pediment(0,-.18,36.8,9.2,1.6)
        for xx in [-1.25,1.25]:b.column(xx,-.48,31.0,36.1,.31,False)
        # Upper balustrade and panel relief.
        b.box(0,-.55,37.6,7.2,.19,.18,1)
        for xx in [-3.3+i*.44 for i in range(16)]:b.lathe(xx,-.55,[(36.9,.045),(37.2,.09),(37.5,.045)],1,10)
    b.frame(front)
    dome_y=tower_front+tower_depth/2
    b.lathe(0,dome_y,[(41.9,8.4),(42.2,8.65),(42.5,8.5)],1,80)
    profile=[]
    for i in range(25):
        a=i/24*math.pi/2;profile.append((42.5+7.6*math.sin(a),8.4*math.cos(a)+.03))
    b.lathe(0,dome_y,profile,1,96)
    # Raised dome seams follow the actual curved roof surface.
    for j in range(12):
        a=math.tau*j/12
        pts=[((8.43*math.cos(t)+.03)*math.cos(a),dome_y+(8.43*math.cos(t)+.03)*math.sin(a),42.52+7.6*math.sin(t)) for t in [i/20*math.pi/2 for i in range(21)]]
        b.tube(pts,.045,1,6)
    b.lathe(0,dome_y,[(49.9,1.5),(50.2,1.5),(50.35,1.8),(50.55,1.8)],2,48)
    for i in range(8):
        a=math.tau*i/8;b.lathe(math.cos(a)*1.18,dome_y+math.sin(a)*1.18,[(50.4,.09),(51.3,.08)],1,12)
    b.lathe(0,dome_y,[(51.3,1.8),(51.5,1.85),(51.65,1.1),(52.65,.5)],1,48)
    b.lathe(0,dome_y,[(52.6,.09),(55.0,.06)],10,12)
    # Dimensional five-point finial star from the present-day photograph.
    star=[(math.sin(i*math.pi/5)*(.62 if i%2==0 else .26),55.1+math.cos(i*math.pi/5)*(.62 if i%2==0 else .26)) for i in range(10)]
    b.prism(star,dome_y-.055,.11,10)
    # Entry steps and sign board. Lion sculptures are deliberately not invented.
    for i in range(4):
        h=(4-i)*.10;b.box(0,-.30-i*.35,h/2,30.0,.42,h,1)
    b.box(0,-.42,7.25,13.4,.25,1.08,2)
    return {'body_roof_m':29.1,'roof_parapet_m':31.5,'finial_height_m':55.72,'front_bays':19,'colonnade_columns':6,
            'photo_based_estimates':['all vertical dimensions','window proportions','ornament profiles','dome section'],
            'explicit_omissions':['bronze lion sculpture anatomy','interior banking hall and mosaic','individual exact stone weathering']}


def russo(b,data):
    fw=data['front_width'];front=data['front_center'];levels=[0,4.8,11.4,17.8]
    roof_and_other_walls(b,data,levels,roof_extension=2.85);b.frame(front)
    centers=[-13.1,-5.65,0,5.65,13.1];bounds=[-fw/2,-9.3,-2.825,2.825,9.3,fw/2]
    # Each real bay is structural masonry surrounding a recessed glass aperture.
    for i,x in enumerate(centers):
        left,right=bounds[i:i+2];width=right-left;xc=(left+right)/2
        # At ground the facade has low segmental-style arches; centre is the door.
        b.bay(xc,width,0,0,4.8,.35,3.45,3.0 if i!=2 else 3.3,True,0,False,True)
        if i in [0,4]:
            b.bay(xc,width,0,4.8,11.4,5.6,9.8,2.25,True,2,True)
            b.bay(xc,width,0,11.4,17.8,12.3,16.65,2.25,False,1,True)
        else:
            b.bay(xc,width,.32,4.8,11.4,5.2,10.35,4.15,True,0,True)
            b.bay(xc,width,.32,11.4,17.8,12.0,17.25,4.15,False,0,True)
            # Circular frieze relief between the two window storeys.
            for xx in [xc-1.75+j*.58 for j in range(7)]:
                pts=[(xx+.19*math.cos(a),-.05,11.48+.19*math.sin(a)) for a in [math.tau*k/20 for k in range(21)]];b.tube(pts,.045,1,6)
            # Hand-built scrolled acanthus-like spandrel relief, not a texture.
            for s in [-1,1]:
                b.scroll(xc+s*1.70,-.14,10.35,.75,s)
                for j in range(3):
                    b.tube([(xc+s*(1.0+j*.23),-.18,10.55),(xc+s*(1.5+j*.22),-.32,10.93),(xc+s*(1.8+j*.16),-.18,11.08)],.07,1,7)
            # Raised carved keystone centred over each lower arch.
            b.prism([(xc-.18,10.15),(xc+.18,10.15),(xc+.26,10.78),(xc-.26,10.78)],-.25,.3,1)
    # Two genuine round Ionic columns; flanking piers are flat, not extra columns.
    for x in [-2.825,2.825]:b.column(x,-.12,5.0,17.8,.49,False)
    for x in [-fw/2+.45,-9.3,9.3,fw/2-.45]:
        b.box(x,-.06,11.5,.90,.40,12.8,1);b.box(x,-.16,5.1,1.2,.6,.48,1)
        b.box(x,-.14,17.7,1.4,.6,.5,1);b.scroll(x,-.45,17.15,.65,1)
    # Complete broad entablature and deeply projecting dental cornice.
    b.box(0,.18,19.15,fw,.70,2.7,0)
    for z in [4.8,17.9,18.3,20.15]:b.cornice(0,fw+.25,z,0,.65,z>20)
    b.cornice(0,fw+1.1,20.65,0,1.15,True)
    # Roof slab and carved parapet, with two triangular pavilion caps.
    b.box(0,.15,22.0,fw,.62,1.8,0);b.box(0,.10,22.96,fw+.12,.82,.18,1)
    for x in [-12.6,12.6]:
        b.box(x,.05,23.15,3.4,.85,1.55,0);b.pediment(x,-.14,24.0,3.8,.7)
    b.box(0,.06,23.2,3.0,.78,1.65,0);b.box(0,-.1,24.12,3.4,1.0,.22,1)
    for x in [-16.2,-8.6,-3.6,3.6,8.6,16.2]:
        b.scroll(x,-.15,23.45,.8,1 if x<0 else -1)
    # Actual central projecting portal with pilasters and triangular hood.
    for x in [-2.05,2.05]:
        b.column(x,-.92,.15,4.45,.27,False)
        b.box(x,-.78,2.3,.48,.55,4.4,1)
    b.cornice(0,5.5,4.5,-.65,.85,True);b.pediment(0,-.95,5.1,5.9,1.0)
    b.box(0,-.92,4.22,4.2,.24,.58,2)
    for i in range(3):
        h=(3-i)*.10;b.box(0,-.55-i*.32,h/2,5.3,.40,h,1)
    # Low wrought-iron railings leave the entry itself open.
    for side in [-1,1]:
        for i in range(25):b.box(side*(3.1+i*.48),-1.0,.65,.035,.05,1.3,7)
        b.box(side*8.9,-1,1.23,11.6,.06,.05,7)
    b.lathe(0,.15,[(24.2,.07),(29.0,.045)],2,12)
    b.geom([(0,.12,28.8),(1.45,.24,28.6),(1.55,.28,27.75),(0,.12,28.05)],[(0,1,2,3)],11)
    return {'body_roof_m':21.4,'parapet_caps_m':24.7,'flagpole_top_m':29.0,'front_bays':5,'round_ionic_columns':2,
            'photo_based_estimates':['all vertical dimensions','shallow sculptural relief interpretations','side and rear window cadence'],
            'explicit_omissions':['exact human figure relief sculpture','office interiors','surveyed rear elevation ornament']}


def text_mesh(body,loc,size,material_slot,front,model):
    curve=bpy.data.curves.new('Raised facade inscription','FONT');curve.body=body;curve.align_x='CENTER';curve.size=size;curve.extrude=.018;curve.bevel_depth=.006;curve.resolution_u=4
    font=HERE/'assets/inscriptions-subset.otf'
    if not font.exists():font=Path('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc')
    if font.exists():curve.font=bpy.data.fonts.load(str(font))
    obj=bpy.data.objects.new('Readable facade lettering',curve);bpy.context.collection.objects.link(obj)
    obj.location=(front[0]+loc[0],front[1]+loc[1],loc[2]);obj.rotation_euler=(math.pi/2,0,0)
    obj.data.materials.append(material_slot)
    bpy.context.view_layer.objects.active=obj;obj.select_set(True);bpy.ops.object.convert(target='MESH');obj.select_set(False)
    return obj


def camera(name,location,target,ortho=None,lens=48):
    data=bpy.data.cameras.new(name);obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj);obj.location=location
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler();data.lens=lens
    if ortho:data.type='ORTHO';data.ortho_scale=ortho
    return obj


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--building',choices=['hsbc','russo'],default='hsbc')
    parser.add_argument('--render',action='store_true')
    parser.add_argument('--output',type=Path,default=Path(os.environ.get('CLASSICAL_BANK_OUTPUT_DIR',str(HERE))),help='Output root; each building gets its own subdirectory')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    key='bund12' if args.building=='hsbc' else 'bund15';data=json.loads((HERE/'geometry-input.json').read_text())[key];out=args.output.resolve()/args.building;out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    mats=materials();b=Builder();details=(hsbc if args.building=='hsbc' else russo)(b,data)
    mesh=bpy.data.meshes.new('Architectural masonry with open apertures');mesh.from_pydata(b.verts,[],b.faces);mesh.update()
    obj=bpy.data.objects.new('HSBC Bund 12' if key=='bund12' else 'Russo Chinese Bank Bund 15',mesh);bpy.context.collection.objects.link(obj)
    for m in mats:mesh.materials.append(m)
    for p,mi,sm in zip(mesh.polygons,b.material,b.smooth):p.material_index=mi;p.use_smooth=sm
    texts=[];front=data['front_center']
    if key=='bund12':texts.append(text_mesh('上 海 浦 东 发 展 银 行',(0,-.58,6.99),.59,mats[9],front,obj))
    else:
        texts.append(text_mesh('中 国 外 汇 交 易 中 心',(0,-.24,18.75),.85,mats[9],front,obj))
        texts.append(text_mesh('全国银行间同业拆借中心',(0,-1.07,4.06),.27,mats[9],front,obj))
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
    for t in texts:t.select_set(True)
    bpy.context.view_layer.objects.active=obj;bpy.ops.object.join()
    # Bake architectural facade frame into east/north world metres, anchor at zero.
    u=data['world_basis_u'];v=data['world_basis_v']
    for vertex in obj.data.vertices:
        x,y,z=vertex.co;vertex.co=(u[0]*x+v[0]*y,u[1]*x+v[1]*y,z)
    obj['wgs84_longitude']=data['anchor'][0];obj['wgs84_latitude']=data['anchor'][1];obj['units']='metres';obj['height_accuracy']='photo-derived estimate, not surveyed';obj['true_recessed_window_count']=b.window_count
    scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    def world(p):return (u[0]*p[0]+v[0]*p[1],u[1]*p[0]+v[1]*p[1],p[2])
    W=data['front_width'];cx,cy=front;H=55 if key=='bund12' else 25
    camera_front=camera('Front elevation',world((cx,cy-W*1.9,H*.48)),world((cx,cy,H*.48)),W*1.13)
    camera_three=camera('Street three quarter',world((cx+W*.83,cy-W*1.12,H*.85)),world((cx,cy+W*.18,H*.35)),None,43)
    camera_close=camera('Street detail',world((cx+W*.13,cy-18,2.0)),world((cx+W*.04,cy+1,14 if key=='bund12' else 10)),None,35)
    # Model export excludes all presentation cameras, light and ground.
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.gltf(filepath=str(out/(args.building+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
    light_data=bpy.data.lights.new('Soft Shanghai daylight','SUN');light_data.energy=2.4;light_data.angle=.12
    light=bpy.data.objects.new('Soft Shanghai daylight',light_data);bpy.context.collection.objects.link(light)
    light.location=world((cx-45,cy-70,85));light.rotation_euler=(Vector(world((cx,cy,15)))-light.location).to_track_quat('-Z','Y').to_euler()
    scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.62,.72,.84,1);bg.inputs['Strength'].default_value=.65
    ground_material=material('Presentation pavement only',(.30,.32,.33),.9)
    bpy.ops.mesh.primitive_plane_add(size=260,location=(0,0,-.035));ground=bpy.context.object;ground.name='Presentation ground (not exported)';ground.data.materials.append(ground_material)
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False
    scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.camera=camera_three
    scene.render.film_transparent=False
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(args.building+'.blend')),compress=True)
    mesh.calc_loop_triangles();triangles=len(mesh.loop_triangles);size=(out/(args.building+'.glb')).stat().st_size
    low=[min(v.co[i] for v in obj.data.vertices) for i in range(3)];high=[max(v.co[i] for v in obj.data.vertices) for i in range(3)]
    metadata={'id':args.building,'building':data['name'],'anchor':data['anchor'],'model_axis':'GLB X east / Y up / Z south; local metres; ground 0','front_width_m':W,'footprint_source':data['source']['osm'],'footprint_courtyards_preserved':len(data['rings'])-1,'bounds_blender':{'min':low,'max':high},'triangles':triangles,'glb_bytes':size,'window_apertures':b.window_count,'window_recess_depth_m':.57,'wall_thickness_m':.62,'architecture':details,'no_solid_box_behind_windows':True}
    (out/'model.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    assert size<100_000_000 and triangles<300_000,(size,triangles)
    if args.render:
        for name,cam in [('front',camera_front),('three-quarter',camera_three),('street-detail',camera_close)]:
            scene.camera=cam;scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
    print('MODEL_VALIDATED',json.dumps(metadata,ensure_ascii=False))

if __name__=='__main__':main()
