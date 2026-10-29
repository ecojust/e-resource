"""Run in Blender: compare saved model triangles against actual source GLB."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import bpy
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
data=a.raw.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);binary=data[28+n:]
def access(i):
 ac=doc['accessors'][i];view=doc['bufferViews'][ac['bufferView']];offset=view.get('byteOffset',0)+ac.get('byteOffset',0)
 width={'VEC3':3,'VEC2':2,'SCALAR':1}[ac['type']];dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[ac['componentType']]
 assert 'byteStride' not in view
 return np.frombuffer(binary,dtype=dtype,count=ac['count']*width,offset=offset).reshape(-1,width)
source=[]
for mesh in doc['meshes']:
 for prim in mesh['primitives']:source.append(access(prim['attributes']['POSITION'])[access(prim['indices']).reshape(-1,3)])
bpy.ops.wm.open_mainfile(filepath=str(a.native.resolve()));actual=[]
for name in bpy.context.scene['model_mesh_names']:
 obj=bpy.data.objects[name];verts=np.array([obj.matrix_world @ v.co for v in obj.data.vertices],dtype='<f4')
 verts=verts[:,[0,2,1]]*np.array([1,1,-1],dtype='<f4');faces=np.array([list(f.vertices) for f in obj.data.polygons]);assert faces.shape[1]==3;actual.append(verts[faces])
def canonical(parts):
 t=np.concatenate(parts).astype('<f4');t[t==0]=0
 v=t.view([('x','<f4'),('y','<f4'),('z','<f4')]).reshape(-1,3);v.sort(axis=1,order=['x','y','z']);return np.sort(v.view('V36').reshape(-1))
x=canonical(source);y=canonical(actual);assert np.array_equal(x,y),'Saved native triangles differ from source GLB'
source_uv=[];native_uv=[]
for mesh in doc['meshes']:
 for prim in mesh['primitives']:
  if doc['materials'][prim['material']]['name']=='pebbledash':
   ix=access(prim['indices']).ravel();source_uv.append(np.concatenate([access(prim['attributes']['POSITION']),access(prim['attributes']['TEXCOORD_0'])],axis=1)[ix])
for name in bpy.context.scene['model_mesh_names']:
 obj=bpy.data.objects[name]
 if not any(m and m.name=='pebbledash' for m in obj.data.materials):continue
 for face in obj.data.polygons:
  if obj.data.materials[face.material_index].name!='pebbledash':continue
  for li in face.loop_indices:
   loop=obj.data.loops[li];v=obj.matrix_world@obj.data.vertices[loop.vertex_index].co;uv=obj.data.uv_layers.active.data[li].uv
   native_uv.append([v.x,v.z,-v.y,uv.x,1-uv.y])
def ordered(rows):
 rows=np.asarray(rows);return rows[np.lexsort(tuple(rows[:,i] for i in reversed(range(5))))]
source_uv=ordered(np.concatenate(source_uv));native_uv=ordered(native_uv)
assert source_uv.shape==native_uv.shape
assert np.array_equal(source_uv[:,:3],native_uv[:,:3])
uv_error=float(np.max(np.abs(source_uv[:,3:]-native_uv[:,3:])));assert uv_error<2e-6,uv_error
packed={hashlib.sha256(image.packed_file.data).hexdigest() for image in bpy.data.images if image.packed_file}
expected={hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__).resolve().parent.parent/'textures').glob('*.png')}
assert len(expected)==3 and expected.issubset(packed),'Native packed texture bytes differ'
a.report.write_text(json.dumps({'raw_sha256':hashlib.sha256(data).hexdigest(),'native_sha256':hashlib.sha256(a.native.read_bytes()).hexdigest(),'triangles':len(x),'saved_native_triangle_positions_exact':True,'display_stage_excluded':True,'textured_corner_count':len(source_uv),'native_uv_max_error_after_v_flip':uv_error,'three_original_texture_pngs_packed_exact':True},indent=2)+'\n');print('PASS: saved native geometry, UVs and packed images match raw GLB')
