"""Actual underside engraving for a 6.4 x 6.4 imperial-seal art reconstruction.

Typeface: Noto Serif CJK TC Bold (SIL Open Font License), deliberately not
presented as an authenticated Qin seal-script reconstruction.

Coordinate convention: print/impression reads normally from +Z with +Y up.
The actual stamp face is viewed from -Z, so the lettering is mirrored there.
Right column: 受命於天. Left column: 既壽永昌. Both read top to bottom.
"""
import os
import bpy
import bmesh
from mathutils import Vector

FONT_PATH = os.path.join(os.path.dirname(__file__), 'seal_assets', 'NotoSerifCJKtc-Bold.otf')

def _activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def _difference(base, cutter):
    _activate(base)
    mod = base.modifiers.new('True incised seal engraving', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)

def add_inscription(base, jade_material):
    """Cut eight traditional Chinese glyphs and a frame into the z=0 base face.

    The base must be a mesh with applied scale, width 6.4, bottom z=0.
    Returns a metadata dict; cutters are removed after the boolean operations.
    Engraving is 0.095 Blender units deep and modeled into the actual base mesh.
    """
    font = bpy.data.fonts.load(FONT_PATH)
    glyph_metadata = []
    for column, xpos in [('受命於天', 1.35), ('既壽永昌', -1.35)]:
        for row, char in enumerate(column):
            curve = bpy.data.curves.new('Engraving glyph '+char, type='FONT')
            curve.body = char
            curve.font = font
            curve.resolution_u = 8
            curve.fill_mode = 'BOTH'
            curve.extrude = 0.070
            obj = bpy.data.objects.new('Cut '+char, curve)
            bpy.context.collection.objects.link(obj)
            _activate(obj)
            bpy.ops.object.convert(target='MESH')
            obj = bpy.context.object
            # Normalize the actual ink bounds, retaining a generous column gap.
            xs = [v.co.x for v in obj.data.vertices]
            ys = [v.co.y for v in obj.data.vertices]
            xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
            for vertex in obj.data.vertices:
                vertex.co.x = (vertex.co.x - (xmin+xmax)/2) * 2.12 / (xmax-xmin)
                vertex.co.y = (vertex.co.y - (ymin+ymax)/2) * 1.08 / (ymax-ymin)
                # Font extrude spans [-extrude,+extrude].
                vertex.co.z += 0.025
            obj.location = (xpos, 1.98-row*1.32, 0)
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.00001)
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
            bm.to_mesh(obj.data)
            bm.free()
            # Font cap triangulations can contain T-junctions. Voxel conversion
            # produces a closed cutter and subtly softens engraved stroke edges.
            _activate(obj)
            remesh = obj.modifiers.new('Closed carving tool', 'REMESH')
            remesh.mode = 'VOXEL'
            remesh.voxel_size = 0.012
            remesh.use_smooth_shade = False
            bpy.ops.object.modifier_apply(modifier=remesh.name)
            glyph_metadata.append({'glyph': char, 'vertices':len(obj.data.vertices)})
            _difference(base, obj)

    # Closed incised square frame. Straight tool bars overlap at the corners.
    for name, loc, dims in [
        ('north',(0,2.86,.025),(5.80,.075,.14)),
        ('south',(0,-2.86,.025),(5.80,.075,.14)),
        ('east',(2.86,0,.025),(.075,5.80,.14)),
        ('west',(-2.86,0,.025),(.075,5.80,.14)),
    ]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        cutter = bpy.context.object
        cutter.name = 'Incised frame '+name
        cutter.dimensions = dims
        _activate(cutter)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        _difference(base, cutter)
    bm = bmesh.new()
    bm.from_mesh(base.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.00001)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(base.data)
    bm.free()
    base['inscription'] = '受命於天，既壽永昌'
    base['inscription_typeface'] = 'Noto Serif CJK TC Bold; artistic reconstruction, not historical seal script'
    base['inscription_layout'] = 'Two vertical columns; right 受命於天, left 既壽永昌 in the impression'
    base['inscription_depth'] = 0.095
    return {'font': FONT_PATH, 'glyphs': glyph_metadata, 'depth':0.095}

if __name__ == '__main__':
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,1.1))
    base=bpy.context.object
    base.name='Imperial seal inscription test'
    base.dimensions=(6.4,6.4,2.2)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel=base.modifiers.new('Soft carved edges','BEVEL')
    bevel.width=.12
    bevel.segments=3
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    result=add_inscription(base,None)
    print('INSCRIPTION_TEST',result,'final_faces',len(base.data.polygons))
    assert len(base.data.polygons)>100
    assert all(g['vertices']>20 for g in result['glyphs'])
    bpy.ops.wm.save_as_mainfile(filepath='/workspace/seal_inscription_test.blend')
