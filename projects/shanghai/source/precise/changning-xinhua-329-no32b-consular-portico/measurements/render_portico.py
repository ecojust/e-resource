"""Render original-geometry views from the measured camera pair."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
from PIL import Image

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
RASTER=runpy.run_path(str(PROJECT/'source/precise/changning-st-johns-gezhi-science-hall/measurements/render_science_views.py'))['raster']

def render(mesh,output):
    output.mkdir(parents=True,exist_ok=True)
    poses=json.loads((HERE/'portico-camera-pair.json').read_bytes())['stations']
    records={}
    views = [('portrait','portrait',(0,0,1280,1919),442),
             ('wide','wide',(129,135,386,350),442),
             ('pier-number','portrait',(229,1370,337,1537),270),
             ('iron-fanlight','portrait',(385,650,944,996),544),
             ('heritage-plaque','portrait',(77,979,242,1128),348),
             ('courtyard-elevation','wide',(90,85,420,345),548)]
    for name, station, crop, width in views:
        target = output / (name+'-model.jpg')
        scale = width / (crop[2] - crop[0])
        height = round((crop[3] - crop[1]) * scale)
        image = Image.new('RGB',(width,height))
        # Bound z-buffer and textured face allocations even when the camera
        # crops down to the very small plaque or the lettering on the column.
        for top in range(0,height,72):
            bottom = min(height,top+72)
            band = (crop[0],crop[1]+top/scale,crop[2],crop[1]+bottom/scale)
            tile = RASTER(mesh,poses[station],band,width)
            if tile.size != (width,bottom-top):
                raise ValueError('Photo projection produced the wrong strip dimensions')
            image.paste(tile,(0,top))
        image.save(target,quality=93)
        records[name] = dict(station=station,crop=crop,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    (output/'rendered-views.json').write_text(json.dumps(dict(model_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),views=records),indent=2)+'\n')
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path)
    args=cli.parse_args();render(args.mesh,args.output)
