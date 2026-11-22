"""The cement courses wrapping the exterior pier next to a timber window in Zhonghe Cun."""
def finish(rgb,roughness=.85,metallic=0):
    return dict(color=[v/255/12.92 if v/255<=.04045 else ((v/255+.055)/1.055)**2.4 for v in rgb],roughness=roughness,metallic=metallic)
PALETTE={label:finish(rgb) for label,rgb in [
 ('granite render',(155,142,125)),('warm cement',(165,151,132)),('shell boundary',(138,126,109)),
 ('recessed joint',(98,86,74)),('cement sill',(161,147,129)),('lower lip',(139,126,109)),
 ('wood muntin',(74,66,58)),('wood frame',(81,72,63)),('lead bead',(103,93,82)),('weathered grain',(133,121,105))]}
PALETTE['window glass']=finish((130,146,149),.30,.12);PALETTE['translucent lower glass']=finish((160,164,155),.49,.06)

def box(b,name,x0,x1,y0,y1,z0,z1,material):
    v=[(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1),(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)]
    b.add(v,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],material,name)

def course(b,row,z,height):
    # Two finished faces turn ninety degrees around the outside corner. The sloping lower
    # surface and dark mortar at the joint produce separate lines from oblique directions.
    v=[]
    for zz,relief in [(z,.003),(z+.021,.047),(z+height-.010,.047),(z+height,.041)]:
        v.extend([(-1.28,-.34-relief,zz),(-.31+relief,-.34-relief,zz),(-.31+relief,.104,zz),
                  (-.48,.104,zz),(-.48,-.22,zz),(-1.28,-.22,zz)])
    faces=[]
    for ring in range(3):
        for i in range(6):faces.append((ring*6+i,ring*6+(i+1)%6,(ring+1)*6+(i+1)%6,(ring+1)*6+i))
    # End caps are split along the concave corner to remain planar convex quads.
    for offset,flip in [(0,True),(18,False)]:
        for ids in [(0,1,4,5),(1,2,3,4)]:
            tup=tuple(offset+i for i in ids);faces.append(tuple(reversed(tup)) if flip else tup)
    b.add(v,faces,'warm cement' if row%3==2 else 'granite render',f'cement course around corner {row+1}')

def add_building(b,lod=False):
    box(b,'front bed behind coursing',-1.28,-.312,-.339,-.21,.0,2.73,'recessed joint')
    box(b,'return bed behind coursing',-.48,-.312,-.339,.105,.0,2.73,'recessed joint')
    pitch=.388
    for i in range(7):
        course(b,i,i*pitch+.01,.359)
        if not lod:
            # A limited coat of low-relief aggregate distinguishes the intact render from the smooth window sill.
            vertices=[];faces=[]
            for k in range(180):
                x=-1.265+(.96*((i*47+k*513)%997)/997);z=i*pitch+.056+.279*((i*137+k*k*31+k*7)%991)/991
                r=.002+(.0018*(k%4));u=len(vertices)
                vertices.extend([(x-r,-.3872,z-r),(x+r,-.3872,z-r),(x,-.3872,z+r),(x+.0006,-.389,z)])
                faces.extend([(u,u+1,u+3),(u+1,u+2,u+3),(u+2,u,u+3)])
            b.add(vertices,faces,'weathered grain','visible aggregate '+str(i+1))
    # Glazing and sash are set behind the front plane of the pier.
    box(b,'upper window head',-.30,1.84,.095,.248,2.533,2.744,'shell boundary')
    box(b,'right reveal finish',1.732,1.84,.095,.248,.32,2.533,'granite render')
    box(b,'cement apron below sill',-.30,1.84,.093,.264,0,.304,'granite render')
    for i,(y,z0,z1) in enumerate([(-.005,.296,.345),(-.031,.345,.398),(.004,.398,.431),(-.068,.431,.488)]):
        box(b,'projecting stepped sill '+str(i+1),-.304,1.81,y,.246,z0,z1,'cement sill' if i%2 else 'lower lip')
    for i in range(3):
        x0=-.284+i*.671;x1=x0+.668
        box(b,'reflective upper pane '+str(i),x0,x1,.188,.204,1.022,2.513,'window glass')
        box(b,'frosted lower pane '+str(i),x0,x1,.186,.205,.489,1.030,'translucent lower glass')
        for z in [.984,1.855]:
            box(b,'wood glazing rail '+str(i),x0,x1,.140,.198,z-.021,z+.021,'wood muntin')
    for i in range(4):
        x=-.283+i*.671
        box(b,'timber stile '+str(i),x-.023,x+.024,.104,.196,.484,2.543,'wood frame')
        box(b,'side glazing bead '+str(i),x+.024,x+.031,.138,.191,.491,2.531,'lead bead')
    box(b,'upper frame',-.30,1.75,.120,.192,2.484,2.55,'wood frame')
    box(b,'lower frame',-.30,1.75,.114,.191,.488,.533,'wood frame')
