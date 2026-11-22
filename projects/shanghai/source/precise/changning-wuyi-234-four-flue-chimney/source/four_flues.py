"""Four round terminals and two long recessed joints on the brick stack above the centre wing."""
from math import cos,sin,pi
BRICKS=('red fired brick','dark claret brick','rose fired brick','earth red brick')
def ash(rgb):
    return {'color':[((v/255+.055)/1.055)**2.4 for v in rgb],'roughness':.89}
PALETTE={k:ash(v) for k,v in {'red fired brick':(154,92,70),'dark claret brick':(121,70,58),'rose fired brick':(172,107,79),'earth red brick':(147,84,67),
 'mortar':(126,90,72),'corbel edge':(140,78,62),'sooty clay lip':(137,131,118),'weathered clay':(171,162,143),'blackened flue':(57,51,46),'flue shadow':(36,33,31),'sill mortar':(139,109,87)}.items()}
L=1.65;D=.55;TOP=2.58
CENTERS=[-.61875,-.20625,.20625,.61875]
SEAMS=[-.269,.275]
def block(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)
def cladding(b,x0,x1,z0,z1,front,n,label,material,face_only):
    y=front
    if n=='back':
        if not face_only:block(b,x0,x1,y-.013,y,z0,z1,material,label)
        else:b.add([(x1,y,z0),(x0,y,z0),(x0,y,z1),(x1,y,z1)],[(0,1,2),(0,2,3)],material,label)
    elif n=='front':
        if not face_only:block(b,x0,x1,y,y+.013,z0,z1,material,label)
        else:b.add([(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1)],[(0,1,2),(0,2,3)],material,label)
def stacks(b,z0,z1,projection,mat,name):
    for j,(u,v) in enumerate([(-L/2-.4*projection,SEAMS[0]-.018),(SEAMS[0]+.018,SEAMS[1]-.018),(SEAMS[1]+.018,L/2+.4*projection)]):
        block(b,u,v,-D/2-projection,D/2+projection,z0,z1,mat,name)
def terminal(b,cx,sections):
    outer=[(.140,TOP-.009,'weathered clay'),(.140,TOP+.07,'weathered clay'),(.144,TOP+.101,'sooty clay lip'),(.138,TOP+.113,'sooty clay lip'),(.112,TOP+.113,'sooty clay lip'),(.108,TOP+.094,'blackened flue'),(.108,TOP-.235,'blackened flue')]
    for j,((ra,za,_),(rb,zb,mat))in enumerate(zip(outer,outer[1:])):
        verts=[(cx+r*cos(2*pi*i/sections),r*sin(2*pi*i/sections),z)for r,z in [(ra,za),(rb,zb)]for i in range(sections)]
        faces=[]
        for i in range(sections):
            k=(i+1)%sections;faces.extend([(i,k,k+sections),(i,k+sections,i+sections)])
        b.add(verts,faces,mat,'clay mouth lip and recessed pipe')
    # From above a real deep shadow is visible. The concealed remainder of the shaft is excluded.
    ring=[(cx+.108*cos(2*pi*i/sections),.108*sin(2*pi*i/sections),TOP-.235)for i in range(sections)]
    b.add(ring,[(0,i,i+1)for i in range(1,sections-1)],'flue shadow','bottom of the exhibited flue section')
    # Square crown cell joins the circular pot in all four quadrants.
    for i in range(sections):
        verts=[]
        for scale in ('edge','circle'):
            for j in (i,(i+1)%sections):
                c=cos(2*pi*j/sections);s=sin(2*pi*j/sections)
                r=min((L/8)/max(abs(c),1e-12),(D/2)/max(abs(s),1e-12)) if scale=='edge' else .139
                verts.append((cx+c*r,s*r,TOP))
        b.add(verts,[(0,1,3),(0,3,2)],'sill mortar','bedded top between four flues')
def add_building(b,lod=False):
    # Thin external shells permit an unobstructed normal view into the four real openings.
    block(b,-L/2,L/2,-D/2+.016,-D/2+.050,.012,TOP,'mortar','long street face mortar')
    block(b,-L/2,L/2,D/2-.050,D/2-.016,.012,TOP,'mortar','rear mortar')
    for side in (-1,1):
        x=side*L/2
        block(b,x-.007,x+.007,-D/2,D/2,.012,TOP,'mortar','chimney end mortar')
    block(b,-L/2,L/2,-D/2,D/2,0,.012,'dark claret brick','base of measured shaft')
    for row in range(33):
        a=row*.074+.004;btop=min((row+1)*.074-.004,TOP-.182)
        if a>=btop:continue
        brick=.215;count=10
        for k in range(count):
            low=-L/2+k*brick-(.105 if row%2 else 0);hi=min(L/2,low+brick-.007);low=max(low,-L/2)
            if hi<=low:continue
            for j,(s,t) in enumerate([(-L/2,SEAMS[0]-.012),(SEAMS[0]+.012,SEAMS[1]-.012),(SEAMS[1]+.012,L/2)]):
                u=max(s,low);v=min(t,hi)
                if v<=u:continue
                for name,sg in [('front',-1),('back',1)]:
                    cladding(b,u,v,a,btop,sg*D/2,name,f'long face masonry course {row+1}',BRICKS[(row+k+j)%4],lod)
        for k in range(4):
            y=-D/2+k*.21-(.105 if row%2 else 0);v=min(D/2,y+.202);y=max(-D/2,y)
            if v<=y:continue
            for sg in (-1,1):
                x=sg*(L/2+.012)
                block(b,min(x,sg*(L/2-.004)),max(x,sg*(L/2-.004)),y,v,a,btop,BRICKS[(k+3*row)%4],'end face brickwork')
    for z0,z1,pr,name in [(1.27,1.34,.028,'lower thin stringcourse'),(1.63,1.695,.021,'first course below cornice'),(1.70,1.765,.044,'second corbel'),(1.77,1.84,.067,'third corbel'),(1.845,1.91,.093,'crowning corbel')]:
        stacks(b,z0,z1,pr,'corbel edge',name)
    for sg in (-1,1):
        for k in range(22):
            x0=-L/2+k*.075;x1=x0+.069
            cladding(b,x0,x1,TOP-.182,TOP-.004,sg*(D/2+.008),'front' if sg<0 else 'back','upright bricks at chimney crown',BRICKS[k%4],lod)
        x=sg*L/2
        for k in range(7):
            y0=-D/2+k*(D/7)+.003;y1=y0+D/7-.006
            block(b,min(x,x+sg*.014),max(x,x+sg*.014),y0,y1,TOP-.182,TOP-.004,BRICKS[k%4],'upright bricks on narrow end')
    for cx in CENTERS:terminal(b,cx,16 if lod else 32)
