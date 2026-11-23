"""Archive the editable architectural source and verify both exported GLBs from a clean extraction."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

HERE = Path(__file__).resolve().parent
PROJECT = next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
ID = HERE.parent.name
SHARED = (
    'tools/package_architectural_model.py', 'tools/verify_editable_model.py',
    'source/precise/hongkou-general-post-office/source/common/photo_architecture.py',
    'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs',
    'source/precise/hongkou-general-post-office/source/package_assets.py',
    'source/precise/hongkou-tanggu-road-apartment-dated-crown/source/crown_builder.py',
    'source/precise/jingan-country-hospital/source/build_garden.py',
    'source/precise/jingan-country-hospital/source/check_meshes.py',
    'source/precise/jingan-country-hospital/source/make_native.py',
    'source/precise/jingan-country-hospital/source/portico.py',
    'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py',
    'source/precise/xuhui-huashan-823-827-stair-loggia/source/build_blender_source.py',
    'source/precise/xuhui-huashan-823-827-stair-loggia/source/package_editable.py',
    'source/precise/xuhui-yanqing-159-garden-residence/source/build_blender_source.py',
    'source/precise/xuhui-yanqing-159-garden-residence/source/package_model.py',
    'source/precise/xuhui-yanqing-159-garden-residence/source/garden_finishes.py',
    'source/precise/xuhui-baisaizhong-apartments-fuxing-road-corner/source/build_blender_source.py',
    'source/precise/hongkou-gongyi-fang-975-987-sichuan-road/source/asset_rights.py',
    'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact/glb_triangles.py',
    'data/audit/postal-office-v1/independent-glb-review-helpers.py', 'vendor/meshopt_decoder.module.js',
)
README = '''# 大福里3号院门与露台

原照由Livelikerw于2016年2月6日拍摄。门牌上可读“3”和“延庆路二十九弄”，旁边的4号牌区分了下一座院门。大号数字3的临摹轮廓按CC BY-SA 4.0提供。原片与许可见https://commons.wikimedia.org/wiki/File:Dafu_Li_Shanghai.JPG 。本包保存带SHA-256的脚本、程序纹理、摄像机、测量记录及所需的共用模块，路径与制作仓库一致。

从解压目录运行以下命令。两档建模使用Python 3、NumPy、Shapely 2.1和Pillow。压缩、逐面核对和可编辑工程另需Node.js、gltfpack及Blender。下列各通用脚本的帮助可通过 --help 查看。

```sh
src=projects/shanghai/source/precise/xuhui-dafuli-yanqing-29-no3-court/source
mkdir -p rebuilt/whole rebuilt/packaged rebuilt/native
python "$src/build_model.py" --output rebuilt/whole/full-source.glb
python "$src/build_model.py" --output rebuilt/whole/lod-source.glb --lod
python "$src/package_model.py" rebuilt/whole rebuilt/packaged --gltfpack gltfpack
python "$src/package_editable.py" prepare rebuilt/packaged rebuilt/native
python "$src/package_editable.py" run rebuilt/packaged rebuilt/native
```
'''
def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def add(z, path, data):
    entry=ZipInfo(path,(1980,1,1,0,0,0))
    entry.compress_type=ZIP_DEFLATED
    entry.external_attr=0o100644<<16
    z.writestr(entry,data)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--verify-mesh-dir',type=Path,required=True)
    args=parser.parse_args(); args.output.parent.mkdir(parents=True,exist_ok=True)
    files={PROJECT/s for s in SHARED}
    files.update(p for p in HERE.iterdir() if p.is_file() and p.suffix in {'.py','.png','.json'})
    files.update(p for p in (HERE.parent/'measurements').glob('*') if p.is_file() and p.suffix in {'.py','.json','.md','.geojson'})
    source_names={}
    temp=args.output.with_suffix('.partial')
    with ZipFile(temp,'w') as z:
        for p in sorted(files):
            name='projects/shanghai/'+p.relative_to(PROJECT).as_posix()
            data=p.read_bytes()
            add(z,name,data);source_names[name]=dict(bytes=len(data),sha256=digest(data))
        add(z,'README.md',README.encode())
        add(z,'source-files.json',(json.dumps(source_names,indent=2,ensure_ascii=False)+'\n').encode())
    with tempfile.TemporaryDirectory(dir=args.output.parent,prefix='verified-source-')as folder:
        root=Path(folder)
        with ZipFile(temp)as z:
            assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
            z.extractall(root)
        source=(root/'projects/shanghai'/HERE.relative_to(PROJECT)/'build_model.py')
        result={}
        for role in ('full','lod'):
            mesh=root/(role+'-source.glb')
            command=[sys.executable,source,'--output',mesh]
            if role=='lod':command.append('--lod')
            subprocess.run(command,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'},check=True)
            expected=(args.verify_mesh_dir/mesh.name).read_bytes()
            actual=mesh.read_bytes()
            if actual!=expected:raise ValueError(f'Clean source rebuild changed {role} bytes')
            result[role]=dict(bytes=len(actual),sha256=digest(actual))
    temp.replace(args.output)
    report=dict(archive=args.output.name,bytes=args.output.stat().st_size,sha256=digest(args.output.read_bytes()),
                source_paths=len(source_names),verified_external_original_assets=0,verified_geometry=result)
    args.output.with_suffix('.verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
