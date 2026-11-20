"""Set the delivery camera, denoise the reopened native render and bind the final bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def finish():
    p=argparse.ArgumentParser(add_help=False)
    p.add_argument("--out",type=Path,required=True);p.add_argument("--audit",type=Path,required=True)
    p.add_argument("--blender",default="blender");p.add_argument("--oidn",default="oidnDenoise")
    a,_=p.parse_known_args()
    manifest_path=a.out/"manifest.json";report_path=a.audit/"geometry-native.json"
    meta=json.loads(manifest_path.read_bytes());report=json.loads(report_path.read_bytes())
    blend=(a.out/meta["assets"]["native"]["file"]).resolve();raw=(a.out/meta["assets"]["raw"]["file"]).resolve()
    preview=(a.audit/report["preview"]).resolve()
    blender=[a.blender,"-b","--threads","2","--python-exit-code","1","--python"]
    with tempfile.TemporaryDirectory() as work:
        work=Path(work);frame=work/preview.name
        subprocess.run([*blender,HERE/"fit_camera.py","--",blend,frame],check=True)
        verify=work/"verified.json"
        subprocess.run([*blender,PROJECT/"tools/verify_editable_model.py","--",blend,raw,verify],check=True)
        subprocess.run(["magick",frame,"-colorspace","sRGB","-endian","LSB",work/"input.pfm"],check=True)
        subprocess.run([a.oidn,"-d","cpu","--threads","2","--ldr",work/"input.pfm","--srgb","-o",work/"output.pfm"],check=True)
        subprocess.run(["magick",work/"output.pfm","-set","colorspace","sRGB","-depth","8",preview],check=True)
        report["native_reopened_and_compared"]=json.loads(verify.read_bytes())
        report["render_unfiltered_sha256"]=digest(frame)
    meta["assets"]["native"].update(bytes=blend.stat().st_size,sha256=digest(blend))
    report["sha256"]["native"]=digest(blend)
    report["preview_sha256"]=digest(preview)
    report["render"]="Reopened native model, stepped river frontage, archive entrance and raised crown. Cycles, 48 samples. OIDN RT sRGB."
    for path in HERE.glob("*.py"):report["input_sha256"][str(path.relative_to(PROJECT))]=digest(path)
    for path,data in [(manifest_path,meta),(report_path,report)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")

if __name__=="__main__":
    finish()
