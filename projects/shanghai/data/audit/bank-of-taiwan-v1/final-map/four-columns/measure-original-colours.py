"""Count real 21115 sign-background pixels over the four column masks; text and borders are omitted."""
from pathlib import Path
from PIL import Image,ImageDraw
from scipy.ndimage import label,find_objects
import numpy as np,json,hashlib,sys
p=Path(__file__).resolve().parent;s=Path(sys.argv[1]).resolve();r=json.loads((p/'columns.json').read_bytes());cal=json.loads((s/'baseline-calibration.json').read_bytes())
for key,v in cal.items():
    png=p.parent/'original153'/('map-'+key+'.png')
    image=Image.open(png).convert('RGB');rgb=np.asarray(image,dtype='i')
    green=np.all(np.abs(rgb-[30,67,69])<9,axis=2)
    labels,n=label(green);bodies=np.zeros_like(green);cards=[]
    for i,box in enumerate(find_objects(labels),1):
        if not box:continue
        y,x=box;mask=labels[box]==i
        if y.start<180 or not(18<y.stop-y.start<=64 and 37<x.stop-x.start<=221 and mask.sum()>500):continue
        bodies[box]|=mask;cards.append([x.start,y.start,x.stop,y.stop])
    assert len(cards)==(3 if key=='mobile' else 8)
    xy=json.loads((s/('original-'+key+'-xy.json')).read_bytes());columns=[]
    for i,c in r['columns'].items():
        im=Image.new('1',image.size);draw=ImageDraw.Draw(im)
        for t in c['triangles']:draw.polygon([tuple(xy[i][j])for j in t],fill=True)
        axis=np.asarray(im,dtype=bool);columns.append({'local_x_m':c['center_x_m'],'on_screen_pixels':int(axis.sum()),'actual_name_background_pixels_over_shaft_lower_bound':int((axis&bodies).sum())})
    v.update(screenshot=png.name,screenshot_sha256=hashlib.sha256(png.read_bytes()).hexdigest(),detected_name_background_extents=cards,shafts=columns)
    print(key,[(x['on_screen_pixels'],x['actual_name_background_pixels_over_shaft_lower_bound'])for x in columns])
out={'source':'Original 21115 desktop and mobile default screenshots and recorded cameras. Transfer of the unchanged HUD insets was checked by replaying every revised live projected vertex to under 0.001 CSS pixel. The coverage counts are conservative: only the connected dark-green sign backgrounds are included (no text, borders, or antialiasing beyond the stated colour threshold).','screens':cal}
(s/'original-coverage.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
