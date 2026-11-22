"""Compare independent crown profiles and short course joints in three dated photographs.
All coordinates refer to upright source pixels. Supply the three originals for the
luminance profiles (reference images are not written into the public outputs).
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps
from scipy.ndimage import map_coordinates,gaussian_filter1d
from scipy.signal import find_peaks

# Crop-to-original transforms for the reviewed full-resolution crown. Labels
# rising from the west/north corner are sorted in image order left to right.
PHOTOS={
'2014':{'basename':'ccf21','crop':[1770,65,2980,1120],'review':[562,490],'strip_origin':[2114,291],
 'silhouette':{'central_pad_edges':[(258,32),(296,26)],'inner_shoulders':[(247,54),(310,46)],'broad_shoulders':[(211,79),(348,64)],'outside_pier_caps':[(176,103),(351,80)],'outer_wing_roof':[(145,151),(423,130)]},
 'strips':[(93,171,122,104),(312,400,86,84)],'notes':'Black 21 shop sign below the short central courses. Long blue attachments partly mask three pier heads and the outermost west pier. Pale rooftop lantern at upper left belongs behind the corner crown.'},
'2018':{'basename':'cc2015','crop':[1180,345,2600,1500],'review':[602,490],'strip_origin':[1533,599],
 'silhouette':{'central_pad_edges':[(241,56),(272,48)],'inner_shoulders':[(231,73),(288,75)],'broad_shoulders':[(209,103),(325,69)],'outside_pier_caps':[(175,152),(329,85)],'outer_wing_roof':[(141,191),(404,125)]},
 'strips':[(119,193,220,185),(321,418,133,110)],'notes':'Left rise overlaps the setback tower, so its outline is a brick edge against another building surface rather than a sky contour. No inferred crown height comes from the setback roof.'},
'2024':{'basename':'cc2024a','crop':[925,230,2240,1370],'review':[565,490],'strip_origin':[1239,525],
 'silhouette':{'central_pad_edges':[(292,49),(332,49)],'inner_shoulders':[(278,70),(344,71)],'broad_shoulders':[(238,93),(384,94)],'outside_pier_caps':[(204,113),(395,107)],'outer_wing_roof':[(161,164),(457,165)]},
 'strips':[(230,330,93,83),(485,589,81,93)],'notes':'White flower and illuminated shop letters below the short stone strips. The image-left and image-right shoulders carry individual higher returns, separated from the central courses by the heavy piers.'}}
def process(folder):
 out={}
 for yr,v in PHOTOS.items():
  path=folder/(v['basename']+'.jpg');im=np.array(ImageOps.exif_transpose(Image.open(path)).convert('L'),float)
  crop=np.array(v['crop']);scale=(crop[2:]-crop[:2])/v['review'];traces={}
  for key,points in v['silhouette'].items():traces[key]=np.round(crop[:2]+np.array(points)*scale,1).tolist()
  ox,oy=v['strip_origin'];bands=[]
  for a,b,za,zb in v['strips']:
   x=np.arange(a,b);y=za+(zb-za)*(x-a)/(b-a)
   slice=np.mean([map_coordinates(im,[oy+y+o,ox+x],order=1)for o in [0,1,2]],axis=0)
   lows=find_peaks(-gaussian_filter1d(slice,1),distance=8,prominence=3)[0]
   bands.append({'profile_from_to_px':[[a+ox,za+oy],[b+ox,zb+oy]],'dark_vertical_divisions_original_px':[[int(ox+x[i]),round(oy+y[i],1)] for i in lows], 'count_in_sample':len(lows)})
  out[yr]={'original_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'silhouette_original_px':traces,'central_short_bands':bands,'notes':v['notes']}
 return {'units':'original upright image pixels','mark_precision':'Approx. 5–12 original px on clear steps. Obscured or low-contrast older edges are less precise (up to 25 px).','photos':out,'interpretation':'In 2024 each central short band has five visible vertical separators, making six intervals including two edge intervals. The 2018 samples also retain five on each band. In 2014, five are optically recovered at image left and four at image right; the dark right endpoint is not interpolated. Larger flanking piers split these central strips from a distinctly higher short course on each shoulder. Farther along the wings, the continuous roof edge carries additional smaller divisions, not counted as central ornaments. The central raised pad and the immediately lower narrow shoulders, broad shoulders, flanking pier tops and lower outer roof are homologous. Modern lettering, the 2014 blue crest attachments and the separate rooftop lantern are excluded.'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('photos',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args();args.output.write_text(json.dumps(process(args.photos),ensure_ascii=False,indent=2)+'\n')
