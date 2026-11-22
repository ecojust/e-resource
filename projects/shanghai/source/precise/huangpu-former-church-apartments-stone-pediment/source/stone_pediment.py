"""Raking stone cornice and projecting impost blocks of the former Church Apartments."""
from math import cos, pi, sin

def stone(rgb):
    channels = [value / 255 for value in rgb]
    linear = [c / 12.92 if c < .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
    return dict(color=linear, roughness=.87, metallic=0)
PALETTE = {name:stone(rgb) for name,rgb in [
    ('weathered stone',(150,139,119)),('darker limestone',(133,122,104)),
    ('mortar line',(93,87,75)),('cornice cap',(169,156,135)),
    ('stone roll',(157,144,122)),('stone fillet',(148,138,119)),
    ('soffit',(125,115,96))]}

def plate(b,name,xz,front,back,mat):
    n=len(xz)
    v=[(x,y,z) for y in (front,back) for x,z in xz]
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    faces.extend((i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n))
    b.add(v,faces,mat,name)

def block(b,name,x0,x1,z0,z1,front,back,mat):
    plate(b,name,[(x0,z0),(x1,z0),(x1,z1),(x0,z1)],front,back,mat)

def rake(b,name,side,lo,hi,front,back,mat):
    slope=.565
    profile=[(0,1.687+lo),(1.63,1.687+lo-slope*1.63),
             (1.63,1.687+hi-slope*1.63),(0,1.687+hi)]
    if side<0:profile.reverse()
    plate(b,name,[(x*side,z)for x,z in profile],front,back,mat)

def add_building(b,lod=False):
    # Conspicuous projecting pier capitals interrupt the base of the triangular field.
    for side in (-1,1):
        mid=1.17*side
        for index,(z0,z1,half,face,mat) in enumerate([
            (0,.26,.248,-.09,'darker limestone'),(.26,.28,.245,-.08,'mortar line'),
            (.28,.332,.267,-.132,'stone fillet'),(.332,.54,.273,-.14,'weathered stone'),
            (.54,.59,.288,-.17,'soffit'),(.59,.63,.302,-.194,'stone roll'),
            (.63,.684,.326,-.22,'cornice cap'),(.684,.717,.314,-.206,'stone fillet')]):
            block(b,f'pier capital {side} course {index}',mid-half,mid+half,z0,z1,face,.24,mat)
    for index,(z0,z1,front,mat) in enumerate([
        (.11,.16,-.025,'stone fillet'),(.16,.30,-.012,'darker limestone'),
        (.30,.318,-.016,'mortar line'),(.318,.535,-.031,'weathered stone'),
        (.535,.561,-.063,'stone fillet'),(.561,.61,-.089,'soffit'),(.61,.648,-.105,'stone roll')]):
        block(b,f'spanning entablature {index}',-1.45,1.45,z0,z1,front,.24,mat)
    plate(b,'stone backing behind masonry joints',[(-1.59,.645),(1.59,.645),(0,1.545)],.079,.25,'mortar line')
    # The 2017 front view shows the separate horizontal beds in the flat tympanum.
    floor=.651
    for j,rise in enumerate([.188,.187,.183,.176,.152]):
        z=floor+rise
        a=(1.548-floor)/.564; upper=max(.001,(1.548-z)/.564)
        top=min(z,1.547)
        joints=[-a*.31,a*.43] if j in (0,2) else [a*.12] if j in (1,3) else []
        ends=[-a]+joints+[a]
        for k,(left,right)in enumerate(zip(ends,ends[1:])):
            x0=left+(.006 if k else 0);x1=right-(.006 if k<len(ends)-2 else 0)
            poly=[(x0,floor),(x1,floor)]
            # Subdivide at each vertical joint. At a sloping edge the top bed gets shorter.
            for x in (x1,x0):
                cut=1.548-.564*abs(x)
                if cut<top-.001 and cut>floor+.001:poly.append((x,cut))
                topx=max(-upper,min(upper,x));v=(topx,top)
                if v not in poly:poly.append(v)
            if len(poly)>2:plate(b,f'tympanum bed {j} block {k}',poly,.034,.081,'weathered stone' if (j+k)%3 else 'darker limestone')
        floor=z+.009
    for side in (-1,1):
        rake(b,f'lower shadow roll {side}',side,-.131,-.093,-.081,.224,'soffit')
        rake(b,f'second recessed ledge {side}',side,-.093,-.058,-.143,.236,'stone fillet')
        strips=3 if lod else 12
        # A rounded moulding broadens the silhouette toward the outer stone cap.
        for i in range(strips):
            u=i/strips;t=(i+1)/strips
            face=-.155-.048*sin((u+t)*pi/2)
            rake(b,f'rounded raking moulding {side} flute {i}',side,-.058+.13*u,-.058+.13*t,face,.248,'stone roll')
        rake(b,f'raking flat cap {side}',side,.072,.13,-.214,.257,'cornice cap')
