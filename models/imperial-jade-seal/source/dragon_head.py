"""Procedural carved Chinese dragon head; Blender 4.3 compatible.

Usage:
    from dragon_head import build_head
    objects = build_head(jade_material, dark_jade_material, gold_material)

The muzzle faces -Y; the neck attachment is near (0, .1, 3.8).
"""
import math
import bpy
from mathutils import Vector


def _dh_uv(name, location, scale, material, segments=40, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        location=location)
    obj = bpy.context.object
    obj.name = 'DragonHead_' + name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material:
        obj.data.materials.append(material)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def _dh_curve(name, coords, radii, radius, material, resolution=12):
    data = bpy.data.curves.new('DragonHead_' + name, 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = resolution
    data.bevel_depth = radius
    data.bevel_resolution = 4
    data.use_fill_caps = True
    spline = data.splines.new('BEZIER')
    spline.bezier_points.add(len(coords)-1)
    for point, coord, rad in zip(spline.bezier_points, coords, radii):
        point.co = coord
        point.radius = rad
        point.handle_left_type = 'AUTO'
        point.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new('DragonHead_' + name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(material)
    return obj


def _dh_fuse(objects, name, voxel=.034):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    result = bpy.context.object
    result.name = 'DragonHead_' + name
    result.data.remesh_voxel_size = voxel
    result.data.use_remesh_preserve_volume = True
    bpy.ops.object.voxel_remesh()
    smooth = result.modifiers.new('Soft carved transitions', 'SMOOTH')
    smooth.factor = .65
    smooth.iterations = 5
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    for poly in result.data.polygons:
        poly.use_smooth = True
    return result


def _dh_leaf(name, points, width, material):
    """A tapered curled jade plate along a small center line."""
    centers = [Vector(p) for p in points]
    verts, faces = [], []
    for i, center in enumerate(centers):
        frac = i / (len(centers)-1)
        tangent = centers[min(i+1,len(centers)-1)]-centers[max(i-1,0)]
        tangent.normalize()
        side = tangent.cross(Vector((0,-1,0)))
        if side.length < .001:
            side = Vector((1,0,0))
        side.normalize()
        normal = side.cross(tangent).normalized()
        r = width * (.36 + .64*math.sin(math.pi*frac)) * (1-frac*.92)
        for j in range(10):
            angle=2*math.pi*j/10
            verts.append(center + side*(r*math.cos(angle)) + normal*(r*.35*math.sin(angle)))
    for i in range(len(centers)-1):
        for j in range(10):
            faces.append((i*10+j,i*10+(j+1)%10,(i+1)*10+(j+1)%10,(i+1)*10+j))
    faces.append(tuple(range(9,-1,-1)))
    faces.append(tuple((len(centers)-1)*10+j for j in range(10)))
    mesh=bpy.data.meshes.new('DragonHead_'+name)
    mesh.from_pydata(verts,[],faces)
    mesh.materials.append(material)
    obj=bpy.data.objects.new('DragonHead_'+name,mesh)
    bpy.context.collection.objects.link(obj)
    sub=obj.modifiers.new('Polished leaf surface','SUBSURF')
    sub.levels=2
    for face in mesh.polygons:
        face.use_smooth=True
    return obj


def build_head(jade_material, dark_jade_material, gold_material):
    """Build a smooth carved dragon head and return all objects created."""
    initial=set(bpy.data.objects)
    shell = [
        _dh_uv('Cranium',(0,-.36,4.13),(.70,.62,.59),jade_material),
        _dh_uv('Forehead',(0,-.68,4.32),(.57,.48,.37),jade_material),
        _dh_uv('Nasal bridge',(0,-.94,4.14),(.38,.46,.30),jade_material),
        _dh_uv('Broad muzzle',(0,-1.22,3.97),(.62,.34,.24),jade_material),
        _dh_uv('Lower jaw',(0,-.97,3.56),(.57,.50,.16),jade_material),
        _dh_uv('Chin',(0,-1.20,3.55),(.42,.29,.17),jade_material),
        _dh_uv('Neck root',(0,.04,3.87),(.57,.46,.49),jade_material),
    ]
    for side in [-1,1]:
        shell.append(_dh_uv('Cheek', (side*.53,-.48,3.94),(.33,.44,.43),jade_material))
        shell.append(_dh_uv('Nose scroll', (side*.39,-1.21,4.04),(.26,.30,.22),jade_material))
        brow=_dh_uv('Heavy brow',(side*.47,-.77,4.40),(.40,.23,.15),jade_material)
        brow.rotation_euler.y=side*-.24
        shell.append(brow)
    _dh_fuse(shell,'Continuous carved skull')

    # Deep shadow in the slightly open mouth, bounded by the carved jaws.
    _dh_uv('Mouth cavity',(0,-1.08,3.755),(.50,.33,.105),dark_jade_material)
    _dh_curve('Upper lip', [(-.53,-1.34,3.84),(-.34,-1.48,3.82),(0,-1.51,3.82),(.34,-1.48,3.82),(.53,-1.34,3.84)],
              [.65,1,1,1,.65],.045,jade_material)
    _dh_curve('Lower lip',[(-.48,-1.31,3.67),(0,-1.49,3.64),(.48,-1.31,3.67)],
              [.4,1,.4],.037,jade_material)

    for side in [-1,1]:
        def p(x,y,z): return (side*x,y,z)
        tag='L' if side<0 else 'R'
        # Narrow eyes under the thick descending brows. The small amber focus
        # leaves the overall form a monochrome jade carving.
        eye=_dh_uv('Eye socket '+tag,p(.58,-.86,4.27),(.21,.14,.115),dark_jade_material)
        eye.rotation_euler.z=-side*.30
        eye.rotation_euler.y=side*.12
        _dh_uv('Amber eye '+tag,p(.63,-.975,4.285),(.072,.043,.055),gold_material,32,16)
        _dh_uv('Slit pupil '+tag,p(.635,-1.014,4.285),(.016,.010,.042),dark_jade_material,24,12)
        _dh_curve('Eye lid '+tag,[p(.33,-.96,4.28),p(.50,-1.015,4.37),p(.68,-.90,4.36),p(.78,-.71,4.31)],
                  [.35,1,1,.25],.059,jade_material)
        _dh_curve('Cheek flourish '+tag,[p(.58,-.93,4.12),p(.78,-.73,4.13),p(.83,-.44,4.02),p(.75,-.28,3.86)],
                  [.3,.9,1,.1],.047,jade_material)
        # Oval nostrils with a polished raised rim.
        nose=_dh_uv('Nostril '+tag,p(.28,-1.505,4.08),(.11,.026,.060),dark_jade_material,32,16)
        nose.rotation_euler.y=side*.25
        _dh_curve('Nostril rim '+tag,[p(.15,-1.51,4.08),p(.23,-1.53,4.155),p(.35,-1.48,4.14),p(.42,-1.40,4.07)],
                  [.3,1,1,.1],.032,jade_material)
        # Horns grow from a broad base, with asymmetric antler branches.
        _dh_curve('Main antler '+tag,[p(.43,-.17,4.58),p(.48,-.02,4.83),p(.56,.19,5.10),p(.57,.43,5.30),p(.70,.65,5.48)],
                  [1.20,1.05,.80,.48,.035],.15,jade_material)
        _dh_curve('Antler tine '+tag,[p(.52,.10,4.99),p(.80,.14,5.18),p(.94,.29,5.41)],
                  [.85,.50,.035],.12,jade_material)
        _dh_curve('Antler front tine '+tag,[p(.47,-.04,4.81),p(.65,-.25,4.97),p(.69,-.34,5.12)],
                  [.70,.45,.025],.10,jade_material)
        for j in range(3):
            z=4.65+j*.11
            _dh_curve('Horn collar '+tag+str(j),[p(.31+j*.025,-.16+j*.06,z),p(.42+j*.03,-.24+j*.06,z+.02),p(.54+j*.03,-.13+j*.06,z)],
                      [.3,.65,.3],.021,dark_jade_material)
        # Side ears and layered mane retain the vocabulary of archaic jade.
        _dh_leaf('Swept ear '+tag,[p(.60,-.05,4.35),p(.85,.11,4.45),p(1.04,.28,4.61),p(1.10,.43,4.71)],.24,jade_material)
        _dh_curve('Ear ridge '+tag,[p(.67,-.075,4.40),p(.86,.12,4.50),p(1.06,.36,4.68)],
                  [.3,.6,.03],.025,dark_jade_material)
        for i in range(4):
            _dh_leaf('Cheek mane '+tag+str(i),[p(.62,-.26+i*.12,4.05-i*.12),p(.86,-.05+i*.12,4.03-i*.13),p(.91,.23+i*.12,4.06-i*.14),p(.85,.42+i*.1,4.17-i*.15)],
                      .15-i*.013,jade_material)
        # The long drooping whisker returns in an elegant curled tip.
        _dh_curve('Long whisker '+tag,[p(.50,-1.29,3.98),p(.89,-1.46,3.95),p(1.19,-1.44,4.08),p(1.29,-1.24,4.29),p(1.13,-1.11,4.38),p(1.02,-1.18,4.27)],
                  [1.15,.91,.67,.46,.28,.025],.063,jade_material)
        _dh_curve('Small whisker '+tag,[p(.48,-1.25,3.93),p(.80,-1.40,3.77),p(.95,-1.27,3.64),p(.90,-1.11,3.68)],
                  [1,.7,.35,.025],.045,jade_material)
        # Down-curved canines and smaller incisors.
        _dh_curve('Fang '+tag,[p(.43,-1.33,3.88),p(.45,-1.40,3.75),p(.40,-1.40,3.63)],
                  [1,.70,.02],.065,jade_material)
        _dh_curve('Lower canine '+tag,[p(.33,-1.38,3.66),p(.33,-1.43,3.75),p(.30,-1.41,3.79)],
                  [1,.55,.02],.045,jade_material)
    for x in [-.16,0,.16]:
        _dh_curve('Incisor',[ (x,-1.48,3.84),(x,-1.49,3.76)], [1,.30], .040,jade_material)
    # Longitudinal forehead ridges and a curled imperial beard.
    for x in [-.18,0,.18]:
        _dh_curve('Forehead relief',[(x,-.95,4.39),(x*.85,-.70,4.61),(x*.70,-.38,4.70),(x*.65,-.16,4.63)],
                  [.15,.7,.8,.1],.034,jade_material)
    for i in [-2,-1,0,1,2]:
        x=i*.11
        _dh_curve('Beard tendril',[(x,-1.23,3.48),(x*1.25,-1.22,3.26),(x*1.37,-1.05,3.08+abs(i)*.045),(x*1.15,-.90,3.14+abs(i)*.065)],
                  [1,.8,.5,.025],.065-abs(i)*.008,jade_material)
    return [obj for obj in bpy.data.objects if obj not in initial]
