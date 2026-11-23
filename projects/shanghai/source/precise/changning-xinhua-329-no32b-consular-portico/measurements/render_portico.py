"""Render original-geometry views from the measured camera pair."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
from PIL import Image,ImageDraw

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
RASTER=runpy.run_path(str(PROJECT/'source/precise/changning-st-johns-gezhi-science-hall/measurements/render_science_views.py'))['raster']

def render(mesh,output):
    output.mkdir(parents=True,exist_ok=True)
    poses=json.loads((HERE/'portico-camera-pair.json').read_bytes())['stations']
    records={}
    for name,crop,width in [('portrait',(0,0,1280,1919),442),('wide',(129,135,386,350),442)]:
        target=output/(name+'-model.jpg')
        RASTER(mesh,poses[name],crop,width).save(target,quality=93)
        records[name]=dict(crop=crop,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    (output/'rendered-views.json').write_text(json.dumps(dict(model_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),views=records),indent=2)+'\n')
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path)
    args=cli.parse_args();render(args.mesh,args.output)
