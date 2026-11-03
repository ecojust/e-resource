"""Original closed curved-surface construction for the aviation building.
Map ENU metres; openings remain geometric voids with bounded glass/backstops.
"""
import math
import numpy as np
from shapely.geometry import Point,box

def cut_shell(builder, mapper, us, zs, holes, back, front, material, label, periodic=False, height_at=None):
    """One manifold wall shell from a sampled u/z grid, with genuine openings.

    Each retained grid cell has front/back skins; only void boundaries receive
    reveals. Neighbouring solid cells share vertices and have no internal faces.
    mapper's u cross z must point along outward depth. Width subdivisions make
    curved skins follow the cylinder instead of a single large chord.
    """
    us=sorted(set(round(float(v),9) for v in us));zs=sorted(set(round(float(v),9) for v in zs))
    um=(np.asarray(us[:-1])+np.asarray(us[1:]))/2;zm=(np.asarray(zs[:-1])+np.asarray(zs[1:]))/2
    valid=np.ones((len(um),len(zm)),dtype=bool)
    for hole in holes:
      a,b,c,d=hole.bounds
      valid[(um>a)&(um<c),:]=valid[(um>a)&(um<c),:] & ~((zm>b)&(zm<d))[None,:]
    if height_at:
      heights=np.array([height_at(u) for u in um]);valid &= zm[None,:]<=heights[:,None]
    verts=[];faces=[];index={}
    def ix(i,j,d):
      k=(0 if periodic and i==len(us)-1 else i,j,d)
      if k not in index:index[k]=len(verts);verts.append(mapper(us[k[0]],zs[j],d))
      return index[k]
    def exists(i,j):
      if periodic:i%=len(us)-1
      return 0<=i<len(us)-1 and 0<=j<len(zs)-1 and valid[i,j]
    for i in range(len(us)-1):
     for j in range(len(zs)-1):
      if not valid[i,j]:continue
      ring=[(i,j),(i+1,j),(i+1,j+1),(i,j+1)]
      faces.append(tuple(ix(a,c,front) for a,c in ring));faces.append(tuple(ix(a,c,back) for a,c in reversed(ring)))
      neighbours=[(i,j-1),(i+1,j),(i,j+1),(i-1,j)]
      for k,n in enumerate(neighbours):
       if exists(*n):continue
       a,c=ring[k];b,d=ring[(k+1)%4]
       faces.append((ix(a,c,back),ix(b,d,back),ix(b,d,front),ix(a,c,front)))
    builder.add(verts,faces,material,label)

def sampled_wall(builder,mapper,u0,u1,z0,z1,holes,thickness,material,label,step=.35,periodic=False):
    us=list(np.linspace(u0,u1,max(2,int(math.ceil((u1-u0)/step))+1)));zs=[z0,z1]
    for h in holes:
      a,b,c,d=h.bounds;us.extend([max(u0,a),min(u1,c)]);zs.extend([max(z0,b),min(z1,d)])
    cut_shell(builder,mapper,us,zs,holes,-thickness,0,material,label,periodic)

def cylindrical_mapper(cx,cy,radius,theta0=0):
    # Increasing u runs counterclockwise; u cross z points outward.
    def mapper(u,z,d):
      a=theta0+u/radius;r=radius+d
      return (cx+r*math.cos(a),cy+r*math.sin(a),z)
    return mapper

def curved_plate(builder,mapper,shape,back,front,material,label,step=.22):
    # Rectangular geometry only. Circular/wing relief shapes use flat Facade.prism.
    u0,z0,u1,z1=shape.bounds
    us=np.linspace(u0,u1,max(2,int(math.ceil((u1-u0)/step))+1))
    cut_shell(builder,mapper,us,[z0,z1],[],back,front,material,label)

def curved_window(builder,mapper,shape,label,detail=True,vertical=False):
    u0,z0,u1,z1=shape.bounds;w=u1-u0;h=z1-z0
    curved_plate(builder,mapper,box(u0+.07,z0+.07,u1-.07,z1-.07),-.29,-.265,'dark recessed glass',label+' / bounded glass')
    bars=[box(u0+.015,z0+.015,u1-.015,z0+.08),box(u0+.015,z1-.08,u1-.015,z1-.015),box(u0+.015,z0+.08,u0+.08,z1-.08),box(u1-.08,z0+.08,u1-.015,z1-.08)]
    if detail:
      for j in range(1,3 if vertical else 2):
       z=z0+h*j/(3 if vertical else 2);bars.append(box(u0+.08,z-.025,u1-.08,z+.025))
      n=1 if vertical else 3
      for j in range(1,n+1):
       u=u0+w*j/(n+1);bars.append(box(u-.023,z0+.08,u+.023,z1-.08))
    for k,bar in enumerate(bars):curved_plate(builder,mapper,bar,-.235,-.18,'dark green metal',label+f' / frame {k}')
    if vertical and detail:
      # Photo-supported repeated squared fretwork; simplified linework.
      for j in range(4):
       z=z0+.18+(h-.36)*(j+.5)/4
       for s in [-1,1]:
        x=(u0+u1)/2+s*w*.23
        for k,bar in enumerate([box(x-.08,z-.13,x+.08,z-.095),box(x-.08,z+.095,x+.08,z+.13),box(x-.08,z-.095,x-.045,z+.095),box(x+.045,z-.095,x+.08,z+.095)]):curved_plate(builder,mapper,bar,-.17,-.13,'dark green metal',label+f' / fret {j}-{s}-{k}')
