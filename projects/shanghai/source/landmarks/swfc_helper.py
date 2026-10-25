"""Compact, quarter-scale Shanghai World Financial Center landmark.

Blender x=east, y=north, z=up. The sky portal is actual open geometry.
"""
import bpy
from mathutils import Vector


def _sf_mesh(name, verts, faces, material):
    data=bpy.data.meshes.new(name)
    data.from_pydata(verts,[],faces)
    data.update()
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(material)
    return obj


def _sf_box(name, location, dimensions, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    obj=bpy.context.object;obj.name=name;obj.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(material)
    if bevel:
        mod=obj.modifiers.new('Crisp architectural edges','BEVEL');mod.width=bevel;mod.segments=1
        obj.modifiers.new('Facade normals','WEIGHTED_NORMAL')
    return obj


def build_swfc(materials):
    """Build SWFC at (226,18), height123, and return new Blender objects."""
    initial=set(bpy.data.objects)
    cx,cy=226,18
    glass=materials['glass_blue'];silver=materials['silver'];stone=materials['stone']
    def width(z):return 18-8*z/123
    def depth(z):return 14-4*z/123
    verts=[]
    for z in [0,123]:
        w,d=width(z)/2,depth(z)/2
        verts.extend([(cx-w,cy-d,z),(cx+w,cy-d,z),(cx+w,cy+d,z),(cx-w,cy+d,z)])
    body=_sf_mesh('SWFC · tapered glass body',verts,
                  [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],glass)
    # The signature bottle-opener portal goes fully through both main facades.
    cut=_sf_box('SWFC temporary sky portal',(cx,cy,111.5),(7.4,30,13),stone)
    bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
    mod=body.modifiers.new('Actual open sky portal','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cut,do_unlink=True)
    body['landmark']='上海环球金融中心 / Shanghai World Financial Center'
    body['original_height_m']=492
    # Delicate horizontal mullions grouped into one mesh. Nothing spans the hole.
    v=[];f=[]
    def quad(points):
        i=len(v);v.extend(points);f.append(tuple(i+j for j in range(4)))
    levels=[z*2.0 for z in range(1,53)]+[119,121,122.7]
    for z in levels:
        h=.055;w=width(z)/2;d=depth(z)/2
        for side in [-1,1]:
            y=cy+side*(d+.018)
            quad([(cx-w,y,z-h),(cx+w,y,z-h),(cx+w,y,z+h),(cx-w,y,z+h)])
            x=cx+side*(w+.018)
            quad([(x,cy-d,z-h),(x,cy+d,z-h),(x,cy+d,z+h),(x,cy-d,z+h)])
    # Tall mullions follow the tapered envelope. Main center grid stops below
    # the portal, while corner mullions continue to the sky bridge.
    for side in [-1,1]:
        for fraction in [-1,-.8,-.6,-.4,-.2,0,.2,.4,.6,.8,1]:
            top=122.8 if abs(fraction)>.8 else 104.7
            x0=cx+fraction*width(.3)/2;x1=cx+fraction*width(top)/2
            y0=cy+side*(depth(.3)/2+.025);y1=cy+side*(depth(top)/2+.025)
            t=.024 if abs(fraction)<.99 else .072
            quad([(x0-t,y0,.3),(x0+t,y0,.3),(x1+t,y1,top),(x1-t,y1,top)])
        for fraction in [-.75,-.5,-.25,0,.25,.5,.75]:
            z0,z1=.3,122.8
            y0=cy+fraction*depth(z0)/2;y1=cy+fraction*depth(z1)/2
            x0=cx+side*(width(z0)/2+.025);x1=cx+side*(width(z1)/2+.025)
            quad([(x0,y0-.022,z0),(x0,y0+.022,z0),(x1,y1+.022,z1),(x1,y1-.022,z1)])
    _sf_mesh('SWFC · silver mullion grid',v,f,silver)
    # Portal rim emphasizes its depth without blocking the actual opening.
    for side in [-1,1]:
        y=cy+side*(depth(111.5)/2+.04)
        _sf_box('SWFC · portal jamb',(cx-3.74,y,111.5),(.10,.12,13.15),silver)
        _sf_box('SWFC · portal jamb',(cx+3.74,y,111.5),(.10,.12,13.15),silver)
        _sf_box('SWFC · skybridge underside',(cx,y,118.05),(7.6,.14,.17),silver)
        _sf_box('SWFC · skydeck sill',(cx,y,104.95),(7.6,.14,.17),silver)
    _sf_box('SWFC · low podium',(cx,cy,1.2),(24,20,2.4),stone,.2)
    _sf_box('SWFC · entrance canopy',(cx,cy-11,2.6),(13,4,.35),silver,.08)
    return [obj for obj in bpy.data.objects if obj not in initial]


if __name__=='__main__':
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    mats={}
    for name,col in [('glass_blue',(.08,.22,.32)),('silver',(.55,.64,.68)),('stone',(.35,.37,.39))]:
        m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);mats[name]=m
    objects=build_swfc(mats)
    print('SWFC_TEST',len(objects),'objects',sum(len(o.data.polygons) for o in objects),'faces')
    assert len(objects)>3
