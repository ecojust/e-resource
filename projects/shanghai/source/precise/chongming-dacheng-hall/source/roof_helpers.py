"""Roof mesh helpers adapted from the repository's Baoshan model, MIT.
Only primitive roof tessellation reused; Zunjing dimensions/profile are supplied
by its own authoring code. No Baoshan facade or carving geometry is reused.
"""
import math
import numpy as np
class RoofHelpers:
 def roofZ(self,x,y,tier):
  if tier=='lower':
   ix,iy=self.lowerInner
   ty=(abs(y)-iy)/(self.hy-iy);tx=(abs(x)-ix)/(self.hx-ix)
   if ty>=tx:t=max(0,ty);w=ix+(self.hx-ix)*t;return float(self.lower(0,(x/w+1)/2,t)[2])
   t=max(0,tx);w=iy+(self.hy-iy)*t;return float(self.lower(2,(y/w+1)/2,t)[2])
  ay=abs(y);ax=abs(x)
  if ax<=self.ridge or ay>=self.breaky+(self.uy-self.breaky)*(ax-self.ridge)/(self.ux-self.ridge):
   w=self.ridge+(self.ux-self.ridge)*max(0,(ay-self.breaky)/(self.uy-self.breaky));return float(self.upper(0,(x/w+1)/2,ay/self.uy)[2])
  t=(ax-self.ridge)/(self.ux-self.ridge);w=self.breaky+(self.uy-self.breaky)*t;return float(self.upper(2,(y/w+1)/2,t)[2])
 def roof_patch(self,point,tier,field):
  n=7 if self.lod else 12;nu=n*2
  vs=[point(s,t) for t in np.linspace(0,1,n+1) for s in np.linspace(0,1,nu+1)]
  fs=[(j*(nu+1)+i,j*(nu+1)+i+1,(j+1)*(nu+1)+i+1,(j+1)*(nu+1)+i) for j in range(n) for i in range(nu)]
  self.shell(vs,fs,.085,'roof underlay',f'{tier}/field{field}/closed-curved-shell')
  width=np.linalg.norm(point(1,1)-point(0,1));count=max(10,round(width/(.39 if self.lod else .24)))
  for i in range(count):
   s=(i+.5)/count;pts=[point(s,t)+[0,0,.052] for t in np.linspace(0,1,7 if self.lod else 12)]
   self.b.tube(pts,.073 if self.lod else .062,f'grey tile {i%3}',6,f'{tier}/field{field}/cap-tile-course-{i}')
   if not self.lod:
    # Pan-tile cross-sections and each lap are actual shaped surfaces, not images.
    verts=[];rows=9;cols=2
    for t in np.linspace(0,1,rows):
     for j in range(cols+1):
      ss=(i+j/cols)/count;p=point(ss,t);p[2]+=.012+.036*(abs(j/cols-.5)*2)**2;verts.append(p)
    quads=[(k*(cols+1)+j,k*(cols+1)+j+1,(k+1)*(cols+1)+j+1,(k+1)*(cols+1)+j) for k in range(rows-1) for j in range(cols)]
    self.shell(verts,quads,.018,f'grey tile {(i+1)%3}',f'{tier}/field{field}/concave-pan-{i}')
    for j,t in enumerate(np.linspace(.12,.99,5)):
     p=point(s,t)+[0,0,.054];dir=point(s,min(1,t+.008))-point(s,max(0,t-.008));dir/=np.linalg.norm(dir)
     self.b.tube([p-dir*.009,p+dir*.009],.066,'ridge ceramic',6,f'{tier}/field{field}/tile-lap-{i}-{j}')
   end=point(s,1);out=end-point(s,.98);out/=np.linalg.norm(out);p=end+[0,0,.054]
   self.b.tube([p-out*.025,p+out*.035],.078,'ridge ceramic',8 if self.lod else 12,f'{tier}/field{field}/circular-end-tile-{i}')
   if not self.lod:
    crest=[p+[0,0,.05],p-out*.035+[0,0,.15],p-out*.025+[0,0,.25],p+out*.018+[0,0,.30]]
    self.b.tube(crest,.024,'ridge ceramic',5,f'{tier}/field{field}/small-upright-end-crest-{i}')
    cross=np.cross(out,[0,0,1]);cross/=np.linalg.norm(cross);vertical=np.cross(cross,out)
    ring=[p+out*.037+.052*(math.cos(a)*cross+math.sin(a)*vertical) for a in np.linspace(0,math.tau,9)]
    self.b.tube(ring,.009,'grey tile 2',4,f'{tier}/field{field}/end-tile-ring-{i}')
  for i,s in enumerate(np.linspace(.03,.97,10 if self.lod else 22)):
   pts=[point(s,t)-[0,0,.18] for t in np.linspace(.05,1,8)]
   self.b.tube(pts,.038,'aged red brown timber',5,f'{tier}/field{field}/underside-rafter-{i}')
  edge=[point(s,1)-[0,0,.09] for s in np.linspace(0,1,25)]
  self.b.tube(edge,.09,'aged red brown timber',8,f'{tier}/field{field}/eave-fascia')
  # Shared hips are owned by front/back only; avoid coincident duplicates.
  if field<2:
   start=0 if tier=='lower' else self.breaky/self.uy
   for side in [0,1]:
    pts=[point(side,t)+[0,0,.14] for t in np.linspace(start,1,17)]
    self.b.tube(pts,.15,'ridge ceramic',10,f'{tier}/field{field}/hip-ridge-{side}')
    for k,t in enumerate([.72,.80,.88,.96]):
     p=point(side,t)+[0,0,.22]
     self.beast(p,f'{tier}/field{field}/hip-figure-{side}-{k}',.75 if tier=='lower' else 1.)
  self.mark('curved_tiled_roof_patch',tier=tier,field=field,cap_courses=count,roof_shell_thickness_m=.085)
 def beast(self,p,label,scale=1.):
  # Small photographed ridge figures reconstructed as restrained silhouettes.
  x,y,z=p;s=scale
  self.b.lathe((x,y),[(z,.10*s),(z+.11*s,.12*s),(z+.25*s,.07*s),(z+.34*s,.045*s)],'ridge ceramic',6 if self.lod else 8,label+'/seated-body')
  self.b.tube([[x,y,z+.25*s],[x+.02*s,y-.04*s,z+.39*s],[x+.08*s,y-.06*s,z+.43*s]],.055*s,'ridge ceramic',6,label+'/head')
