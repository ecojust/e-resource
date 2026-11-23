"""Package the editable construction source and its two shared geometry helpers."""
import argparse
import hashlib
import json
import os
import site
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ID = 'changning-xinhua-231-rong-garden-roof'
BUILDERS = ('source/precise/hongkou-tanggu-road-apartment-dated-crown/source/crown_builder.py',
            'source/precise/hongkou-general-post-office/source/common/photo_architecture.py')
INPUTS = ('README.md', 'source/build_model.py', 'source/cameras.json', 'source/finishes.py',
          'source/garden-roof-tiles.png', 'measurements/check_actual_meshes.py',
          'measurements/roof_views.py', 'measurements/published-sources.json',
          'measurements/roof-orientation.json')
GUIDE = """# 新华路231号住宅花园侧模型源码

在解压目录运行 `python rebuild.py output`，即可生成近远两个 GLB、构件表、照片配准及首击结果、彩瓦纹理对照图。生成时使用包内的共用几何工具。依赖版本列于 requirements.txt。从 source/precise/changning-xinhua-231-rong-garden-roof/source/ 进入本栋模型的部件、材质和机位定义，照片来源和量取值在同栋的 measurements/。相机对齐沿用宽550像素的公开图，外部摄影与航片由各自来源提供。
"""
RUN = """from pathlib import Path
import argparse
import os
import subprocess
import sys

root = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('output', type=Path)
out = p.parse_args().output.resolve()
out.mkdir(parents=True, exist_ok=True)
building = root/'source/precise/changning-xinhua-231-rong-garden-roof'
env = dict(os.environ, OPENBLAS_NUM_THREADS='1',
           OMP_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
env.pop('E_RESOURCE_SHANGHAI', None)
def run(script, *args):
    subprocess.run([sys.executable, '-B', building/script, *args], check=True, env=env)
run('source/build_model.py', '--output', out/'full-source.glb')
run('source/build_model.py', '--lod', '--output', out/'lod-source.glb')
run('measurements/check_actual_meshes.py', out, out/'mesh-and-photo-check.json')
run('measurements/roof_views.py', out)
"""

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project', type=Path, required=True)
    ap.add_argument('--building', type=Path, required=True)
    ap.add_argument('--verify-mesh-dir', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--hide-workspace', type=Path, help='Use bubblewrap to mask this directory and disable networking during independent reproduction')
    args = ap.parse_args()
    prefix = Path('source/precise')/ID
    entries = {str(prefix/item):(args.building/item).read_bytes() for item in INPUTS}
    for item in BUILDERS:
        entries[item] = (args.project/item).read_bytes()
    entries.update({'README.md':GUIDE.encode(), 'rebuild.py':RUN.encode(),
                    'requirements.txt':b'numpy==2.3.5\nShapely==2.2.0\nPillow==13.0.0\n',
                    'LICENSE':(args.project/'LICENSE').read_bytes()})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.out, 'w') as z:
        for name, data in sorted(entries.items()):
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    with tempfile.TemporaryDirectory(dir=args.out.parent) as scratch:
        unpack = Path(scratch)
        with ZipFile(args.out) as z:
            assert z.testzip() is None
            z.extractall(unpack)
        unpack=unpack.resolve()
        command=[sys.executable, '-B', unpack/'rebuild.py', unpack/'generated']
        if args.hide_workspace:
          command=['bwrap','--ro-bind','/','/','--bind',str(unpack),str(unpack),'--tmpfs',str(args.hide_workspace.resolve()),
                   '--unshare-net','--clearenv','--setenv','PATH',os.defpath,'--setenv','PYTHONUSERBASE',site.getuserbase(),'--chdir',str(unpack),'--',*command]
        subprocess.run(command, check=True)
        checks = []
        for name in ('full-source.glb', 'lod-source.glb', 'full-source.geometry.json',
                     'lod-source.geometry.json', 'mesh-and-photo-check.json', 'model-comparison.jpg'):
            p = unpack/'generated'/name
            assert p.read_bytes() == (args.verify_mesh_dir/name).read_bytes(), name
            checks.append(dict(file=name, sha256=sha(p), bytes=p.stat().st_size))
    report = dict(archive=args.out.name, bytes=args.out.stat().st_size, sha256=sha(args.out),
                  archive_members=sorted(entries), independent_rebuild=checks,
                  workspace_masked=bool(args.hide_workspace),network_disabled=bool(args.hide_workspace))
    args.out.with_suffix('.verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(sha(args.out))

if __name__ == '__main__':
    main()
