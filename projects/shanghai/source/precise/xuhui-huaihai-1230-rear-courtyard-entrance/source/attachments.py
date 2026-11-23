"""Photographed exterior fittings flanking the rear court door at No. 1230.

The default state follows Masa's January 2016 photograph. Gao's 2013 plate
shows the flatter grille at the masonry opening. See attachment-observations.json.
X increases to the viewer's right, +Y enters the wall, Z is up.
"""
from math import cos, pi, sin, sqrt

METAL = '1230 attachments | dull zinc-grey guard'
EDGE = '1230 attachments | pale edge rail'
CASE = '1230 attachments | warm-grey condenser'
GRILLE = '1230 attachments | shaded fan grille'
BRACKET = '1230 attachments | painted steel supports'
PALETTE = {
    METAL: {'color':[.33,.36,.35], 'roughness':.71, 'metallic':.24},
    EDGE: {'color':[.46,.48,.46], 'roughness':.68, 'metallic':.22},
    CASE: {'color':[.63,.61,.55], 'roughness':.79},
    GRILLE: {'color':[.28,.29,.27], 'roughness':.76},
    BRACKET: {'color':[.27,.26,.23], 'roughness':.86, 'metallic':.15},
}

def box(b, x0,x1,y0,y1,z0,z1,material,name):
    pts=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
         (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
           (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    b.add(pts,faces,material,name)

def rail(b,p,q,half,material,label):
    """Closed square-section member between the two measured edge axes."""
    delta=[d-c for c,d in zip(p,q)]
    length=sqrt(sum(t*t for t in delta))
    v=[t/length for t in delta]
    ref=(0,0,1) if abs(v[2])<.8 else (0,1,0)
    def cross(a,c):
        return [a[1]*c[2]-a[2]*c[1],a[2]*c[0]-a[0]*c[2],a[0]*c[1]-a[1]*c[0]]
    u=cross(ref,v)
    n=sqrt(sum(t*t for t in u))
    u=[t/n for t in u]
    w=cross(v,u)
    pts=[tuple(o[k]+half*(i*u[k]+j*w[k]) for k in range(3))
         for o in (p,q) for i,j in ((-1,-1),(1,-1),(1,1),(-1,1))]
    faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7)]
    for i in range(4):
        j=(i+1)%4
        faces.extend(((i,j,j+4),(i,j+4,i+4)))
    b.add(pts,faces,material,label)

def guard(b,name,left,right,base,top,face,intervals,lod):
    # The turned lower lip and the side returns distinguish the later outer baskets.
    root='1230 rear | '+name+' window guard '
    knee=base+.23
    for z,y in [(base,face+.105),(knee,face),(base+.58,face),(top-.11,face),(top,face)]:
        rail(b,(left,y,z),(right,y,z),.018,EDGE,root+'horizontal rail')
    for i in range(intervals+1):
        x=left+(right-left)*i/intervals
        rail(b,(x,face,knee),(x,face,top),.012 if lod else .009,METAL,root+'upright')
        rail(b,(x,face+.105,base),(x,face,knee),.011,METAL,root+'turned foot')
    for x in (left,right):
        for z in (base+.03,(base+top)/2,top):
            y=face+.10 if z<knee else face
            rail(b,(x,y,z),(x,-.03,z),.018,EDGE,root+'side return')
        rail(b,(x,-.035,base+.03),(x,-.035,top),.017,METAL,root+'side jamb')
        if not lod:
            rail(b,(x,face/2,base+.04),(x,face/2,top),.010,METAL,root+'side upright')
    for i in range(1,5):
        x=left+(right-left)*i/5
        rail(b,(x,face+.105,base),(x,-.035,base),.014,METAL,root+'underside')

def condenser(b,name,left,base,right,top,lod):
    label='1230 courtyard | '+name
    width=right-left
    height=top-base
    y=-.31
    box(b,left,right,y,-.065,base,top,CASE,label+' casing')
    radius=min(height*.355,width*.265)
    x=left+.395*width
    z=base+.52*height
    n=12 if lod else 22
    pts=[(x+radius*cos(2*pi*i/n),v,z+radius*sin(2*pi*i/n))
         for v in (y-.017,y-.006) for i in range(n)]
    faces=[(0,i,i+1) for i in range(1,n-1)]+[(n,n+i+1,n+i)for i in range(1,n-1)]
    for i in range(n):
        j=(i+1)%n
        faces.extend(((i,n+i,n+j),(i,n+j,j)))
    b.add(pts,faces,GRILLE,label+' round grille')
    if not lod:
        for dy in (-.65,-.32,0,.32,.65):
            reach=radius*sqrt(1-dy*dy)*.94
            rail(b,(x-reach,y-.023,z+radius*dy),(x+reach,y-.023,z+radius*dy),.005,CASE,label+' grille bar')
    for f in (.22,.80):
        xx=left+f*width
        box(b,xx-.021,xx+.021,y-.016,-.025,base-.032,base,BRACKET,label+' support')

def add_attachments(b,lod=False,*,period=2016):
    if period==2013:
        # The older photograph exposes an inset grille at this opening.
        l,r,base,top=2.02,3.34,1.81,3.11
        for t in (.18,.39,.61,.82):
            z=base+(top-base)*t
            rail(b,(l,-.025,z),(r,-.025,z),.012,METAL,'1230 courtyard | 2013 inset rail')
        for x in (l+.37*(r-l),l+.70*(r-l)):
            rail(b,(x,-.025,base),(x,-.025,top),.013,METAL,'1230 courtyard | 2013 inset upright')
        return
    if period!=2016:
        raise ValueError('The measured courtyard exterior dates are 2013 and 2016.')
    guard(b,'west visible section',-5.56,-1.881,1.735,3.604,-.38,16 if lod else 24,lod)
    # At the balcony jamb, the independently measured 2016 bars continue
    # at the rail plane. Only two short joining returns meet that frame.
    guard(b,'east to balcony seam',1.8745,4.078,1.6278,3.2981,-.42,12 if lod else 20,lod)
    for z in (2.06,2.845):
        rail(b,(4.078,-.42,z),(4.132,-.21,z),.011,EDGE,'1230 rear | east guard seam return')
    units=[
        ('door left',-1.3921,2.786,-.7094,3.2019),
        ('door right',1.0577,2.8669,1.7023,3.3572),
        ('grey band left',-.6076,4.1033,.0864,4.6063),
        ('grey band right',.2561,4.1283,.962,4.6219),
        ('third level',-.7629,7.7842,-.0045,8.3549),
        ('fourth level lower',-1.4525,10.1799,-.8336,10.8179),
        ('fourth level upper',-.6855,11.279,-.023,11.9211),
        ('fourth level centre',.3574,10.6303,.998,11.2013),
    ]
    for unit in units:
        condenser(b,*unit,lod)
