"""Project indexed coordinates through both ordinary Chromium cameras actually recorded."""
import json,struct,hashlib,sys
from pathlib import Path

def mesh_points(file):
    data=file.read_bytes()
    length,=struct.unpack_from('<I',data,12)
    obj=json.loads(data[20:20+length]); b0=28+length
    for index in {p['attributes']['POSITION'] for m in obj['meshes'] for p in m['primitives']}:
        acc=obj['accessors'][index]; bv=obj['bufferViews'][acc['bufferView']]
        assert acc['componentType']==5126 and acc['type']=='VEC3'
        start=b0+bv.get('byteOffset',0)+acc.get('byteOffset',0)
        for i in range(acc['count']):
            yield struct.unpack_from('<fff',data,start+i*bv.get('byteStride',12))
def project(points,c):
    f=c['forward'];up=c['up'];right=(f[1]*up[2]-f[2]*up[1],f[2]*up[0]-f[0]*up[2],f[0]*up[1]-f[1]*up[0])
    dot=lambda a,b:sum(x*y for x,y in zip(a,b))
    lo=[1.,1.];hi=[0.,0.];p=c['projection']
    for point in points:
        delta=[v-e for v,e in zip(point,c['position'])];z=dot(delta,f);assert z>0
        uv=((1+dot(delta,right)*p[0]/z-p[8])/2,(1-dot(delta,up)*p[5]/z+p[9])/2)
        for k in (0,1):lo[k]=min(lo[k],uv[k]);hi[k]=max(hi[k],uv[k])
    return lo+hi
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
model=Path(sys.argv[1]);run=Path(sys.argv[2]);points=list(mesh_points(model));out={};report=json.loads((run/'report.json').read_bytes())
for r in report['runs']:
    frame=next(v for v in r['screens'] if v['camera']=='overview')
    box=project(points,frame['observed_camera'])
    assert min(box[:2])>=0 and max(box[2:])<=1,box
    out[r['device']]={'fractional_bounds_left_top_right_bottom':box,'canvas_sha256':frame['sha256'],'observed_camera':frame['observed_camera']}
result={'model_sha256':digest(model),'actual_report_sha256':digest(run/'report.json'),'coordinates':'0..1, top left origin','camera_width_m':21.5,'devices':out}
Path(sys.argv[3]).write_text(json.dumps(result,indent=2)+'\n')
print([s['fractional_bounds_left_top_right_bottom'] for s in out.values()])
