"""Photo-led architectural reconstructions of Bund 2 and 3.

blender --background --python build_classics.py
BUND_CLASSICS_OUTPUT=/path BUND_CLASSICS_RENDER=1 select output/rendering.
Coordinates are east/north/up in Blender, east/up/south in glTF.
All footprint vertices are from the supplied current OSM ways, not rectangles.
Decorative dimensions are photo interpretations; see metadata/evidence JSON.
"""
import bpy, json, math, os, sys
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from mesh_utils import Builder

STONE,TRIM,GLASS,FRAME,ROOF,METAL,DARK,BRONZE=range(8)
PALETTE=[('limestone',(0.57,0.54,0.48),.8,0),('carved pale stone',(0.74,0.71,0.64),.76,0),
 ('recessed blue grey glazing',(0.09,0.15,0.17),.25,.15),('painted window frames',(0.20,0.22,0.21),.62,0),
 ('weathered slate',(0.12,0.15,0.16),.9,0),('wrought iron',(0.10,0.11,0.105),.55,.5),
 ('deep shadow',(0.065,0.07,0.067),1,0),('aged cupola metal',(0.29,0.32,0.29),.64,.35)]

class Facade:
    def __init__(self,b,a,c):
        self.b=b;self.a=Vector((*a,0));self.c=Vector((*c,0));self.L=(self.c-self.a).length
        self.t=(self.c-self.a).normalized();self.n=Vector((self.t.y,-self.t.x,0));self.mid=(self.a+self.c)/2
    def p(self,u,z,d=0):return self.mid+self.t*u+self.n*d+Vector((0,0,z))
    def box(self,u,z,w,h,depth=.45,d=-.20,mat=STONE):
        self.b.box(self.p(u,z,d),(w,depth,h),mat,[self.t,self.n,Vector((0,0,1))])
    def beam(self,z,h,projection=.24,mat=TRIM,start=None,end=None):
        lo=-self.L/2 if start is None else start; hi=self.L/2 if end is None else end
        self.box((lo+hi)/2,z,hi-lo,h,.55+projection,projection/2-.15,mat)
    def poly(self,points,mat,depth=0):
        verts=[self.p(u,z,depth) for u,z in points]
        self.b.geom(verts,[tuple(range(len(verts)))],mat)
    def line(self,u0,z0,u1,z1,width=.08,depth=.08,d=.05,mat=FRAME):
        self.b.segment(self.p(u0,z0,d),self.p(u1,z1,d),width,depth,self.n,mat)
    def arch(self,u,spring,radius,width=.17,d=.08,mat=TRIM,segments=20):
        for j in range(segments):
            a=math.pi*j/segments;aa=math.pi*(j+1)/segments
            self.line(u+radius*math.cos(a),spring+radius*math.sin(a),u+radius*math.cos(aa),spring+radius*math.sin(aa),width,.17,d,mat)
    def window(self,u,z0,z1,w,arch=False,trim=True,mullions=2):
        # Glazing is recessed 24 cm behind the face. Actual jambs reveal depth.
        x0=u-w/2;x1=u+w/2; spring=z1-w/2 if arch else z1
        if arch:
            pts=[(x0,z0),(x1,z0)]+[(u+w/2*math.cos(math.pi*j/24),spring+w/2*math.sin(math.pi*j/24)) for j in range(25)]
            self.poly(pts,GLASS,-.24)
            self.arch(u,spring,w/2,.09,-.13,FRAME)
        else:self.box(u,(z0+z1)/2,w,z1-z0,.045,-.25,GLASS)
        for side in [-1,1]:
            self.box(u+side*w/2,(z0+spring)/2,.10,spring-z0,.38,-.09,TRIM)
            if trim:self.box(u+side*(w/2+.13),(z0+spring)/2,.18,spring-z0+.10,.18,.04,TRIM)
        self.box(u,z0-.05,w+.22,.10,.54,-.02,TRIM)
        if not arch:self.box(u,z1+.04,w+.22,.16,.32,-.02,TRIM)
        for i in range(1,mullions+1):
            uu=x0+w*i/(mullions+1);top=z1
            if arch:top=spring+math.sqrt(max(0,w*w/4-(uu-u)**2))
            self.line(uu,z0,uu,top,.065,.06,-.17,FRAME)
        rows=max(2,int((z1-z0)/1.05))
        for i in range(1,rows):
            zz=z0+(z1-z0)*i/rows
            half=w/2 if zz<=spring else math.sqrt(max(0,w*w/4-(zz-spring)**2))
            self.line(u-half,zz,u+half,zz,.055,.06,-.17,FRAME)
        if arch and trim:self.arch(u,spring,w/2+.14,.20,.04,TRIM)
    def cell(self,u,width,z0,z1,w,lo,hi,arch=False):
        # The limestone wall is assembled around each opening; no painted-on windows.
        if width-w>.001:
            for side in [-1,1]:
                self.box(u+side*(width+w)/4,(z0+z1)/2,(width-w)/2,z1-z0)
        if lo>z0:self.box(u,(z0+lo)/2,w,lo-z0)
        if hi<z1:self.box(u,(hi+z1)/2,w,z1-hi)
        if arch:
            r=w/2;s=hi-r
            for j in range(20):
                x=-r+2*r*j/20;xx=-r+2*r*(j+1)/20
                zz=s+math.sqrt(max(0,r*r-x*x));zzz=s+math.sqrt(max(0,r*r-xx*xx))
                self.poly([(u+x,zz),(u+xx,zzz),(u+xx,hi),(u+x,hi)],STONE,.025)
        self.window(u,lo,hi,w,arch)
    def pediment(self,u,z,w,arched=False):
        if arched:self.arch(u,z-w*.05,w*.47,.18,.18,TRIM,24)
        else:
            self.line(u-w/2,z,u,z+w*.26,.22,.28,.17,TRIM)
            self.line(u,z+w*.26,u+w/2,z,.22,.28,.17,TRIM)
        self.box(u,z,w+.2,.16,.42,.15,TRIM)
    def rail(self,u,z,w,height=.88,balusters=False):
        self.box(u,z,w,.18,.78,.40,TRIM)
        self.box(u,z+height,w,.13,.13,.73,TRIM if balusters else METAL)
        count=max(3,int(w/.34))
        for j in range(count+1):
            uu=u-w/2+j*w/count
            self.box(uu,z+height/2,.10 if balusters else .045,height,.11,.73,TRIM if balusters else METAL)
            if balusters:
                self.b.cylinder(self.p(uu,z+height*.52,.73),.095,.18,TRIM,10)
    def dentils(self,z,spacing=.46):
        count=int(self.L/spacing)
        for j in range(count):self.box(-self.L/2+(j+.5)*self.L/count,z,.20,.22,.45,.18,TRIM)
    def rustication(self,z0,z1,spacing=.63):
        for i in range(1,int((z1-z0)/spacing)):
            self.box(0,z0+i*spacing,self.L,.027,.045,.031,DARK)
    def garland(self,u,z,w):
        # Low relief festoon: the silhouette is photo-based, leaf carving simplified.
        last=None
        for j in range(25):
            x=-w/2+w*j/24;zz=z-.34*(1-(x/(w/2))**2)
            pt=self.p(u+x,zz,.20)
            self.b.cylinder(pt,.105,.13,TRIM,10,self.n)
            if last is not None:self.b.segment(last,pt,.11,.11,self.n,TRIM)
            last=pt
        for s in [-1,1]:
            c=self.p(u+s*w/2,z,.23)
            self.b.cylinder(c,.23,.13,TRIM,16,self.n)
            self.b.ring(c+self.n*.075,.23,.13,STONE,self.n,24)

def lathe(b,center,profile,mat=BRONZE,segments=40):
    x,y=center;v=[]
    for z,r in profile:
        for j in range(segments):
            a=math.tau*j/segments;v.append((x+r*math.cos(a),y+r*math.sin(a),z))
    faces=[]
    for k in range(len(profile)-1):
        for j in range(segments):faces.append((k*segments+j,k*segments+(j+1)%segments,(k+1)*segments+(j+1)%segments,(k+1)*segments+j))
    b.geom(v,faces,mat,True)

def column(b,xy,z0,z1,r,ionic=False):
    x,y=xy;h=z1-z0
    lathe(b,(x,y),[(z0,r*1.35),(z0+.18,r*1.35),(z0+.25,r*1.06),(z0+.45,r),(z1-.45,r*.84),(z1-.30,r),(z1-.10,r*1.3),(z1,r*1.3)],TRIM,24)
    b.box((x,y,z0+.10),(r*2.9,r*2.9,.20),TRIM)
    b.box((x,y,z1-.08),(r*2.8,r*2.8,.18),TRIM)
    if ionic:
        for dx in [-r*1.02,r*1.02]:
            b.cylinder((x+dx,y,z1-.23),r*.34,r*1.7,TRIM,20,axis=(0,1,0))

def shell(b,polygon,height):
    # Inner dark shell leaves a genuine setback behind the masonry window surrounds.
    b.outline([(x*.95,y*.95) for x,y in polygon],0,height,DARK)
    b.outline(polygon,0,.35,STONE)

def edge_facades(b,polygon):
    return [Facade(b,polygon[i],polygon[(i+1)%len(polygon)]) for i in range(len(polygon))]

def roof_hip(b,poly,z0,z1,shrink=.70):
    n=len(poly);v=[(x,y,z0) for x,y in poly]+[(x*shrink,y*shrink,z1) for x,y in poly]
    b.geom(v,[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]+[tuple(n+i for i in range(n))],ROOF)

def club_tower(b,f,u):
    # Twin open Baroque belvederes, rather than solid generic blocks.
    q=f.p(u,0,-1.4);x,y=q.x,q.y;w=4.7
    b.box((x,y,25.4),(w,w,2.4),TRIM,[f.t,f.n,Vector((0,0,1))])
    b.box((x,y,26.75),(w+.45,w+.45,.35),TRIM,[f.t,f.n,Vector((0,0,1))])
    for su in [-1,1]:
        for sd in [-1,1]:
            p=f.p(u+su*1.65,0,-1.4+sd*1.65)
            column(b,(p.x,p.y),27.0,31.2,.33)
    corners=[q+f.t*a+f.n*d for a,d in [(-2,-2),(2,-2),(2,2),(-2,2)]]
    for i in range(4):
        a,c=corners[i],corners[(i+1)%4];g=Facade(b,a.xy,c.xy)
        g.arch(0,30.35,1.38,.36,.0,TRIM,24)
        g.arch(0,30.35,1.58,.18,.0,TRIM,24)
        g.beam(27.1,.20,.12);g.rail(0,27.25,3.0,.75,True)
    lathe(b,(x,y),[(31.2,2.0),(31.45,2.0),(31.8,1.94),(32.4,1.72),(33.0,1.30),(33.45,.72),(33.60,.15)],TRIM,48)
    lathe(b,(x,y),[(33.5,.19),(33.8,.32),(34.05,.22),(34.4,.17),(34.75,.06),(35.0,0)],TRIM,24)

def build_club(c):
    b=Builder();p=c['polygon_local_east_north'];shell(b,p,23.8);fs=edge_facades(b,p)
    front=fs[4];L=front.L;wing=5.2;central=L-2*wing;bay=central/5
    # Other walls follow the measured stepped footprint, with modest interpreted windows.
    for idx,f in enumerate(fs):
        if idx==4:continue
        count=max(1,round(f.L/4.2));bw=f.L/count
        for j in range(count):
            u=-f.L/2+bw*(j+.5)
            for z0,z1 in [(0,6.1),(6.1,13.7),(13.7,18.4),(18.4,23.8)]:
                f.cell(u,bw,z0,z1,min(2.0,bw*.62),z0+1.1,z1-.75,False)
        for z in [6.1,18.4,23.8]:f.beam(z,.30,.25)
    # Central five bays, six Ionic columns; two end pavilions are separate masses.
    recessed=Facade(b,(front.a-front.n*.65).xy,(front.c-front.n*.65).xy)
    for j in range(5):
        u=-central/2+bay*(j+.5)
        recessed.cell(u,bay,0,6.1,2.30,.6,4.85,j%2==0)
        recessed.cell(u,bay,6.1,13.7,3.0,7.0,12.8,False)
        recessed.pediment(u,13.12,3.55,j%2==0)
        recessed.cell(u,bay,13.7,18.4,2.70,14.55,17.25)
        for k in range(3):
            uu=u+(k-1)*1.15
            front.cell(uu,1.15,19.5,23.8,.88,20.10,23.10,True)
        gap=bay-3*1.15
        for s in [-1,1]:front.box(u+s*(bay/2-gap/4),21.65,gap/2,4.3)
        front.rail(u,6.27,3.60,.82,True)
    for j in range(6):
        u=-central/2+j*bay;pos=front.p(u,0,.45)
        column(b,(pos.x,pos.y),6.38,18.12,.60,True)
    for s in [-1,1]:
        u=s*(L/2-wing/2)
        front.cell(u,wing,0,6.1,3.0,.55,5.6,True)
        front.cell(u,wing,6.1,13.7,3.0,7.1,12.7)
        front.pediment(u,13.08,3.55)
        front.cell(u,wing,13.7,18.4,2.9,14.52,17.32)
        front.cell(u,wing,19.5,24.1,3.9,20.0,23.56,True)
        front.pediment(u,24.0,5.3)
        front.garland(u,23.88,3.0)
        front.garland(u,6.95,2.35)
        front.rail(u,6.3,3.8,.88,True)
        # Corner pilasters and stone bands remain distinct from window glass.
        for e in [-1,1]:front.box(u+e*(wing/2-.26),12.2,.38,11.1,.5,.12,TRIM)
        club_tower(b,front,u)
    front.beam(6.1,.33,.52);front.beam(18.5,.44,.75);front.beam(19.2,.50,.62)
    front.dentils(18.87);front.beam(23.78,.24,.37)
    front.rustication(.55,6.0,.66)
    # Six-storey descriptions include one basement. Roof dormers are not another full floor.
    roof_hip(b,p,23.85,26.9,.72)
    for u in [-8.8,0,8.8]:
        front.box(u,25.40,3.65,2.2,1.60,-2.90,STONE)
        g=Facade(b,front.p(u-1.825,0,-1.48).xy,front.p(u+1.825,0,-1.48).xy)
        g.cell(0,3.65,24.30,26.50,2.65,24.55,26.12,False)
        g.beam(26.45,.20,.18)
    # Reversible present-day entrance canopy, dark pitched roof and two slender posts.
    front.box(0,3.28,7.7,.26,2.6,1.0,ROOF)
    for u in [-3.3,3.3]:front.box(u,1.58,.16,3.0,.16,2.05,METAL)
    return b,{'observedAboveGroundStoreys':5,'basementStoreys':1,'mainRoofRidgeM':26.9,
      'modelHeightM':35.0,'heightStatus':'Reported 26.9 m has no documented endpoint; roof ridge assignment and 35 m belvedere tips are photo-based estimates, not measured elevations.',
      'facadeStructure':'Seven principal axes: five central bays between six Ionic columns, two end pavilions; five groups of three attic arch windows; twin open Baroque belvederes and hipped/mansard-like dark roof.',
      'estimatedGeometry':['Facade vertical bands','Roof ridge and tower tip elevations','Rear facade openings','Sculptural capitals simplified','Dormer proportions']}

def union_tower(b,f):
    # The OSM northeast chamfer defines the tower/entrance axis.
    q=f.p(0,0,-2.8);u=f.t;n=f.n;w=5.6
    b.box((q.x,q.y,33.35),(w,w,2.15),STONE,[u,n,Vector((0,0,1))])
    b.box((q.x,q.y,34.5),(w+.55,w+.55,.38),TRIM,[u,n,Vector((0,0,1))])
    # Circular oculus, modeled ring and dark inset, immediately below the open shaft.
    c=f.p(0,33.45,.12);b.cylinder(c,.85,.08,GLASS,40,n);b.ring(c+n*.08,1.04,.83,TRIM,n,48)
    for aa in range(24):
        a=math.tau*aa/24;v=u*math.cos(a)+Vector((0,0,1))*math.sin(a)
        b.cylinder(c+n*.10+v*1.16,.10,.12,TRIM,10,n)
    # Four corners each use two columns, around a recessed central shaft.
    b.box((q.x,q.y,37.85),(2.9,2.9,6.3),DARK,[u,n,Vector((0,0,1))])
    shaft_corners=[q+u*a+n*d for a,d in [(-1.8,-1.8),(1.8,-1.8),(1.8,1.8),(-1.8,1.8)]]
    for i in range(4):
        aa,cc=shaft_corners[i],shaft_corners[(i+1)%4];g=Facade(b,aa.xy,cc.xy)
        g.cell(0,3.6,34.75,41.00,1.18,35.3,40.35,True)
        g.pediment(0,40.53,2.0,True)
    for su in [-1,1]:
        for sn in [-1,1]:
            for d in [-.28,.28]:
                xy=q+u*(su*2.05+d)+n*(sn*2.05)
                column(b,(xy.x,xy.y),34.75,40.60,.30)
    b.box((q.x,q.y,40.85),(w+.10,w+.10,.48),TRIM,[u,n,Vector((0,0,1))])
    b.box((q.x,q.y,41.22),(w-.15,w-.15,.25),STONE,[u,n,Vector((0,0,1))])
    b.cylinder((q.x,q.y,41.70),2.0,.80,STONE,8)
    b.cylinder((q.x,q.y,42.12),2.13,.20,TRIM,8)
    lathe(b,(q.x,q.y),[(42.2,.95),(42.3,1.13),(42.55,1.38),(42.90,1.43),(43.25,1.12),(43.43,.65),(43.52,.48),(43.74,.50),(43.90,.30),(44.06,.16),(44.15,0)],BRONZE,48)
    b.cylinder((q.x,q.y,44.9),.035,1.70,METAL,12)

def build_union(c):
    b=Builder();p=c['polygon_local_east_north'];shell(b,p,32.4);fs=edge_facades(b,p)
    bands=[(0,6.1,1.0,5.5,True),(6.1,11.7,7.0,10.95,False),(11.7,17.2,12.5,16.5,False),
           (17.2,23.2,18.0,22.4,True),(23.2,27.7,24.0,27.0,False),(27.7,32.4,28.4,31.85,True)]
    for idx,f in enumerate(fs):
        chamfer=idx==3; frontage=idx==2; street=idx==4
        count=1 if chamfer else 5 if frontage else 12 if street else max(2,round(f.L/5.5))
        bw=f.L/count
        for j in range(count):
            u=-f.L/2+(j+.5)*bw
            for floor,(z0,z1,lo,hi,arch) in enumerate(bands):
                w=min(3.1,bw*.59)
                if floor==0 and chamfer:w=4.35;lo=.10
                if floor==5 and not chamfer:
                    for d in [-bw*.19,bw*.19]:f.cell(u+d,bw/2,z0,z1,min(1.25,bw*.29),lo,hi,True)
                else:f.cell(u,bw,z0,z1,w,lo,hi,arch)
                if floor in [1,2]:
                    f.box(u,lo-.43,w-.20,.48,.12,.03,STONE)
                    for d in [-1,1]:f.box(u+d*(w/2+.31),(lo+hi)/2,.20,hi-lo+.25,.20,.02,TRIM)
                if floor==3 and (frontage or street):
                    f.box(u,hi+.24,w+1.0,.24,.45,.13,TRIM)
                    for d in [-1,1]:f.box(u+d*(w/2+.25),hi-.05,.28,.50,.42,.12,TRIM)
            if street or frontage:
                # Paired tall pilasters articulate the central three floors.
                for d in [-1,1]:
                    f.box(u+d*(bw/2-.18),14.70,.26,16.8,.23,.06,TRIM)
                if j in [0,count-1] or (street and j in [5,6]):
                    f.rail(u,17.45,min(3.75,bw*.85),.90,False)
            if chamfer:
                f.rail(0,17.42,4.8,.98,False);f.rail(0,27.78,4.9,.95,False)
                f.rail(0,6.25,4.4,.85,True)
                f.pediment(0,5.55,5.0,True)
        for z,h,proj in [(6.1,.26,.28),(11.7,.16,.14),(17.2,.24,.30),(23.2,.60,.80),(23.65,.18,.60),(27.7,.18,.17),(32.4,.42,.65)]:
            f.beam(z,h,proj)
        f.dentils(22.75);f.dentils(32.13,.48)
        f.rustication(.4,6.0,.61)
        # Roof terrace parapet and thin wrought-iron crest.
        f.beam(33.0,.76,.10,STONE);f.beam(33.43,.15,.22)
        if idx in [2,4]:f.rail(0,33.53,f.L-.7,.62,False)
        # Alternating raised quoin blocks at facade ends, true projecting geometry.
        for end in [-1,1]:
            for k in range(40):
                zz=.45+k*.80
                f.box(end*(f.L/2-.35),zz,.70 if k%2 else .95,.32,.18,.09,TRIM)
    b.outline(p,32.45,32.65,ROOF)
    union_tower(b,fs[3])
    return b,{'observedAboveGroundStoreys':6,'entranceLocalizedStoreys':7,'mainCorniceM':32.4,
      'modelHeightM':45.75,'heightStatus':'45.75 m is a secondary-source published overall height, not independently surveyed; all floor and roof/tower split elevations are photo estimates.',
      'facadeStructure':'Mapped northeast chamfer entrance; six main storeys, arches on ground/fourth/sixth, paired top-floor arches, strongly projected cornices, iron balconies, eight-column corner belvedere and gourd-shaped crown.',
      'estimatedGeometry':['Floor elevations','Facade bay widths; front five large bays and north twelve are photographic interpretations','Tower column/crown proportions','Hidden rear facade','Stone sculptural ornaments simplified']}

def material(name,color,rough,metal):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
    return m

def export(c,b,description,out):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    mesh=bpy.data.meshes.new(c['id']+' detailed geometry');mesh.from_pydata(b.vertices,[],b.faces);mesh.materials.clear()
    for args in PALETTE:mesh.materials.append(material(*args))
    mesh.update()
    for poly,mi,sm in zip(mesh.polygons,b.indices,b.smooth):poly.material_index=mi;poly.use_smooth=sm
    obj=bpy.data.objects.new(c['id'],mesh);bpy.context.collection.objects.link(obj);obj.select_set(True);bpy.context.view_layer.objects.active=obj
    mesh.calc_loop_triangles()
    # Remove collapsed ornamental tip/spandrel triangles; preserve every visible face.
    kept=[];face_meta=[];removed=0
    for tri in mesh.loop_triangles:
        a,bb,cc=[mesh.vertices[i].co for i in tri.vertices]
        if (bb-a).cross(cc-a).length*.5<=1e-10:removed+=1;continue
        kept.append(tuple(tri.vertices));poly=mesh.polygons[tri.polygon_index];face_meta.append((poly.material_index,poly.use_smooth))
    if removed:
        mesh.clear_geometry();mesh.from_pydata(b.vertices,[],kept);mesh.update()
        for poly,(mi,sm) in zip(mesh.polygons,face_meta):poly.material_index=mi;poly.use_smooth=sm
        mesh.calc_loop_triangles()
    triangles=len(mesh.loop_triangles)
    name={'bund02':'shanghai-club','bund03':'union-building','bund17':'north-china-daily-news'}[c['id']]
    path=out/(name+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_materials='EXPORT',export_extras=True)
    assert path.stat().st_size<100_000_000
    v=[tuple(x) for x in b.vertices];bounds=[[min(vv[k] for vv in v) for k in range(3)],[max(vv[k] for vv in v) for k in range(3)]]
    meta={'id':name,'candidateId':c['id'],'name':c['name_zh'],'historicBundNumber':c['historic_bund_number'],
      'anchorWGS84':[c['origin_longitude'],c['origin_latitude']],'coordinateSystem':'glTF x east, y up, z south; origin at OSM footprint centroid and ground; rotation already baked',
      'rotationRequired':False,'footprint':c['geometry'],'footprintAreaM2':c['dimensions']['footprint_area_m2'],
      'groundPolygonLocalXZ':[[x,-y] for x,y in c['polygon_local_east_north']],
      'mappedFacadeNormalAzimuthDegrees':c['streetfront']['candidate_edges'][0]['outward_azimuth_deg'],
      'replaceExactBuildingIds':c['replacement']['building_ids'],'exclusionByRadius':False,
      'coverage':{'completeCandidateFootprint':True,'includesSideAndRearMass':True,'includesRoof':True,'facadeOnly':False,'detailLimit':'Street-facing recognizable details follow photographs; hidden rear openings and many vertical dimensions remain estimates.'},
      'source':c['osm']['url'],'sourceLicense':'OSM derived geometry ODbL-1.0, attribution OpenStreetMap contributors',
      'geometryStatus':'Architectural interpretation from attributed reference photographs; footprint measured from OSM; not a measured heritage survey',
      'bytes':path.stat().st_size,'triangles':triangles,'vertices':len(mesh.vertices),'boundsBlenderXYZ':bounds,**description}
    (out/(name+'.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(name+'.blend')))
    if os.environ.get('BUND_CLASSICS_RENDER','1')!='0':render(obj,name,out,bounds)
    print(json.dumps({'model':name,'bytes':path.stat().st_size,'triangles':triangles,'height':bounds[1][2]},ensure_ascii=False))

def render(obj,name,out,bounds):
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.12
    scene.render.resolution_x=1200;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
    scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.59,.64,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    bpy.ops.object.light_add(type='AREA',location=(65,35,105));bpy.context.object.data.energy=65000;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=55
    bpy.ops.object.light_add(type='SUN',location=(-20,-20,70));bpy.context.object.rotation_euler=(.4,-.4,-.3);bpy.context.object.data.energy=2.0
    target=Vector((0,0,bounds[1][2]*.43))
    bpy.ops.object.camera_add(location=(100,94,65) if name=='union-building' else (115,2,47) if name=='shanghai-club' else (115,5,43))
    camera=bpy.context.object;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=95 if name=='union-building' else 76 if name=='shanghai-club' else 65;scene.camera=camera
    bpy.ops.mesh.primitive_plane_add(size=240,location=(0,0,-.08));plane=bpy.context.object;plane.data.materials.append(material('verification ground',(.30,.33,.35),.9,0))
    scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=str(out/(name+'-render.png'))
    bpy.ops.render.render(write_still=True)

def main():
    out=Path(os.environ.get('BUND_CLASSICS_OUTPUT',str(HERE/'output')));out.mkdir(parents=True,exist_ok=True)
    for c in json.loads((HERE/'footprints.json').read_text()):
        b,d=(build_club if c['id']=='bund02' else build_union)(c)
        export(c,b,d,out)

if __name__=='__main__':main()
