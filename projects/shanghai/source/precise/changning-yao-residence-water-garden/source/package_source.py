"""Bundle the Yao Residence water garden source and verify the textures, geometry and encoded deliveries from that archive."""
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

README = """# 淮阴路姚氏住宅水庭转角长窗与水平格栅

本模型据2017年和2019年报道刊出的两张庭院照片建成。两站共同可辨的长窗、五层格栅、薄檐转角及临窗水池各有独立几何。报道年份用于标记视角。程序表面和网格为本项目原创，资料署名和使用范围见本栋来源说明。

解压后，从本目录运行下列命令。建模使用 Python 3、NumPy、Shapely 和 Pillow；重新拟合机位另需 SciPy，GLB 编码需 Node.js 和 gltfpack，原生与交换格式需 Blender 4.3 或较新版本。

```sh
src=projects/shanghai/source/precise/changning-yao-residence-water-garden/source
mkdir -p rebuilt/whole rebuilt/packaged rebuilt/native
python "$src/build_model.py" --output rebuilt/whole/full-source.glb
python "$src/build_model.py" --output rebuilt/whole/lod-source.glb --lod
python "$src/package_model.py" rebuilt/whole rebuilt/packaged --gltfpack gltfpack
python "$src/package_editable.py" prepare rebuilt/packaged rebuilt/native
python "$src/package_editable.py" run rebuilt/packaged rebuilt/native
python "$src/package_exchange.py" rebuilt/packaged rebuilt/exchange
```

source-files.json列出源件字节数及SHA-256。FBX为带材质的建筑网格，OBJ包包含几何、材质库和程序纹理。STL仅承载几何形状，坐标单位为米。GLB、Blender、FBX及OBJ附带两组程序色纹和法线。
"""


def fingerprint(data):
    return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def source_files():
    paths = {PROJECT / name for name in (*shared['SHARED'], ARCHIVE_HELPER, 'LICENSE',
        
        'source/precise/xuhui-huaihai-1230-rear-courtyard-entrance/measurements/register_court.py',
        'source/precise/xuhui-huaihai-1230-rear-courtyard-entrance/measurements/render_registered_entrance.py',
        'source/precise/xuhui-huaihai-1230-rear-courtyard-entrance/source/make_editable_scene.py',
        'source/precise/xuhui-huaihai-1230-rear-courtyard-entrance/source/prepare_editable_groups.py',
        'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py',
        'source/precise/changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py',
        'source/precise/huangpu-yuanmingyuan-apartments-street-front/measurements/photo_glb_raster.py',
        'source/precise/huangpu-yuanmingyuan-apartments-street-front/measurements/photo_glb_raster.c',
        'source/precise/huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c',
        'source/precise/xuhui-yuqing-80-twin-winter-gardens/measurements/garden_daylight.c',
        'source/precise/xuhui-shaanxi-202-former-yihe-hospital/measurements/sky_sampling.py',
        'source/precise/xuhui-jianguo-336-lane-one-villa/measurements/render_registered_court.py',
        'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact/glb_triangles.py',
        'source/precise/xuhui-jianguo-336-lane-one-villa/measurements/register_court.py',
        'source/precise/xuhui-jianguo-336-lane-one-villa/measurements/court_normal_map.h')}
    for folder, types in ((HERE, {'.py','.png','.json','.js','.c'}),
                          (HERE.parent/'measurements', {'.py','.json','.md','.geojson','.csv','.tsv','.c','.h'})):
        paths.update(p for p in folder.iterdir() if p.is_file() and p.suffix in types)
    measurements = HERE.parent/'measurements'
    paths.update(HERE.parent.glob('*.md'))
    paths.update(p for p in (HERE.parent/'measurements').glob('*.txt'))
    paths.update(p for p in (HERE.parent/'measurements').glob('*.cpp'))
    paths.add(PROJECT/'yao-residence-water-garden.html')
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
    pngs={p.name for p in source.glob('*.png')}
    if pngs:
        initial={name:fingerprint((source/name).read_bytes()) for name in pngs}
        for name in pngs:
            (source/name).unlink()
        # Load the same local module search paths as the normal builder.
        subprocess.run([sys.executable, '-c', 'import garden_finishes; garden_finishes.generate()'],
                       cwd=source, env=env, check=True)
        for name in sorted(pngs):
            data=(source/name).read_bytes()
            if fingerprint(data)!=initial[name]:raise ValueError('Regenerated texture differs: '+name)
            textures[name]=initial[name]['sha256']
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
    with tempfile.TemporaryDirectory(dir=out.parent,prefix='yao-water-garden-source-') as staging:
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
