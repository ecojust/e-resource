"""Rasterise the four decoded granite shafts at each recorded site's actual camera."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
import hashlib,json,sys
root=Path(__file__).parent
out=Path(sys.argv[1]);read=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
report=read(out/'browser.json');columns=read(root/'columns.json')['columns'];results={}
for name,view in report['views'].items():
    xyfile=out/(name+'-projection.json');assert view['projection_sha256']==sha(xyfile.read_bytes())
    assert view['sha256']==sha((out/(name+'.png')).read_bytes())
    xy=read(xyfile);width,height=view['viewport'];labelmask=Image.new('1',(width,height));draw=ImageDraw.Draw(labelmask)
    for label in view['labels']:
        left=round(label['x']-label['width']/2);top=round(label['y']-label['height']/2)
        draw.rectangle((left,top,left+label['width']-1,top+label['height']-1),fill=1)
    actual=np.asarray(labelmask).astype(bool);per=[]
    for k,item in columns.items():
        mask=Image.new('1',(width,height));dra=ImageDraw.Draw(mask);points=np.asarray(xy[k])
        for triangle in item['triangles']:dra.polygon([tuple(points[i])for i in triangle],fill=1)
        pixels=np.asarray(mask).astype(bool);intersection=int(np.count_nonzero(pixels&actual))
        bounds=[points[:,0].min(),points[:,1].min(),points[:,0].max(),points[:,1].max()]
        left=min(0,int(np.floor(bounds[0]))-2);top=min(0,int(np.floor(bounds[1]))-2)
        right=max(width,int(np.ceil(bounds[2]))+3);bottom=max(height,int(np.ceil(bounds[3]))+3)
        padded=Image.new('1',(right-left,bottom-top));pd=ImageDraw.Draw(padded)
        for tri in item['triangles']:pd.polygon([tuple(points[j]-[left,top])for j in tri],fill=1)
        total=int(np.asarray(padded).sum())
        card=view['hud']['#location-card'];x0=max(0,int(np.ceil(card['left'])));x1=min(width,int(np.ceil(card['right'])))
        y0=max(0,int(np.ceil(card['top'])));y1=min(height,int(np.ceil(card['bottom'])))
        card_pixels=int(pixels[y0:y1,x0:x1].sum())
        per.append(dict(projected_pixels_before_viewport_crop=total,offscreen_pixels=total-int(pixels.sum()),
                        inside_location_card_rect_pixels=card_pixels,local_x=item['center_x_m'],triangles=item['triangle_count'],on_screen_pixels=int(pixels.sum()),under_rendered_sign_pixels=intersection,pixel_extents=bounds,fully_in_viewport=bool(min(bounds[:2])>=0 and bounds[2]<width and bounds[3]<height)))
    hits=[h for p in view['labels']for h in p['hits']];bad=[dict(sign=p['id'],hit=h)for p in view['labels']for h in p['hits']if h['picked']!=p['id'] or 'maplibregl-canvas'not in h['top']]
    results[name]=dict(png_sha256=view['sha256'],viewport=view['viewport'],camera=view['camera'],signs=len(view['labels']),column_shafts=per,hit_points=len(hits),incorrect_hit_points=bad)
doc={'actual_site':report['base'],'catalog_sha256':report['catalog_sha256'],'method':'Four individual decoded near-model granite shafts (984 triangles each, z 1.52–13.42 m), projected with the recorded active MapLibre transform, compared at CSS resolution to the actually rendered building labels. Building occlusion is also inspected in the grounded screenshots.','views':results}
(out/'shaft-coverage.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
for n,r in results.items():print(n,r['signs'],[(a['on_screen_pixels'],a['under_rendered_sign_pixels'])for a in r['column_shafts']],len(r['incorrect_hit_points']))
