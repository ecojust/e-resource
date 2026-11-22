"""Two dated passages at Hengchang Li. The lining is measured in arch-bay units."""
from math import cos, hypot, pi, sin
from pathlib import Path
import json


def material(rgb, roughness=.82, metallic=0.0):
    def linear(code):
        value = code / 255
        return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4
    return {'color': [linear(code) for code in rgb], 'roughness': roughness, 'metallic': metallic}


PALETTE = {
    'Passage / grey mortar': material((106, 104, 99)),
    'Passage / grey facing brick': material((105, 103, 99)),
    'Passage / slate facing brick': material((93, 95, 92)),
    'Passage / worn brick edge': material((116, 112, 104)),
    'Passage / red brick string': material((149, 91, 62)),
    'Passage / pale arch render': material((190, 187, 178)),
    'Passage / moulding light edge': material((206, 204, 196)),
    'Passage / moulding shadow': material((151, 149, 142)),
    'Passage / riven plinth': material((139, 136, 129)),
    'Passage / dark plinth stone': material((113, 110, 105)),
    'Passage / dark grey paving': material((90, 90, 87)),
    'Passage / warm ceiling': material((208, 204, 192)),
    'Passage / dark track and housing': material((52, 53, 49), .53, .21),
    'Passage / lamp lens': material((220, 210, 181), .35),
    'Passage / reddish window frame': material((108, 65, 48), .66),
    'Passage / inset shaded glass': material((63, 78, 78), .34, .19),
    'Passage / warm display backing': material((207, 190, 162), .78),
    'Passage / line of print': material((141, 120, 98)),
    'Passage / metal frame': material((71, 62, 55), .61, .23),
    'Passage / historical panel face': material((109, 123, 125)),
    'Passage / enamel blue': material((67, 112, 133), .61, .16),
    'Passage / enamel green': material((91, 126, 113), .61, .16),
    'Passage / enamel numerals': material((214, 214, 194), .63),
    'Passage / red box': material((151, 62, 50), .61, .10),
    'Passage / shaded brick window reveal': material((81,78,70),.89),
    'Passage / red varnished bench slats': material((148,78,55),.61),
    'Passage / black iron bench ends': material((57,57,52),.47,.29),
    'Passage / 2018 plaster': material((151, 143, 119)),
}
(MORTAR, BRICK, SLATE, WORN, RED, RENDER, LIGHT, SHADE, STONE, ROCK, PAVING, CEILING,
 TRACK, LENS, SASH, GLASS, PAPER, INK, FRAME, PANEL, BLUE, GREEN, WHITE, BOX_RED, REVEAL, BENCH_WOOD, BENCH_IRON, OLD) = PALETTE


def rings(builder, sections, mat, name):
    n = len(sections[0])
    last = (len(sections)-1)*n
    triangles = [(0, i+1, i) for i in range(1,n-1)]
    triangles += [(last,last+i,last+i+1) for i in range(1,n-1)]
    for k in range(len(sections)-1):
        for i in range(n):
            a = k*n+i
            b = k*n+(i+1)%n
            triangles.extend(((a,b,b+n),(a,b+n,a+n)))
    vertices = [v for row in sections for v in row]
    volume = 0
    for a,b,c in triangles:
        x,y,z = vertices[a]
        u,v,w = vertices[b]
        r,s,t = vertices[c]
        volume += x*(v*t-w*s)+y*(w*r-u*t)+z*(u*s-v*r)
    if volume < 0:
        triangles = [(a,c,b) for a,b,c in triangles]
    builder.add(vertices,triangles,mat,name)


def box(b, at, l,r,z,h,d,e,mat,name):
    if r-l <= .00001 or h-z <= .00001:
        return
    face = [(l,z),(r,z),(r,h),(l,h)]
    rings(b,[[at(u,v,q) for u,v in face] for q in (d,e)],mat,name)


def quad(b, at, pts,d,e,mat,name):
    rings(b,[[at(u,z,q) for u,z in pts] for q in (d,e)],mat,name)


def arch(b, at, center, radius, rise, spring, thickness, depth, lod, name):
    for j,(offset,width,front,mat) in enumerate(((0,thickness,.078,RENDER),(.017,.014,.096,LIGHT),(.045,.018,.091,SHADE),(thickness-.023,.023,.099,LIGHT))):
        rows=[]
        for i in range((18 if lod else 38)+1):
            angle = i*pi/(18 if lod else 38)
            dx,dz=cos(angle),sin(angle)
            r=radius+offset
            h=rise+offset
            inner=(center+r*dx,spring+h*dz)
            outer=(center+(r+width)*dx,spring+(h+width)*dz)
            rows.append([at(*inner,depth),at(*outer,depth),at(*outer,front),at(*inner,front)])
        rings(b,rows,mat,name+' | arch mould '+str(j+1))


def glass_window(b,at,c,p,lod,name):
    l,r=c-.301*p,c+.301*p
    bot,top=.869*p,1.766*p
    frame=.031*p
    box(b,at,l,r,bot,top,-.158,-.146,GLASS,name+' | recessed glazing')
    for x in (l,c-frame*.34,r-frame):
        box(b,at,x,x+(frame if x!=c-frame*.34 else frame*.68),bot,top,-.144,-.095,SASH,name+' | window stile')
    for z in (bot,bot+(top-bot)*.35,bot+(top-bot)*.66,top-frame):
        box(b,at,l,r,z,z+frame,-.144,-.092,SASH,name+' | window rail')
    for left,right in ((l-.035,l),(r,r+.035)):
        box(b,at,left,right,bot,top,-.16,.006,REVEAL,name+' | brick reveal')
    box(b,at,l-.036,r+.036,bot-.046,bot,-.16,.029,WORN,name+' | brick sill')
    # The 2023 photograph shows a red cylindrical exhibit fitting sitting inside the sill.
    circ=[]
    for i in range(8 if lod else 16):
        a=2*pi*i/(8 if lod else 16)
        circ.append((c+.075*p+.050*p*cos(a),-.039+.050*p*sin(a)))
    for z,h,mat,tag in ((bot,bot+.36*p,BOX_RED,'barrel'),(bot+.145*p,bot+.225*p,WHITE,'band'),(bot+.355*p,bot+.38*p,BOX_RED,'cap')):
        rings(b,[[at(x,k,d) for x,d in circ] for k in (z,h)],mat,name+' | red exhibit '+tag)


def wall_bricks(b,at,start,end,height,p,lod,opening,name):
    split=[0.,height]
    if opening:split.extend(opening[2:])
    for low,high in zip(sorted(split),sorted(split)[1:]):
        fits=opening and opening[2]<(low+high)/2<opening[3]
        intervals=((start,opening[0]),(opening[1],end)) if fits else ((start,end),)
        for l,r in intervals:
            box(b,at,l,r,low,high,-.15,-.012,MORTAR,name+' | masonry body')
    # Keep small mortar joints and the original stretcher bond. Batch the courses by material.
    course=p/25.6
    brick=.176*p
    for row in range(int(height/course)+1):
        z=row*course
        top=min(height,z+course-.006)
        if top<=z:continue
        color=RED if 0.787*p<z<.851*p or 1.465*p<z<1.536*p else BRICK
        if lod and color!=RED:
            if row%2:continue
            top=min(height,z+2*course-.007)
        u=start-(.5*brick if row%2 else 0.)
        j=0
        while u<end:
            left=max(start,u+.003)
            right=min(end,(end if lod else u+brick-.003))
            intervals=[(left,right)]
            if opening and z<opening[3] and top>opening[2]:
                intervals=[(left,min(right,opening[0])),(max(left,opening[1]),right)]
            for l,r in intervals:
                shade=color
                if color==BRICK and not lod:
                    shade=(BRICK,BRICK,WORN,BRICK,SLATE)[(row*7+j*17)%5]
                box(b,at,l,r,z,top,-.012,.002,shade,name+' | brickwork')
            if lod:break
            u+=brick;j+=1


def pier(b,at,x,p,name):
    base=.337*p
    spring=1.56*p
    for left,right,z,high,d,mat,label in [
        (-.105,.105,base,1.56,.063,RENDER,'pier'),
        (-.089,.089,base+.014,1.49,.086,LIGHT,'outer margin'),
        (-.070,.070,base+.038,1.475,.095,SHADE,'sunk panel'),
        (-.063,.063,base+.053,1.458,.100,RENDER,'flat panel'),
        (-.119,.119,1.50,1.537,.090,SHADE,'capital lower'),
        (-.127,.127,1.537,1.562,.118,LIGHT,'capital lip'),
        (-.132,.132,1.562,1.62,.102,RENDER,'capital block')]:
        z0=base if label=='pier' else (z if label in ('outer margin','sunk panel','flat panel') else z*p)
        box(b,at,x+left*p,x+right*p,z0,high*p,-.012,d,mat,name+' | '+label)


def panel(b,at,c,p,k,is_west,lod,name):
    lo=.862*p;hi=1.527*p;w=.445*p
    if is_west and k==0:
        # Original two vertical columns of relief, represented by abstract relief slugs.
        for column in (-.105,.105):
            for row in range(4):
                x=c+column*p;z=lo+(row+.25)*.16*p
                box(b,at,x-.046*p,x+.046*p,z,z+.093*p,.014,.039,FRAME,name+' | title relief')
        return
    box(b,at,c-w/2-.011,c+w/2+.011,lo-.012,hi+.012,.020,.046,FRAME,name+' | framed board')
    box(b,at,c-w/2,c+w/2,lo,hi,.046,.049,PAPER,name+' | cream placard')
    bodylo=lo+.11*p
    bodyhi=lo+.30*p
    if is_west or k in (2,3,6,7):
        box(b,at,c-.084*p,c+.084*p,hi-.29*p,hi-.125*p,.049,.051,INK,name+' | image field')
    if not lod:
        for j in range(7):
            width=.32*p if j<6 else .23*p
            z=bodylo+j*(bodyhi-bodylo)/7
            box(b,at,c-.16*p,c-.16*p+width,z,z+.004*p,.049,.051,INK,name+' | text rules')


# Numerals transcribed from the two independent photographs; designed line segments.
ENAMEL_NUMBERS=(('34','255','1051'),('4','1055','719'),('51','851','480'),
                ('1293','1065','749'),('21','155','111'),('4','1352','1357'),('978','1375','753'))
GLYPHS=('abcedf','bc','abged','abgcd','fgbc','afgcd','afgcde','abc','abcdefg','abcdfg')
SEGMENTS={'a':(.12,.91,.87,1.),'b':(.84,.52,.97,.96),'c':(.84,.04,.97,.5),
          'd':(.12,0,.87,.095),'e':(.03,.04,.16,.50),'f':(.03,.52,.16,.96),'g':(.12,.455,.87,.55)}

def numerals(b,at,y,z,size,characters,name):
    stroke_width=size*.57
    pitch=stroke_width*1.32
    start=y+pitch*(len(characters)-1)/2
    for i,ch in enumerate(characters):
        mid=start-i*pitch
        for key in GLYPHS[int(ch)]:
            l,lo,r,hi=SEGMENTS[key]
            # On the east wall, the visible left-to-right direction points towards the street.
            box(b,at,mid+(.5-r)*stroke_width,mid+(.5-l)*stroke_width,z+size*lo,z+size*hi,.056,.059,WHITE,name)

def blue_register(b,at,a,p,lod,name):
    width=1.48*p;bottom=.34*p;top=2.24*p
    box(b,at,a,a+width,bottom,top,-.025,.038,PANEL,name+' | grey-blue tablet')
    # Seven columns of three enamel cards measured independently in both photographs.
    for col in range(7):
        for row in range(3):
            l=a+width*(.035+(6-col)*.135)
            r=l+width*.11;z=bottom+(1.03+.198*(2-row))*p
            box(b,at,l,r,z,z+.152*p,.038,.055,GREEN if col<3 or col==6 else BLUE,name+' | 21 enamel address plates')
            numerals(b,at,(l+r)/2,z+.061*p,.052*p,ENAMEL_NUMBERS[col][row],name+' | address numerals')
            if not lod:
                box(b,at,l+.016*p,r-.016*p,z+.045*p,z+.052*p,.055,.057,WHITE,name+' | plate legend')
    for j,h in enumerate((.07,.13,.09,.16,.12,.22,.31,.16,.13,.09,.15,.20,.11,.12,.19,.14,.08,.15,.12,.09,.13)):
        l=a+width*j/21
        box(b,at,l,l+width/21-.003,bottom,bottom+h*p,.038,.064,INK,name+' | lower relief skyline')


def display_bench(b,wall,lod):
    """One public exhibition bench visible in 2022, surveyed independently of the masonry."""
    def at(x,z,y):return (wall+x,y,z)
    y0,y1=10.43,12.19
    timber=BENCH_WOOD;iron=BENCH_IRON
    # The seat slats run along the lane; back boards follow the reclined iron ends.
    for n in range(5):
        x=.22+n*.079
        box(b,at,x,x+.071,.407+.005*abs(n-2),.442+.005*abs(n-2),y0,y1,timber,'Display bench | five seat slats')
    for n in range(4):
        z=.48+n*.093
        x=.232-(z-.47)*.29
        quad(b,at,[(x,z),(x+.029,z+.007),(x+.009,z+.085),(x-.02,z+.078)],y0,y1,timber,'Display bench | reclined back slats')
    def rib(points,cy,w,thick,label):
        sections=[]
        for i,(x,z) in enumerate(points):
            before,after=points[max(0,i-1)],points[min(len(points)-1,i+1)]
            dx,dz=after[0]-before[0],after[1]-before[1]
            length=hypot(dx,dz)
            nx,nz=-dz/length*thick/2,dx/length*thick/2
            sections.append([at(x-nx,z-nz,cy-w/2),at(x+nx,z+nz,cy-w/2),at(x+nx,z+nz,cy+w/2),at(x-nx,z-nz,cy+w/2)])
        rings(b,sections,iron,label)
    for j,y in enumerate((y0+.027,(y0+y1)/2,y1-.027)):
        name='Display bench | casting '+str(j+1)
        # Ferrules under the two end frames are visible against the pavement.
        if j!=1:
            rib([(.055,.020),(.080,.091),(.136,.172),(.258,.253),(.413,.276),(.526,.217),(.594,.123),(.636,.023)],y,.040,.048,name+' curved foot')
            rib([(.134,.806),(.158,.708),(.182,.606),(.211,.501),(.245,.413),(.365,.352),(.459,.336),(.567,.395)],y,.038,.044,name+' upright')
        rib([(.182,.508),(.180,.571),(.224,.622),(.310,.646),(.419,.646),(.506,.621),(.553,.571),(.562,.503),(.561,.443)],y,.035,.030,name+' arm bow')
        rib([(.209,.399),(.327,.367),(.451,.362),(.569,.403)],y,.037,.036,name+' seat strap')


def add_passage(b,lod=False,layout=None):
    """Add the corridor, using a distinct unlined envelope for the 2018 state."""
    if layout is None:layout=json.loads(Path(__file__).with_name('gatehouse-layout.json').read_bytes())
    source=layout.get('passage',{})
    portal=layout['portal']
    center=(portal['left']+portal['right'])/2
    p=source.get('bay_pitch',1.55)
    w=source.get('inner_clear_width',1.55*4.55/1.77198221136)
    start=source.get('decorated_start_y',.32)
    end=min(start+10*p,layout['tower_depth']-.15)
    floor=source.get('floor_z',0.)
    historic=str(layout.get('period','2022')).startswith('2018')
    left,right=(portal['left'],portal['right']) if historic else (center-w/2,center+w/2)
    top=portal['head'] if historic else source.get('soffit_z',2.46*p)
    def global_at(x,z,y):return(x,y,z+floor)
    span=layout['tower_depth']
    box(b,global_at,portal['left'],portal['right'],-.094,0,.045,span,PAVING,'Lane | continuous walked floor')
    if historic:
        box(b,global_at,left-.12,left,.0,top,.10,span,OLD,'2018 | west shaded passage')
        box(b,global_at,right,right+.12,.0,top,.10,span,OLD,'2018 | east shaded passage')
        box(b,global_at,left,right,top,top+.10,.10,span,OLD,'2018 | high soffit')
        return
    box(b,global_at,left,right,top,top+.12,start,end,CEILING,'Passage | soffit')
    for k,(y,frac) in enumerate(((.135,.18),(.318,.15),(.514,.13),(.713,.11),(.914,.12))):
        pos=start+(end-start)*y
        box(b,global_at,left,right,top-frac*p,top,pos-.11,pos+.11,CEILING,'Passage | transverse soffit joist '+str(k+1))
    display_bench(b,left,lod)
    for west in (True,False):
        wall=left if west else right
        sign=1 if west else -1
        name='West exhibit wall' if west else 'East exhibit wall'
        def at(y,z,d):return (wall+sign*d,y,floor+z)
        # A short splay joins the separate external brick portal to the renovated lining.
        foot=portal['left'] if west else portal['right']
        rings(b,[[(x,y,z+floor) for x,z in ((edge,0),(edge,high),(edge-sign*.10,high),(edge-sign*.10,0))]
                   for y,edge,high in ((.11,foot,portal['head']),(start,wall,top))],RENDER,name+' | entrance reveal')
        q=-p*.115 if west else 0.
        y0=start+q
        idx_window=3
        c=y0+(idx_window+.5)*p
        hole=None if west else (c-.301*p,c+.301*p,.869*p,1.766*p)
        wall_bricks(b,at,start,end,top,p,lod,hole,name)
        # Stagger the two rows of visible coarse stone along the foot of each wall.
        for row in range(2):
            n=0;step=.385*p;y=start-(step*.45 if row else 0)
            while y<end:
                z=.337*p*row/2
                box(b,at,max(start,y+.003),min(end,y+step-.004),z,z+.337*p/2-.006,.002,.054,
                    ROCK if (n+3*row)%5==1 else STONE,name+' | plinth course '+str(row+1))
                y+=step;n+=1
        first=0 if west else 2
        for i in range(first,10):
            c=y0+(i+.5)*p
            if c+.46*p>end+.22:continue
            label=('West' if west else 'East')+' bay '+str(i+1)
            arch(b,at,c,.385*p,.325*p,1.56*p,.091*p,-.001,lod,label)
            quad(b,at,[(c-.075*p,1.88*p),(c+.075*p,1.88*p),(c+.119*p,2.242*p),(c-.119*p,2.242*p)],
                 .045,.138,RENDER,label+' | keystone')
            if not west and i==idx_window:glass_window(b,at,c,p,lod,label)
            else:panel(b,at,c,p,i,west,lod,label)
            pier(b,at,y0+i*p,p,label)
            # Track fittings have a rectangular yoke and a round directional lamp.
            if i%2==0 or not lod:
                box(b,at,c-.015,c+.015,top-.22,top-.067,.030,.102,TRACK,label+' | light stem')
                tube=[]
                for h in (0.,.115):
                    cz=top-.21-h*.42
                    tube.append([at(c+.035*cos(j*2*pi/10),cz+.036*sin(j*2*pi/10),.082+h) for j in range(10)])
                rings(b,tube,TRACK,label+' | track light')
                rings(b,[tube[-1],[(x+sign*.005,y,z) for x,y,z in tube[-1]]],LENS,label+' | lens')
        pier(b,at,min(end-.012,y0+10*p),p,name+' | end pier')
        if not west:blue_register(b,at,start+.04*p,p,lod,'East red-history display')
        # A suspended slotted strip is visible above the keystones in both current views.
        track_low=2.227*p
        for k in range(3):
            z=track_low+k*.043*p
            box(b,at,start,end,z,z+.010*p,.102,.117,TRACK,name+' | perforated valance rails')
        step=(.145 if lod else .06)*p
        for j in range(int((end-start)/step)):
            y=start+j*step
            for k in range(2):
                x=y+k*step/2
                box(b,at,x,min(end,x+.012*p),track_low+k*.043*p,track_low+(k+1)*.043*p,.102,.117,TRACK,name+' | valance slot webs')
        for k in (1,3,5,7,9):
            y=start+k*p
            box(b,at,y-.008,y+.008,track_low+.085*p,top,.106,.122,TRACK,name+' | track hangers')
        box(b,at,start,end,top-.125,top-.044,-.022,.075,TRACK,name+' | continuous dark light rail')
        box(b,at,start,end,top-.045,top-.024,-.022,.086,SHADE,name+' | raised track lip')
