"""Compact crouching jade guardian-dragon, based on Sohu cover illustration.
Blender 4.3. Main body faces -Y, sits on z=3.45. Artistic reconstruction.
"""
import math
from pathlib import Path
import bpy
from mathutils import Vector


def _rb_sphere(name,loc,scale,mat,segments=32,rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
    o=bpy.context.object;o.name='ReferenceBeast_'+name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o


def _rb_curve(name,points,radii,radius,mat):
    c=bpy.data.curves.new('ReferenceBeast_'+name,'CURVE');c.dimensions='3D';c.resolution_u=14;c.bevel_resolution=4;c.bevel_depth=radius;c.use_fill_caps=True
    s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for b,pt,r in zip(s.bezier_points,points,radii):b.co=pt;b.radius=r;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
    o=bpy.data.objects.new(c.name,c);bpy.context.collection.objects.link(o);c.materials.append(mat);return o


def _rb_fuse(objects,name,voxel=.042):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.convert(target='MESH');bpy.ops.object.join()
    o=bpy.context.object;o.name='ReferenceBeast_'+name;o.data.remesh_voxel_size=voxel;o.data.use_remesh_preserve_volume=True
    bpy.ops.object.voxel_remesh()
    m=o.modifiers.new('Hand polished transitions','SMOOTH');m.factor=.55;m.iterations=4;bpy.ops.object.modifier_apply(modifier=m.name)
    for p in o.data.polygons:p.use_smooth=True
    return o


def _rb_scroll(name,center,u,v,radius,mat,start=-.65*math.pi,turns=1.05,thick=.027):
    c=Vector(center);u=Vector(u);v=Vector(v);pts=[];rad=[]
    for j in range(23):
        t=j/22;a=start+t*2*math.pi*turns;r=radius*(1-.84*t)
        pts.append(c+u*(r*math.cos(a))+v*(r*math.sin(a)));rad.append(.30+.70*math.sin(math.pi*t)**.3)
    return _rb_curve(name,pts,rad,thick,mat)


def build_reference_beast(jade_material,recess_material):
    """Return all created objects; includes coherent fused core and jade relief."""
    initial=set(bpy.data.objects);shell=[]
    def solid(name,loc,scale):
        o=_rb_sphere(name,loc,scale,jade_material);shell.append(o);return o
    # Broad continuous mass, with a low, short back and near-upright forequarters.
    solid('Torso',(0,.15,4.58),(1.76,1.63,1.10))
    solid('Hunched back',(0,.60,5.02),(1.37,1.25,1.04))
    solid('Broad chest',(0,-.88,4.66),(1.15,.82,1.18))
    solid('Throat',(0,-.64,5.46),(.82,.68,.91))
    for side in [-1,1]:
        solid('Round shoulder',(side*1.30,-.56,4.65),(.89,.92,.93))
        solid('Bent forearm',(side*1.48,-1.12,4.09),(.55,.61,.66))
        solid('Front palm',(side*1.48,-1.55,3.65),(.59,.53,.22))
        solid('Haunch',(side*1.40,1.03,4.35),(.88,.91,.83))
        solid('Rear hock',(side*1.77,1.33,3.86),(.42,.53,.47))
        solid('Rear palm',(side*1.79,1.18,3.64),(.45,.48,.19))
        for j in range(4):
            solid('Front toe',(side*1.48+(j-1.5)*.225,-1.89,3.67),(.155,.30,.22))
        for j in range(3):solid('Rear toe',(side*1.79+(j-1)*.23,.89,3.66),(.15,.28,.20))
    # Short, broad, round dragon-lion head. Cheeks link jaws into the same body.
    solid('Cranium',(0,-.66,5.94),(.94,.70,.71))
    solid('Forehead',(0,-.86,6.26),(.79,.56,.37))
    solid('Nose bridge',(0,-1.16,6.18),(.53,.55,.34))
    solid('Upper muzzle',(0,-1.49,6.03),(.73,.41,.22))
    solid('Nose cushion',(0,-1.59,6.23),(.51,.29,.25))
    solid('Lower jaw',(0,-1.37,5.67),(.71,.48,.18))
    solid('Chin',(0,-1.56,5.61),(.45,.29,.18))
    for side in [-1,1]:
        solid('Cheek',(side*.72,-.70,5.86),(.37,.53,.48))
        solid('Muzzle scroll',(side*.51,-1.44,6.14),(.31,.36,.29))
        brow=solid('Heavy eyebrow',(side*.56,-1.02,6.37),(.45,.26,.16));brow.rotation_euler.y=side*-.16
    # Curled, short ears/horns merge into the skull, rather than tall antlers.
    for side in [-1,1]:
        def q(x,y,z):return(side*x,y,z)
        horn=_rb_curve('Short curled horn',[q(.76,-.15,6.33),q(1.01,.06,6.46),q(1.17,.27,6.49),q(1.10,.39,6.32),q(.99,.28,6.27)],
                       [1.2,1,.78,.48,.07],.16,jade_material);shell.append(horn)
        ear=solid('Rounded folded ear',q(1.0,-.04,6.10),(.31,.28,.23));ear.rotation_euler.y=side*.35
    # A thick tail curls against the rear flank and ends in a soft hooked tuft.
    tail=_rb_curve('Compact curled tail',[(0,1.38,4.55),(-.56,1.88,4.52),(-1.29,1.96,4.61),(-1.85,1.48,4.79),(-1.82,.95,5.02),(-1.52,.74,5.13)],
                  [1.12,1.08,.96,.78,.50,.03],.29,jade_material);shell.append(tail)
    # Scalloped central mane close to the back surface.
    for j in range(7):
        y=-.16+j*.31;z=6.39-.43*j/6
        solid('Back scallop',(0,y,z),(.31,.23,.23))
    main=_rb_fuse(shell,'Unified crouching guardian',.043)
    main['visual_reference']='Sohu article cover photograph; single crouching guardian-dragon beast'
    # Shadow recesses and polished same-material lips.
    _rb_sphere('Mouth shadow',(0,-1.67,5.845),(.58,.15,.066),recess_material)
    _rb_curve('Upper lip',[(-.67,-1.68,5.95),(-.42,-1.85,5.94),(0,-1.90,5.95),(.42,-1.85,5.94),(.67,-1.68,5.95)],
              [.3,.8,1,.8,.3],.046,jade_material)
    _rb_curve('Lower lip',[(-.59,-1.65,5.74),(0,-1.82,5.74),(.59,-1.65,5.74)],[.2,1,.2],.042,jade_material)
    for side in [-1,1]:
        def q(x,y,z):return(side*x,y,z)
        # Tiny inset eyes beneath thick eyebrows; no metallic eyeballs.
        _rb_sphere('Eye recess',q(.70,-1.11,6.245),(.16,.055,.062),recess_material)
        _rb_sphere('Jade eye',q(.70,-1.155,6.25),(.070,.024,.041),jade_material,24,16)
        _rb_curve('Curled eye brow',[q(.34,-1.30,6.32),q(.52,-1.28,6.44),q(.77,-1.05,6.48),q(.94,-.82,6.39),q(.87,-.73,6.29)],
                  [.3,.8,1,.7,.1],.059,jade_material)
        _rb_sphere('Nostril',q(.28,-1.85,6.26),(.108,.026,.059),recess_material,24,16)
        _rb_curve('Nostril curl',[q(.13,-1.86,6.25),q(.21,-1.89,6.36),q(.35,-1.84,6.36),q(.43,-1.74,6.26)],
                  [.2,.8,1,.1],.038,jade_material)
        _rb_curve('Upper tusk',[q(.46,-1.80,5.98),q(.47,-1.85,5.82),q(.43,-1.82,5.69)],[1,.75,.025],.072,jade_material)
        _rb_curve('Short whisker',[q(.53,-1.61,6.03),q(.85,-1.48,6.02),q(1.03,-1.15,6.12),q(.96,-.93,6.21)],
                  [1,.85,.52,.025],.053,jade_material)
        # Relief scrolls lie tightly on the spherical shoulders. Their explicit
        # coordinates follow the visible shell, avoiding floating decorations.
        _rb_curve('Shoulder great cloud',[
            q(.93,-1.30,5.30),q(1.28,-1.42,5.17),q(1.61,-1.39,4.99),
            q(1.82,-1.22,4.74),q(1.78,-1.29,4.48),q(1.59,-1.42,4.39),
            q(1.40,-1.47,4.48),q(1.45,-1.48,4.65),q(1.58,-1.47,4.66)],
            [.2,.7,1,1,.9,.8,.6,.4,.02],.038,jade_material)
        _rb_curve('Shoulder inner cloud',[
            q(.97,-1.42,5.08),q(1.20,-1.47,4.98),q(1.31,-1.50,4.78),
            q(1.21,-1.53,4.64),q(1.08,-1.52,4.67),q(1.08,-1.51,4.79)],
            [.1,.8,1,.8,.5,.03],.029,jade_material)
        # Downward wind grooves across neck and cheek are represented by subtle
        # jade ridges. No contrasting painted pattern is used.
        for j in range(3):
            _rb_curve('Cheek flow '+str(j),[
                q(.80+j*.07,-.65,6.01-j*.10),q(.93+j*.065,-.49,5.86-j*.11),
                q(1.09+j*.065,-.48,5.61-j*.11),q(1.16+j*.065,-.72,5.42-j*.11)],
                [.05,.65,.8,.05],.024,jade_material)
        # Haunch spiral facing each side; x surface follows rounded flank.
        _rb_curve('Haunch cloud',[
            q(1.97,.49,4.89),q(2.17,.83,4.65),q(2.25,1.15,4.39),
            q(2.15,1.37,4.16),q(2.08,1.13,4.06),q(2.18,.99,4.19)],
            [.1,.7,1,.8,.6,.05],.032,jade_material)
        # Short incisions separating each blunt claw are dark jade in the creases.
        for j in range(3):
            x=side*1.48+(j-1)*.225
            _rb_curve('Toe crease',[(x,-2.11,3.66),(x,-2.08,3.80),(x,-1.88,3.87)],
                      [.05,.7,.05],.012,recess_material)
    # A solid, tapered central beard follows the reference's long triangular fan.
    # Narrow neighboring strands merge visually into a broad carved beard.
    for i in range(-5,6):
        x=i*.057
        _rb_curve('Beard strand',[(x,-1.73,5.64),(x*.88,-1.69,5.40),(x*.65,-1.65,5.16),(x*.30,-1.59,4.97)],
                  [1,.86,.57,.025],.038,jade_material)
    _rb_curve('Chest flowing cloud',[(-.44,-1.64,4.96),(-.64,-1.66,4.65),(-.59,-1.66,4.26),(-.26,-1.69,4.05),(.14,-1.71,4.06),(.38,-1.72,4.29),(.25,-1.74,4.47),(.04,-1.75,4.42)],
              [.05,.75,1,1,.9,.8,.5,.02],.039,jade_material)
    _rb_curve('Chest inner flow',[(-.25,-1.69,4.89),(-.38,-1.74,4.60),(-.31,-1.75,4.34),(-.10,-1.77,4.26),(.05,-1.77,4.34)],
              [.05,.7,.8,.6,.03],.026,jade_material)
    # Conform cloud relief to the actual fused shell instead of leaving floating
    # ornaments above its curved shoulders and chest.
    bpy.context.view_layer.update()
    inv=main.matrix_world.inverted()
    for o in bpy.data.objects:
        if o in initial or o.type!='CURVE':continue
        front=any(key in o.name for key in ['Shoulder great cloud','Shoulder inner cloud','Chest flowing cloud','Chest inner flow'])
        flank='Haunch cloud' in o.name
        if not(front or flank):continue
        for point in o.data.splines[0].bezier_points:
            v=point.co.copy()
            if front:origin=Vector((v.x,-10,v.z));direction=Vector((0,1,0))
            else:
                side=1 if v.x>0 else -1
                origin=Vector((side*10,v.y,v.z));direction=Vector((-side,0,0))
            ok,hit,normal,index=main.ray_cast(inv@origin,(inv.to_3x3()@direction).normalized())
            if ok:
                world=main.matrix_world@hit
                if front:point.co.y=world.y-.012
                else:point.co.x=world.x+side*.012
    # Engrave the conformed clouds into the jade rather than leaving wires.
    cloud_cutters=[]
    for o in list(bpy.data.objects):
        if o in initial or o.type!='CURVE':continue
        front=any(key in o.name for key in ['Shoulder great cloud','Shoulder inner cloud','Chest flowing cloud','Chest inner flow'])
        flank='Haunch cloud' in o.name
        if not(front or flank):continue
        for point in o.data.splines[0].bezier_points:
            if front:point.co.y+=.018
            else:point.co.x-=.018 if point.co.x>0 else -.018
        o.data.resolution_u=7;o.data.bevel_resolution=3
        cloud_cutters.append(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in cloud_cutters:o.select_set(True)
    bpy.context.view_layer.objects.active=cloud_cutters[0]
    bpy.ops.object.convert(target='MESH');bpy.ops.object.join();cutter=bpy.context.object
    bpy.ops.object.select_all(action='DESELECT');main.select_set(True);bpy.context.view_layer.objects.active=main
    boolean=main.modifiers.new('Shallow carved cloud spirals','BOOLEAN');boolean.operation='DIFFERENCE';boolean.solver='EXACT';boolean.object=cutter
    bpy.ops.object.modifier_apply(modifier=boolean.name);bpy.data.objects.remove(cutter,do_unlink=True)
    created=[o for o in bpy.data.objects if o not in initial]
    for o in created:
        o.scale.x*=1.15;o.location.x*=1.15
    bpy.context.view_layer.update()
    # The reference has a taller, rounded forehead and a narrower upper head.
    # Continuous deformation retains the fused neck and all facial attachments.
    def upper_shape(v):
        v=v.copy()
        if v.z>5.3:
            t=min(1,(v.z-5.3)/.85)
            v.x*=1-.11*t
            v.z=5.3+(v.z-5.3)*1.18
        return v
    for o in created:
        mat=o.matrix_world.copy();inverse=mat.inverted()
        if o.type=='MESH':
            for v in o.data.vertices:v.co=inverse@upper_shape(mat@v.co)
        elif o.type=='CURVE':
            for spline in o.data.splines:
                for point in spline.bezier_points:point.co=inverse@upper_shape(mat@point.co)
    return created

if __name__=='__main__':
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    jade=bpy.data.materials.new('Test jade');jade.diffuse_color=(.55,.68,.56,1)
    recess=bpy.data.materials.new('Test recess');recess.diffuse_color=(.14,.19,.12,1)
    objects=build_reference_beast(jade,recess)
    print('REFERENCE_BEAST_TEST',len(objects),'objects',sum(len(o.data.polygons) for o in objects if o.type=='MESH'),'polygons')
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name('reference_beast_test.blend')))
