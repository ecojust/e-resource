"""Render the plate and raised lettering from the delivered surfaces with a front-facing orthographic camera."""
from argparse import ArgumentParser
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
from photo_ray_mesh import ProjectedMesh,material_appearance

def check(model,image_path,report_path):
    g=json.loads(model.with_suffix('.geometry.json').read_bytes())
    scene=ProjectedMesh(model,g)
    features=[r['label'] for r in scene.parts]
    plate='west pier/green lane number plate'
    tri=scene.tri[scene.labels==features.index(plate)]
    low=tri.min(axis=(0,1));high=tri.max(axis=(0,1));margin=.025
    scale=900/(high[0]-low[0]+2*margin)
    height=round((high[2]-low[2]+2*margin)*scale)
    frame=Image.new('RGB',(900,height),(135,130,124));draw=ImageDraw.Draw(frame)
    appearances=material_appearance(model)['materials'];records={}
    ids=np.flatnonzero(np.array([name==plate or name.startswith('address plate/') for name in features])[scene.labels])
    for idx in ids[np.argsort(scene.tri[ids,:,1].mean(axis=1))[::-1]]:
        part=scene.parts[scene.labels[idx]]
        vertices=scene.tri[idx]
        xy=[((v[0]-low[0]+margin)*scale,(high[2]-v[2]+margin)*scale) for v in vertices]
        linear=appearances[part['material']]['baseColorFactor'][:3]
        srgb=tuple(int(round(255*(12.92*c if c<=.0031308 else 1.055*c**(1/2.4)-.055))) for c in linear)
        draw.polygon(xy,fill=srgb)
        records[part['label']]=records.get(part['label'],0)+1
    frame.save(image_path)
    report={'model':scene.asset,'scope':'Orthographic detail of green plate and its actual ivory mesh lettering. Sorted by depth and drawn with the delivered base colour, without antialiasing or screen fonts. Native source photograph readings and street-camera displacement appear in the independent photo observations and ray reports.','output_sha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),'width_metres':float(high[0]-low[0]),'height_metres':float(high[2]-low[2]),'triangles_by_label':records,'colours':{k:appearances[k] for k in ('green enamel address plate','ivory sign lettering')}}
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('model',type=Path);parser.add_argument('image',type=Path);parser.add_argument('report',type=Path)
    a=parser.parse_args();check(a.model,a.image,a.report)
