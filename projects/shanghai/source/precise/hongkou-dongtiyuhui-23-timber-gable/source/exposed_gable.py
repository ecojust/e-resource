"""Timber frame, central upper light and four curved braces on No. 23, Lane 119."""
import math


def finish(rgb,rough):
    return dict(color=[c/3294.6 if c<=10 else ((c/255+.055)/1.055)**2.4 for c in rgb],roughness=rough,metallic=0)


PALETTE={k:finish(c,r)for k,c,r in [('infill',(180,172,154),.94),('warm timber',(140,88,73),.94),
 ('worn timber',(158,108,94),.92),('barge fascia',(191,180,166),.90),('dark drip',(125,119,101),.85),
 ('eave soffit',(162,157,138),.88),('wood frame',(142,110,93),.92),('window glass',(123,131,123),.36),
 ('light brick',(176,127,88),.92),('dun brick',(159,106,76),.92),('mortar',(155,133,106),.94)]}


def plate(b,outline,y0,y1,mat,name):
    verts=[(x,y,z)for y in (y0,y1)for x,z in outline];n=len(outline)
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,n+(i+1)%n,n+i)for i in range(n))
    b.add(verts,faces,mat,name)


def strip(b,start,end,width,front,back,mat,name):
    x,z=start;xx,zz=end;length=math.hypot(xx-x,zz-z)
    nx=-(zz-z)*width/(2*length);nz=(xx-x)*width/(2*length)
    plate(b,[(x+nx,z+nz),(x-nx,z-nz),(xx-nx,zz-nz),(xx+nx,zz+nz)],front,back,mat,name)


def rect(b,l,r,z0,z1,front,back,mat,name):
    plate(b,[(l,z0),(r,z0),(r,z1),(l,z1)],front,back,mat,name)


def brace(b,side,x0,z0,length,height,segments,name):
    # Narrow solid haunch. Under its curved lower face the pale triangular infill remains visible.
    for i in range(segments):
        a=math.pi*i/(2*segments);c=math.pi*(i+1)/(2*segments)
        lo=(x0+side*length*(1-math.sin(a)),z0+height*(1-math.cos(a)))
        hi=(x0+side*length*(1-math.sin(c)),z0+height*(1-math.cos(c)))
        # Material occupies the corner above the arc on the post side.
        # Reflect the triangle to put the point against its post, keeping the arc open.
        outer=(x0,z0)
        plate(b,[outer,lo,hi],-.055,.012,'warm timber',name)


def add_building(b,lod=False):
    width=2.03;peak=1.87
    def line(x):return peak-abs(x)*peak/width
    # The small rectangular opening stops under the horizontal collar tie.
    opening=.251;lo=.537;hi=1.104
    for l,r in ((-width,-opening),(opening,width)):
        plate(b,[(l,0),(r,0),(r,line(r)),(l,line(l))],.016,.245,'infill','plastered flank of the gable')
    rect(b,-opening,opening,0,lo,.016,.245,'infill','pale inset below the upper light')
    plate(b,[(-opening,hi),(opening,hi),(opening,line(opening)),(0,peak),(-opening,line(opening))],.016,.245,'infill','infill over the central light')
    rect(b,-opening,opening,lo,hi,.062,.082,'window glass','single central glazed casement')
    for x in (-opening+.019,opening-.019):
        rect(b,x-.019,x+.019,lo,hi,-.017,.071,'wood frame','central casement jamb')
    for z in (lo+.027,hi-.027):
        rect(b,-opening,opening,z-.027,z+.027,-.022,.071,'wood frame','central casement rails')
    rect(b,-width,width,-.118,.018,-.077,.253,'worn timber','timber plate over red masonry')
    for side in (-1,1):
        for x in (.274,.77,1.35):
            u=side*x
            strip(b,(u,0),(u,line(u)-.024),.076,-.048,.049,'warm timber','visible upright '+str(u))
        strip(b,(side*.77,line(.77)-.059),(side*.318,.55),.080,-.061,.05,'worn timber','upper diagonal to the middle')
        strip(b,(side*.318,.55),(side*.77,.027),.080,-.061,.05,'warm timber','lower diagonal to the foot')
        brace(b,side,side*1.34,.023,.37,.22,7 if lod else 21,'lower incurved bracket')
        brace(b,side,side*.038,1.155,.31,.225,7 if lod else 21,'incurved bracket under apex')
        # Shallow overhang has a separate underside, a weathered front board and a cap projecting beyond it.
        strip(b,(side*2.19,-.028),(0,2.05),.135,-.300,.317,'eave soffit','projecting rake soffit')
        strip(b,(side*2.19,.024),(0,2.101),.109,-.337,-.257,'barge fascia','broad painted bargeboard')
        strip(b,(side*2.207,.083),(0,2.174),.046,-.357,-.255,'dark drip','upper drip of the rake')
    strip(b,(-.79,1.143),(.79,1.143),.084,-.066,.052,'warm timber','continuous collar below apex')
    strip(b,(0,1.16),(0,1.865),.082,-.055,.049,'warm timber','short timber below the ridge')
    rect(b,-2.01,2.01,-.40,-.113,0,.26,'mortar','cut wall below gable')
    for course in range(3):
        l=-2.01-(.10 if course%2 else 0)
        j=0
        while l<2.01:
            a=max(-2.01,l);c=min(2.01,l+.238)
            if c-a>.012:
                rect(b,a+.003,c-.003,-.394+course*.093,-.307+course*.093,-.013,.011,'light brick' if (course+j)%4 else 'dun brick','exposed brick under the plate')
            j+=1;l+=.238
