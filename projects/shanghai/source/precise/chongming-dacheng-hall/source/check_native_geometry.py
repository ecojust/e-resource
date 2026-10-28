"""Run in Blender: compare saved model triangles against actual source GLB."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import bpy
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
data=a.raw.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);binary=data[28+n:]
def access(i):
 ac=doc['accessors'][i];view=doc['bufferViews'][ac['bufferView']];offset=view.get('byteOffset',0)+ac.get('byteOffset',0)
 width=3 if ac['type']=='VEC3' else 1;dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[ac['componentType']]
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
a.report.write_text(json.dumps({'raw_sha256':hashlib.sha256(data).hexdigest(),'native_sha256':hashlib.sha256(a.native.read_bytes()).hexdigest(),'triangles':len(x),'saved_native_triangle_positions_exact':True,'display_stage_excluded':True},indent=2)+'\n');print('PASS: saved native geometry matches raw GLB')
