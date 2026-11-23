from pathlib import Path
import json,hashlib,struct,sys
SOURCE=Path(__file__).resolve().parents[1]
MATERIAL='1号楼 | 红褐清水砖'
TEXTURES={MATERIAL:SOURCE/'gallery-running-bond.jpg','1号楼 | 浅褐窗间面砖':SOURCE/'south-buff-face.jpg','1号楼 | 坡屋面陶瓦':SOURCE/'south-clay-pantiles.jpg'}
GLASS='1号楼 | 浅绿透光屏'
UV='Gongyi Fang block one metric surface UV'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def oriented_face(vertices):
    return min(tuple(vertices[i:] + vertices[:i]) for i in range(3))


def texture_faces(path, material_name=MATERIAL):
    texture_file=TEXTURES[material_name]
    """Index actual GLB texcoords per oriented triangle, keeping seams at shared vertices."""
    blob = path.read_bytes()
    magic, version, length, size, chunk = struct.unpack_from("<4sIIII", blob)
    assert magic == b"glTF" and version == 2 and length == len(blob) and chunk == 0x4E4F534A
    doc = json.loads(blob[20:20 + size])
    bin_size, chunk = struct.unpack_from("<II", blob, 20 + size)
    binary = memoryview(blob)[28 + size:]
    assert chunk == 0x004E4942 and bin_size == len(binary)

    def unpack(index):
        a = doc["accessors"][index]
        v = doc["bufferViews"][a["bufferView"]]
        fmt = {("VEC3", 5126): "<3f", ("VEC2", 5126): "<2f",
               ("SCALAR", 5125): "<I", ("SCALAR", 5123): "<H", ("SCALAR", 5121): "<B"}[a["type"], a["componentType"]]
        start = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = v.get("byteStride", struct.calcsize(fmt))
        return [struct.unpack_from(fmt, binary, start + i * stride) for i in range(a["count"])]

    material, = [m for m in doc["materials"] if m["name"] == material_name]
    texture = doc["textures"][material["pbrMetallicRoughness"]["baseColorTexture"]["index"]]
    sampler = doc["samplers"][texture["sampler"]]
    assert sampler.get("wrapS", 10497) == sampler.get("wrapT", 10497) == 10497
    image = doc["images"][texture["source"]]
    assert image["name"] == texture_file.name and image["mimeType"] == ("image/png" if texture_file.suffix == ".png" else "image/jpeg")
    v = doc["bufferViews"][image["bufferView"]]
    start = v.get("byteOffset", 0)
    assert hashlib.sha256(binary[start:start + v["byteLength"]]).hexdigest() == sha(texture_file)
    faces = {}
    for mesh in doc["meshes"]:
        for primitive in mesh["primitives"]:
            if doc["materials"][primitive["material"]]["name"] != material_name:
                continue
            points = [(x, -z, y) for x, y, z in unpack(primitive["attributes"]["POSITION"])]
            coords = [(u, 1 - v) for u, v in unpack(primitive["attributes"]["TEXCOORD_0"])]
            indices = [row[0] for row in unpack(primitive["indices"])]
            for pos in range(0, len(indices), 3):
                tri = indices[pos:pos + 3]
                vertices = [points[i] for i in tri]
                key = oriented_face(vertices)
                assert key not in faces and len(set(vertices)) == 3
                faces[key] = dict(zip(vertices, (coords[i] for i in tri)))
    assert faces
    return faces


def native_uv(scene, faces, assign, material_name=MATERIAL):
    used = set()
    maximum_error = 0.0
    for obj in scene.objects:
        if obj.type != "MESH" or material_name not in obj.data.materials:
            continue
        mesh = obj.data
        layer = mesh.uv_layers.get(UV)
        if assign:
            layer = layer or mesh.uv_layers.new(name=UV)
            mesh.uv_layers.active = layer
            layer.active_render = True
        assert layer is not None and layer.active_render
        for poly in mesh.polygons:
            if mesh.materials[poly.material_index].name != material_name:
                continue
            vertices = [tuple(obj.matrix_world @ mesh.vertices[mesh.loops[i].vertex_index].co) for i in poly.loop_indices]
            key = oriented_face(vertices)
            assert key not in used
            used.add(key)
            for i, point in zip(poly.loop_indices, vertices):
                expect = faces[key][point]
                if assign:
                    layer.data[i].uv = expect
                u, v = layer.data[i].uv
                maximum_error = max(maximum_error, abs(u - expect[0]), abs(v - expect[1]))
    assert used == faces.keys() and maximum_error < 1.e-5
    return maximum_error



def check_or_apply(scene, raw, assign):
    import bpy
    result={}
    for name,texture in TEXTURES.items():
        mat=bpy.data.materials[name];nt=mat.node_tree
        shader=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
        if assign:
            uv=nt.nodes.new('ShaderNodeUVMap');uv.uv_map=UV
            node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(texture),check_existing=True);node.image.pack();node.extension='REPEAT'
            nt.links.new(uv.outputs['UV'],node.inputs['Vector']);nt.links.new(node.outputs['Color'],shader.inputs['Base Color'])
        image=shader.inputs['Base Color'].links[0].from_node
        assert image.type=='TEX_IMAGE' and image.extension=='REPEAT' and image.inputs['Vector'].links[0].from_node.uv_map==UV
        assert hashlib.sha256(bytes(image.image.packed_file.data)).hexdigest()==sha(texture)
        faces=texture_faces(raw,name);error=native_uv(scene,faces,assign,name)
        result[name]=dict(texture=texture.name,sha256=sha(texture),corners=3*len(faces),maximum_uv_error=error)
    return result

def check_glass(scene,raw,assign):
    import bpy
    binary=raw.read_bytes()
    length=struct.unpack_from('<I',binary,12)[0]
    doc=json.loads(binary[20:20+length])
    m,=[m for m in doc['materials'] if m['name']==GLASS]
    alpha=m['pbrMetallicRoughness']['baseColorFactor'][3]
    assert m['alphaMode']=='BLEND' and abs(alpha-.6)<1e-7
    mat=bpy.data.materials[GLASS]
    shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    if assign:
        rgba=list(mat.diffuse_color);rgba[3]=alpha;mat.diffuse_color=rgba
        shader.inputs['Alpha'].default_value=alpha
        if hasattr(mat,'surface_render_method'):mat.surface_render_method='DITHERED'
        elif hasattr(mat,'blend_method'):mat.blend_method='HASHED'
    assert abs(mat.diffuse_color[3]-alpha)<1e-6 and abs(shader.inputs['Alpha'].default_value-alpha)<1e-6
    return {'name':GLASS,'gltf_mode':m['alphaMode'],'gltf_alpha':alpha,'principled_alpha':shader.inputs['Alpha'].default_value}

def fitted_cameras(scene,views,assign):
    import bpy,math
    from mathutils import Vector
    expected={'front','oblique','above','balconies','ironwork','south'}
    assert set(views)==expected
    stage=bpy.data.collections['Preview lighting and camera']
    aspect=scene.render.resolution_x/scene.render.resolution_y
    results={}
    for idx,(name,row) in enumerate(views.items()):
        target,axis,height,width=row
        to_blender=lambda v:Vector((v[0],-v[2],v[1]))
        look=to_blender(target);direction=to_blender(axis).normalized()
        fov=math.radians(36)
        distance=.59*max(height,width/aspect)/math.tan(fov/2)
        eye=look+direction*distance
        title='1号楼 '+name
        if assign:
            cam=scene.camera if idx==0 else bpy.data.objects.new(title,bpy.data.cameras.new(title))
            if idx:stage.objects.link(cam)
            cam.name=cam.data.name=title
            cam.location=eye;cam.rotation_euler=(look-eye).to_track_quat('-Z','Y').to_euler()
            cam.data.type='PERSP';cam.data.sensor_fit='VERTICAL';cam.data.lens=cam.data.sensor_height/(2*math.tan(fov/2));cam.data.clip_end=400
            cam['web_target_gltf']=target;cam['web_angle_gltf']=axis
        else:cam=bpy.data.objects[title]
        assert (cam.location-eye).length<5e-5 and cam.data.type=='PERSP'
        assert all(abs(v-a)<1e-5 for v,a in zip(cam['web_target_gltf'],target))
        results[name]={'eye':list(cam.location),'target':list(look),'distance':distance}
    return results
