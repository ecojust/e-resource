"""Extract tabulated framing and pane measurements from Rosholt's circa-1938 print."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates,gaussian_filter1d

def primary_uv(x,y):
    return 581.3+(y-422)*.052+x,422.+.0215*x+(y-422)
def measure(primary,secondary):
    im=np.array(Image.open(primary).convert('L')).astype(float)
    if im.shape!=(706,1020):raise ValueError('The original 1,020 by 706 archive image is required.')
    def get(x,y):
        u,v=primary_uv(x,y);return map_coordinates(im,[v,u],order=1,mode='nearest')
    vline=[]
    for center in [15.6,30.2,46.0]:
        cuts=[]
        for y0,y1 in [(437.75,445.75),(457.,465.),(475.,481.)]:
            xs=np.arange(center-2.4,center+2.401,.125);x,y=np.meshgrid(xs,np.arange(y0,y1,.25));prof=np.median(get(x,y),axis=0);i=int(np.argmin(gaussian_filter1d(prof,1.5)))
            cuts.append(dict(y_range=[y0,y1],x_darkest=round(float(xs[i]),3),grey=round(float(prof[i]),2)))
        # The lower row is poorly exposed. It remains a check on the stronger,
        # separated upper rows rather than steering the frame sideways.
        vline.append({'centre':round(float(np.mean([v['x_darkest']for v in cuts[:2]])),3),'profiles':cuts})
    hline=[]
    for row in [430.,451.,472.35]:
        cuts=[]
        for x0,x1 in [(6.,12.),(21.,26.),(35.,41.),(51.,56.)]:
            ys=np.arange(row-2.2,row+2.21,.125);x,y=np.meshgrid(np.arange(x0,x1,.25),ys);prof=np.median(get(x,y),axis=1);i=int(np.argmin(gaussian_filter1d(prof,1.3)))
            cuts.append(dict(x_range=[x0,x1],y_darkest=round(float(ys[i]),3),grey=round(float(prof[i]),2)))
        hline.append(dict(centre=round(float(np.median([r['y_darkest']for r in cuts])),3),profiles=cuts))
    pane=[];edges=[3.6]+[s['centre']for s in vline]+[60.8];levels=[hline[i]['centre']for i in range(3)]+[484.4]
    for i,(l,r) in enumerate(zip(edges,edges[1:])):
        c=[]
        for j,(t,b)in enumerate(zip(levels,levels[1:])):
            x,y=np.meshgrid(np.linspace(l+(r-l)*.24,r-(r-l)*.24,7),np.linspace(t+(b-t)*.29,b-(b-t)*.23,9))
            c.append(round(float(np.median(get(x,y))),2))
        pane.append(c)
    result={'source':{'catalogue':'Historical Photographs of China, University of Bristol, Ro-s018','photographer':'Malcolm Rosholt','date':'circa 1938, catalogue estimate','url':'https://www.hpcbristol.net/visual/Ro-s018','sha256':hashlib.sha256(primary.read_bytes()).hexdigest(),'native_px':[1020,706],'rights':'CC BY-NC-ND 4.0, numerical observations only; the archive image is not reproduced.'},
        'crosscheck':{'source_url':'https://wiki.histoire-chine.fr/index.php?title=Il_%C3%A9tait_une_fois..._l%27Institut_Pasteur_de_Shanghai','image_reference':'https://wiki.histoire-chine.fr/images/5/5f/Le_Laboratoire_Municipal_avant_de_devenir_Institut_Pasteur_entre_1934_et_1938.jpg','caption':'Le Laboratoire Municipal avant de devenir Institut Pasteur entre 1934 et 1938','sha256':hashlib.sha256(secondary.read_bytes()).hexdigest(),'native_px':list(Image.open(secondary).size),'observed_native_quad_px':[[500,264],[529,267],[529,328],[500,328]],'scope':'Independent interwar oblique photograph confirms the unusual dark glazed bay in the centre of an otherwise pale-framed lower row. Some panes catch light at a different angle; the lower boundary meets vegetation and the street fence.'},
        'registration':'x in native pixels from the approximate west edge of the dark opening, y original row. u=581.3+0.052*(y-422)+x, v=y+0.0215*x.',
        'primary_opening_quad_px':[[581.3,422],[649.9,423.5],[653.6,501.5],[585.4,500]],
        'frame_plane_y_m':.25,'tested_x_mullions':vline,'tested_y_transoms':hline,'lower_dark_crosspiece_y':484.4,'pane_column_row_middle_grey_0_to_255':pane,
        'visible_limit':'The opaque lower field is traced to the hedge line at row 499. Its lower termination, construction material, colour, state behind the glass and connection to the ground are unrecorded.'}
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('original','second','output'):p.add_argument(k,type=Path)
    a=p.parse_args();d=measure(a.original,a.second)
    a.output.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');print([q['centre']for q in d['tested_x_mullions']],[q['centre']for q in d['tested_y_transoms']],d['pane_column_row_middle_grey_0_to_255'])
