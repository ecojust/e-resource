"""Stepped bronze-coloured entrance head at 107 Fuzhou Road, with overlapping V-shaped ribs."""
from math import cos,sin,pi
def material(rgb,metal):
    s=[c/255 for c in rgb]
    return dict(color=[c/12.92 if c<.04045 else ((c+.055)/1.055)**2.4 for c in s],roughness=.54 if metal else .86,metallic=metal)
PALETTE={k:material(c,m) for k,c,m in [
    ('brown dressed stone',(154,130,102),0),('mortar seam',(118,103,82),0),('bronze border',(81,65,49),.38),
    ('dark transom metal',(63,52,42),.31),('chevron face',(116,96,72),.40),('back diagonal',(91,76,60),.36),
    ('beaded pendant',(104,86,66),.36),('finial apron',(86,72,57),.32),('black recess',(44,40,35),.15)]}
def extrude(b,name,xz,front,back,mat):
    n=len(xz);v=[(x,y,z) for y in (front,back)for x,z in xz]
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    faces += [(j,(j+1)%n,n+(j+1)%n,n+j)for j in range(n)]
    b.add(v,faces,mat,name)
def box(b,name,x0,x1,z0,z1,front,back,mat):
    extrude(b,name,[(x0,z0),(x1,z0),(x1,z1),(x0,z1)],front,back,mat)
def chevron(b,label,extent,drop,tip,width,y,mat):
    top=tip+drop
    # Four convex points per branch keep the stepped open centre between the ribs.
    for side in (-1,1):
        profile=[(0,tip),(side*extent,top),(side*(extent-width),top),(0,tip+width)]
        if side<0:profile.reverse()
        extrude(b,label+(' left' if side<0 else ' right'),profile,y,y+.024,mat)
def boss(b,name,x,z,rx,rz,depth,mat,steps):
    v=[(x,-.078-depth,z)]
    for ring,dep in [(.46,.87),(.83,.45),(1,0)]:
        for i in range(steps):
            a=2*pi*i/steps;v.append((x+rx*ring*cos(a),-.078-depth*dep,z+rz*ring*sin(a)))
    f=[(0,1+i,1+(i+1)%steps)for i in range(steps)]
    for j in (0,1):
        base=1+j*steps
        f.extend((base+i,base+steps+i,base+steps+(i+1)%steps,base+(i+1)%steps)for i in range(steps))
    b.add(v,f,mat,name)
def add_building(b,lod=False):
    for side,(left,right) in enumerate([(-1.22,-.92),(.92,1.22)]):
        box(b,'vertical seal behind jamb '+str(side),left,right,-.14,.95,.015,.18,'mortar seam')
        for j,(lo,hi) in enumerate([(-.14,.18),(.185,.48),(.486,.73),(.736,.95)]):
            box(b,f'stone jamb {side}-{j}',left,right,lo,hi,-.002,.16,'brown dressed stone')
    for j,(x0,x1) in enumerate([(-.92,-.34),(-.337,.337),(.34,.92)]):
        box(b,'stone head course '+str(j),x0,x1,.827,.95,-.002,.16,'brown dressed stone')
    box(b,'recessed doorhead plate',-.91,.91,0,.826,.054,.105,'dark transom metal')
    for name,x0,x1,z0,z1 in [('outer jamb left',-.91,-.85,0,.83),('outer jamb right',.85,.91,0,.83),('lintel rail',-.85,.85,.782,.825),('lower rebate',-.87,.87,.0,.045)]:
        box(b,name,x0,x1,z0,z1,-.015,.077,'bronze border')
    box(b,'recess behind central insignia',-.56,.56,.11,.758,.031,.060,'black recess')
    # Two lighter strokes turn up below the large descending chevrons.
    for side in (-1,1):
        x=[(.018,.126),(.44,.126),(.142,.342),(.094,.298)]
        extrude(b,'lower fan facet '+str(side),[(side*xx,zz) for xx,zz in (x if side==1 else reversed(x))],.012,.04,'back diagonal')
    for i,(extent,drop,tip) in enumerate([(.535,.548,.152),(.457,.456,.251),(.371,.364,.356)]):
        chevron(b,'folded V rib '+str(i),extent,drop,tip,.048,-.038-.009*i,'chevron face')
    for j,side in enumerate((-1,1)):
        x=.64*side
        p=[(x-.102,.734),(x+.102,.734),(x+.102,.214),(x+.076,.214),(x+.076,.151),(x+.032,.151),(x+.032,.104),(x-.045,.104),(x-.045,.14),(x-.095,.14)]
        extrude(b,'stepped side apron '+str(j),list(reversed(p)),-.068,.047,'finial apron')
        for k,(z,r)in enumerate([(.680,.054),(.566,.040),(.472,.029),(.405,.021),(.351,.018),(.305,.015),(.264,.013)]):
            boss(b,f'pendant boss {j}-{k}',x,z,r,r,.029 if k<2 else .014,'beaded pendant',8 if lod else 18)
        for k in range(2):
            box(b,f'recessed vertical strip {j}-{k}',x+(-.076+.14*k)-.008,x+(-.076+.14*k)+.008,.205,.749,-.079,-.064,'bronze border')
