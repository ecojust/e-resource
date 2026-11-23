"""Decode the delivered triangles. Test front rays through the gate and gable separately."""
import json,struct,hashlib,math,sys
from pathlib import Path
def read_glb(path):
    b=path.read_bytes();a=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+a]);bin=b[28+a:]
    def array(i):
        v=g['accessors'][i];view=g['bufferViews'][v['bufferView']]
        fmt={5123:'H',5125:'I',5126:'f'}[v['componentType']]*{'SCALAR':1,'VEC3':3,'VEC2':2}[v['type']]
        size=struct.calcsize('<'+fmt);off=view.get('byteOffset',0)+v.get('byteOffset',0)
        return list(struct.iter_unpack('<'+fmt,bin[off:off+size*v['count']]))
    faces=[];pts=[];names=set()
    for mesh in g['meshes']:
        names.add(mesh['name'])
        for p in mesh['primitives']:
            m=g['materials'][p['material']]['name'];vertices=[(x,-z,y)for x,y,z in array(p['attributes']['POSITION'])];idx=[q[0]for q in array(p['indices'])]
            assert len(array(p['attributes']['NORMAL']))==len(array(p['attributes']['TEXCOORD_0']))==len(vertices)
            pts.extend(vertices)
            for a,b_,c in zip(idx[::3],idx[1::3],idx[2::3]):faces.append((mesh['name'],m,vertices[a],vertices[b_],vertices[c]))
    return g,pts,faces
def cast(faces,x,z,near):
    hits=[]
    for name,mat,a,b,c in faces:
        den=(b[0]-a[0])*(c[2]-a[2])-(b[2]-a[2])*(c[0]-a[0])
        if abs(den)<1e-8:continue
        u=((x-a[0])*(c[2]-a[2])-(z-a[2])*(c[0]-a[0]))/den
        v=((b[0]-a[0])*(z-a[2])-(b[2]-a[2])*(x-a[0]))/den
        if u>=-1e-7 and v>=-1e-7 and u+v<=1+1e-7:
            t=a[1]+u*(b[1]-a[1])+v*(c[1]-a[1])
            if t>=near:hits.append((t,name,mat))
    return min(hits) if hits else None
def checks(path):
    g,pts,faces=read_glb(path);out=[]
    def must(label,x,z,near,prefix,lo,hi):
        hit=cast(faces,x,z,near)
        assert hit and hit[1].startswith(prefix) and lo<=hit[0]<=hi,(label,hit)
        out.append(dict(probe=label,x=x,z=z,origin_y=near,surface=hit[1],material=hit[2],y_m=round(hit[0],5)))
    for x in (-.95,-.43,.36,.86):
        for z in (.35,.78,1.33,1.98):must('double metal gate',x,z,-1,'02.',-.03,.06)
    must('centre gap ends at rear house plane',0,1.92,-1,'10.front',7.99,8.01)
    for x in (-1.47,1.47):must('gatepost',x,.66,-1,'01.',-.07,0)
    must('enamel number plate',1.35,2.015,-1,'04.number',-.071,-.06)
    must('painted numeral four',1.473,1.989,-1,'04.enamel-digit',-.074,-.065)
    for x,z in ((.931,4.985),(.766,4.84),(1.093,4.82)):must('unfilled through vent with set-back inner shadow',x,z,6,'12.dark-interior',8.33,8.35)
    for x in (.43,.74,1.06,1.38):
        for z in (3.45,3.68,3.92,4.12,4.33):must('steel sash glazing',x,z,6,'11.four-light-steel-window-glass',8.07,8.09)
    for x in (.602,.914,1.225):must('standing steel mullion',x,3.77,6,'11.four-light-steel-window-stiles',8.010,8.02)
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),triangles=len(faces),parts=len(g['meshes']),textures=[i['name']for i in g['images']],probes=out)
if __name__=='__main__':
    folder,out=map(Path,sys.argv[1:]);values={k:checks(folder/(k+'.glb')) for k in ('raw','full','lod')};assert len({v['sha256'] for v in values.values()})==3
    out.write_text(json.dumps(values,ensure_ascii=False,indent=2)+'\n');print([(k,len(v['probes']),v['triangles'])for k,v in values.items()])
