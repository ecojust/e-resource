"""Bundle the Fudefang garden house source and verify the textures, geometry and encoded deliveries from that archive."""
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

HERE = Path(__file__).absolute().parent
PROJECT = next(p for p in HERE.parents if (p / 'tools/package_architectural_model.py').is_file())
ID = HERE.parent.name
ARCHIVE_HELPER = 'source/precise/xuhui-yanqing-2-green-street-residence/source/package_source.py'
shared = runpy.run_path(str(PROJECT / ARCHIVE_HELPER))

README = """# 福德坊建国西路336弄1号住宅

本包重建院内住宅、前部两对圆柱、弧形下阳台、上层直廊、两翼切角窗和西侧窗墙。门阶、栏杆与窗下浮雕均保留独立几何。门内暖色玻璃灯保留独立发光材质。四个有证据的现场站位为02、03、04和05。编辑工程内的三台摄影对照相机保留03、04和05原位的透视与横滚；隔门看西墙的02站用于独立核验。点位、误差及照片较难辨认的部位见 measurements 目录。

在解压目录使用 Python 3、NumPy、Shapely 2.1 和 Pillow，运行以下命令。重算摄影相机需 SciPy。网页编码需 gltfpack 和 Node.js，编辑工程需 Blender。

```sh
src=projects/shanghai/source/precise/xuhui-jianguo-336-lane-one-villa/source
mkdir -p rebuilt/whole rebuilt/packaged rebuilt/native
python "$src/finish_surfaces.py" --output rebuilt/finishes
python "$src/roof_finish.py" --output rebuilt/roof-only
python "$src/build_model.py" --output rebuilt/whole/full-source.glb
python "$src/build_model.py" --output rebuilt/whole/lod-source.glb --lod
python "$src/package_model.py" rebuilt/whole rebuilt/packaged --gltfpack gltfpack
python "$src/package_editable.py" prepare rebuilt/packaged rebuilt/native
python "$src/package_editable.py" run rebuilt/packaged rebuilt/native
```

source-files.json 记录源码、原创纹理与测量文件，包括字节数及 SHA-256。院面照片由高参88的图集收录，各幅署名与可确认的拍摄时间见 measurements 内的记录。原摄影作品需由读者根据来源自取，包内附原创几何和程序纹理。
"""


def fingerprint(data):
    return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def source_files():
    paths = {PROJECT / name for name in (*shared['SHARED'], ARCHIVE_HELPER, 'LICENSE',
        'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py',
        'source/precise/changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py',
        'source/precise/huangpu-yuanmingyuan-apartments-street-front/measurements/photo_glb_raster.py',
        'source/precise/huangpu-yuanmingyuan-apartments-street-front/measurements/photo_glb_raster.c',
        'source/precise/huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c',
        'source/precise/xuhui-yuqing-80-twin-winter-gardens/measurements/garden_daylight.c',
        'source/precise/xuhui-shaanxi-202-former-yihe-hospital/measurements/sky_sampling.py')}
    for folder, types in ((HERE, {'.py','.png','.json','.js','.c'}),
                          (HERE.parent/'measurements', {'.py','.json','.md','.geojson','.csv','.tsv','.c','.h'})):
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
    run('finish_surfaces.py','--output',generated)
    roof_test=root/'independent-roof'
    run('roof_finish.py','--output',roof_test)
    roof_files=list(roof_test.glob('*.png'))
    if len(roof_files)!=2 or any(p.read_bytes()!=(generated/p.name).read_bytes() for p in roof_files):
        raise ValueError('Independent roof generation disagrees with integrated finish generator')
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
    with tempfile.TemporaryDirectory(dir=out.parent,prefix='fudefang-source-') as staging:
        stage = Path(staging)
        archive = stage/out.name
        index = write_archive(archive)
        root = stage/'extracted'
        textures,geometry,deliveries = verify(archive,root,args.verify_mesh_dir.absolute(),
            args.verify_packaged_dir.absolute() if args.verify_packaged_dir else None,args.gltfpack)
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
