"""Update an existing ordinary catalog record and verify its complete SHA-256 chain."""
from argparse import ArgumentParser
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile

MODEL='yangpu-library'
MACRO='14-13722-6690'
SOURCE=Path('source/precise/yangpu-library/revisions/east-entry-relief')
AUDIT=Path('data/audit/yangpu-library-east-entry-relief-v1')
CANDIDATE=Path('data/precise-candidates/yangpu-library.json')
LANDMARKS=Path('data/landmarks.json')
INDEX=Path('data/precise-buildings/macros')/MACRO/'index.json'
CATALOG=Path('data/precise-buildings/catalog.json')
REGISTRY=Path('data/precise-buildings-v6.json')
BASELINE='ae55637ce1d7cbc4d21fd94934c8309aca1dcd09'
V13_RECORD_BLOB='4acfe2c2780ea671bd590caf720e86855979df1e'


def sha(data):return sha256(data).hexdigest()


def encoded(doc):
    return (json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode()


def base_blob(project,relative):
    return subprocess.check_output(['git','-C',project,'show',f'{BASELINE}:projects/shanghai/{relative}'])


def receipt(project,relative):
    data=(project/relative).read_bytes()
    return dict(file=relative.as_posix(),bytes=len(data),sha256=sha(data))


def checked_target(rows,key,value):
    matches=[item for item in rows if item.get(key)==value]
    if len(matches)!=1:raise ValueError(f'Expected exactly one {key}={value} record')
    return matches[0]


def build_record(project,manifest,relative_manifest,repo):
    original=json.loads(subprocess.check_output(['git','-C',repo,'cat-file','blob',V13_RECORD_BLOB]))
    if original['id']!=MODEL or original['owner']['feature_local_id']!=1196:raise ValueError('Incorrect immutable V13 record')
    if (manifest.get('id'),manifest.get('revision'),manifest.get('url_base'),manifest.get('viewer_page'))!=(
        MODEL,'east-entry-relief','project-root','index.html#landmark=yangpu-library&mode=walk'):
        raise ValueError('Revision identity differs from the original navigation target')
    revised=deepcopy(original)
    assets=manifest['assets'];assert set(assets)=={'raw','full','lod','native'}
    for role,key,alias in [('raw','raw','editable_model'),('full','web','model'),('lod','lod','lod_model'),('native','native','native_model')]:
        a=assets[role]
        prefix=('assets/native'if role=='native'else'assets/models')+f'/precise/{MACRO}/{MODEL}/revisions/east-entry-relief/'
        assert a['file'].startswith(prefix) and '..' not in Path(a['file']).parts
        checked=receipt(project,Path(a['file']))
        if any(checked[k]!=a[k]for k in checked) or a['bytes']>=100000000:raise ValueError('Invalid '+role+' asset')
        revised['assets'][key]=checked
        revised[alias]=a['file'];revised[key+'_bytes']=a['bytes'];revised[key+'_sha256']=a['sha256']
        if role!='native':
            assert isinstance(a['triangles'],int)and a['triangles']>0
            revised['triangles'if key=='web'else key+'_triangles']=a['triangles']
    proofs={}
    for gate,document,scope in [
        ('geometry_proof',AUDIT/'geometry-revision.json','Actual V13 and revised oriented faces, bounds, material assignment and unchanged areas of both complete models.'),
        ('visible_facade_opening_grid',AUDIT/'visual-review.json','Matched photographs and isolated renders of the revised exterior doors, stone arch and side frieze.'),
        ('size_proof',relative_manifest,'New raw, web, LOD and native files are signed, checked and below the per-file limit.'),
        ('source_photos',SOURCE/'reference-review.json','2019 exterior detail, separately published archive photograph and 2018 whole east façade identify the actual outer doors.'),
        ('browser_proof',AUDIT/'isolated-browser.json','A real isolated WebGL renderer loaded both revised distribution GLBs. Original city navigation and owner stay unchanged.')]:
        info=receipt(project,document);proofs[gate]=info
        if gate=='browser_proof':
            result=json.loads((project/document).read_bytes())
            assert result['passed'] and result['manifest_sha256']==sha((project/relative_manifest).read_bytes())
        revised['acceptance'][gate]=dict(status='passed',evidence_file=info['file'],evidence_bytes=info['bytes'],
                                         evidence_sha256=info['sha256'],scope=scope)
    revised['source_package']=SOURCE.as_posix()
    revised['detail_note']=original['detail_note']+' 东侧主门依据原图细化双扇门、云纹镶面、石拱花饰与两侧卷草带。'
    revised['revision']=dict(id='east-entry-relief',manifest=relative_manifest.as_posix(),scope=manifest['model_scope_zh'],
        previous_raw_sha256=original['raw_sha256'],original_navigation=original['navigation'],
        source_register=(SOURCE/'reference-review.json').as_posix(),evidence=proofs)
    return original,revised


def serialize_updates(project,manifest_path,repo):
    rel=manifest_path.resolve().relative_to(project)
    original,revised=build_record(project,json.loads(manifest_path.read_bytes()),rel,repo)
    paths=[CANDIDATE,LANDMARKS,INDEX,CATALOG,REGISTRY]
    origin={name:(project/name).read_bytes() if (project/name).exists() else base_blob(repo,name) for name in paths}
    docs={key:json.loads(value) for key,value in origin.items()}
    for entry in [docs[CANDIDATE],checked_target(docs[LANDMARKS],'id',MODEL),
                  checked_target(docs[INDEX]['models'],'id',MODEL)]:
        if entry not in (original,revised):
            raise ValueError('A third revision has modified the target. Inspect the current record before applying this one.')
        entry.clear();entry.update(deepcopy(revised))
    generated={p:encoded(docs[p])for p in (CANDIDATE,LANDMARKS,INDEX)}
    pointer=checked_target(docs[CATALOG]['macros'],'id',MACRO)
    if pointer['file']!=INDEX.as_posix()or pointer['record_count']!=len(docs[INDEX]['models']):raise ValueError('Macro pointer mismatch')
    pointer.update(bytes=len(generated[INDEX]),sha256=sha(generated[INDEX]))
    generated[CATALOG]=encoded(docs[CATALOG])
    highest=docs[REGISTRY]['ordinary_catalog']
    if highest['file']!=CATALOG.as_posix():raise ValueError('Ordinary catalog path mismatch')
    highest.update(bytes=len(generated[CATALOG]),sha256=sha(generated[CATALOG]))
    generated[REGISTRY]=encoded(docs[REGISTRY])
    return origin,generated


def main():
    cli=ArgumentParser(description=__doc__)
    cli.add_argument('--project',required=True,type=Path);cli.add_argument('--manifest',required=True,type=Path)
    cli.add_argument('--base-repo',type=Path,help='Git checkout containing the signed V13 baseline; defaults to --project')
    cli.add_argument('--verify',action='store_true');args=cli.parse_args();project=args.project.resolve()
    mf=args.manifest if args.manifest.is_absolute()else (project/args.manifest)
    originals,updates=serialize_updates(project,mf,args.base_repo or project)
    # Validate the complete change before replacing any file. A retry repairs
    # a mixture of old/revised target records following an interrupted write.
    if not args.verify:
        for rel,data in updates.items():
            path=project/rel
            if path.exists():
                current=path.read_bytes()
                if current==data:continue
                if current!=originals[rel]:raise ValueError('Concurrent change in '+str(rel))
            path.parent.mkdir(parents=True,exist_ok=True)
            fd,temp=tempfile.mkstemp(prefix=path.name+'.incoming-',dir=path.parent)
            try:
                with os.fdopen(fd,'wb')as stream:stream.write(data)
                os.replace(temp,path)
            finally:Path(temp).unlink(missing_ok=True)
    for rel,data in updates.items():
        if not (project/rel).exists() or (project/rel).read_bytes()!=data:raise ValueError('Unbound ordinary record '+str(rel))
    print(json.dumps({str(rel):sha(data)for rel,data in updates.items()},indent=2))


if __name__=='__main__':main()
