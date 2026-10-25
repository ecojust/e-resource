"""Shanghai Customs House: mapped front block and photo-proportioned clock tower.

Official dimensions: 79.2 m overall, main building 36.2 m, clock tower 43 m,
clock diameter 5.4 m, minute hand 3.17 m including 0.72 m counterweight, hour
hand 2.3 m. Other elevations are photo-based, not survey measurements.

The front-block outline is OSM way 178407318, transformed in an ellipsoidal
WGS84 local azimuthal-equidistant projection and baked into east/north axes.
The origin is its polygon centroid. Rear wings are intentionally omitted.

CUSTOMS_OUTPUT_DIR=/path blender --background --python customs_house.py
CUSTOMS_RENDER=0 disables the optional verification render.
"""
import bpy
import math
import os
import json
from pathlib import Path
from mathutils import Vector

ANCHOR = (121.4854354265109, 31.238615036350964)
AZIMUTH_DEG = 6.56531510671183  # Front normal, counterclockwise from east.
OFFICIAL = 'https://web.archive.org/web/20100610110157/http://shanghai.customs.gov.cn/publish/portal27/tab8419/module26899/info82241.htm'
PHOTO = 'https://commons.wikimedia.org/wiki/File:ShanghaiBundCustomsHouse.jpg'
FOOTPRINT = [
    (-11.7101073598,18.1737786873),(-11.7061463449,12.4591220528),
    (-11.7099879756,-10.6539305542),(-11.7101078406,-18.1538046579),
    (-5.4962354646,-18.1546913289),(5.8184597440,-18.1622797273),
    (11.7149448100,-18.1712704459),(11.7106548851,-10.6262485234),
    (11.7040620018,13.1464713860),(11.7054019476,18.1574021304),
    (4.5999838758,18.1604444121),(-6.1013664082,18.1644111136)]


class Builder:
    def __init__(self):
        self.vertices=[]; self.faces=[]; self.indices=[]; self.smooth=[]
    def geom(self, verts, faces, mat, smooth=False):
        n=len(self.vertices); self.vertices.extend([tuple(v) for v in verts])
        self.faces.extend([tuple(n+i for i in f) for f in faces])
        self.indices.extend([mat]*len(faces));self.smooth.extend([smooth]*len(faces))
    def box(self,center,size,mat,basis=None):
        c=Vector(center);axes=basis or [Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))]
        verts=[c+axes[0]*a*size[0]/2+axes[1]*b*size[1]/2+axes[2]*d*size[2]/2
               for a,b,d in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        self.geom(verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    def cylinder(self,center,radius,depth,mat,segments=48,axis=(0,0,1)):
        c=Vector(center);n=Vector(axis).normalized();u=n.cross(Vector((0,0,1)))
        if u.length<.01:u=Vector((1,0,0))
        u.normalize();v=n.cross(u);verts=[]
        for sign in [-1,1]:
            for i in range(segments):
                a=math.tau*i/segments;verts.append(c+n*depth*sign/2+radius*(u*math.cos(a)+v*math.sin(a)))
        faces=[tuple(reversed(range(segments))),tuple(segments+i for i in range(segments))]
        faces.extend((i,(i+1)%segments,(i+1)%segments+segments,i+segments) for i in range(segments))
        self.geom(verts,faces,mat,True)
        self.smooth[-len(faces)]=False
        self.smooth[-len(faces)+1]=False
    def ring(self,center,outer,inner,mat,normal=(1,0,0),segments=96):
        c=Vector(center);n=Vector(normal);u=Vector((-n.y,n.x,0));v=Vector((0,0,1));verts=[]
        for i in range(segments):
            a=math.tau*i/segments
            for radius in [inner,outer]:verts.append(c+(u*math.sin(a)+v*math.cos(a))*radius)
        self.geom(verts,[(2*i,2*((i+1)%segments),2*((i+1)%segments)+1,2*i+1) for i in range(segments)],mat)
    def frustum(self,center,z0,z1,lower,upper,mat):
        x,y=center;a,b=lower[0]/2,lower[1]/2;c,d=upper[0]/2,upper[1]/2
        self.geom([(x-a,y-b,z0),(x+a,y-b,z0),(x+a,y+b,z0),(x-a,y+b,z0),
                   (x-c,y-d,z1),(x+c,y-d,z1),(x+c,y+d,z1),(x-c,y+d,z1)],
                  [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    def outline(self,polygon,z0,z1,mat):
        n=len(polygon);verts=[(x,y,z) for z in [z0,z1] for x,y in polygon]
        faces=[tuple(reversed(range(n))),tuple(n+i for i in range(n))]
        faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
        self.geom(verts,faces,mat)
    def segment(self,a,b,width,depth,normal,mat):
        a,b=Vector(a),Vector(b);along=(b-a).normalized();n=Vector(normal);across=n.cross(along).normalized()
        self.box((a+b)/2,(width,depth,(b-a).length),mat,[across,n,along])
    def east_arch(self,x,y,spring,radius,height,mat):
        # Filled round-headed dark window, front-facing +X.
        poly=[(x,y-radius,spring-height),(x,y+radius,spring-height)]
        for j in range(21):
            a=math.pi*j/20;poly.append((x,y+radius*math.cos(a),spring+radius*math.sin(a)))
        self.geom(poly,[tuple(range(len(poly)))],mat)


def material(name,color,rough=.64,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m


def pane(b,x,y,z,w,h,side=1):
    # Thin frames give the tall strips depth without a generic all-glass grid.
    b.box((side*x,y,z),(.10,w,h),2)
    for yy in [y-w/2-.06,y+w/2+.06]:b.box((side*(x+.07),yy,z),(.16,.12,h+.20),1)
    for zz in [z-h/2-.08,z+h/2+.08]:b.box((side*(x+.08),y,zz),(.18,w+.24,.16),1)
    for yy in [y-w/6,y+w/6]:b.box((side*(x+.09),yy,z),(.12,.045,h),4)
    for j in range(1,4):b.box((side*(x+.09),y,z-h/2+h*j/4),(.12,w,.045),4)


def clock(b,normal,center_xy,z=55.25):
    n=Vector(normal);u=Vector((-n.y,n.x,0));v=Vector((0,0,1))
    c=Vector((*center_xy,z))+n*4.175
    b.cylinder(c,2.70,.105,6,96,n)
    b.ring(c+n*.065,2.70,2.57,7,n)
    b.ring(c+n*.068,2.15,2.105,7,n)
    b.ring(c+n*.070,1.70,1.66,7,n)
    for i in range(60):
        a=math.tau*i/60;radial=u*math.sin(a)+v*math.cos(a);tangent=u*math.cos(a)-v*math.sin(a)
        major=i%5==0
        b.box(c+n*.083+radial*(2.46 if major else 2.50),(.045 if major else .018,.023,.19 if major else .09),7,[tangent,n,radial])
    # Roman hour numerals are modeled strokes, with no external font dependency.
    roman=['XII','I','II','III','IIII','V','VI','VII','VIII','IX','X','XI']
    strokes={'I':[((0,-.22),(0,.22))],
             'V':[((-.085,.22),(0,-.22)),((0,-.22),(.085,.22))],
             'X':[((-.085,-.22),(.085,.22)),((-.085,.22),(.085,-.22))]}
    for i,label in enumerate(roman):
        a=math.tau*i/12;radial=u*math.sin(a)+v*math.cos(a);tangent=u*math.cos(a)-v*math.sin(a)
        center=c+n*.085+radial*2.29
        for j,char in enumerate(label):
            offset=(j-(len(label)-1)/2)*.20
            for start,end in strokes[char]:
                aa=center+tangent*(offset+start[0])+radial*start[1]
                bb=center+tangent*(offset+end[0])+radial*end[1]
                b.segment(aa,bb,.030,.025,n,7)
        # Fine central radial division lines are visible in the reference dial.
        b.segment(c+n*.075+radial*.46,c+n*.075+radial*1.65,.018,.015,n,7)
    for angle,tip,tail,width in [(math.radians(-55),1.85,.45,.095),(math.radians(60),2.45,.72,.070)]:
        radial=u*math.sin(angle)+v*math.cos(angle)
        b.segment(c+n*.14-radial*tail,c+n*.14+radial*tip,width,.06,n,7)
    b.cylinder(c+n*.18,.115,.09,7,24,n)


def build_customs_house():
    mats=[material('Warm limestone',(.62,.58,.49)),material('Pale stone relief',(.73,.70,.61)),
          material('Recessed blue-gray glazing',(.045,.075,.086),.28,.08),material('Weathered roof stone',(.34,.35,.29)),
          material('Bronze window divisions',(.16,.18,.15),.48,.3),material('Basement granite',(.39,.40,.36)),
          material('Clock opal glass',(.87,.85,.75),.40),material('Clock dark iron',(.025,.030,.027),.40,.25),
          material('Flag red',(.65,.018,.014)),material('Flag stars',(.94,.70,.06))]
    b=Builder();F=11.71;W=36.345;D=23.425
    # Exact mapped outline: 178407318 covers this front block, not the rear wing.
    b.outline(FOOTPRINT,0,1.55,5)
    b.outline(FOOTPRINT,1.55,33.20,0)
    b.box((0,0,1.60),(D+.24,W+.24,.22),1)
    for z,thick,overhang in [(6.9,.45,.32),(7.35,.25,.35),(25.7,.30,.36),(27.55,.58,.62),(28.15,.25,.42),(33.15,.45,.52)]:
        b.box((0,0,z),(D+overhang,W+overhang,thick),1)
    # Seven tall slots with enlarged corner piers, matching the main photograph.
    columns=[-14.1,-7.8,-3.9,0,3.9,7.8,14.1]
    for side in [-1,1]:
        for y in columns:
            pane(b,F+.045,y,4.30,1.65,3.90,side)
            b.box((side*(F+.026),y,16.6),(.055,1.92,17.7),2)
            for z,h in [(9.65,3.25),(14.25,3.45),(18.65,3.45),(23.0,3.50)]:pane(b,F+.065,y,z,1.66,h,side)
            for z in [11.70,16.20,20.55]:
                b.box((side*(F+.09),y,z),(.12,1.73,.80),4)
                for yy in [y-.57,y,y+.57]:b.box((side*(F+.16),yy,z),(.035,.045,.63),0)
        # Shallow limestone course joints stay on the piers, not through windows.
        intervals=[];edge=-W/2
        for y in columns:
            intervals.append((edge,y-1.10));edge=y+1.10
        intervals.append((edge,W/2))
        for low,high in intervals:
            if high-low<.12:continue
            for z in [8.0+i*1.55 for i in range(12)]:
                b.box((side*(F+.012),(low+high)/2,z),(.018,high-low,.025),3)
        # Decorated entablature: rectangular dentils rather than classical columns.
        for j in range(34):
            y=-17.5+j*1.06
            b.box((side*(F+.24),y,26.65),(.25,.42,.78),1)
            b.box((side*(F+.31),y,27.18),(.29,.65,.13),0)
        for y in [-7.8,-3.9,0,3.9,7.8]:pane(b,F+.065,y,30.60,1.85,2.70,side)
        # Attic balcony railing runs between the taller corner pavilions.
        for y in [-10.8+i*.9 for i in range(25)]:b.box((side*(F+.34),y,28.85),(.075,.075,.80),4)
        b.box((side*(F+.34),0,29.28),(.09,22.0,.09),4)
    # Secondary elevations remain seven-storey, with restrained rectangular bays.
    for side in [-1,1]:
        for x in [-8,-4,0,4,8]:
            for z in [4.30,9.65,14.25,18.65,23.0,30.60]:
                b.box((x,side*(W/2+.035),z),(1.65,.09,3.1 if z<27 else 2.6),2)
                for xx in [x-.92,x+.92]:b.box((xx,side*(W/2+.09),z),(.12,.15,3.35 if z<27 else 2.85),1)
                b.box((x,side*(W/2+.12),z-1.67),(2.02,.22,.14),1)
    # The two eastern attic corner pavilions reach the official main-block top.
    for y in [-14.35,14.35]:
        b.box((7.8,y,32.20),(7.95,7.15,7.0),0)
        b.box((7.8,y,35.15),(8.35,7.55,.46),1)
        b.frustum((7.8,y),35.38,36.0,(8.35,7.55),(7.62,6.90),3)
        b.box((7.8,y,36.10),(7.72,7.00,.20),1)
        b.east_arch(F+.13,y,31.40,.69,2.15,2)
        for yy in [y-.85,y+.85]:b.box((F+.21,yy,30.65),(.28,.25,3.5),1)
        b.box((F+.25,y,32.60),(.38,2.25,.20),1)
        b.geom([(F+.33,y-1.22,32.70),(F+.33,y+1.22,32.70),(F+.33,y,33.32)],[(0,1,2)],1)
        for zz in [29.1,30.3,31.5,32.7,33.9]:
            b.box((F+.04,y,zz),(.035,6.9,.025),3)
    # Tower is centered on the photographed frontage; rear placement is inferred.
    C=(5.30,0)
    b.box((C[0],0,36.65),(11.8,14.4,6.9),0)
    for z,width,thick in [(36.8,14.7,.40),(39.65,15.1,.50),(40.15,14.4,.28)]:
        b.box((C[0],0,z),(width-2.6,width,thick),1)
    # Paired block-shaped tower shoulders, visible above the attic roof.
    for side in [-1,1]:
        b.box((C[0],side*6.5,39.1),(10.8,2.10,4.1),0)
        b.box((C[0],side*6.5,41.10),(11.3,2.55,.40),1)
        b.box((C[0],side*6.5,41.65),(10.5,2.10,.60),3)
    b.box((C[0],0,44.65),(10.6,10.6,9.50),0)
    # Three uninterrupted narrow vertical glazing strips on every tower side.
    for nx,ny in [(1,0),(-1,0),(0,1),(0,-1)]:
        n=Vector((nx,ny,0));u=Vector((-ny,nx,0));v=Vector((0,0,1));origin=Vector((*C,44.70))+n*5.335
        for offset in [-2.08,0,2.08]:
            b.box(origin+u*offset,(1.08,.08,6.10),2,[u,n,v])
            for zoff in [-2.3,-1.15,0,1.15,2.3]:b.box(origin+u*offset+v*zoff,(1.08,.12,.045),4,[u,n,v])
        for z in [40.9,42.2,43.5,44.8,46.1,47.4]:
            b.box(Vector((*C,z))+n*5.312,(10.5,.025,.025),3,[u,n,v])
    for z,width,thick in [(48.5,11.05,.38),(49.0,11.30,.46),(49.5,10.85,.26),(50.05,10.65,.32)]:
        b.box((C[0],0,z),(width,width,thick),1 if z!=49.0 else 3)
    # Clock chamber: 5.4 m dial / 8.2 m wall = 0.659, matching the photo ratio.
    b.box((C[0],0,54.55),(8.2,8.2,8.60),0)
    for nx,ny in [(1,0),(-1,0),(0,1),(0,-1)]:
        n=Vector((nx,ny,0));u=Vector((-ny,nx,0));v=Vector((0,0,1))
        for off in [-3.86,3.86]:b.box(Vector((*C,54.65))+n*4.17+u*off,(.21,.18,8.05),1,[u,n,v])
        for z in [50.55,51.35,52.15,52.95,53.75,54.55,55.35,56.15,56.95,57.75,58.55]:
            b.box(Vector((*C,z))+n*4.112,(7.95,.022,.020),3,[u,n,v])
        clock(b,(nx,ny,0),C,55.25)
    for z,width,thick in [(50.35,8.65,.25),(58.95,8.50,.32),(59.45,8.85,.60),(59.90,8.50,.25)]:b.box((C[0],0,z),(width,width,thick),1)
    # Narrow bell chamber and lantern: no oversized pyramidal roof.
    b.frustum(C,60.02,60.45,(7.9,7.9),(6.65,6.65),3)
    b.box((C[0],0,61.45),(6.1,6.1,2.30),0)
    for nx,ny in [(1,0),(-1,0),(0,1),(0,-1)]:
        n=Vector((nx,ny,0));u=Vector((-ny,nx,0));v=Vector((0,0,1));origin=Vector((*C,61.50))+n*3.07
        b.box(origin,(3.2,.08,1.30),2,[u,n,v])
        for j in range(5):
            for k in range(2):
                b.ring(origin+n*.05+u*((j-2)*.54)+v*((k-.5)*.51),.20,.15,1,n,20)
    b.box((C[0],0,62.75),(6.45,6.45,.35),1)
    b.frustum(C,62.93,63.55,(6.5,6.5),(4.15,4.15),3)
    b.box((C[0],0,65.10),(4.10,4.10,3.10),0)
    for nx,ny in [(1,0),(-1,0),(0,1),(0,-1)]:
        n=Vector((nx,ny,0));u=Vector((-ny,nx,0));v=Vector((0,0,1));origin=Vector((*C,65.1))+n*2.08
        for offset in [-.72,0,.72]:b.box(origin+u*offset,(.40,.08,2.25),2,[u,n,v])
    b.box((C[0],0,66.78),(4.45,4.45,.30),1)
    b.frustum(C,66.93,68.48,(4.40,4.40),(3.0,3.0),3)
    b.box((C[0],0,68.60),(3.10,3.10,.24),1)
    # The reference's thin flag mast completes the 79.2 m overall envelope.
    b.cylinder((C[0],0,(68.72+79.2)/2),.055,79.2-68.72,1,12)
    b.cylinder((C[0],0,68.82),.18,.22,4,16)
    # Small five-star flag, rendered as untextured geometry.
    fv=[]
    for j in range(9):
        t=j/8;y=t*1.55;wave=.09*math.sin(t*math.tau)
        fv.extend([(C[0]+wave,y,78.60-.10*t),(C[0]+wave,y,77.55-.10*t)])
    b.geom(fv,[(2*j,2*j+1,2*j+3,2*j+2) for j in range(8)],8)
    for sy,sz,r in [(.32,78.30,.16),(.63,78.47,.055),(.77,78.30,.055),(.76,78.10,.055),(.62,77.96,.055)]:
        star=[]
        for i in range(10):
            a=math.pi/2+math.pi*i/5;rr=r if i%2==0 else r*.40
            star.append((C[0]+.09*math.sin(sy/1.55*math.tau)+.012,sy+rr*math.cos(a),sz+rr*math.sin(a)))
        b.geom(star,[tuple(range(10))],9)
    # Bake measured orientation into EN geometry. GLB will be x east, y up, z south.
    angle=math.radians(AZIMUTH_DEG);ca,sa=math.cos(angle),math.sin(angle)
    b.vertices=[(x*ca-y*sa,x*sa+y*ca,z) for x,y,z in b.vertices]
    mesh=bpy.data.meshes.new('OSM-front-block and photo-proportioned clock tower')
    mesh.from_pydata(b.vertices,[],b.faces);mesh.update()
    obj=bpy.data.objects.new('Shanghai Customs House · 上海海关前楼',mesh);bpy.context.collection.objects.link(obj)
    for m in mats:mesh.materials.append(m)
    for poly,idx,smooth in zip(mesh.polygons,b.indices,b.smooth):poly.material_index=idx;poly.use_smooth=smooth
    obj['height_m']=79.2;obj['main_block_height_m']=36.2;obj['clock_diameter_m']=5.4
    obj['clock_chamber_width_m']=8.2;obj['three_window_tower_width_m']=10.6
    obj['wgs84_longitude'],obj['wgs84_latitude']=ANCHOR
    obj['footprint_source']='https://www.openstreetmap.org/way/178407318'
    obj['height_source']=OFFICIAL;obj['photo_reference']=PHOTO
    obj['orientation_baked_degrees_from_east']=AZIMUTH_DEG
    return obj


def render_preview(out,obj):
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32
    scene.cycles.use_denoising=False;scene.cycles.use_adaptive_sampling=True
    scene.cycles.adaptive_threshold=.065;scene.cycles.max_bounces=4
    scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.15,.19,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
    scene.render.resolution_x=900;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX'
    for name,loc,power,size in [('Key',(65,-55,110),140000,70),('Fill',(-40,40,90),85000,60),('Rim',(-25,-30,120),110000,65)]:
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
        o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
        o.rotation_euler=(Vector((0,0,35))-o.location).to_track_quat('-Z','Y').to_euler()
    a=math.radians(AZIMUTH_DEG);direction=Vector((math.cos(a),math.sin(a),0))
    bpy.ops.object.camera_add(location=direction*130+Vector((0,0,43)))
    cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,40))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO';cam.data.ortho_scale=88;scene.camera=cam
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(out/'render.png')
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    obj=build_customs_house();scene=bpy.context.scene
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    out=Path(os.environ.get('CUSTOMS_OUTPUT_DIR',str(Path(__file__).resolve().parent/'output'/'customs-refined')))
    out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.gltf(filepath=str(out/'customs-house.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
    positions=[obj.matrix_world@v.co for v in obj.data.vertices]
    low=[min(p[i] for p in positions) for i in range(3)];high=[max(p[i] for p in positions) for i in range(3)]
    assert abs(low[2])<1e-5 and abs(high[2]-79.2)<1e-4,(low,high)
    assert (out/'customs-house.glb').stat().st_size<5_000_000
    metadata={'id':'customs-house','name':'上海海关大楼前楼','anchor':{'longitude':ANCHOR[0],'latitude':ANCHOR[1]},
        'height':79.2,'main_block_height':36.2,'clock_tower_height':43.0,'clock_face_diameter':5.4,
        'minute_hand_total_length':3.17,'minute_hand_tip':2.45,'minute_hand_tail':.72,'hour_hand_total_length':2.3,
        'clock_chamber_width':8.2,'three_window_tower_width':10.6,
        'front_block_footprint_dimensions':[36.3450488238,23.4250526504],'front_block_footprint_area':850.547654668,
        'footprint_source':'https://www.openstreetmap.org/way/178407318','footprint_license':'ODbL-1.0',
        'orientation_degrees_ccw_from_east':AZIMUTH_DEG,'orientation_baked':True,'exclusionRadius':23.5,
        'dimensions_source':OFFICIAL,'photo_reference':PHOTO,'photo_author':'Diomidis Spinellis','photo_license_option':'CC BY 2.5',
        'units':'meters','up':'Y','boundsBlender':{'min':low,'max':high},
        'triangles':sum(len(p.vertices)-2 for p in obj.data.polygons),'bytes':(out/'customs-house.glb').stat().st_size,
        'scope':'Mapped front block only; rear wings remain represented by the separate city footprint layer.',
        'accuracy':'Official heights and clock dimensions; OSM front outline and centroid; remaining elevations interpreted from the photograph. Not a survey mesh.',
        'notes':['Total envelope includes the photographed thin mast.','Tower and attic horizontal details are photo-derived, not measured plans.','Do not apply another yaw: EN orientation is already baked into the GLB.']}
    (out/'customs-house.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    print('CUSTOMS_REFINED_VALIDATED',json.dumps(metadata,ensure_ascii=False))
    if os.environ.get('CUSTOMS_RENDER','1')!='0':render_preview(out,obj)

if __name__=='__main__':main()
