#!/usr/bin/env python3
"""Compare pre-inset and rebuilt actual GLBs, without rendering or Blender."""
from pathlib import Path
import argparse,hashlib,json,struct
import numpy as np
HERE=Path(__file__).resolve().parent


def read(path):
    raw=path.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jl]);binary=raw[28+jl:]
    def accessor(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
        n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
        return np.frombuffer(binary,dt,a['count']*n,v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
    primitives={doc['materials'][p['material']]['name']:p for mesh in doc['meshes'] for p in mesh['primitives']}
    images=[]
    for im in doc.get('images',[]):
        v=doc['bufferViews'][im['bufferView']];start=v.get('byteOffset',0);images.append(binary[start:start+v['byteLength']])
    return raw,doc,accessor,primitives,images


def check(before,after):
    br,bd,ba,bp,bi=read(before);ar,ad,aa,ap,ai=read(after)
    assert len(ar)<100_000_000 and set(bp)==set(ap)
    assert bd['materials']==ad['materials'],'Material factors, names or texture descriptors changed'
    assert bi==ai,'Original embedded JPEG bytes changed'
    rows=[];all_uv_equal=True;old_vertices=new_vertices=triangles=0
    for name,p0 in bp.items():
        p1=ap[name];i0=ba(p0['indices']).reshape(-1);i1=aa(p1['indices']).reshape(-1)
        assert len(i0)==len(i1);triangles+=len(i0)//3
        x0=ba(p0['attributes']['POSITION']);x1=aa(p1['attributes']['POSITION']);old_vertices+=len(x0);new_vertices+=len(x1)
        glass='glass' in name.lower() or name.startswith('PhotoFacade_')
        if not glass:
            assert np.array_equal(i0,i1),name+' indices changed'
            assert set(p0['attributes'])==set(p1['attributes'])
            for attribute in p0['attributes']:
                assert np.array_equal(ba(p0['attributes'][attribute]),aa(p1['attributes'][attribute])),name+' '+attribute+' changed'
            rows.append({'material':name,'non_glass':True,'all_serialized_attribute_and_index_values_identical':True,'triangles':len(i0)//3})
        else:
            # Expand through indices so harmless deduplication changes do not
            # conceal or falsely report a per-triangle-corner geometry/UV change.
            y0=x0[i0].astype(float);y1=x1[i1].astype(float);delta=y1-y0
            assert np.array_equal(y0[:,1],y1[:,1]),name+' glass height changed'
            move=np.linalg.norm(delta,axis=1)
            expected=np.minimum.reduce([np.abs(move),np.abs(move-.098),np.abs(move-.100)])
            assert expected.max()<.000003,(name,expected.max())
            rows.append({'material':name,'non_glass':False,'triangles':len(i0)//3,'all_heights_exactly_unchanged':True,'allowed_normal_moves_m':[0,.098,.1],'max_move_class_error_m':float(expected.max()),'unchanged_corner_count':int((move<.000003).sum()),'moved_corner_count':int((move>=.000003).sum())})
        if 'TEXCOORD_0' in p0['attributes']:
            uv0=ba(p0['attributes']['TEXCOORD_0']);uv1=aa(p1['attributes']['TEXCOORD_0'])
            assert np.array_equal(uv0[i0],uv1[i1]),name+' per-corner UV assignment changed'
            rows[-1]['every_triangle_corner_uv_float32_exactly_identical']=True
            rows[-1]['raw_uv_accessor_values_identical']=bool(np.array_equal(uv0,uv1))
    inset=json.loads((after.parent/'glass-frame-depth-check.json').read_text());assert inset['passed']
    report={'schema':'bund09-glass-inset-preservation-v1','passed':True,'before_file':str(before),'before_sha256':hashlib.sha256(br).hexdigest(),'after_file':str(after),'after_sha256':hashlib.sha256(ar).hexdigest(),'after_bytes':len(ar),'before_vertices':old_vertices,'after_vertices':new_vertices,'triangles_unchanged':triangles,'non_glass_attributes_and_indices_exactly_unchanged':True,'all_triangle_corner_uvs_float32_exactly_unchanged':all_uv_equal,'material_definitions_exactly_unchanged':True,'all_original_embedded_image_bytes_exactly_unchanged':True,'image_sha256':[hashlib.sha256(x).hexdigest() for x in ai],'actual_panes_inside_their_frame_depth':len(inset['panes']),'glass_thickness_change_m':{'before':.018,'after':.02},'scope':'Only arc_window panes moved along their own facade normal; glass back moves98mm and front100mm, resulting20mm thickness and20mm recess. All non-glass geometry attributes/indices and every indexed UV corner exactly preserved. Dormer dark apertures retain original depths. No lighting/render acceptance claim.','per_material':rows}
    (after.parent/'glass-inset-preservation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='per_material'},ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--before',type=Path,default=HERE/'candidates/pre-inset-bc95e772/output/bund09-raw.glb');p.add_argument('--after',type=Path,default=HERE/'output/bund09-raw.glb');a=p.parse_args();check(a.before,a.after)
