"""Compare original GLB and editable-camera rays through the published 2013 window and No. 1230 plaque.

Run in Blender after opening the final .blend. Fractions of pixels refer to
centres in the native 1247 by 885 reference. Photo observations describe the
2013 exposure. The principal model records the later 2016 enclosure.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy
import numpy as np
from mathutils import Vector

HERE = Path(__file__).absolute().parent
sys.path.insert(0, str(HERE))
from register_court import Camera

# Fixed image coordinates. Left and right identify the viewer's left and right.
POINTS = (
    ('upper light 1', 188, 193), ('upper light 2', 243, 194),
    ('upper light 3', 298, 195), ('upper light 4', 345, 195),
    ('left open leaf interior in 2013', 182, 255), ('second dark opening in 2013', 246, 262),
    ('third light', 293, 249), ('fourth light', 349, 250),
    ('right pair middle divider', 321, 252), ('cross rail on rightmost pane', 344, 273),
    ('green plate at upper left', 135, 589), ('green plate at lower right', 159, 603),
    ('first numeral region', 139, 595), ('second numeral region', 144, 595),
    ('third numeral region', 149, 595), ('fourth numeral region', 155, 595),
)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def triangles(path):
    blob = path.read_bytes()
    header = struct.unpack_from('<I', blob, 12)[0]
    doc = json.loads(blob[20:20+header])
    buf = memoryview(blob)[28+header:]
    def array(i):
        a = doc['accessors'][i]; view = doc['bufferViews'][a['bufferView']]
        width = {'SCALAR':1, 'VEC3':3}[a['type']]
        dtype = np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
        offset = view.get('byteOffset',0) + a.get('byteOffset',0)
        return np.ndarray((a['count'],width),dtype,buf,offset,strides=(view.get('byteStride',width*dtype.itemsize),dtype.itemsize))
    positions,materials=[],[]
    for m in doc['meshes']:
        for p in m['primitives']:
            v=array(p['attributes']['POSITION'])[:,[0,2,1]].astype('float64')
            v[:,1]*=-1
            faces=array(p['indices']).reshape(-1,3)
            positions.append(v[faces])
            materials.append(np.full(len(faces),p['material']))
    return np.concatenate(positions), np.concatenate(materials), [m['name'] for m in doc['materials']]


def first(tri, materials, names, eye, ray):
    a=tri[:,0]; e=tri[:,1]-a; f=tri[:,2]-a
    h=np.cross(ray,f); det=np.einsum('ij,ij->i',e,h)
    inverse=np.divide(1.,det,out=np.zeros_like(det),where=np.abs(det)>1e-10)
    delta=eye-a
    u=np.einsum('ij,ij->i',delta,h)*inverse; q=np.cross(delta,e)
    v=(q@ray)*inverse
    t=np.einsum('ij,ij->i',q,f)*inverse
    valid=(np.abs(det)>1e-10)&(u>=0)&(v>=0)&(u+v<=1)&(t>0)
    t[~valid]=np.inf
    index=int(t.argmin())
    return (names[materials[index]],eye+t[index]*ray) if np.isfinite(t[index]) else (None,None)


def run(raw, output, render_crops=False):
    output.mkdir(parents=True, exist_ok=True)
    scene=bpy.context.scene
    view=next(v for v in json.loads((HERE.parent/'source/cameras.json').read_bytes()) if v['name']=='photo-2013')
    cam=bpy.data.objects[view['label']]; scene.camera=cam
    size=(view['width'],view['height'])
    reference=Camera('04')
    assert size==(reference.width,reference.height)
    render=scene.render; render.resolution_x,render.resolution_y=size; render.resolution_percentage=100
    render.pixel_aspect_x=render.pixel_aspect_y=1.
    graph=bpy.context.evaluated_depsgraph_get()
    projection=cam.calc_matrix_camera(graph,x=size[0],y=size[1])
    inv=projection.inverted(); c=cam.matrix_world.translation.copy()
    original=triangles(raw); checks=[]
    for label,x,y in POINTS:
        # The photo uses top-left pixel centres. NDC uses the frame boundary.
        camera_point=inv@Vector((2*(x+.5)/size[0]-1,1-2*(y+.5)/size[1],-1,1))
        local=camera_point.to_3d()/camera_point.w
        direction=(cam.matrix_world@local-c).normalized()
        hit,location,_,face,obj,_=scene.ray_cast(graph,c,direction,distance=150.)
        mat=obj.material_slots[obj.data.polygons[face].material_index].material.name if hit else None
        ray=reference.ray((x,y));ray=ray/np.linalg.norm(ray)
        expected,pos=first(*original,reference.c,ray)
        error=float(np.linalg.norm(pos-np.asarray(location))) if hit and pos is not None else None
        passed=(expected==mat and ((not hit and pos is None) or error is not None and error<.001))
        checks.append(dict(label=label,pixel=[x,y],original_material=expected,editable_material=mat,
                           editable_object=obj.name if hit else None,
                           original_xyz_m=pos.round(6).tolist() if pos is not None else None,
                           editable_xyz_m=[round(float(k),6) for k in location] if hit else None,
                           distance_between_hits_m=error,passed=passed))
    crops=[]
    if render_crops:
        scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8
        scene.cycles.use_denoising=False;render.threads_mode='FIXED';render.threads=1
        render.image_settings.file_format='PNG';render.use_border=render.use_crop_to_border=True
        for label, bounds in [('window',(143,154,398,352)),('street-number',(123,578,172,613))]:
            l,t,r,b=bounds
            render.border_min_x=l/size[0];render.border_max_x=r/size[0]
            render.border_min_y=1-b/size[1];render.border_max_y=1-t/size[1]
            photo=output/(label+'-native-resolution.png');render.filepath=str(photo)
            bpy.ops.render.render(write_still=True)
            crops.append(dict(subject=label,bounds_px=bounds,file=photo.name,sha256=sha(photo),bytes=photo.stat().st_size))
    receipt=dict(editable_sha256=sha(Path(bpy.data.filepath)),raw_sha256=sha(raw),camera=view['name'],
                 native_reference_pixels=size,checks=checks,passed=sum(r['passed'] for r in checks),count=len(checks),renders=crops)
    (output/'native-window-and-address.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    if receipt['passed']!=len(checks):raise ValueError('Editable and original photographic rays disagree')


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:]
    run(Path(args[0]),Path(args[1]),'--render-crops' in args[2:])
