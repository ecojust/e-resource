"""Compress accepted raw geometry, restore copyright and bind hashes to output."""
import argparse,hashlib,json,struct,subprocess,os
from pathlib import Path
import numpy as np

COPYRIGHT=('Original architectural reconstruction and wall-union source: MIT. '
           'Footprint: © OpenStreetMap contributors, ODbL-1.0. '
           'Reference photographs are documented separately and are not embedded. '
           'Wall repair preserves the existing geographic anchor, detail and apertures; '
           'dimensions remain photo-derived estimates, not a survey.')

def read_glb(path):
    data=Path(path).read_bytes();length,kind=struct.unpack_from('<II',data,12)
    assert kind==0x4e4f534a
    doc=json.loads(data[20:20+length]);binary=data[28+length:]
    return doc,binary

def provenance(path):
    doc,binary=read_glb(path);doc['asset']['copyright']=COPYRIGHT
    doc['asset'].setdefault('extras',{})['structural_wall_repair']='Source-identified panel-volume union, with existing openings and true depth setbacks retained.'
    encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
    binary+=b'\0'*((-len(binary))%4)
    result=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary
    temp=Path(path).with_suffix('.provenance.tmp');temp.write_bytes(result);os.replace(temp,path)

def normalize_zero_area_triangles(path):
    """Drop only zero-area index triples; keep original attribute bytes intact."""
    before=Path(path).read_bytes();doc,binary=read_glb(path);original_binary=binary
    def accessor(index):
        a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']]
        if a.get('sparse')or a.get('normalized'):raise ValueError('Unexpected sparse/normalized raw accessor')
        dtype={5121:np.dtype('u1'),5123:np.dtype('<u2'),5125:np.dtype('<u4'),5126:np.dtype('<f4')}[a['componentType']]
        components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        stride=view.get('byteStride',components*dtype.itemsize)
        return np.ndarray((a['count'],components),dtype=dtype,buffer=binary,
                          offset=view.get('byteOffset',0)+a.get('byteOffset',0),strides=(stride,dtype.itemsize))
    removed=[]
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            if primitive.get('mode',4)!=4:raise ValueError('Expected triangle primitive')
            positions=accessor(primitive['attributes']['POSITION']).astype(np.float64)
            indices=accessor(primitive['indices']).reshape(-1,3)
            points=positions[indices]
            twice_area=np.cross(points[:,1]-points[:,0],points[:,2]-points[:,0])
            zero=np.all(twice_area==0,axis=1);count=int(np.count_nonzero(zero))
            if not count:continue
            kept=indices[~zero].reshape(-1);assert len(kept)
            binary+=b'\0'*((-len(binary))%4);offset=len(binary);binary+=kept.tobytes()
            view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':kept.nbytes,'target':34963})
            old=doc['accessors'][primitive['indices']];new={'bufferView':view,'componentType':old['componentType'],'count':len(kept),'type':'SCALAR','min':[int(kept.min())],'max':[int(kept.max())]}
            primitive['indices']=len(doc['accessors']);doc['accessors'].append(new)
            removed.append({'mesh':mesh.get('name'),'material':doc['materials'][primitive['material']]['name'],'removed_zero_area_triangles':count})
    assert binary[:len(original_binary)]==original_binary
    if removed:
        doc['buffers'][0]['byteLength']=len(binary)
        encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4);binary+=b'\0'*((-len(binary))%4)
        result=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary
        temporary=Path(path).with_suffix('.normalized.tmp');temporary.write_bytes(result);os.replace(temporary,path)
    return {'source_sha256':hashlib.sha256(before).hexdigest(),'normalized_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            'removed':removed,'removed_zero_area_triangles':sum(x['removed_zero_area_triangles']for x in removed),
            'original_binary_prefix_preserved':True,'attribute_buffer_bytes_unchanged':True,
            'native_faces_changed':False,'criterion':'Exactly zero cross product in original FLOAT32-position coordinates evaluated as FLOAT64; no area epsilon.'}

def summarize(path):
    data=Path(path).read_bytes();doc,_=read_glb(path)
    return {'file':Path(path).name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
            'triangles':sum(doc['accessors'][p['indices']]['count']//3 for m in doc.get('meshes',[])for p in m['primitives']),
            'meshes':len(doc.get('meshes',[])),'images':len(doc.get('images',[])),
            'copyright':doc['asset'].get('copyright'),'extensions_required':doc.get('extensionsRequired',[])}

def finalize(workdir,gltfpack):
    reports=[]
    for bid in ['bund19','bund20','bund23']:
        directory=Path(workdir)/'candidate'/bid;raw=directory/f'{bid}.glb'
        normalization=normalize_zero_area_triangles(raw)
        provenance(raw)
        commands=[]
        for suffix,options in [('web',[]),('lod',['-si','0.35','-se','0.002','-sp'])]:
            output=directory/f'{bid}-{suffix}.glb'
            cmd=[str(gltfpack),'-i',str(raw),'-o',str(output),'-cc','-noq','-km','-ke',*options]
            subprocess.run(cmd,check=True);provenance(output);commands.append(cmd)
        assets={role:summarize(directory/name)for role,name in [('raw',f'{bid}.glb'),('web',f'{bid}-web.glb'),('lod',f'{bid}-lod.glb')]}
        normalization['released_raw_sha256']=assets['raw']['sha256']
        native=directory/f'{bid}.blend';assets['native']={'file':native.name,'bytes':native.stat().st_size,'sha256':hashlib.sha256(native.read_bytes()).hexdigest()}
        assert all(a['bytes']<100_000_000 for a in assets.values())
        assert assets['raw']['triangles']==assets['web']['triangles']
        report={'id':bid,'compression_commands':commands,'assets':assets,'export_normalization':normalization,'raw_geometry_changed_by_provenance':False,
                'web_compression_flags':['-cc','-noq','-km','-ke'],
                'lod_compression_flags':['-cc','-noq','-km','-ke','-si','0.35','-se','0.002','-sp']}
        (directory/'asset-release.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');reports.append(report)
        print(bid,[(role,a['bytes'],a.get('triangles'))for role,a in assets.items()],flush=True)
    return reports

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--workdir',type=Path,required=True);parser.add_argument('--gltfpack',type=Path,required=True)
    args=parser.parse_args();finalize(args.workdir,args.gltfpack)
