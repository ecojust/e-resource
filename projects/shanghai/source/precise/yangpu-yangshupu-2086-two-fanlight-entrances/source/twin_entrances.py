"""Street-side pair of fanlights, panelled leaves and rusticated surrounds at 2086 Yangshupu Road."""
from math import cos, pi, sin

def paint(rgb):
    return {'color':[(q/3294.6 if q<11 else ((q/255+.055)/1.055)**2.4) for q in rgb],'roughness':.82}

PALETTE={k:paint(v) for k,v in {
    'dark oak':(77,55,40),'oak panel':(103,74,45),'oak bevel':(130,96,61),'upper glass':(87,101,100),
    'fanlight iron':(53,54,50),'fanlight glass':(72,84,82),'brick shade':(128,73,57),'brick face':(148,85,65),
    'pale brick':(156,94,75),'mortar':(123,102,88),'rusticated stone':(155,145,128),
    'shadow stone':(131,124,112),'coping stone':(171,159,141),'sandstone':(161,147,128)
}.items()}

def block(b,x,z,y,w,h,d,mat,label):
    b.box((x,y,z),(w,d,h),mat,label=label)

def profile(b,points,front,back,mat,label):
    n=len(points)
    verts=[(x,y,z) for y in (front,back) for x,z in points]
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    faces.extend((i,n+i,n+(i+1)%n,(i+1)%n) for i in range(n))
    b.add(verts,faces,mat,label)

def sector(b,x,z,inner,outer,start,end,front,back,mat,label):
    def p(r,t):return (x+r*cos(t),z+r*sin(t))
    profile(b,[p(inner,start),p(outer,start),p(outer,end),p(inner,end)],front,back,mat,label)

def arc(b,x,z,inner,outer,front,back,mat,label,n=35):
    for j in range(n):
        sector(b,x,z,inner,outer,pi*j/n,pi*(j+1)/n,front,back,mat,label)

def left_and_right(b,lod,x,r,right):
    z=3.13
    key='photo right' if right else 'photo left'
    foot=.125 if right else .30
    door_top=2.80 if right else 2.76
    for leaf in (-1,1):
        width=r*.92
        cx=x+leaf*width/2
        block(b,cx,(foot+door_top)/2,.12,width-.016,door_top-foot,.10,'dark oak',key+' door leaf')
        for ix in (-1,1):
            px=cx+ix*width*.21
            block(b,px,foot+.555,.044,width*.335,.80,.068,'oak bevel',key+' raised lower panel')
            block(b,px,foot+.555,-.003,width*.254,.672,.035,'oak panel',key+' inset lower panel')
        pane_top=door_top-.102
        pane_bottom=1.59 if right else 1.62
        for col in range(3):
            for row in range(3):
                pw=(width-.11)/3;ph=(pane_top-pane_bottom)/3
                px=cx-width/2+.055+(col+.5)*pw
                pz=pane_bottom+(row+.5)*ph
                block(b,px,pz,.061,pw-.026,ph-.031,.027,'upper glass',key+' three by three glazing')
        for edge in (-1,1):
            block(b,cx+edge*(width*.5-.039),(foot+door_top)/2,.046,.062,door_top-foot,.080,'oak panel',key+' door stile')
        block(b,cx,pane_bottom-.061,.031,width,.092,.065,'oak panel',key+' middle rail')
    for j in range(35 if not lod else 21):
        n=35 if not lod else 21
        t=pi*j/n;u=pi*(j+1)/n
        profile(b,[(x,z),(x+r*cos(t),z+r*sin(t)),(x+r*cos(u),z+r*sin(u))],.125,.17,'fanlight glass',key+' glazed semicircle')
    for ir,orr,mat in ((.938,1.003,'fanlight iron'),(.61,.637,'fanlight iron'),(.202,.229,'fanlight iron'),
                        (1.012,1.052,'sandstone')):
        arc(b,x,z,ir*r,orr*r,.012,.085,mat,key+' concentric fanlight rib',28 if lod else 48)
    for angle in (pi*.118,pi*.265,pi*.402,pi*.57,pi*.723,pi*.859):
        lo=.222*r if .25*pi<angle<.75*pi else .624*r
        b.tube([(x+lo*cos(angle),.027,z+lo*sin(angle)),(x+.951*r*cos(angle),.027,z+.951*r*sin(angle))],.017,'fanlight iron',6 if lod else 10,key+' radial glazing bar')
    count=33 if right else 29
    for j in range(count):
        a=pi*(j+.06)/count;c=pi*(j+.94)/count
        sector(b,x,z,r*1.056,r*1.219,a,c,-.017,.12,('pale brick','brick face','brick shade','brick face')[j%4],key+' arch radial brick')
    arc(b,x,z,1.048*r,1.23*r,.025,.23,'mortar',key+' arch mortar bed',45 if not lod else 25)
    # The pale inverted keystone projects below the panel over each arch.
    profile(b,[(x-.122*r,z+1.064*r),(x+.114*r,z+1.064*r),(x+.172*r,z+1.49*r),(x-.168*r,z+1.49*r)],-.070,.115,'rusticated stone',key+' large keystone')
    n=44 if not lod else 25
    for j in range(n):
        a=pi*j/n;c=pi*(j+1)/n
        xx=x+r*1.23*cos(a);yy=x+r*1.23*cos(c)
        top=z+1.53*r
        profile(b,[(xx,z+r*1.23*sin(a)),(xx,top),(yy,top),(yy,z+r*1.23*sin(c))],.035,.30,'brick face',key+' masonry spandrel')
    # Dark jambs and a transom lining close the small gap between wood and stone.
    block(b,x,(z+door_top)/2,.18,2.13*r,z-door_top,.105,'dark oak',key+' deep transom lining')
    for side in (-1,1):
        block(b,x+side*r*.982,(foot+door_top)/2,.171,r*.19,door_top-foot,.115,'dark oak',key+' inner jamb lining')
    # The stretcher courses stop against the radial brick ring; the lowest courses are cut back.
    ring=1.227*r
    red=('brick face','pale brick','brick shade','brick face','brick face')
    for j in range(30):
        low=foot+j*.145
        if low>z+1.485*r:break
        high=min(z+1.50*r,low+.137)
        for side in (-1,1):
            chord=(max(0,ring**2-max(0,low-z)**2))**.5 if low>=z else r*1.012
            clear=chord+.010
            far=1.247*r
            for k in range(9):
                l=max(clear,k*.222+(j%2)*.111+.002)
                h=min(far,(k+1)*.222+(j%2)*.111-.003)
                if h-l>.015:
                    block(b,x+side*(l+h)/2,(low+high)/2,.022,h-l,high-low,.024,red[(j+2*k+side)%5],key+' horizontal narrow red brick')
    for side in (-1,1):
        block(b,x+side*(r*1.12),(z+foot)/2,.14,r*.24,z-foot,.30,'brick face',key+' door reveal')
    if right:
        for side in (-1,1):
            block(b,x+side*r*1.015,(foot+2.86)/2,-.041,r*.19,2.86-foot,.24,'sandstone',key+' full height stone casing')
            block(b,x+side*r*.995,2.54,-.164,r*.14,.41,.20,'shadow stone',key+' square lintel bracket')
        block(b,x,2.866,-.108,2.41*r,.205,.36,'sandstone',key+' overhanging lower lintel')
        block(b,x,3.045,-.135,2.54*r,.164,.43,'coping stone',key+' projecting flat hood')
    else:
        block(b,x,2.91,-.008,2.06*r,.227,.20,'shadow stone',key+' straight inner lintel')
        block(b,x,3.075,-.061,2.14*r,.088,.263,'coping stone',key+' narrow transom shelf')
    block(b,x,foot-.046,-.10,2.2*r,.092,.66,'sandstone',key+' door sill')
    if not right:
        block(b,x,foot-.17,-.27,2.28*r,.145,.76,'coping stone',key+' street step')

def add_building(b,lod=False):
    left_and_right(b,lod,-1.69,.94,False)
    left_and_right(b,lod,1.65,1.025,True)
    for x,width in ((-3.21,.67),(-.075,.66),(3.23,.61)):
        for i in range(13):
            block(b,x,.205+.387*i,.103,width,.361,.42,'rusticated stone','jointed stone pier '+str(i+1))
    for cx,half,side in ((-1.69,.94,False),(1.65,1.025,True)):
        for sx in (-1,1):
            edge=cx+sx*half*1.225
            block(b,edge,2.70,.190,.23,4.28,.27,'brick face','red side pier')
