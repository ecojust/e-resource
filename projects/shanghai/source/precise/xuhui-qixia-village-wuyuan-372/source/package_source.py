"""Bundle the Qixia Village source and verify the textures, geometry and encoded deliveries from that archive."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
PROJECT = next(p for p in HERE.parents if (p / 'tools/package_architectural_model.py').is_file())
ID = HERE.parent.name
ARCHIVE_HELPER = 'source/precise/xuhui-yanqing-2-green-street-residence/source/package_source.py'
shared = runpy.run_path(str(PROJECT / ARCHIVE_HELPER))

README = '''# 五原路372弄6–9号栖霞村

这是上海市第五批优秀历史建筑 5D071 的三维模型源码。2016年1月20日连续拍摄的院面照片可辨认6、7、9号。中间一张通过相邻窗框和阳台与两侧配准，8号单户界线仍有不确定性。照片的原始网址、像点、相机参数、尺度假设和屋顶定位记录保存在 measurements 目录。图像作者为「中国の風景」，图集见 https://4travel.jp/travelogue/11103136 。

在解压目录运行以下命令，使用 Python 3、NumPy、Shapely 2.1 和 Pillow。重算联合摄影机另需 SciPy。压缩网页模型需要 gltfpack 和 Node.js，编辑工程需要 Blender。

```sh
src=projects/shanghai/source/precise/xuhui-qixia-village-wuyuan-372/source
mkdir -p rebuilt/whole rebuilt/packaged rebuilt/native
python "$src/court_finishes.py" --output rebuilt/finishes
python "$src/build_model.py" --output rebuilt/whole/full-source.glb
python "$src/build_model.py" --output rebuilt/whole/lod-source.glb --lod
python "$src/package_model.py" rebuilt/whole rebuilt/packaged --gltfpack gltfpack
python "$src/package_editable.py" prepare rebuilt/packaged rebuilt/native
python "$src/package_editable.py" run rebuilt/packaged rebuilt/native
```

source-files.json 记录包内源码、原创程序纹理和测量文件的字节数及 SHA-256。原摄影作品保存在所引网站。
'''


def fingerprint(data):
    return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def source_files():
    paths = {PROJECT / name for name in (*shared['SHARED'], ARCHIVE_HELPER, 'LICENSE')}
    for folder, types in ((HERE, {'.py','.png','.json','.js'}),
                          (HERE.parent/'measurements', {'.py','.json','.md','.geojson','.csv','.tsv'})):
        paths.update(p for p in folder.iterdir() if p.is_file() and p.suffix in types)
    paths.update(HERE.parent.glob('*.md'))
    # Adapters may directly reuse a source-tree script. Include that file even
    # when the previous building's shared-path list started a level below it.
    pending = list(paths)
    while pending:
        path = pending.pop()
        if path.suffix != '.py':
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node,ast.Constant) or not isinstance(node.value,str):
                continue
            value = node.value
            if value.startswith(('source/precise/','tools/','data/audit/','vendor/')) and value.endswith(('.py','.js','.mjs','.c')):
                linked = PROJECT / value
                if linked.is_file() and linked not in paths:
                    paths.add(linked)
                    pending.append(linked)
    return sorted(paths)


def write_archive(path):
    index = {}
    with ZipFile(path,'w') as archive:
        for source in source_files():
            member = 'projects/shanghai/' + source.relative_to(PROJECT).as_posix()
            data = source.read_bytes()
            shared['add'](archive,member,data)
            index[member] = fingerprint(data)
        shared['add'](archive,'README.md',README.encode())
        shared['add'](archive,'source-files.json',(json.dumps(index,ensure_ascii=False,indent=2)+'\n').encode())
    return index


def verify(archive, root, expected_mesh, expected_packed, encoder):
    with ZipFile(archive) as z:
        if z.testzip() is not None or len(z.namelist()) != len(set(z.namelist())):
            raise ValueError('Invalid source archive')
        z.extractall(root)
    project = root/'projects/shanghai'
    source = project/HERE.relative_to(PROJECT)
    env = dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',E_RESOURCE_SHANGHAI=str(project))
    env.pop('PYTHONPATH',None)
    def run(script, *args):
        subprocess.run([sys.executable,source/script,*args],cwd=root,env=env,check=True)
    for name, recorded in json.loads((root/'source-files.json').read_bytes()).items():
        if fingerprint((root/name).read_bytes()) != recorded:
            raise ValueError(f'Extracted source member changed: {name}')
    textures = {}
    generated = root/'regenerated-textures'
    run('court_finishes.py','--output',generated)
    pngs = {p.name for p in source.glob('*.png')}
    if {p.name for p in generated.glob('*.png')} != pngs:
        raise ValueError('Generated and archived source texture filenames differ')
    for name in sorted(pngs):
        data = (generated/name).read_bytes()
        if data != (source/name).read_bytes():
            raise ValueError(f'Procedural texture differs after regeneration: {name}')
        textures[name] = fingerprint(data)['sha256']
    geometry, deliveries = {}, {}
    whole = root/'whole'
    whole.mkdir()
    for role in ('full','lod'):
        mesh = whole/(role+'-source.glb')
        run('build_model.py','--output',mesh,*(['--lod'] if role=='lod' else []))
        data = mesh.read_bytes()
        if data != (expected_mesh/mesh.name).read_bytes():
            raise ValueError(f'Clean source rebuild changed {role} geometry')
        geometry[role] = fingerprint(data)
    if expected_packed:
        packed = root/'packaged'
        run('package_model.py',whole,packed,'--gltfpack',encoder)
        for role in ('raw','web','lod'):
            name = f'{ID}-{role}.glb'
            data = (packed/name).read_bytes()
            if data != (expected_packed/name).read_bytes():
                raise ValueError(f'Clean source rebuild changed the {role} delivery')
            deliveries[role] = fingerprint(data)
    return textures,geometry,deliveries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--verify-mesh-dir',type=Path,required=True)
    parser.add_argument('--verify-packaged-dir',type=Path)
    parser.add_argument('--gltfpack',default=os.environ.get('GLTFPACK','gltfpack'))
    args = parser.parse_args()
    out = args.output.resolve()
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent,prefix='qixia-source-') as staging:
        stage = Path(staging)
        archive = stage/out.name
        index = write_archive(archive)
        root = stage/'extracted'
        textures,geometry,deliveries = verify(archive,root,args.verify_mesh_dir.resolve(),
            args.verify_packaged_dir.resolve() if args.verify_packaged_dir else None,args.gltfpack)
        report = {'archive':out.name,**fingerprint(archive.read_bytes()),'source_paths':len(index),
                  'verified_external_original_assets':0,'verified_geometry':geometry,
                  'verified_deliveries':deliveries,'regenerated_textures':textures}
        receipt = stage/'receipt.json'
        receipt.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        archive.replace(out)
        receipt.replace(out.with_suffix('.verification.json'))
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    main()
