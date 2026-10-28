#!/usr/bin/env python3
"""Build the estimated Jinshanwei gatehouse exterior. agent, MIT."""
from pathlib import Path
import gzip
import hashlib
import json
import sys
import platform
import argparse
import os
import struct
import numpy as np
from architecture import construct
from brick_material import assign_brick_uv
ROOT=Path(__file__).resolve().parent.parent
D=json.loads((ROOT/'source/design-input.json').read_text())


def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def desc(p):return {'file':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replace-unaccepted-draft',action='store_true',help='Atomically replace own draft artifacts only; default refuses existing GLBs')
    args=parser.parse_args()
    out=ROOT/'exports';out.mkdir(exist_ok=True)
    for n in ['jinshanwei-gatehouse-raw.glb','jinshanwei-gatehouse-lod-source.glb']:
        p=out/n
        if p.exists():
            if not args.replace_unaccepted_draft:raise FileExistsError('Use fresh outputs; accepted files are never overwritten.')
            raw=p.read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size])
            if p.stat().st_nlink!=1 or not doc.get('extras',{}).get('status','').startswith('Draft for independent review'):
                raise ValueError('Replacement only permits independent unaccepted draft files')
    frame=D['frame'];x=np.asarray(frame['architecture_X_EN']);y=np.asarray(frame['architecture_Y_EN'])
    rotation=np.array([[x[0],y[0],0],[x[1],y[1],0],[0,0,1.]])
    assert abs(np.linalg.det(rotation)-1)<1e-10
    assets={};feature_sets={}
    for lod,filename in [(False,'jinshanwei-gatehouse-raw.glb'),(True,'jinshanwei-gatehouse-lod-source.glb')]:
        b,features=construct(D,lod);role='lod' if lod else 'full';feature_sets[role]=features
        print('CONSTRUCTED',role,len(b.parts),flush=True)
        for part in b.parts:
            if b.palette[part['material']].get('texture'):assign_brick_uv(part)
            part['vertices']=(np.asarray(part['vertices'])@rotation.T).tolist()
        metadata={'name':D['name']+(' LOD' if lod else ' exterior'), 'model_id':D['model_id'],
            'author':'agent','copyright':'Original geometry, source code and procedural textures: agent / MIT; font outlines derived from Noto Serif CJK / SIL OFL1.1. Geographic reference sources retain their own licences.',
            'anchor':frame['anchor'],'coordinates':'Anchor-local East/Up/-North in GLB; heading0; EN rotation baked',
            'architecture_X_EN':x.tolist(),'architecture_Y_EN':y.tolist(),'dimensions_estimated':True,
            'design_scope':D['scope'],'source_relationship':D['source_relationship'],
            'status':'Draft for independent review; not accepted, installed or published',
            'height_source':'Independent imagery proportions; not CNBH source polygon height',
            'no_source_photo_pixels':True,'no_interior_or_walkable_stairs_claim':True,
            'normal_contract':'No TANGENT; raw V-down; generic brick1.28m by0.64m REPEAT',
            'lod_omissions':(['fine lower-panel beads','small door rings','small bracket cross-blocks','fine roof tile surface subdivisions'] if lod else [])}
        temp=out/('.'+filename+'.pending.glb')
        if temp.exists():raise FileExistsError(temp)
        report=b.save(temp,metadata);report['file']=filename
        dump(temp.with_suffix('.geometry.json'),report)
        os.replace(temp,out/filename);os.replace(temp.with_suffix('.geometry.json'),(out/filename).with_suffix('.geometry.json'))
        assets[role]={**desc(out/filename),'triangles':report['triangles'],'bounds_glb':report['bounds_glb'],'parts':len(b.parts)}
        part_temp=out/f'.{role}-construction-parts.pending.json.gz'
        with gzip.GzipFile(filename=str(part_temp),mode='wb',mtime=0) as f:
            f.write(json.dumps({'coordinates':'Anchor-local East/North/Up; GLB(E,U,-N)','parts':b.parts},ensure_ascii=False,separators=(',',':')).encode())
        os.replace(part_temp,out/f'{role}-construction-parts.json.gz')
        dump(out/f'{role}-features.json',features)
        print('EXPORTED',role,assets[role]['bytes'],report['triangles'],flush=True)
    # LOD retains identical leaf-level apertures, real arched gate and all steps.
    preserved=['entry_opening','front_window_leaf','front_steps','east_exterior_stair']
    aperture_equal=all([f for f in feature_sets['full'] if f['kind']==k]==[f for f in feature_sets['lod'] if f['kind']==k] for k in preserved if k!='entry_opening')
    # The arch uses32 rather than48 arc segments but shares metric dimensions.
    full_gate=next(f for f in feature_sets['full'] if f['kind']=='entry_opening');lod_gate=next(f for f in feature_sets['lod'] if f['kind']=='entry_opening')
    gate_equal=all(full_gate[k]==lod_gate[k] for k in ['width_m','height_m','bottom_m','front_plane_y_m','closed_recessed_door'])
    assert aperture_equal and gate_equal
    total=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
    assert total<35_000_000
    dump(out/'build-report.json',{'schema':'jinshanwei-gatehouse-draft-build-v1','author':'agent','assets':assets,
        'design':desc(ROOT/'source/design-input.json'),'python':platform.python_version(),'numpy':np.__version__,
        'frame_determinant':float(np.linalg.det(rotation)),'lod_preserved_features':preserved,
        'lod_leaf_steps_and_stair_features_equal':aperture_equal,'lod_gate_metric_dimensions_equal':gate_equal,
        'directory_bytes_after_raws':total,'native_not_yet_generated':True,'accepted':False,'MAIN_modified':False})
    print('BUILD_COMPLETE',total,flush=True)


if __name__=='__main__':main()
