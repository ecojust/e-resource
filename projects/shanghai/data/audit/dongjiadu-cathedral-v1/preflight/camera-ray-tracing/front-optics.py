import runpy,json,numpy as np,math
from pathlib import Path
s=Path('/tmp/dong64/camera/render.py').read_text();v={};exec(s[:s.index('poses=[];stats=')],v);globals().update({k:x for k,x in v.items()if not k.startswith('_')})
sets=[]
for z,p,tx in [(20.00,62,-5),(20.25,66,-6),(20.35,69,-6),(20.50,70,-5),(20.10,58,-5),(20.30,60,-4)]:
 e,mn=model_en(np.array([tx,0,0]))[:2];ll=[lng+e/rxdeg,np.rad2deg(np.arctan(np.sinh(ln+mn/rx)))];c={'center':ll,'elevation':13.4,'pitch':p,'bearing':1,'zoom':z,'padding':{}};im,stats=image_pose(c,870,660,.56);label(im,f'city detail zoom {z}, pitch {p}, target X {tx}',f"model {stats['whole']}");sets.append(im)
montage(sets,'street-test.jpg',2)
