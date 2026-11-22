"""Courtyard entrances marked 9 and 11 in Gao Can 88's photographs of Lane 225.

The reference appearance is July 2015. The unpainted No. 9 arch in the
December 2012 photograph supplies the construction behind the white finish.
Coordinates are metres. Positive Y points into the house.
"""
from math import sin, cos, pi
import numpy as np

WHITE='Courtyard door | white painted brick'
LIP='Courtyard door | pale moulding'
JOINT='Courtyard door | shallow painted joints'
RED='Courtyard door | fired red brick'
RED2='Courtyard door | dull red recessed face'
LIGHT='Courtyard door | rubbed terracotta'
DEEP='Courtyard door | recessed carving'
FRAME='Courtyard door | dark timber'
IRON='Courtyard door | gate iron'
GLASS='Courtyard door | No.9 dimpled glazing'
PANE='Courtyard door | No.11 surviving light pane'
BLADES='Courtyard door | No.11 dark horizontal slats'
SIGN='Courtyard door | enamel green plate'
INK='Courtyard door | painted sign white'
STONE='Courtyard door | worn grey step'
PALETTE={k:{'color':rgb,'roughness':rough} for k,rgb,rough in [
    (WHITE,[.78,.752,.677],.90),(LIP,[.83,.805,.729],.85),(JOINT,[.665,.643,.587],.91),
    (RED,[.153,.060,.044],.92),(RED2,[.113,.048,.038],.95),(LIGHT,[.224,.091,.067],.89),
    (DEEP,[.090,.030,.024],.90),(FRAME,[.041,.026,.021],.74),(IRON,[.059,.050,.039],.73),
    (GLASS,[.059,.061,.052],.53),(PANE,[.119,.098,.081],.38),(BLADES,[.045,.036,.029],.8),
    (SIGN,[.063,.27,.203],.57),(INK,[.833,.833,.696],.65),(STONE,[.301,.292,.264],.93)]}
PALETTE[PANE]['alpha']=.90
PALETTE[GLASS]['alpha']=.94

# Values are relative to the clear width across No.9's timber transom. Each row
# records its own threshold, opening, impost, head, blind arch and panel.
DOORS=[
    dict(number=9,axis=0.,half=.544,foot=0.,spring=1.88,rise=.659,
         plaque=1.96,shoulder=2.43,top=3.10,panel_bottom=3.11,panel_top=3.48,
         blind_base=3.55,blind_rise=.257,spandrel=.404),
    dict(number=11,axis=2.515,half=.636,foot=-.113,spring=1.921,rise=.679,
         plaque=2.002,shoulder=2.50,top=3.19,panel_bottom=3.20,panel_top=3.58,
         blind_base=3.64,blind_rise=.274,spandrel=.417),
]


def _settings(layout):
    layout=layout or {}
    return (float(layout.get('door9_clear_width',1.43)),
            float(layout.get('door9_axis_x',0.)),
            float(layout.get('door9_threshold_z',0.)),float(layout.get('door_wall_y',0.)))


def door_openings(layout=None):
    """Boundary of the cut through the common façade, viewed from the court."""
    w,x0,z0,_=_settings(layout)
    result=[]
    for d in DOORS:
        x=x0+d['axis']*w;z=z0+d['spring']*w
        rx=d['half']*w;rz=d['rise']*w;bottom=z0+d['foot']*w
        outline=[(x-rx,bottom),(x+rx,bottom)]
        outline.extend((x+rx*cos(t),z+rz*sin(t)) for t in np.linspace(0,pi,49))
        result.append(dict(number=d['number'],center_x=x,bottom=bottom,spring_z=z,
                           radius_x=rx,radius_z=rz,outline_xz=outline))
    return result


def _triangulate(loop):
    """Ear clipping for the simple, occasionally concave, moulding profiles."""
    p=np.asarray(loop,float);n=len(p)
    cross=lambda a,b:a[0]*b[1]-a[1]*b[0]
    area=sum(cross(a,b)for a,b in zip(p,np.roll(p,-1,axis=0)))
    ids=list(range(n)) if area>0 else list(reversed(range(n)));faces=[]
    while len(ids)>3:
        for j,b in enumerate(ids):
            a,c=ids[j-1],ids[(j+1)%len(ids)]
            if cross(p[b]-p[a],p[c]-p[b])<1e-10:continue
            def inside(i):
                return min(cross(p[v]-p[u],p[i]-p[u]) for u,v in ((a,b),(b,c),(c,a)))>=-1e-10
            if any(inside(i) for i in ids if i not in (a,b,c)):continue
            faces.append([a,b,c]);ids.pop(j);break
        else:raise ValueError(('invalid moulding',loop))
    faces.append(ids)
    if area<0:faces=[v[::-1]for v in faces]
    return faces


def add_entrances(b,lod,layout=None):
    """Append the two separately editable portals, fanlights and visible steps."""
    w,x0,z0,y0=_settings(layout);far=lod is True or lod=='lod';b.palette.update(PALETTE)
    for d in DOORS:
        no=d['number'];cx=d['axis'];rx=d['half'];spring=d['spring'];rise=d['rise'];foot=d['foot']
        def part(xyz,faces,mat,name):
            p=np.array(xyz,dtype=float);p[:,0]+=cx;p=p*w+np.array([x0,y0,z0]);f=np.asarray(faces,int)
            tri=p[f];v=np.sum(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])))
            if v<0:f=f[:,::-1]
            b.add(p,f.tolist(),mat,label=f'Courtyard {no} | {name}')
        def prism(loop,yfront,yback,mat,name):
            p=np.array(loop,float);n=len(p);faces=_triangulate(loop)
            front=np.column_stack([p[:,0],np.full(n,yfront),p[:,1]])
            back=front.copy();back[:,1]=yback
            shell=faces+[list(reversed([j+n for j in f]))for f in faces]
            for i in range(n):
                j=(i+1)%n;shell.extend(([i,i+n,j+n],[i,j+n,j]))
            part(np.vstack([front,back]),shell,mat,name)
        def rect(left,right,low,high,yfront,yback,mat,name):
            prism([(left,low),(right,low),(right,high),(left,high)],yfront,yback,mat,name)
        def ring(x,z,ix,iz,ox,oz,start,end,front,back,mat,name,count):
            ang=np.linspace(start,end,count+1)
            loop=[(x+ox*cos(t),z+oz*sin(t))for t in ang]
            loop.extend((x+ix*cos(t),z+iz*sin(t))for t in ang[::-1])
            prism(loop,front,back,mat,name)
        def ribbon(points,width,depth,mat,name,samples=6):
            points=np.asarray(points);t=np.linspace(0.,1.,samples)[:,None]
            def cubic(a,b,c,e):
                return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t**2*c+t**3*e
            curve=np.vstack([cubic(*points[i:i+4])[(1 if i else 0):] for i in range(0,len(points)-3,3)])
            gradient=np.gradient(curve,axis=0);gradient/=np.linalg.norm(gradient,axis=1)[:,None]
            side=np.column_stack([-gradient[:,1],gradient[:,0]])
            sections=6 if far else 10
            vertices=[];faces=[]
            for j,(pt,normal)in enumerate(zip(curve,side)):
                if callable(width):radius=width(j/(len(curve)-1))
                else:radius=width
                for k in range(sections):
                    t=2*pi*k/sections;q=pt+radius*cos(t)*normal
                    vertices.append([q[0],depth-radius*.78*sin(t),q[1]])
            for j in range(len(curve)-1):
                for k in range(sections):
                    a=j*sections+k;c=j*sections+(k+1)%sections
                    faces.extend(([a,c,c+sections],[a,c+sections,a+sections]))
            for i in range(1,sections-1):faces.extend(([0,i+1,i],[(len(curve)-1)*sections,(len(curve)-1)*sections+i,(len(curve)-1)*sections+i+1]))
            part(vertices,faces,mat,name)
        def straight(a,e,r,y,mat,name):
            a=np.asarray(a);e=np.asarray(e);v=e-a
            ribbon([a,a+v/3,a+2*v/3,e],r,y,mat,name,3)
        # Faces of the visible arch, including the lower soffit and the splayed
        # upper shoulders. The straight side walls are supplied by the caller.
        lip=.063;edge=.198;outer=rx+edge;shoulder=d['shoulder'];cap=d['top'];ch=.385 if no==9 else .425
        def top(x):
            ax=abs(x)
            if ax<=ch:return cap
            if ax<=outer:return cap+(shoulder-cap)*(ax-ch)/(outer-ch)
            return shoulder
        divisions=22 if far else 38;angs=np.linspace(0,pi,divisions+1)
        for j,(t,u)in enumerate(zip(angs,angs[1:])):
            outer_x,outer_x2=outer*cos(t),outer*cos(u)
            a=(rx*cos(t),spring+rise*sin(t));aa=(rx*cos(u),spring+rise*sin(u))
            dd=(outer_x,top(outer_x));cc=(outer_x2,top(outer_x2))
            prism([a,dd,cc,aa],-.19,.024,WHITE,'radial masonry and soffit')
            if not far and j and j!=divisions//2:
                norm=.0023;line=np.array(dd)-a;side=norm*np.array([-line[1],line[0]])/np.linalg.norm(line)
                prism([a-side,dd-side,dd+side,a+side],-.1908,-.186,JOINT,'painted radial joints')
        ring(0,spring,rx,rise,rx+.018,rise+.018,0,pi,-.204,-.185,LIP,'inner archivolt',22 if far else 38)
        for sign in [-1,1]:
            side=[(sign*(outer+.022),spring-.087),(sign*(outer+.022),shoulder-.047),(sign*(ch+.005),cap-.045),
                  (sign*.002,cap-.045),(sign*.002,cap+.013),(sign*(ch+.033),cap+.013),
                  (sign*(outer+.065),shoulder-.012),(sign*(outer+.065),spring-.087)]
            prism(side,-.220,-.184,LIP,'shoulder coping')
            if not far:
                pts=[(sign*(outer+.066),shoulder-.014),(sign*(ch+.037),cap+.014)]
                straight(*pts,.009,-.214,WHITE,'outer coping bead')
            # A stepped jamb, a rounded boss below the impost and the spiral
            # ending of the raised contour are distinct in both exposures.
            l=rx;r=outer+.035
            corners=[(l,foot),(r+.128,foot),(r+.128,spring-.985),(r+.042,spring-.794),
                     (r+.077,spring-.735),(r+.077,spring-.668),(r,spring-.647),
                     (r,spring-.08),(r+.018,spring+.073),(l,spring+.073)]
            prism([(sign*x,z)for x,z in corners],-.113,.014,WHITE,'jamb pier and stopped bolster')
            mid=sign*(outer+.022);z=spring+.065;rr=.126
            loop=[(mid+rr*cos(t),z+rr*sin(t))for t in np.linspace(0,2*pi,19 if far else 33)[:-1]]
            prism(loop,-.215,-.108,WHITE,'volute boss')
            trace=[];steps=21 if far else 42
            for k in range(steps):
                t=k/(steps-1);angle=.54*pi+t*2.67*pi;r0=.112*(1-t)+.009*t
                trace.append((mid+sign*r0*cos(angle),z+r0*sin(angle)))
            for a,e in zip(trace,trace[1:]):straight(a,e,.011,-.221,LIP,'scroll of impost')
        prism([(-.089,cap+.012),(.089,cap+.012),(.060,spring+rise-.016),(-.064,spring+rise-.016)],-.232,-.187,LIP,'central keystone')
        # The blind brick half-round under the upstairs sill is separate from the
        # occupied fanlight below. Its inset panel retains visible brick courses.
        z=d['blind_base'];ax=.266 if no==9 else .278;az=d['blind_rise'];bw=d['spandrel']
        left=-bw;right=bw
        rect(left,right,z-.214,z+az+.145,-.063,.021,RED,'brick spandrel below window sill')
        loop=[(-ax,z),(ax,z)]+[(ax*cos(t),z+az*sin(t))for t in np.linspace(.01,pi-.01,27)]
        prism(loop,-.073,-.060,RED2,'shallow blind tympanum')
        for h in np.arange(.036,az,.049):
            lim=ax*np.sqrt(max(1-(h/az)**2,0))
            if lim>.02:rect(-lim,lim,z+h-.0028,z+h+.0028,-.0745,-.072,DEEP,'recessed horizontal brick bed')
        n=14 if far else 27
        for a,e in zip(np.linspace(0,pi,n+1)[:-1],np.linspace(0,pi,n+1)[1:]):
            ring(0,z,ax,az,ax+.080,az+.078,a+.002,e-.002,-.117,-.069,RED,'radial hood bricks',1)
        ring(0,z,ax+.018,az+.017,ax+.031,az+.029,0,pi,-.125,-.115,LIGHT,'inner bead of blind hood',n)
        rect(-bw-.017,bw+.017,z+az+.117,z+az+.147,-.101,-.061,RED,'window sill drip')
        z1=d['panel_bottom'];z2=d['panel_top'];h=z2-z1;px=.273 if no==9 else .297
        profile=[(-px-.062,z1),(px+.062,z1),(px+.041,z1+.06),(px+.020,z2-.065),(px+.055,z2),(-px-.055,z2),(-px-.020,z2-.065),(-px-.041,z1+.06)]
        prism(profile,-.145,-.060,RED,'tapered carved panel body')
        rect(-px,px,z1+.024,z2-.046,-.148,-.143,DEEP,'recess behind carved foliage')
        for k in range(3):
            over=.027+.012*k
            rect(-px-over,px+over,z2-.045+k*.023,z2-.020+k*.023,-.155-.009*k,-.14,RED if k!=1 else LIGHT,'three projecting cornice courses')
        # Mirrored acanthus branches traced from the small spandrel over No.9 and
        # cross-checked against its separate No.11 companion. The central leaf
        # droops onto a small palmette. The panel on the adjoining gable is larger.
        def fol(x,v,sgn):return (sgn*x*px,z1+.029+v*(h-.080))
        def ivy(controls,thick,sgn,name):
            curve=[fol(x,y,sgn)for x,y in controls];ribbon(curve,lambda t:thick*(.25+.75*sin(pi*t)**.66),-.160,RED if sgn==1 else LIGHT,name,5 if far else 9)
        def leaflet(start,mid,end,width,sign,name):
            a,m,e=[np.array(fol(u,v,sign))for u,v in (start,mid,end)]
            points=[];sections=5 if far else 8
            for t in np.linspace(.025,.975,sections):
                c=(1-t)**2*a+2*(1-t)*t*m+t*t*e
                tangent=(1-t)*(m-a)+t*(e-m);normal=np.array([-tangent[1],tangent[0]])/np.linalg.norm(tangent)
                half=width*(sin(pi*t)**.68)*(1-.32*t)
                # The upper half of each tapered sprig curls away from the panel
                # and the centre rib projects farthest beneath the high light.
                l,r=c-normal*half,c+normal*half
                points.extend([[l[0],-.164,l[1]],[c[0],-.170-.023*sin(pi*t),c[1]],
                               [r[0],-.165,r[1]],[c[0],-.152,c[1]]])
            faces=[]
            for i in range(sections-1):
                for k in range(4):
                    a=i*4+k;e=i*4+(k+1)%4
                    faces.extend(([a,e,e+4],[a,e+4,a+4]))
            faces.extend(([0,2,1],[0,3,2],[len(points)-4,len(points)-3,len(points)-2],
                          [len(points)-4,len(points)-2,len(points)-1]))
            part(points,faces,LIGHT if name.endswith('upper lobe') else RED,name)
        for sign in [-1,1]:
            leaflet((.16,.54),(.19,.93),(.61,.85),.032,sign,'curled upper lobe')
            leaflet((.35,.73),(.53,.87),(.74,.60),.029,sign,'drooping acanthus point')
            leaflet((.29,.61),(.37,.69),(.50,.49),.025,sign,'short inward lobe')
            leaflet((.10,.14),(.25,.41),(.44,.41),.029,sign,'palmette lateral lobe')
            leaflet((.015,.065),(.19,-.01),(.24,.12),.024,sign,'palmette base')
            ivy([(0,.18),(.19,.15),(.08,.95),(.48,.84),(.68,.79),(.81,.89),(.94,.88)],.025,sign,'upper sweeping acanthus stem')
            ivy([(.18,.52),(.15,.89),(.48,.99),(.72,.77)],.017,sign,'tip of high acanthus leaf')
            ivy([(.29,.64),(.51,.89),(.55,.72),(.71,.60)],.025,sign,'lower carved leaf lobe')
            ivy([(.85,.89),(.97,.86),(.95,.69),(.84,.69)],.012,sign,'upper outside return')
            ivy([(.96,.45),(.93,.13),(.45,.03),(.47,.33),(.48,.49),(.78,.53),(.74,.35),(.70,.26),(.62,.32),(.64,.39)],.021,sign,'turned lower scroll')
            ivy([(.23,.26),(.29,.47),(.43,.51),(.46,.45)],.014,sign,'central fan leaflet')
            ivy([(.02,.07),(.19,-.018),(.22,.08),(.25,.16)],.021,sign,'palmette lower lobe')
            ivy([(.92,.22),(.84,.16),(.79,.06),(.91,.015)],.014,sign,'outer lower leaf')
        # Stained timber fan, three radii and its half-round centre. Photograph 08
        # resolves horizontal slats on the outer lights of the No.11 transom.
        fx=rx-.036;fz=rise-.076;fy=.081
        for s in [-1,1]:
            l,r=sorted([s*rx,s*(rx-.041)])
            rect(l,r,foot,spring+.018,fy,fy+.048,FRAME,'vertical door lining')
        rect(-rx,rx,spring-.078,spring+.026,fy-.017,fy+.060,FRAME,'transom')
        rect(-rx+.014,rx-.014,spring+.016,spring+.037,fy-.021,fy+.005,FRAME,'upper transom bead')
        rect(-rx+.014,rx-.014,spring-.086,spring-.067,fy-.021,fy+.005,FRAME,'lower transom bead')
        ring(0,spring,fx,fz,rx,rise,0,pi,fy,fy+.048,FRAME,'timber fan frame',18 if far else 32)
        small=.116
        for a,e in zip(np.linspace(0,pi,5)[:-1],np.linspace(0,pi,5)[1:]):
            ring(0,spring,small,small,fx,fz,a,e,fy+.029,fy+.041,GLASS if no==9 else PANE,'four fanlight sectors',7 if far else 10)
        for t in [pi/4,pi/2,3*pi/4]:
            straight((small*cos(t),spring+small*sin(t)),(fx*cos(t),spring+fz*sin(t)),.0105,fy+.008,FRAME,'fanlight radial glazing bar')
        loop=[(-small,spring),(small,spring)]+[(small*cos(t),spring+small*sin(t))for t in np.linspace(.01,pi-.01,19)]
        prism(loop,fy+.029,fy+.041,GLASS if no==9 else RED2,'central semi-disc')
        ring(0,spring,small-.004,small-.004,small+.013,small+.013,0,pi,fy-.002,fy+.044,FRAME,'semicircular fan centre',16 if far else 24)
        if no==11:
            for s in [-1,1]:
                for h in [.08,.15,.22,.29,.36,.43]:
                    l=max(h*fx/fz,small+.015);r=fx*np.sqrt(max(0.,1-(h/fz)**2))
                    if l+.018<r:
                        a,c=sorted([s*l,s*r]);rect(a,c,spring+h-.008,spring+h+.008,fy+.020,fy+.029,BLADES,'horizontal outer-light slats')
        # The plate lies directly over the transom. Numerals follow the two
        # photographed porcelain signs, keeping the unequal No.9 and No.11 plates.
        sw=.102 if no==9 else .116;sz=spring+(.087 if no==9 else .082);sy=fy-.033
        plate_x=.123 if no==9 else .061
        rect(plate_x-sw,plate_x+sw,sz-.070,sz+.070,sy,sy+.009,SIGN,'green number plate')
        if no==9:
            ribbon([(plate_x+dx,sz+dy) for dx,dy in [(.025,.024),(.024,+.082),(-.041,+.060),(-.023,+.025),(-.013,+.003),(.023,+.009),(.025,+.036),(.030,+.010),(.005,-.016),(-.020,-.013)]],.006,sy-.005,INK,'plate number nine',8)
        else:
            for x in [plate_x-.027,plate_x+.025]:
                straight((x-.009,sz+.043),(x,sz+.052),.0055,sy-.005,INK,'plate number eleven')
                straight((x,sz+.052),(x,sz-.011),.006,sy-.005,INK,'plate number eleven')
                straight((x-.011,sz-.013),(x+.012,sz-.013),.0055,sy-.005,INK,'plate number eleven')
        # Hand-drawn, seven-character lower line on both photographed address
        # plates. Use stroke centrelines so the lettering remains editable.
        glyphs={
            '武':['12 42','04 74','51 63 66 77','71 72','24 27','25 45','06 36'],
            '进':['31 36 27','61 66','23 73','25 75','01 12','03 13 15 06 27 77'],
            '路':['01 21 23 03 01','13 16','14 24','05 07 26','52 61','42 62 53 34','43 65 75','45 75 77 47 45'],
            '二':['13 63','06 76'],'五':['11 71','42 25','23 63 65','06 76'],
            '弄':['11 71','22 62','41 44','14 74','06 76','35 37 27','55 57']}
        text='武进路二二五弄';gw=sw*.234;gh=.040
        for ci,ch in enumerate(text):
            for sequence in glyphs[ch]:
                pts=[(plate_x+(ci-3.45)*gw+int(v[0])*gw/8,sz-.030-int(v[1])*gh/8)for v in sequence.split()]
                for (ax,az),(bx,bz) in zip(pts,pts[1:]):
                    dx,dz=bx-ax,bz-az;length=np.hypot(dx,dz)
                    nx,nz=-dz/length*.00135,dx/length*.00135
                    prism([(ax+nx,az+nz),(bx+nx,bz+nz),(bx-nx,bz-nz),(ax-nx,az-nz)],
                          sy-.0018,sy-.0003,INK,'plate 武进路二二五弄')
        # Recessed, visible gate on the left; the right doorway was open on the
        # dated 2015 exposure. Its four visible nosings terminate at the threshold.
        if no==9:
            recess=.32
            for t in np.linspace(-.90,.90,9):
                x=fx*t;rect(x-.005,x+.005,foot+.035,spring-.100,recess-.023,recess-.009,IRON,'recessed gate bars')
            for h in [.060,1.38,spring-.14]:
                rect(-fx,fx,foot+h-.009,foot+h+.009,recess-.023,recess-.005,IRON,'recessed gate rails')
        for k in range(2 if no==9 else 4):
            height=.104;drop=height*k;run=(.211 if no==11 else .180)*(k+1)
            rect(-rx-.031,rx+.031,foot-drop-height,foot-drop,-run,-.008,STONE,'threshold and stair nosings')
