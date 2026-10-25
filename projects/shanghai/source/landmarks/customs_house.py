"""Shanghai Customs House / 江海关大楼, procedural architectural interpretation.

Local meters, ground at z=0; Blender Z-up -> glTF Y-up. The model's stated 90 m
height includes its clock tower and finial. It is not a surveyed building mesh.
WGS84 placement anchor: OSM node 476149343, (121.4856441, 31.2386397).

Run: CUSTOMS_OUTPUT_DIR=/path/to/landmarks blender --background --python customs_house.py
"""
import bpy
import math
import os
import json
from pathlib import Path
from mathutils import Vector


class MeshBuilder:
    def __init__(self):
        self.vertices=[];self.faces=[];self.materials=[];self.smooth=[]
    def geom(self, vertices, faces, material, smooth=False):
        offset=len(self.vertices);self.vertices.extend(vertices)
        self.faces.extend([tuple(offset+i for i in f) for f in faces])
        self.materials.extend([material]*len(faces));self.smooth.extend([smooth]*len(faces))
    def box(self, center, dims, material, basis=None):
        center=Vector(center)
        if basis is None:basis=[Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))]
        points=[center+basis[0]*(sx*dims[0]/2)+basis[1]*(sy*dims[1]/2)+basis[2]*(sz*dims[2]/2)
                for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        self.geom(points,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material)
    def cylinder(self,center,radius,depth,material,segments=24,axis=(0,0,1)):
        c=Vector(center);n=Vector(axis).normalized();u=n.cross(Vector((0,0,1)))
        if u.length<.1:u=Vector((1,0,0))
        u.normalize();v=n.cross(u)
        points=[]
        for end in [-1,1]:
            for i in range(segments):
                a=math.tau*i/segments;points.append(c+n*depth*.5*end+radius*(u*math.cos(a)+v*math.sin(a)))
        faces=[tuple(reversed(range(segments))),tuple(segments+i for i in range(segments))]
        faces.extend((i,(i+1)%segments,(i+1)%segments+segments,i+segments) for i in range(segments))
        self.geom(points,faces,material,True)
    def frustum(self,z0,z1,lower,upper,material):
        a,b=lower[0]/2,lower[1]/2;c,d=upper[0]/2,upper[1]/2
        self.geom([(-a,-b,z0),(a,-b,z0),(a,b,z0),(-a,b,z0),(-c,-d,z1),(c,-d,z1),(c,d,z1),(-c,d,z1)],
                  [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material)
    def arc(self,x,y,z,radius,thickness,material):
        # A half-round doorway arch in the east-facing facade.
        pts=[];segments=16
        for i in range(segments+1):
            a=math.pi*i/segments
            for r in [radius,radius+thickness]:pts.append((x,y+r*math.cos(a),z+r*math.sin(a)))
        self.geom(pts,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(segments)],material)
    def clock(self,normal,z=71.0):
        n=Vector(normal);u=Vector((-n.y,n.x,0));v=Vector((0,0,1));center=n*12.33+Vector((0,0,z))
        self.cylinder(center,5.60,.32,5,64,n)
        self.cylinder(center+n*.20,5.16,.18,6,64,n)
        for i in range(60):
            a=math.tau*i/60;radial=u*math.sin(a)+v*math.cos(a);tangent=u*math.cos(a)-v*math.sin(a)
            major=i%5==0
            self.box(center+n*.34+radial*(4.55 if major else 4.85),(.20 if major else .07,.11,.65 if major else .20),7,[tangent,n,radial])
        # Ten past ten, with raised dark hands and hub.
        for a,length,width in [(math.radians(-55),2.8,.27),(math.radians(60),3.95,.18)]:
            radial=u*math.sin(a)+v*math.cos(a);tangent=u*math.cos(a)-v*math.sin(a)
            self.box(center+n*.48+radial*(length*.45),(width,.14,length),7,[tangent,n,radial])
        self.cylinder(center+n*.58,.32,.22,5,24,n)


def mat(name,color,rough=.65,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m


def build_customs_house():
    mats=[mat('Limestone warm ivory',(.69,.65,.53)),mat('Pale carved cornices',(.85,.82,.70)),
          mat('Recessed dark blue windows',(.055,.105,.14),.25,.20),mat('Aged copper roof',(.16,.26,.22),.52,.35),
          mat('Granite plinth',(.40,.42,.40)),mat('Clock bronze edging',(.30,.28,.20),.35,.5),
          mat('Clock ivory face',(.89,.87,.72)),mat('Clock hands and minute indices',(.055,.065,.065))]
    b=MeshBuilder()
    # Broad, seven-storey stone office block. Long facade faces the Huangpu east.
    b.box((0,0,20.0),(45,80,40),0)
    b.box((0,0,.50),(47,82,1),4)
    b.box((0,0,1.15),(46.4,81.4,.32),1)
    for z in [7.5,13,18.5,24,29.5,35,40.0]:
        b.box((0,0,z),(46.0,81,.45 if z<39 else .85),1)
    b.box((0,0,41.2),(47,82,1.0),1)
    b.box((0,0,42.0),(45,80,.65),0)
    # Roof parapet, including visible corner piers.
    for side in [-1,1]:
        b.box((side*22.6,0,42.8),(.65,81,1.6),1)
        b.box((0,side*40.1,42.8),(45.8,.65,1.6),1)
    for x in [-22.7,22.7]:
        for y in [-40.3,40.3]:b.box((x,y,43.0),(1.5,1.5,2.4),1)
    # Stone strips and recessed windows on all elevations.
    for side in [-1,1]:
        for y in range(-35,36,5):
            b.box((side*22.65,y,23.0),(.48,.35,32.5),1)
        for y in [-32.5+i*5 for i in range(14)]:
            for z in [10.1,15.6,21.1,26.6,32.1,37.4]:
                b.box((side*22.54,y,z),(.10,3.25,3.65),2)
                b.box((side*22.70,y,z-1.91),(.65,3.65,.23),1)
                b.box((side*22.68,y,z+1.91),(.50,3.75,.24),1)
                b.box((side*22.67,y,z),(.18,.12,3.65),1)
        for y in [-37.7,37.7]:
            b.box((side*22.72,y,22.9),(.72,2.1,34.3),1)
    for side in [-1,1]:
        for x in range(-18,19,6):
            for z in [10.1,15.6,21.1,26.6,32.1,37.4]:
                b.box((x,side*40.06,z),(3.6,.12,3.65),2)
                b.box((x,side*40.22,z-1.91),(4.0,.55,.23),1)
                b.box((x,side*40.20,z),( .12,.18,3.65),1)
    # Colonnaded main entrance and side doorways.
    for y in [-30,-24,-18,-12,-6,0,6,12,18,24,30]:
        b.box((22.56,y,3.2),(.12,3.8,4.6),2)
        b.arc(22.76,y,5.5,1.9,.25,1)
        for sy in [-1,1]:b.box((22.78,y+sy*2.03,3.35),(.5,.29,4.7),1)
    for y in [-15,-9,-3,3,9,15]:
        b.cylinder((24.2,y,4.2),.68,6.8,1,16)
        b.box((24.2,y,.9),(1.75,1.75,.60),4)
        b.box((24.2,y,7.45),(1.8,1.8,.60),1)
    b.box((24.0,0,7.95),(5.0,34.0,.65),1)
    for i in range(4):b.box((24.3+i*.6,0,.18+i*.18),(3.2-i*.6,34.0,.36),4)
    # Central clock tower grows from the roof in progressively narrower tiers.
    b.box((0,0,49.9),(29,29,15.8),0)
    for z,width in [(43.2,31),(47.0,29.9),(54.8,30.3),(57.7,31.0)]:b.box((0,0,z),(width,width,.70),1)
    for side in [-1,1]:
        for pos in [-9,-4.5,0,4.5,9]:
            for z in [46,51.1,55.8]:
                b.box((side*14.56,pos,z),(.10,2.3,3.3),2)
                b.box((pos,side*14.56,z),(2.3,.10,3.3),2)
        for pos in [-13,13]:
            b.box((side*14.75,pos,50.2),(.65,1.3,14.5),1)
            b.box((pos,side*14.75,50.2),(1.3,.65,14.5),1)
    b.frustum(58.1,60.2,(29.8,29.8),(24,24),1)
    b.box((0,0,69.4),(24,24,18.4),0)
    for z,width in [(60.5,25.6),(63.4,24.7),(77.9,25.2),(79.0,26.3)]:b.box((0,0,z),(width,width,.65),1)
    # Strong corner piers make the clock's square tower legible at city scale.
    for x in [-11.9,11.9]:
        for y in [-11.9,11.9]:
            b.box((x,y,69.6),(1.7,1.7,17.5),1)
            b.box((x,y,79.8),(2.4,2.4,1.3),1)
    for normal in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0)]:b.clock(normal)
    # Tiered oxidised copper crown with a slender 90 m finial.
    b.frustum(79.4,82.2,(24.2,24.2),(17.2,17.2),3)
    b.box((0,0,82.45),(18,18,.5),1)
    b.frustum(82.7,85.2,(17.5,17.5),(11.4,11.4),3)
    b.box((0,0,85.40),(12.2,12.2,.4),1)
    b.frustum(85.6,87.9,(11.9,11.9),(4.2,4.2),3)
    b.box((0,0,88.1),(4.9,4.9,.4),1)
    b.frustum(88.3,89.25,(4.2,4.2),(.7,.7),3)
    b.cylinder((0,0,89.60),.18,.80,5,12)
    mesh=bpy.data.meshes.new('Shanghai Customs House geometry')
    mesh.from_pydata(b.vertices,[],b.faces);mesh.update()
    obj=bpy.data.objects.new('Shanghai Customs House · 江海关大楼',mesh);bpy.context.collection.objects.link(obj)
    for m in mats:mesh.materials.append(m)
    for p,mi,smooth in zip(mesh.polygons,b.materials,b.smooth):p.material_index=mi;p.use_smooth=smooth
    obj['height_m']=90.0
    obj['name_zh']='江海关大楼'
    obj['wgs84_longitude']=121.4856441;obj['wgs84_latitude']=31.2386397
    obj['source']='https://www.openstreetmap.org/node/476149343'
    obj['accuracy']='Recognizable procedural architectural interpretation, not a survey mesh.'
    return obj


def main():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    obj=build_customs_house()
    scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    out=Path(os.environ.get('CUSTOMS_OUTPUT_DIR',str(Path(__file__).resolve().parent/'output'/'landmarks')))
    out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.gltf(filepath=str(out/'customs-house.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
    positions=[obj.matrix_world@v.co for v in obj.data.vertices]
    low=[min(p[i] for p in positions) for i in range(3)];high=[max(p[i] for p in positions) for i in range(3)]
    assert abs(low[2])<1e-5 and abs(high[2]-90)<1e-5,(low,high)
    assert (out/'customs-house.glb').stat().st_size<5_000_000
    metadata={'id':'customs-house','name':'江海关大楼','anchor':{'longitude':121.4856441,'latitude':31.2386397},'height':90,'units':'meters','up':'Y','source':'https://www.openstreetmap.org/node/476149343','boundsBlender':{'min':low,'max':high},'triangles':sum(len(p.vertices)-2 for p in obj.data.polygons),'bytes':(out/'customs-house.glb').stat().st_size}
    (out/'customs-house.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    print('CUSTOMS_HOUSE_VALIDATED',json.dumps(metadata,ensure_ascii=False))

if __name__=='__main__':main()
