"""Measure six long fluted stone panels above the shopfront's curved upper windows."""
import json,hashlib,argparse,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps
from scipy.ndimage import gaussian_filter,gaussian_filter1d,map_coordinates,median_filter
from scipy.signal import find_peaks

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from crown_plane import VERTICAL_VP,at_row

# Positions are native pixels rectified along the vertical vanishing direction.
# The bottom of each stone distinctly meets the deep dark reveal of the window.
COLUMNS=[(1100,1155,1186,1142),(1177,1247,1127,1084),(1275,1354,1195,1164),
         (1924,2011,1174,1205),(2038,2108,1098,1141),(2129,2181,1157,1203)]


def measure(image):
    ref=json.loads((HERE/'corner-crown-image-controls.json').read_bytes())['photo_references']['cc2024a']
    if hashlib.sha256(image.read_bytes()).hexdigest()!=ref['sha256']:raise ValueError('Unexpected original photograph')
    with Image.open(image) as im:
        a=np.asarray(ImageOps.exif_transpose(im).crop((920,810,2350,1370)).convert('RGB'),float)
    vx,vy=VERTICAL_VP
    panels=[]
    for lo,hi,low0,low1 in COLUMNS:
        u=np.arange(lo,hi+1.)
        v=np.arange(875.,1281.)
        xx=vx+(u[None,:]-vx)*(v[:,None]-vy)/(930.-vy)
        colours=np.stack([map_coordinates(a[:,:,k],[np.broadcast_to(v[:,None]-810,xx.shape),xx-920],order=1)for k in range(3)],axis=2)
        lum=gaussian_filter(colours@np.array([.2126,.7152,.0722]),(1.25,.7))
        diff=np.gradient(lum,axis=0)
        estimate=np.linspace(low0,low1,len(u))
        cost=np.where(abs(v[:,None]-estimate)<6.7,diff+.03*(v[:,None]-estimate)**2,1.e3)
        bot=median_filter(v[np.argmin(cost,axis=0)],3)
        # The light stone has less red chroma than the buff facing brick.
        # Locate the sustained colour change, allowing the top of each
        # individual rib to project past the next in the oblique photograph.
        chroma=colours[:,:,0]-colours[:,:,2]
        source_h=np.array([np.mean(lum[d:d+8],axis=0)-np.mean(lum[max(0,d-8):max(1,d)],axis=0)
                           for d in range(len(v)-8)])
        chroma_h=np.array([np.mean(chroma[max(0,d-9):max(1,d)],axis=0)-np.mean(chroma[d:d+9],axis=0)
                           for d in range(len(v)-9)])
        edge=.30*source_h[:-1]+1.35*chroma_h
        distance=bot[None,:]-v[:len(edge),None]
        edge-=.007*(distance-130.)**2
        top=v[np.argmax(np.where((distance>102)&(distance<154),edge,-1.e3),axis=0)]
        top=median_filter(top,5)
        tones=np.array([np.interp(np.linspace(t+16,b-18,22),v,lum[:,i]).mean()for i,(t,b)in enumerate(zip(top,bot))])
        detrend=tones-gaussian_filter1d(tones,5.3)
        peaks=find_peaks(-gaussian_filter1d(detrend,.75),distance=6,prominence=2.8)[0]
        # Exclude secondary tonal blemishes within a single stone bay. Keep
        # the stronger uninterrupted long shadow at the locally measured pitch.
        spacing=float(np.median(np.diff(peaks))) if len(peaks)>2 else 7.
        chosen=[]
        for j in sorted(peaks,key=lambda i:detrend[i]):
            if all(abs(j-h)>.71*spacing for h in chosen):chosen.append(j)
        peaks=sorted(chosen)
        ridges=[]
        for j in peaks:
            if j<2 or j>len(u)-3:continue
            q=(top[j]+bot[j])/2
            xl=at_row(u[j],930.,q)
            ridges.append(dict(u_at_reference_row=float(u[j]),native_px=[round(xl,2),round(float(q),2)],
                               median_luminance_residual=round(float(detrend[j]),3)))
        record=[]
        # Keep all alternating crest and groove boundaries; the top/bottom
        # scallops are observed independently from the shaded shaft surfaces.
        for i in range(len(u)):
            t,b=float(top[i]),float(bot[i])
            record.append(dict(u_at_reference_row=float(u[i]),top_px=[round(at_row(u[i],930.,t),3),t],
                               lower_px=[round(at_row(u[i],930.,b),3),b]))
        panels.append(dict(reference_row_v=930.,bounds_source_samples=record,long_flute_shadows=ridges))
    return dict(source=ref,panels=panels,note="These are six independently visible pale stone window heads. Flute/reveal positions and sloping ends are measured in the photo; the depth and back are estimates.")
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('photo',type=Path);a.add_argument('--output',type=Path,default=HERE/'ribbed-stone-window-heads.json');o=a.parse_args()
    rec=measure(o.photo);o.output.write_text(json.dumps(rec,ensure_ascii=False,separators=(',',':'))+'\n')
    print([[q['u_at_reference_row'] for q in p['long_flute_shadows']] for p in rec['panels']])
