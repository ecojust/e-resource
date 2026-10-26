"""Photo-informed geometric reconstruction of Bund 18, Shanghai.

Run: blender -b --python build_chartered_bank.py -- --render
Local model follows the independently verified OSM footprint; GLB axes are
X east / Y up / Z south, metres, ground zero, origin in metadata.json.
No photographs are used as textures. Recesses, mullions, columns, Ionic
volutes, balustrades, cornices, masonry, and doorway relief are actual meshes.
Unknown roof/side details and photo-derived height are labeled estimates.
"""
import bpy,math,json,sys,argparse,random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT);ap.add_argument('--render',action='store_true')
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);OUT=args.output;OUT.mkdir(parents=True,exist_ok=True)
DATA_ROOT = ROOT if (ROOT/'building-source.json').exists() else ROOT.parent
source=json.loads((DATA_ROOT/'building-source.json').read_text());photo=json.loads((DATA_ROOT/'photo-source.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for block in list(bpy.data.materials):bpy.data.materials.remove(block)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
model=bpy.data.collections.new('MODEL_Bund18_Chartered_Bank');scene.collection.children.link(model)
qa=bpy.data.collections.new('QA_lights_camera_ground');scene.collection.children.link(qa)
rng=random.Random(1801923)

def material(name,color,rough=.7,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
 return m
mats={}
for i,k in enumerate([-.035,-.017,0,.013,.025]):mats['stone'+str(i)]=material('Limestone_'+str(i),(.60+k,.565+k,.49+k),.74)
mats['trim']=material('Carved_limestone_trim',(.68,.64,.56),.65)
mats['darkstone']=material('Recessed_limestone',(.39,.37,.32),.85)
mats['glass']=material('Deep_blue_glass',(.12,.14,.16),.25,.05)
mats['glass2']=material('Reflected_slate_glass',(.16,.18,.20),.28,.05)
mats['bronze']=material('Patinated_bronze_frames',(.085,.105,.095),.37,.65)
mats['gold']=material('Aged_brass_details',(.39,.30,.13),.35,.65)
mats['roof']=material('Roof_zinc',(.20,.23,.23),.62,.35)
mats['interior']=material('Interior_shadow',(.09,.085,.07),.9)
mats['red']=material('Flag_red',(.61,.025,.025),.65)

# Basis is derived from the actual east edge, not a bounding-box guess.
ends=source['streetfront']['candidate_edges'][0]['endpoints_local_east_north_m'];A=Vector(ends[0]);B=Vector(ends[1]);T=(B-A).normalized();N=Vector((-T.y,T.x));C=(A+B)/2;W=(B-A).length
poly_en=source['model_geometry_local_east_north_m']['coordinates'][0][:-1]
polygon=[((Vector(p)-C).dot(T),(Vector(p)-C).dot(N)) for p in poly_en]
D=max(y for x,y in polygon);H=24.65

class Meshes:
 def __init__(self):self.data={}
 def mesh(self,name,verts,faces):
  vs,fs=self.data.setdefault(name,([],[]));base=len(vs);vs.extend(verts);fs.extend([tuple(base+i for i in f) for f in faces])
 def box(self,name,x,y,z,dx,dy,dz):
  if min(dx,dy,dz)<=0:return
  a=dx/2;b=dy/2;c=dz/2
  self.mesh(name,[(x+i*a,y+j*b,z+k*c) for i,j,k in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
 def prism(self,name,outline,y0,y1):
  n=len(outline);vs=[(x,y,z) for y in [y0,y1] for x,z in outline];faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
  faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n));self.mesh(name,vs,faces)
 def tube(self,name,points,radius=.025,sides=8):
  points=[Vector(p) for p in points];vs=[]
  for i,p in enumerate(points):
   direction=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized();aux=Vector((0,0,1))
   if abs(direction.dot(aux))>.95:aux=Vector((0,1,0))
   u=direction.cross(aux).normalized();v=direction.cross(u).normalized()
   vs.extend(tuple(p+radius*(math.cos(j*math.tau/sides)*u+math.sin(j*math.tau/sides)*v)) for j in range(sides))
  fs=[]
  for i in range(len(points)-1):
   for j in range(sides):a=i*sides+j;b=i*sides+(j+1)%sides;fs.append((a,b,b+sides,a+sides))
  fs.extend([tuple(range(sides-1,-1,-1)),tuple((len(points)-1)*sides+j for j in range(sides))]);self.mesh(name,vs,fs)
 def lathe(self,name,x,y,profile,segments=32):
  vs=[(x+r*math.cos(j*math.tau/segments),y+r*math.sin(j*math.tau/segments),z) for z,r in profile for j in range(segments)]
  fs=[]
  for k in range(len(profile)-1):
   for j in range(segments):a=k*segments+j;b=k*segments+(j+1)%segments;fs.append((a,b,b+segments,a+segments))
  fs +=[tuple(range(segments-1,-1,-1)),tuple((len(profile)-1)*segments+j for j in range(segments))];self.mesh(name,vs,fs)
M=Meshes()
box=M.box

def stone():return 'stone'+str(rng.randrange(5))
def framebox(mat,x,y,z,w,d,h,mapper=None):
 if mapper is None:box(mat,x,y,z,w,d,h);return
 vs=[mapper(x+i*w/2,y+j*d/2,z+k*h/2) for i,j,k in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
 M.mesh(mat,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])

def wall_rect(x0,x1,z0,z1,holes,mapper=None,masonry=False):
 xs=sorted(set([x0,x1]+[max(x0,min(x1,v)) for h in holes for v in h[:2]]));zs=sorted(set([z0,z1]+[max(z0,min(z1,v)) for h in holes for v in h[2:]]))
 for a,b in zip(xs,xs[1:]):
  for c,d in zip(zs,zs[1:]):
   if b-a<.01 or d-c<.01:continue
   if any(h[0]<(a+b)/2<h[1] and h[2]<(c+d)/2<h[3] for h in holes):continue
   if masonry:
    rows=max(1,math.ceil((d-c)/.55));cols=max(1,math.ceil((b-a)/1.15))
    for row in range(rows):
     for col in range(cols):
      xx=a+(col+.5)*(b-a)/cols;zz=c+(row+.5)*(d-c)/rows
      framebox(stone(),xx,.27,zz,(b-a)/cols-.012,.54,(d-c)/rows-.014,mapper)
   else:framebox(stone(),(a+b)/2,.24,(c+d)/2,b-a,.48,d-c,mapper)

def rect_window(x,z,w,h,depth=.33,cols=3,rows=3,mapper=None,frame=.09,reveal=True):
 # Glass is genuinely behind a wall opening, with stone jamb and sill depth.
 framebox('glass' if rng.random()<.7 else 'glass2',x,depth+.08,z,w-.08,.045,h-.08,mapper)
 for xx in [x-w/2,x+w/2]:framebox('bronze',xx,depth,z,frame,.14,h,mapper)
 for zz in [z-h/2,z+h/2]:framebox('bronze',x,depth,zz,w,.14,frame,mapper)
 for k in range(1,cols):framebox('bronze',x-w/2+w*k/cols,depth-.015,z,.044,.12,h,mapper)
 for k in range(1,rows):framebox('bronze',x,depth-.015,z-h/2+h*k/rows,w,.12,.045,mapper)
 if reveal:
  for xx in [x-w/2-.07,x+w/2+.07]:framebox('trim',xx,.18,z,.14,.42,h+.22,mapper)
  framebox('trim',x,-.045,z-h/2-.08,w+.25,.60,.16,mapper)

def horizontal_profile(z,width=None,depth=.45):
 width=W if width is None else width
 for zz,front,hh in [(z,.12,.14),(z+.13,.32,.12),(z+.26,.48,.13),(z+.42,depth,.18)]:box('trim',0,-front/2,zz,width+.25+front,front+.55,hh)

def rectangle_relief(x,z,w,h,y=-.10):
 for xx in [x-w/2,x+w/2]:box('trim',xx,y,z,.065,.10,h)
 for zz in [z-h/2,z+h/2]:box('trim',x,y,zz,w,.10,.065)

def rosette(x,y,z,r=.16,petals=10):
 # Raised circular heart and radial petals, no flat decal.
 M.tube('trim',[(x+r*math.cos(i*math.tau/48),y,z+r*math.sin(i*math.tau/48)) for i in range(49)],.027,6)
 for k in range(petals):
  a=k*math.tau/petals;M.tube('trim',[(x+.04*math.cos(a),y-.02,z+.04*math.sin(a)),(x+r*.78*math.cos(a-.14),y-.05,z+r*.78*math.sin(a-.14)),(x+r*.86*math.cos(a),y-.06,z+r*.86*math.sin(a)),(x+r*.78*math.cos(a+.14),y-.05,z+r*.78*math.sin(a+.14)),(x+.04*math.cos(a),y-.02,z+.04*math.sin(a))],.018,5)

def balustrade(x,z,width,y=-.7):
 box('bronze',x,y,z+.72,width,.07,.055);box('bronze',x,y,z+.08,width,.07,.055)
 count=max(3,int(width/.20))
 for k in range(count+1):
  xx=x-width/2+k*width/count;box('bronze',xx,y,z+.4,.035,.05,.65)
 for k in range(max(1,int(width/.48))):
  xx=x-width/2+.24+k*.48
  M.tube('bronze',[(xx+.115*math.cos(j*math.tau/16),y,z+.40+.19*math.sin(j*math.tau/16)) for j in range(17)],.016,5)
 for xx in [x-width/2,x+width/2]:
  box('bronze',xx,y,z+.42,.085,.09,.9);M.lathe('gold',xx,y,[(z+.85,.065),(z+.94,.09),(z+1,.025)],12)

# Front opening layout measured proportionally from the 2021 frontal photograph.
central=5.05;side=11.30
holes=[(-6.76,6.76,5.5,17.20)]
for x in [-side,side]:holes += [(x-1.05,x+1.05,8.70,12.40),(x-.78,x+.78,14.50,17.00)]
for x,w in [(-side,1.9),(-central,2.25),(0,2.35),(central,2.25),(side,1.9)]:holes.append((x-w/2,x+w/2,.25,4.18 if x else 4.75))
for x in [-side,side]:holes.append((x-.75,x+.75,19.35,21.55))
for x in [-central,0,central]:
 holes.append((x-.72,x+.72,19.35,21.55))
 for dx in [-1.48,1.48]:holes.append((x+dx-.21,x+dx+.21,19.35,21.55))
wall_rect(-W/2,W/2,0,23.1,holes,masonry=True)

# Ground-floor open display bays, deep stone reveals and articulated central door.
for x,w in [(-side,1.9),(-central,2.25),(central,2.25),(side,1.9)]:
 rect_window(x,2.215,w,3.93,.36,2,1)
 box('darkstone',x,.08,.18,w+.16,.45,.22)
 # Flat voussoir arch: individual wedge-shaped stones around the opening.
 span=w+.5
 for k in range(7):
  a=-span/2+k*span/7;b=-span/2+(k+1)*span/7
  topA=4.80-.22*abs(a)/(span/2);topB=4.80-.22*abs(b)/(span/2)
  M.prism('trim',[(x+a+.012,4.25),(x+b-.012,4.25),(x+b-.012,topB),(x+a+.012,topA)],-.12,.19)
# Door: six inset panels with circular relief, handles and frame mouldings.
box('bronze',0,.28,2.5,2.24,.15,4.5)
for x in [-.57,.57]:
 for z in [1.08,2.31,3.54]:
  box('interior',x,.18,z,.92,.035,.95)
  for xx in [x-.46,x+.46]:box('bronze',xx,.11,z,.055,.11,.95)
  for zz in [z-.475,z+.475]:box('bronze',x,.11,zz,.94,.11,.055)
  M.tube('bronze',[(x+.31*math.cos(j*math.tau/40),.07,z+.35*math.sin(j*math.tau/40)) for j in range(41)],.035,8)
  for k in range(8):
   a=k*math.tau/8;M.tube('bronze',[(x,.045,z),(x+.25*math.cos(a),.025,z+.27*math.sin(a))],.018,6)
 box('gold',x*.20,.04,2.22,.06,.09,.36)
for xx in [-1.43,1.43]:
 box('trim',xx,-.20,2.60,.38,.65,5.20);box('trim',xx,-.55,2.65,.07,.07,4.40)
for zz,w,dd,hh in [(4.90,3.25,.75,.18),(5.08,3.50,.95,.14),(5.27,3.62,1.05,.20),(5.53,3.30,.60,.22),(5.84,3.40,.55,.36)]:box('trim',0,-dd/2,zz,w,dd,hh)
for xx in [-1.43,1.43]:rosette(xx,-.59,4.48,.13,8)
rosette(0,-.49,5.88,.38,16)
# Layered base entablature runs across entire facade.
horizontal_profile(4.75,depth=.58)

# Portico interiors: soffit, back plane framing, three paired storey windows.
box('darkstone',0,1.05,17.05,13.45,2.0,.22)
for x in [-central,0,central]:
 rect_window(x,6.46,3.05,.85,1.10,5,2,reveal=False)
 rect_window(x,9.64,3.05,3.94,1.10,3,1,reveal=False)
 box('bronze',x,1.085,10.93,3.05,.12,.045)
 rect_window(x,14.97,3.05,2.60,1.10,3,3,reveal=False)
 box('bronze',x,1.10,12.87,3.12,.23,.86)
 rectangle_relief(x,12.87,2.50,.44,1.00)
 for dx in [-.95,-.55,.55,.95]:rosette(x+dx,.94,12.87,.11,6)
 for zz in [7.29,12.08,13.45]:box('bronze',x,1.04,zz,3.12,.32,.17)
 balustrade(x,5.85,3.12,y=.08)
for x,w in [(-6.55,.43),(-central/2,.63),(central/2,.63),(6.55,.43)]:box('bronze',x,1.24,11.31,w,.16,11.53)
# Two true circular Ionic columns, gently tapered shafts with profiled bases.
for x in [-central/2,central/2]:
 box('trim',x,-.05,5.64,1.42,1.40,.34)
 profile=[(5.81,.70),(5.91,.70),(6.02,.61),(6.13,.68),(6.25,.67),(6.36,.58),(6.48,.58),(6.58,.54),(16.16,.47),(16.27,.52),(16.37,.56),(16.49,.59),(16.59,.70)]
 M.lathe('trim',x,-.05,[(z,r*1.25) for z,r in profile],48)
 for zz in [8.50,11.00,13.50]:M.lathe('stone2',x,-.05,[(zz-.012,1.25*(.54-(zz-6.58)*.0073)),(zz+.012,1.25*(.541-(zz-6.58)*.0073))],48)
 box('trim',x,-.05,16.76,1.66,1.35,.22)
 box('trim',x,-.05,16.93,1.76,1.45,.12)
 for yy in [-.69,.57]:
  for sign in [-1,1]:
   pts=[]
   for k in range(65):
    t=k/64*math.pi*4.0;r=.26*(1-k/64)+.025
    pts.append((x+sign*.54+sign*r*math.cos(t),yy,16.54+r*math.sin(t)))
   M.tube('trim',pts,.045,8)
 for i in range(9):box('trim',x-.47+i*.117,-.65,16.31,.045,.08,.14)

# Side bays: inset upper windows, lower French windows, pediments and iron balconies.
for x in [-side,side]:
 rect_window(x,10.55,2.10,3.70,.36,2,4)
 rect_window(x,15.75,1.56,2.50,.36,2,2)
 for dx in [-1.22,1.22]:box('trim',x+dx,-.16,10.63,.18,.40,4.00)
 for z,w in [(8.05,2.75),(13.07,2.85),(13.27,3.02)]:box('trim',x,-.22,z,w,.65,.16)
 M.prism('trim',[(x-1.6,13.37),(x+1.6,13.37),(x,14.15)],-.50,.22)
 M.prism('stone1',[(x-1.24,13.48),(x+1.24,13.48),(x,13.97)],-.54,-.48)
 for sign in [-1,1]:M.tube('trim',[(x+sign*1.62,-.60,13.36),(x,-.60,14.18)],.07,8)
 rosette(x,-.64,14.13,.105,8)
 box('trim',x,-.53,8.01,3.12,1.22,.22);box('trim',x,-.50,7.85,2.85,1.08,.12)
 balustrade(x,8.08,2.85,y=-1.08)
 for dx in [-1.00,1.00]:
  M.prism('trim',[(x+dx-.18,7.10),(x+dx+.18,7.10),(x+dx+.22,7.70),(x+dx+.30,7.87),(x+dx-.30,7.87),(x+dx-.22,7.70)],-.76,-.05)
  rosette(x+dx,-.81,7.40,.15,8)
# Wide pilasters framing the recessed central composition.
for x in [-8.10,8.10,-W/2+.22,W/2-.22]:
 box('trim',x,-.07,11.26,.50,.23,11.60)
 for zz,ww,hh in [(5.45,.79,.20),(5.70,.63,.22),(16.80,.72,.18),(17.00,.95,.18),(17.22,1.12,.20)]:box('trim',x,-.10,zz,ww,.42,hh)

# Entablature and dentils separate the upper attic storey.
horizontal_profile(17.36,depth=.75)
box('stone2',0,.03,18.25,W,.56,.48)
for x in [-central/2,central/2]:M.tube('trim',[(x+.19*math.cos(k*math.tau/36),-.275,18.25+.19*math.sin(k*math.tau/36)) for k in range(37)],.025,6)
for k in range(int(W/.22)):
 x=-W/2+.13+k*.22;box('trim',x,-.43,17.65,.10,.19,.15)
# Attic windows: wide centre openings flanked by genuinely narrow vertical lights.
for x in [-side,side]:rect_window(x,20.45,1.50,2.20,.37,3,4)
for x in [-central,0,central]:
 rect_window(x,20.45,1.44,2.20,.37,3,4)
 for dx in [-1.48,1.48]:rect_window(x+dx,20.45,.42,2.20,.37,1,4,frame=.055)
# Carved fan relief panels and shallow archivolt bars.
for x in [-8.10,8.10]:
 rectangle_relief(x,20.50,1.52,2.20,-.11)
 box('trim',x,-.11,19.70,1.12,.15,.17)
 for k in range(13):
  a=math.pi*.12+k*math.pi*.76/12
  M.tube('trim',[(x,-.16,19.85),(x+.62*math.cos(a),-.19,19.85+1.35*math.sin(a))],.027,6)
for x in [-2.2,2.2]:
 box('trim',x,-.14,22.00,.34,.25,.42);rosette(x,-.30,21.91,.10,8)
# Deep roof cornice: layered string courses, modillions and dentil strip.
for z,w,front,h in [(22.50,W+.25,.20,.18),(22.72,W+.5,.42,.19),(22.94,W+.8,.68,.20),(23.38,W+1.15,.95,.18),(23.59,W+1.25,1.05,.15),(23.85,W+1.38,1.10,.28),(24.10,W+1.48,1.13,.16),(24.32,W+1.55,1.16,.25)]:box('trim',0,-front/2,z,w,front+.42,h)
for k in range(int(W/.30)):
 x=-W/2+.17+k*.30;box('trim',x,-.52,23.11,.13,.55,.26)
for k in range(int(W/.75)):
 x=-W/2+.36+k*.75;box('trim',x,-.35,23.33,.22,.80,.25)

# Remaining footprint walls are genuine perforated shells. Rear/side openings
# are a stated approximation because only the river facade is documented.
for idx,p in enumerate(polygon):
 q=polygon[(idx+1)%len(polygon)];u=Vector((q[0]-p[0],q[1]-p[1]));length=u.length;u.normalize();inside=Vector((-u.y,u.x))
 if abs(p[1])<.05 and abs(q[1])<.05:continue
 def mapper(a,d,z,p=p,u=u,inside=inside):return (p[0]+u.x*a+inside.x*d,p[1]+u.y*a+inside.y*d,z)
 if length<5:
  wall_rect(0,length,0,24.15,[],mapper);continue
 n=max(1,int((length-1.6)/3.8));centers=[(k+.5)*length/n for k in range(n)]
 rows=[(2.65,3.70),(6.85,2.45),(10.2,2.45),(13.55,2.45),(16.8,2.1),(20.45,2.20)]
 hls=[(x-.77,x+.77,z-h/2,z+h/2) for x in centers for z,h in rows]
 wall_rect(0,length,0,24.15,hls,mapper)
 for x in centers:
  for z,h in rows:rect_window(x,z,1.54,h,.32,2,3,mapper)
 for z in [4.95,17.70,22.85,24.15]:framebox('trim',length/2,-.13,z,length+.15,.55,.22,mapper)
# Horizontal slabs make actual interior depth, rather than solid extrusion.
def clip_front(poly,miny):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  ina=a[1]>=miny;inb=b[1]>=miny
  if ina:out.append(a)
  if ina!=inb:
   t=(miny-a[1])/(b[1]-a[1]);out.append((a[0]+t*(b[0]-a[0]),miny))
 return out

def slab(poly,z,thickness,mat):
 n=len(poly);vs=[(x,y,zz) for zz in [z,z+thickness] for x,y in poly]
 fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];M.mesh(mat,vs,fs)
for z in [0,5.2,8.2,11.4,14.6,18.1,21.8]:slab(clip_front(polygon,1.65),z,.17,'interior')
slab(polygon,24.18,.22,'roof')
# Setback roof pavilion and low triangular pediment, as seen above the main eave.
atticW=15.8;atticY=3.2;atticZ=24.43
attic_holes=[]
for k in range(9):
 x=(k-4)*1.43;attic_holes.append((x-.44,x+.44,24.95,25.85))
wall_rect(-atticW/2,atticW/2,atticZ,26.65,attic_holes,mapper=lambda x,y,z:(x,y+atticY,z),masonry=True)
for k in range(9):rect_window((k-4)*1.43,25.40,.88,.90,.30,2,2,mapper=lambda x,y,z:(x,y+atticY,z),frame=.055)
for x in [-atticW/2,atticW/2]:box('stone2',x,15,25.55,.45,23.6,2.25)
box('stone2',0,26.8,25.55,atticW,.45,2.25)
box('roof',0,15,26.7,atticW+1,24.5,.25)
M.prism('stone2',[(-atticW/2-.35,26.65),(atticW/2+.35,26.65),(0,28.20)],atticY-.24,atticY+.40)
for zz,rr in [(0,.07),(.12,.05)]:
 M.tube('trim',[(-atticW/2-.5,atticY-.36,26.63+zz),(0,atticY-.36,28.24+zz),(atticW/2+.5,atticY-.36,26.63+zz)],rr,8)
box('trim',0,atticY-.27,26.60,atticW+1,.55,.18)
rosette(0,atticY-.43,28.20,.17,10)
# Terrace railing is visible above the cornice; continue along rooftop sides.
balustrade(0,24.35,W-.55,y=.60)
for sign in [-1,1]:
 x=sign*(W/2-.55)
 M.tube('bronze',[(x,1,25.1),(x,18,25.1)],.035,8)
 for y in range(1,19):box('bronze',x,y,24.72,.04,.04,.77)
# Flag pole: geometry only; no copied image or text texture.
M.lathe('bronze',0,atticY+.45,[(28.2,.07),(34.45,.035)],12)
flag=[];faces=[]
for i in range(13):
 for j in range(5):
  x=.05+i*.15;y=atticY+.45+.10*math.sin(i*.6+j*.3);z=34.2-j*.24-.08*i/12
  flag.append((x,y,z))
for i in range(12):
 for j in range(4):a=i*5+j;faces.append((a,a+5,a+6,a+1))
M.mesh('red',flag,faces)
# Raised stars remain small, original vector geometry rather than a texture.
for xx,zz,rr in [(.36,33.90,.16),(.64,34.06,.055),(.77,33.92,.055),(.78,33.74,.055),(.66,33.61,.055)]:
 outline=[(xx+(rr if i%2==0 else rr*.42)*math.sin(i*math.pi/5),zz+(rr if i%2==0 else rr*.42)*math.cos(i*math.pi/5)) for i in range(10)]
 M.prism('gold',outline,atticY+.30,atticY+.32)

# Build a compact material-batched native scene, transformed into local true ENU.
objects=[];triangles=0
for key,(vertices,faces) in M.data.items():
 en=[(C.x+T.x*x+N.x*y,C.y+T.y*x+N.y*y,z*1.037) for x,y,z in vertices]
 mesh=bpy.data.meshes.new('Bund18_'+key);mesh.from_pydata(en,[],faces);mesh.materials.append(mats[key]);mesh.update();mesh.calc_loop_triangles();triangles+=len(mesh.loop_triangles)
 obj=bpy.data.objects.new('Bund18_'+key,mesh);model.objects.link(obj);objects.append(obj)
 # Smooth only curved tube/lathe strips would erase stone edges if global; leave
 # geometric normals for walls and use 48-sided columns for rounded silhouettes.
 obj['building']='Bund18 Chartered Bank, 1923';obj['detail']='Photo-proportioned geometry; front photographic material assigned separately'
assert triangles<300000,triangles
# Export only the building, keeping rendering helpers out of GLB.
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:obj.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.export_scene.gltf(filepath=str(OUT/'chartered-bank.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_materials='EXPORT')

# Architectural studio lighting and three repeatable cameras for inspection.
def relink(obj,collection):
 for c in list(obj.users_collection):c.objects.unlink(obj)
 collection.objects.link(obj)
def worldpoint(p):x,y,z=p;return Vector((C.x+T.x*x+N.x*y,C.y+T.y*x+N.y*y,z))
def camera(name,location,target,lens=50):
 bpy.ops.object.camera_add(location=worldpoint(location));o=bpy.context.object;o.name=name;relink(o,qa);o.rotation_euler=(worldpoint(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=lens;o.data.clip_end=1000;return o
cam_front=camera('Camera_front_elevation',(0,-70,14.8),(0,2,14.8),58)
cam_three=camera('Camera_three_quarter',(44,-66,33),(0,8,13),48)
cam_detail=camera('Camera_column_and_door',(15,-37,13),(0,0,11),58)
for name,loc,energy,size in [('Key',(-30,-32,50),4500,20),('Fill',(20,-15,26),2400,16),('Roof',(5,35,50),3600,20)]:
 bpy.ops.object.light_add(type='AREA',location=worldpoint(loc));o=bpy.context.object;o.name=name;relink(o,qa);o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(worldpoint((0,8,12))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='SUN',location=(0,0,50));sun=bpy.context.object;relink(sun,qa);sun.rotation_euler=(math.radians(28),math.radians(-25),math.radians(-30));sun.data.energy=2.0;sun.data.angle=math.radians(6)
bpy.ops.mesh.primitive_plane_add(size=240,location=(0,0,-.05));ground=bpy.context.object;ground.name='QA_ground_not_exported';relink(ground,qa);ground.data.materials.append(material('QA_paving',(.25,.27,.28),.95))
scene.world.color=(.28,.30,.34);scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.12;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.camera=cam_three
scene.render.resolution_x=1500;scene.render.resolution_y=1200
# Useful starting viewport, full building visible rather than clipped at 100m.
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.clip_end=2000;area.spaces.active.region_3d.view_distance=90;area.spaces.active.region_3d.view_location=worldpoint((0,8,13))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'chartered-bank.blend'))
metadata={'id':'bund18-chartered-bank','name_zh':'麦加利银行大楼（外滩18号）','name_en':'Chartered Bank Building, Bund 18','model':'chartered-bank.glb',
 'origin_longitude':source['origin_longitude'],'origin_latitude':source['origin_latitude'],'units':'metres','axes':'GLB X east, Y up, Z south','base_m':0,
 'frontage_m':round(W,3),'depth_m':round(D,3),'main_cornice_height_m':24.65,'roof_pediment_height_m':28.36,'max_height_including_flagpole_m':34.45,
 'height_quality':'estimated_from_frontage_and_2021_photo_proportions_not_surveyed','height_m':28.36,'source_num_floors':7,
 'front_edge_outward_azimuth_deg':source['streetfront']['candidate_edges'][0]['outward_azimuth_deg'],'triangles':triangles,'mesh_objects':len(objects),'textures':0,
 'geometry_detail':['two profiled round Ionic columns with 3D spiral volutes','deep three-bay portico and separate recessed glass/frame meshes','five open ground bays and decorated two-leaf doorway','side French windows, projecting balconies, iron railings and triangular pediments','attic slit windows and radial carved fan panels','layered cornices, individual modillions and dentils','roof terrace railing and setback pediment pavilion','perforated side/rear shells and interior floor slabs'],
 'evidence_limits':['front proportions derived from photograph, not a measured elevation','side/rear and rooftop depth are simplified because reference photographs do not document them','small sculptural motifs are geometric interpretations','existing OSM footprint uses current surveyed/mapped outline; its precision is not certified'],
 'source_footprint':source['osm']['url'],'source_footprint_license':'ODbL-1.0; © OpenStreetMap contributors',
 'reference_photo':{'page':photo['attribution_url'],'author':photo['author'],'license':photo['license'],'license_url':photo['license_url'],'used_as_texture':False},
 'replacement':source['replacement'],'geometry_authoring':'Original procedural reconstruction; no third-party model geometry or photographic texture embedded'}
metadata.update({'height_m':28.36*1.037,'main_cornice_height_m':24.65*1.037,'roof_pediment_height_m':28.36*1.037,'max_height_including_flagpole_m':max(v.co.z for ob in objects for v in ob.data.vertices),'photo_proportion_revision':'v4.3: geometry-changes.json','height_quality':'photo_proportioned_estimate_not_surveyed','geometry_authoring':'Original parametric geometry; optional photographic appearance applied by apply_photo.py'})
(OUT/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
if args.render:
 for name,cam,res in [('front-elevation',cam_front,(1500,1600)),('three-quarter',cam_three,(1600,1250)),('column-door-detail',cam_detail,(1400,1500))]:
  scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=res;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
print(json.dumps({'triangles':triangles,'meshes':len(objects),'glb_bytes':(OUT/'chartered-bank.glb').stat().st_size,'blend_bytes':(OUT/'chartered-bank.blend').stat().st_size,'frontage_m':W,'depth_m':D}))
