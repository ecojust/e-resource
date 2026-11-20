"""Update an existing Bund landmark and its two single-building metadata mirrors.

Run against a prepared Shanghai project directory containing the five current
registry files and the four verified new assets. No site or footprint is added.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile


def read(path):
    return json.loads(path.read_bytes())


def one(rows, ident):
    result, = [row for row in rows if row.get('id')==ident]
    return result


def write(path, data):
    body=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()
    if path.read_bytes()==body:
        return
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as dest:
        temp=Path(dest.name)
        dest.write(body)
    temp.replace(path)


def apply(project,manifest_path,report_path):
    manifest=read(manifest_path)
    ident,assets=manifest['id'],manifest['assets']
    assert ident=='bund15' and manifest['revision']=='river-arch-relief'
    assert set(assets)=={'raw','full','lod','native'}
    assert manifest['url_base']=='project-root'
    for record in assets.values():
        file=project/record['file']
        assert project in file.resolve().parents and file.stat().st_size==record['bytes']
        assert sha256(file.read_bytes()).hexdigest()==record['sha256']
    original=read(manifest_path.with_name('baseline.json'))['assets']
    files=['data/landmarks.json','data/bund/manifest.json','data/bund/lod-v4.json',
           f'data/bund/models/{ident}-web.json',f'data/bund/models/{ident}.json']
    old=[read(project/f) for f in files]
    data=deepcopy(old)
    live,manifest_rows,lod_rows,web,raw=data
    lm=one(live,ident);reg=one(manifest_rows['buildings'],ident);lod=one(lod_rows['models'],ident)
    assert reg['candidate_id']==lm['candidate_id']==web['candidate_id']==ident
    assert raw['id']=='russo' and raw['window_apertures']==96
    ref=manifest_path.relative_to(project).as_posix()
    target=assets['raw']['sha256']
    assert lm['raw_sha256'] in {original['raw']['sha256'],target}
    description='据2014年河岸立面和拱肩特写，东面中央三樘拱窗的南樘新增双侧有翅人物、卷叶及中央张口兽首。位置参照三窗比对，局部尺度、表情和进深据照片估计。'
    source=manifest['source_package']
    common={'editable_model':assets['raw']['file'],'model':assets['full']['file'],
            'lod_model':assets['lod']['file'],'native_model':assets['native']['file'],
            'triangles':assets['full']['triangles'],'lod_triangles':assets['lod']['triangles'],
            'source_package':source,'asset_revision_manifest':ref}
    for internal,public in [('raw','raw'),('full','web'),('native','native'),('lod','lod')]:
        for field in ('sha256','bytes'):
            common[public+'_'+field]=assets[internal][field]
    for row in (lm,reg,web):
        assert row['raw_sha256'] in {original['raw']['sha256'],target}
        row.update(common)
        if description not in row['detail_note']:row['detail_note']+=' '+description
    raw.update({'model':assets['raw']['file'],'native_model':assets['native']['file'],'source_package':source,
                'asset_revision_manifest':ref,'triangles':assets['raw']['triangles'],'glb_bytes':assets['raw']['bytes']})
    for key in ('raw_sha256','raw_bytes','native_sha256','native_bytes'):
        raw[key]=common[key]
    if description not in raw['current_detail_note']:raw['current_detail_note']+=' '+description
    g={'mode':'existing V4.4 LOD with southern river-window spandrel relief',
       'triangles':assets['lod']['triangles'],'bytes':assets['lod']['bytes'],
       'maximum_bounds_change_m':lod['maximum_bounds_change_m'],'accepted':True,
       'base_lod_sha256':original['lod']['sha256'],'base_lod_triangles':44726,
       'added_triangles':assets['lod']['triangles']-44726}
    lod.update({'model':assets['lod']['file'],'sha256':assets['lod']['sha256'],'bytes':assets['lod']['bytes'],
                'triangles':assets['lod']['triangles'],'full_triangles':assets['full']['triangles'],
                'draw_primitives':assets['lod']['draw_primitives'],
                'actual_triangle_ratio':assets['lod']['triangles']/assets['full']['triangles'],
                'full_model_unchanged_sha256':assets['raw']['sha256'],
                'close_up_web_unchanged_sha256':assets['full']['sha256'],'native_unchanged_sha256':assets['native']['sha256'],
                'generation':g,'source_package':source,'asset_revision_manifest':ref})
    if lod['attempts'][-1]!=g:lod['attempts'].append(g)
    for before,after in [(old[0],live),(old[1]['buildings'],manifest_rows['buildings']),(old[2]['models'],lod_rows['models'])]:
        assert len(before)==len(after) and [r['id']for r in before]==[r['id']for r in after]
        assert all(a==b for a,b in zip(before,after)if a['id']!=ident)
    for key in ('lng','lat','heading','bearing','walkStart','bounds_glb','height_m'):
        assert lm.get(key)==one(old[0],ident).get(key)
    for field in ('id','anchor','model_axis','front_width_m','footprint_source','footprint_courtyards_preserved',
                  'bounds_blender','bounds_glb','window_apertures','window_recess_depth_m','wall_thickness_m',
                  'no_solid_box_behind_windows','curtain_repair','wall_topology_cleanup'):
        assert raw[field]==old[4][field],field
    # Validate every change before updating any file. Re-running is idempotent.
    for name,obj in zip(files,data):
        write(project/name,obj)
    if report_path:
        result={'id':ident,'revision':manifest['revision'],'three_catalog_counts':list(map(len,(live,manifest_rows['buildings'],lod_rows['models']))),
                'old_and_new_landmark_ids_equal':True,'other_building_records_unchanged':True,
                'same_anchor_ground_outline_and_city_owner':True,'manifest_sha256':sha256(manifest_path.read_bytes()).hexdigest(),
                'updated_files':{name:sha256((project/name).read_bytes()).hexdigest()for name in files}}
        report_path.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project',type=Path)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    root=args.project.resolve()
    apply(root,root/'source/precise/bund15/revisions/river-arch-relief/manifest.json',args.report)
