#!/usr/bin/env python3
"""Use as the ordinary packager's --blender executable for the brick entrance at No.16 Great Western Villa.

The packager retains the named editable meshes. This adapter supplies the
photographed calibrated slate relief atlas, the source mesh UVs and the measured cameras,
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
from mailbox_material import STONE as MATERIAL, TEXTURE

UV = "Mailbox photograph UV"
IMAGE_NODE = "Packed WQL mailbox photograph"
RAW_ENV = "GREAT_WESTERN_VILLA_16_RAW"
MODE_ENV = "GREAT_WESTERN_VILLA_16_BLENDER_STAGE"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oriented_face(vertices):
    return min(tuple(vertices[i:] + vertices[:i]) for i in range(3))


def texture_faces(path):
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

    material, = [m for m in doc["materials"] if m["name"] == MATERIAL]
    texture = doc["textures"][material["pbrMetallicRoughness"]["baseColorTexture"]["index"]]
    sampler = doc["samplers"][texture["sampler"]]
    assert sampler["wrapS"] == sampler["wrapT"] == 10497
    image = doc["images"][texture["source"]]
    assert image["name"] == TEXTURE.name and image["mimeType"] == "image/png"
    v = doc["bufferViews"][image["bufferView"]]
    start = v.get("byteOffset", 0)
    assert hashlib.sha256(binary[start:start + v["byteLength"]]).hexdigest() == sha(TEXTURE)
    faces = {}
    for mesh in doc["meshes"]:
        for primitive in mesh["primitives"]:
            if doc["materials"][primitive["material"]]["name"] != MATERIAL:
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


def native_uv(scene, faces, assign):
    used = set()
    maximum_error = 0.0
    for obj in scene.objects:
        if obj.type != "MESH" or MATERIAL not in obj.data.materials:
            continue
        mesh = obj.data
        layer = mesh.uv_layers.get(UV)
        if assign:
            layer = layer or mesh.uv_layers.new(name=UV)
            mesh.uv_layers.active = layer
            layer.active_render = True
        assert layer is not None and layer.active_render
        for poly in mesh.polygons:
            if mesh.materials[poly.material_index].name != MATERIAL:
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
    mat = bpy.data.materials[MATERIAL]
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    uv = nodes.new("ShaderNodeUVMap")
    uv.uv_map = UV
    node = nodes.new("ShaderNodeTexImage")
    node.name = IMAGE_NODE
    node.image = bpy.data.images.load(str(TEXTURE), check_existing=True)
    node.image.pack()
    node.extension = "REPEAT"
    links.new(uv.outputs["UV"], node.inputs["Vector"])
    links.new(node.outputs["Color"], shader.inputs["Base Color"])
    raw = Path(os.environ[RAW_ENV])
    native_uv(scene, texture_faces(raw), True)
    scene["source_glb_sha256"] = sha(raw)
    scene["model_license"] = "CC BY-SA 4.0"
    scene["model_license_url"] = "https://creativecommons.org/licenses/by-sa/4.0/"
    scene["photo_author"] = "WQL"
    scene["photo_source"] = "https://commons.wikimedia.org/wiki/File:The_mail_box_of_No.16_Great_Western_Villa.jpg"
    scene["photo_adaptations"] = "Rectified, cropped and adapted as the relief, gilded number and mailbox nameplate."
    scene["mailbox_texture_sha256"] = sha(TEXTURE)
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
    mat = bpy.data.materials[MATERIAL]
    node = mat.node_tree.nodes[IMAGE_NODE]
    shader = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    assert shader.inputs["Base Color"].links[0].from_node == node
    assert node.inputs["Vector"].links[0].from_node.uv_map == UV and node.extension == "REPEAT"
    assert hashlib.sha256(bytes(node.image.packed_file.data)).hexdigest() == scene["mailbox_texture_sha256"] == sha(TEXTURE)
    assert scene["photo_author"] == "WQL" and scene["model_license"] == "CC BY-SA 4.0"
    assert scene["photo_source"].startswith("https://commons.wikimedia.org/wiki/File:The_mail_box")
    assert scene["model_license_url"] == "https://creativecommons.org/licenses/by-sa/4.0/"
    faces = texture_faces(raw)
    report["great_western_villa_16"] = dict(model_license=scene["model_license"], license_url=scene["model_license_url"], photo_author=scene["photo_author"], photo_source=scene["photo_source"], raw_sha256=sha(raw), texture_sha256=sha(TEXTURE), textured_corners=3*len(faces),
                              max_uv_error=native_uv(scene, faces, False), cameras=cameras(scene, False))
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
        faces = texture_faces(Path(sys.argv[2]))
        print(json.dumps(dict(textured_corners=len(faces)*3, texture_sha256=sha(TEXTURE))))
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
    blender = os.environ.get("WESTERN16_BLENDER") or shutil.which("blender")
    if not blender:
        raise FileNotFoundError("Blender")
    os.execvp(blender, [blender, *args])


if __name__ == "__main__":
    main()
