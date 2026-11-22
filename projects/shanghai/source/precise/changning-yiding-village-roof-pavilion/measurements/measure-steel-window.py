from pathlib import Path
import numpy as np
from scipy.ndimage import map_coordinates
from PIL import Image
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
s=Path(__file__).absolute().parent
import json
im=np.asarray(Image.open(s/'antigng-roof-room.jpg').convert('RGB'),float)
matrix=[]
for (x,y),(u,v)in zip([[0,0],[259,0],[259,399],[0,399]],[[568,297],[745,264],[748,538],[571,569]]):
    matrix.extend([[x,y,1,0,0,0,-u*x,-u*y,-u],[0,0,0,x,y,1,-v*x,-v*y,-v]])
H=np.linalg.svd(matrix)[2][-1].reshape(3,3)
x,y=np.meshgrid(np.arange(260),np.arange(400))
q=H@np.stack([x.ravel(),y.ravel(),np.ones(x.size)])
uv=(q[:2]/q[2])[::-1]
rect=np.stack([map_coordinates(im[:,:,c],uv,order=1,mode='nearest')for c in range(3)],axis=1).reshape(400,260,3)
l=rect@np.array([.299,.587,.114])
xx=l[48:347].mean(axis=0)
pp,_=find_peaks(gaussian_filter1d(xx,11)-gaussian_filter1d(xx,1.6),prominence=10,distance=22)
bars=[int(v)for v in pp if xx[v]<175]
columns=[];dark_rails=[]
for a,b in zip(bars,[*bars[1:],259]):
    lc=np.median(l[:,a+7:b-7],axis=1)
    peaks,_=find_peaks(gaussian_filter1d(lc,14)-gaussian_filter1d(lc,1.5),distance=16,prominence=10)
    positions=[int(v)for v in peaks if 39<v<372 and lc[v]<167]
    assert len(positions)==2,positions
    columns.append(dict(left_frac=a/259,right_frac=b/259,rail_fractions_from_top=[v/399 for v in positions]))
    dark_rails.append(positions)
if __name__=='__main__':
    source=json.loads((s/'photographic-source.json').read_bytes())
    out=dict(photo_sha256=source['sha256'],crop_sha256=source['crop_sha256'],crop_quad=[[568,297],[745,264],[748,538],[571,569]],
             rectified_size=[260,400],vertical_dark_lines_px=bars,columns=columns,
             description='四个窄窗格的两道短横档逐格高低交替，在第一和第三格靠上下，第二和第四格集中在中部。')
    (s/'steel-window-pattern.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(bars,dark_rails)
