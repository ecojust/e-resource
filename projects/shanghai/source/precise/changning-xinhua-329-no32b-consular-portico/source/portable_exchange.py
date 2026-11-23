"""Export OBJ/MTL and metre-based binary STL and compare all imported triangles."""
import argparse
import base64
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

def digest(b):
    return hashlib.sha256(b).hexdigest()

def corner(x):
    return tuple(struct.unpack('<fff',struct.pack('<fff',*x)))

def oriented(points):
    a,b,c=map(corner,points)
    return min((a,b,c),(b,c,a),(c,a,b))

def main(package, out, report):
    key=package['metadata']['id']
    out.mkdir(parents=True,exist_ok=True)
    obj=['# Architectural exterior, local coordinates in metres, Z up',
         'mtllib '+key+'.mtl'];mtl=[];texture_names={}
    for i,(name,mat) in enumerate(package['materials'].items(),1):
        keyname='material_'+str(i);texture_names[name]=keyname
        mtl.extend(['newmtl '+keyname,'# '+name,'Kd '+' '.join(map(str,mat['color'])),
                    'Pr '+str(mat['roughness']),'illum 2'])
        if tex:=mat.get('texture'):mtl.append('map_Kd '+tex)
        if nrm:=mat.get('normal'):
            strength=mat.get('normal_strength',1.)
            mtl.append('norm '+(('-bm '+str(strength)+' ') if strength!=1. else '')+nrm)
        if mat.get('alpha',1.)<1.:mtl.append('d '+str(mat['alpha']))
        mtl.append('')
    total=sum(len(p['triangles']) for p in package['parts'])
    stl=bytearray(b'Architectural exterior, metres, Z up'.ljust(80,b'\0')+struct.pack('<I',total))
    expected=Counter();expected_obj=Counter();offset=0;uvoffset=0
    for i,part in enumerate(package['parts'],1):
        name=f"part_{i:06d}"
        obj.append("# architectural_label "+json.dumps(part["label"],ensure_ascii=False))
        mat=texture_names[part['material']]
        obj.extend(['o '+name,'usemtl '+mat])
        xyz=part['vertices'];uv=part.get('texcoords')
        obj.extend('v '+' '.join(format(v,'.17g') for v in point) for point in xyz)
        if uv:obj.extend('vt '+format(u,'.17g')+' '+format(1-v,'.17g') for u,v in uv)
        for a,b,c in part['triangles']:
            pts=tuple(xyz[n] for n in (a,b,c))
            ref=oriented(pts);expected[ref]+=1
            ids=(a,b,c)
            texvals=tuple((round(uv[n][0],6),round(1-uv[n][1],6)) if uv else () for n in ids)
            pts_uv=tuple((corner(p),v) for p,v in zip(pts,texvals))
            expected_obj[(name,mat,min(pts_uv,pts_uv[1:]+pts_uv[:1],pts_uv[2:]+pts_uv[:2]))]+=1
            items=[str(offset+n+1)+('/'+str(uvoffset+n+1) if uv else '') for n in ids]
            obj.append('f '+' '.join(items))
            a1,b1,c1=pts
            u=[y-x for x,y in zip(a1,b1)]
            v=[y-x for x,y in zip(a1,c1)]
            n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            length=math.hypot(*n); assert length>0
            stl.extend(struct.pack('<12fH',*(t/length for t in n),*a1,*b1,*c1,0))
        offset+=len(xyz)
        if uv:uvoffset+=len(uv)
    stlpath=out/(key+'.stl');stlpath.write_bytes(stl)
    wave=out/(key+'-obj.zip')
    entries={key+'.obj':('\n'.join(obj)+'\n').encode(),key+'.mtl':('\n'.join(mtl)+'\n').encode()}
    entries['component-labels.json']=json.dumps({f'part_{i:06d}':p['label'] for i,p in enumerate(package['parts'],1)},ensure_ascii=False,indent=2).encode()
    entries.update({n:base64.b64decode(v) for n,v in package['textures'].items()})
    with ZipFile(wave,'w') as z:
        for name,data in sorted(entries.items()):
            info=ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,data)
    with ZipFile(wave) as z:
        assert z.testzip() is None
        verts=[];uvs=[];actual=Counter();groups=set()
        for line in z.read(key+'.obj').decode().splitlines():
            tok=line.split()
            if not tok:continue
            if tok[0]=='o':group=tok[1];groups.add(group)
            elif tok[0]=='usemtl': material=tok[1]
            elif tok[0]=='v':verts.append(corner([float(t)for t in tok[1:]]))
            elif tok[0]=='vt':uvs.append(tuple(round(float(t),6) for t in tok[1:]))
            elif tok[0]=='f':
                indices=[v.split('/') for v in tok[1:]]
                values=tuple((verts[int(v[0])-1],uvs[int(v[1])-1] if len(v)>1 else ())for v in indices)
                actual[(group,material,min(values,values[1:]+values[:1],values[2:]+values[:2]))]+=1
        assert actual==expected_obj and len(groups)==len(package['parts'])
        parsed=z.read(key+'.mtl').decode().splitlines()
        images={}
        for row in parsed:
            if row.startswith(('map_Kd ','norm ')):
                _,value=row.split(maxsplit=1)
                file=value.split(maxsplit=2)[2] if value.startswith('-bm ') else value
                images[file]=digest(z.read(file))
        assert images=={name:digest(base64.b64decode(blob)) for name,blob in package['textures'].items()}
    restored=Counter()
    data=stlpath.read_bytes();assert struct.unpack_from('<I',data,80)[0]==total and len(data)==84+50*total
    for pos in range(84,len(data),50):
        values=struct.unpack_from('<12fH',data,pos)
        restored[oriented((values[3:6],values[6:9],values[9:12]))]+=1
    assert restored==expected
    report.write_text(json.dumps(dict(triangles=total,parts=len(groups),materials=len(texture_names),
       obj_texture_bytes=images,metres=True,stl_oriented_triangles_verified=True,
       obj_material_uv_corner_records_verified=True,assets={r:dict(file=p.name,bytes=p.stat().st_size,sha256=digest(p.read_bytes()))for r,p in [('obj',wave),('stl',stlpath)]}),indent=2)+'\n')

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for n in ('components','output','report'):ap.add_argument(n,type=Path)
    args=ap.parse_args()
    main(json.loads(args.components.read_bytes()),args.output,args.report)
