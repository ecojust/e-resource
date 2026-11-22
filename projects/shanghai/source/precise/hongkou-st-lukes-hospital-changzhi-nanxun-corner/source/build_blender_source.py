#!/usr/bin/env python3
"""Use as the ordinary packager's --blender executable for the St. Luke’s Hospital residential corner on Changzhi and Nanxun roads.

The packager retains the named editable meshes. This adapter supplies the
original lime-render and roof-tile textures, the source mesh UVs and the measured cameras,
then checks them after a separate Blender process opens the saved file.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
from changzhi_finish import STUCCO as MATERIAL, TEXTURE, TILE, TILE_TEXTURE
TEXTURES = {MATERIAL: TEXTURE, TILE: TILE_TEXTURE}

UV = "Changzhi architectural finish metric UV"
IMAGE_NODE = "Packed Changzhi architectural finish"
RAW_ENV = "ST_LUKES_CORNER_RAW"
MODE_ENV = "ST_LUKES_CORNER_BLENDER_STAGE"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oriented_face(vertices):
    return min(tuple(vertices[i:] + vertices[:i]) for i in range(3))


def texture_faces(path, material_name=MATERIAL):
    """Index actual GLB texcoords per oriented triangle, keeping seams at shared vertices."""
    texture_file = TEXTURES[material_name]
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


def cameras(scene, create):
    import bpy
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view

    views = json.loads((SOURCE / "cameras.json").read_bytes())
    stage = bpy.data.collections["Preview lighting and camera"]
    for i, view in enumerate(views):
        title = view["label"]
        cam = scene.camera if create and i == 0 else bpy.data.objects.get(title)
        if create:
            if cam is None:
                cam = bpy.data.objects.new(title, bpy.data.cameras.new(title))
                stage.objects.link(cam)
            cam.name = cam.data.name = title
            cam.location = view["eye"]
            delta = Vector(view["target"]) - cam.location
            cam.rotation_euler = delta.to_track_quat("-Z", "Y").to_euler()
            cam.data.type = "PERSP"
            cam.data.sensor_fit = "HORIZONTAL"
            cam.data.lens = cam.data.sensor_width * delta.length / view["width_m"]
            cam.data.clip_start, cam.data.clip_end = .005, max(100., 2.*delta.length + view["width_m"])
        assert cam.type == "CAMERA" and (cam.location - Vector(view["eye"])).length < .0001
        distance = (Vector(view["target"]) - cam.location).length
        assert math.isclose(distance * cam.data.sensor_width / cam.data.lens, view["width_m"], abs_tol=.0001)
        if not create:
            xy = world_to_camera_view(scene, cam, Vector(view["target"]))
            assert abs(xy.x - .5) < .001 and abs(xy.y - .5) < .001 and xy.z > 0
    assert scene.camera.name == views[0]["label"]
    return views


def prepare(scene):
    import bpy

    scene = bpy.context.scene
    raw = Path(os.environ[RAW_ENV])
    for material_name,texture_file in TEXTURES.items():
        mat = bpy.data.materials[material_name]
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
        uv = nodes.new("ShaderNodeUVMap")
        uv.uv_map = UV
        node = nodes.new("ShaderNodeTexImage")
        node.name = IMAGE_NODE
        node.image = bpy.data.images.load(str(texture_file), check_existing=True)
        node.image.pack()
        node.extension = "REPEAT"
        links.new(uv.outputs["UV"], node.inputs["Vector"])
        links.new(node.outputs["Color"], shader.inputs["Base Color"])
        native_uv(scene, texture_faces(raw,material_name), True, material_name)
    scene["source_glb_sha256"] = sha(raw)
    scene["model_license"] = GEOMETRY_LICENSE
    scene["photo_author"],scene["photo_source"] = PHOTO_AUTHOR,PHOTO_SOURCE
    scene["license_url"],scene["texture_license"] = LICENSE_URL,TEXTURE_LICENSE
    scene["texture_origin"] = "Original procedural warm grey lime render and red-brown clay roof tiles"
    scene["grain_texture_sha256"] = sha(TEXTURE)
    views = cameras(scene, True)
    scene.render.resolution_x, scene.render.resolution_y = views[0]["width"], views[0]["height"]
    scene.render.resolution_percentage = 100
    bpy.context.view_layer.update()


def check_reopened():
    import bpy

    blend, raw, output = map(Path, sys.argv[sys.argv.index("--") + 1:])
    report = json.loads(output.read_bytes())
    scene = bpy.context.scene
    assert Path(bpy.data.filepath).resolve() == blend.resolve() and report["match_raw"]
    assert scene["source_glb_sha256"] == sha(raw)
    material_checks={}
    for material_name,texture_file in TEXTURES.items():
        mat = bpy.data.materials[material_name]
        node = mat.node_tree.nodes[IMAGE_NODE]
        shader = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        assert shader.inputs["Base Color"].links[0].from_node == node
        assert node.inputs["Vector"].links[0].from_node.uv_map == UV and node.extension == "REPEAT"
        assert hashlib.sha256(bytes(node.image.packed_file.data)).hexdigest() == sha(texture_file)
        faces=texture_faces(raw,material_name)
        material_checks[material_name]=dict(sha256=sha(texture_file),textured_corners=len(faces)*3,max_uv_error=native_uv(scene,faces,False,material_name))
    assert scene["model_license"] == GEOMETRY_LICENSE and scene["texture_origin"] == "Original procedural warm grey lime render and red-brown clay roof tiles"
    assert (scene["photo_author"],scene["photo_source"],scene["license_url"],scene["texture_license"]) == (PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,TEXTURE_LICENSE)
    report["st_lukes_corner"] = dict(model_license=scene["model_license"],photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,texture_license=TEXTURE_LICENSE,texture_origin=scene["texture_origin"],raw_sha256=sha(raw),texture_sha256=sha(TEXTURE),textured_materials=material_checks,textured_corners=sum(v["textured_corners"] for v in material_checks.values()),
        max_uv_error=max(v["max_uv_error"] for v in material_checks.values()),cameras=cameras(scene,False))
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


def main():
    stage = os.environ.get(MODE_ENV)
    if stage == "prepare":
        import bpy
        bpy.app.handlers.save_pre.append(bpy.app.handlers.persistent(prepare))
        return
    if stage == "verify":
        check_reopened()
        return
    if sys.argv[1:2] == ["--check-raw"]:
        raw = Path(sys.argv[2])
        materials = {}
        for material_name, image in TEXTURES.items():
            faces = texture_faces(raw, material_name)
            materials[material_name] = {"textured_corners": len(faces) * 3, "texture_sha256": sha(image)}
        print(json.dumps({"raw_sha256": sha(raw), "materials": materials}, indent=2))
        return
    args = sys.argv[1:]
    script = args.index("--python") + 1
    delim = args.index("--")
    stage = Path(args[script]).name
    if stage == "make_native.py":
        blend = Path(args[delim + 2])
        raw = Path(os.environ.get(RAW_ENV, blend.with_name(blend.stem + "-raw.glb")))
        if not raw.is_file():
            raise FileNotFoundError(raw)
        os.environ[RAW_ENV] = str(raw.resolve())
        os.environ[MODE_ENV] = "prepare"
        args[script-1:script-1] = ["--python", str(Path(__file__).resolve())]
    elif stage == "verify_editable_model.py":
        os.environ[MODE_ENV] = "verify"
        args[delim:delim] = ["--python", str(Path(__file__).resolve())]
    blender = os.environ.get("ST_LUKES_CORNER_BLENDER") or shutil.which("blender")
    if not blender:
        raise FileNotFoundError("Blender")
    os.execvp(blender, [blender, *args])


if __name__ == "__main__":
    main()
