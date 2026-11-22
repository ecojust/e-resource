"""Read the four raised bronze characters from the dated 2022 corner entrance photograph."""
import argparse
import hashlib
import json
from pathlib import Path

import contourpy
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy.ndimage import gaussian_filter
from shapely.geometry import Polygon

# Bounds in an 850×214 reproduction of the entrance lettering. Coordinates
# written to the model measurement file refer to the full upright photograph.
DETAIL=(206,208,345,243)
BOXES={'中':(88,35,217,201),'央':(259,40,390,171),'商':(450,39,591,181),'場':(613,32,751,182)}
SOURCE='https://commons.wikimedia.org/wiki/File:355_Middle_Sichuan_Road_Shanghai-20220828.jpg'


def threshold(values):
    bins=np.arange(-.5,64.5,1.)
    hist=np.histogram(np.clip(values,0,63),bins=bins)[0].astype(float)
    prob=hist/hist.sum();mass=np.cumsum(prob);moment=np.cumsum(prob*np.arange(len(prob)))
    score=(moment[-1]*mass-moment)**2/np.maximum(1e-12,mass*(1-mass))
    return float(np.argmax(score[:50])+.5)


def outlines(signal,cut):
    field=gaussian_filter(signal,1.10)
    field[0]=field[-1]=0;field[:,0]=field[:,-1]=0
    rings=[]
    for pts in contourpy.contour_generator(z=field).lines(cut):
        if np.linalg.norm(pts[0]-pts[-1])>1e-5:continue
        region=Polygon(pts)
        if region.is_valid and region.area>=9:rings.append(region)
    shape=Polygon()
    for p in sorted(rings,key=lambda p:-p.area):shape=shape.symmetric_difference(p)
    polys=shape.geoms if shape.geom_type=='MultiPolygon' else [shape]
    return sorted((p.simplify(.85,preserve_topology=True)for p in polys if p.area>=18),key=lambda p:-p.area)


def extract(im):
    ratio=im.width/690
    box=np.array(np.array(DETAIL)*ratio,dtype=int)
    sample=im.crop(tuple(box));scale=np.array(sample.size)/[850,214]
    overlay=sample.copy();line=ImageDraw.Draw(overlay);relief=Image.new('RGB',sample.size,'#55534e');view=ImageDraw.Draw(relief)
    records=[]
    for letter,b in BOXES.items():
        x0,y0,x1,y1=np.rint(np.asarray(b)*np.tile(scale,2)).astype(int)
        rgb=np.asarray(sample.crop((x0,y0,x1,y1)),float)
        # On this photograph the cast bronze has a warm red-blue separation,
        # including in shade. The weathered stone and cast shadows are neutral.
        red=rgb[:,:,0]
        # Neutral stone cast into the narrow counters acquires a brown tint
        # from nearby bronze. Its lower red-channel luminance separates it
        # from the letter face, most visibly within the final two characters.
        weight,reference={'中':(0.,120.),'央':(.9,131.),'商':(1.15,134.),'場':(.9,131.)}[letter]
        score=red-rgb[:,:,2]-weight*np.maximum(0.,reference-red)
        cut=threshold(score)
        geom=outlines(score,cut)
        origin=np.array([x0,y0]);absolute=box[:2]+origin
        # Two narrow returns take on the bronze hue in deep shade. Their
        # outlines are identified independently from the local luminance step.
        datum=Path(__file__).with_name('2022-cast-counter-edges.json')
        corrections=json.loads(datum.read_bytes())['regions']
        for hole in corrections:
            if hole['character']!=letter:continue
            cutout=Polygon(np.asarray(hole['polygon'])-absolute)
            rebuilt=[]
            for part in geom:
                changed=part.difference(cutout)
                members=changed.geoms if changed.geom_type=='MultiPolygon' else [changed]
                rebuilt.extend(p for p in members if not p.is_empty and p.area>18.)
            geom=rebuilt
        def ring(coords):
            return np.round(np.array(coords)[:-1]+absolute,2).tolist()
        groups=[]
        for p in geom:
            cont=[p.exterior,*p.interiors]
            groups.append({'shell':ring(cont[0].coords),'holes':[ring(h.coords) for h in cont[1:]],'source_area_px2':round(p.area,2)})
            for i,c in enumerate(cont):
                loc=[tuple(v)for v in np.asarray(c.coords)+origin]
                line.line(loc,fill='#6af3c4',width=2)
                view.polygon(loc,fill='#b69a70'if not i else'#55534e')
        records.append(dict(character=letter,area_box_upright=(np.array([x0,y0,x1,y1])+np.tile(box[:2],2)).tolist(),bronze_score_threshold=cut,shadow_weight=weight,shadow_red_reference=reference,components=groups))
    s=Image.new('RGB',(sample.width,sample.height*2));s.paste(overlay);s.paste(relief,(0,sample.height))
    return records,s


if __name__=='__main__':
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument('original',type=Path);arg.add_argument('output',type=Path);arg.add_argument('--sheet',type=Path)
    a=arg.parse_args()
    with Image.open(a.original)as img:
        im=ImageOps.exif_transpose(img);components,s=extract(im)
    if a.sheet:s.thumbnail((735,500));s.save(a.sheet,quality=93)
    report={'source':SOURCE,'photographer':'Shwangtianyuan','date':'2022-08-28','license':'CC BY-SA 4.0','photo_sha256':hashlib.sha256(a.original.read_bytes()).hexdigest(),'upright_size':list(im.size),'coordinates':'x right and y down on the upright original. Closed outlines bound the front face of individual pieces of the raised script, including negative counters. Approximate depth and the material response are inferred.','transcription':'中央商場','letters':components}
    a.output.write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
    print([(r['character'],r['bronze_score_threshold'],[(p['source_area_px2'],len(p['holes']))for p in r['components']]) for r in components])
