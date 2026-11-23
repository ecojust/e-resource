"""The garden return with two open galleries, a pierced parapet and three brick arches."""
import math
import numpy as np
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union

B='warm red facing brick';P='pale precast cement';M='coarse grey-brown pebble dash';W='deep green window joinery';G='dark casement glass';T='terracotta roof';D='dark cast rainwater iron'
def arch(center,half,spring,rise,n):
    curve=[(center+half*math.cos(t),spring+rise*math.sin(t)) for t in np.linspace(0,math.pi,n)]
    return Polygon([(center-half,-.03),(center+half,-.03),*curve])
def make(builder,lod):
    b=builder
    def side(shape,lo,hi,mat,label):
        b.prism(shape,lo,hi,lambda y,z,x:(x,y,z),mat,label)
    L=8.04;start=.26;face=7.38;edge=9.00
    col=[.40,2.95,5.46,7.87]
    # The two open storeys share four pilasters. Each horizontal recessed
    # course turns the visible corner; its shallow joint is part of the section.
    for i,y in enumerate(col):
        if i:
            b.box((face-.24,y,4.956),(.48,.54,6.19),B,label=f'garden piers/pier {i+1}')
        for k,z in enumerate(np.arange(1.97,7.99,.336)):
            width=.052;outer=.013 if k%2 else .010
            b.box((face+outer/2,y,z),(.043,.541,width),B,label=f'garden pier {i+1}/course {k+1:02}')
    # The back wall carries the shadow line behind the open balustrade.
    # Glazing on the rear wall is visible in the three upper bays, behind the railing.
    ymid=(start+L)/2;length=L-start
    for floor,z in [('lower',2.26),('upper',5.19)]:
        b.box((5.92,ymid,z+.82),(.24,length,1.64),M,label='gallery rear/'+floor+' solid apron')
        wall=box(start,z+1.58,L,z+2.96)
        for i,(a,c) in enumerate(zip(col,col[1:])):
            mid=(a+c)/2;window=box(mid-.58,z+1.65,mid+.58,z+2.75);wall=wall.difference(window)
            side(window.difference(window.buffer(-.042,join_style='mitre')),5.82,6.00,W,f'gallery rear {floor}/window {i+1} frame')
            side(window.buffer(-.039,join_style='mitre'),5.806,5.825,G,f'gallery rear {floor}/window {i+1} glass')
            b.box((5.995,mid,z+2.20),(.047,.027,1.05),W,label=f'gallery rear {floor}/window {i+1} mullion')
        side(wall,5.80,6.04,M,'gallery rear/'+floor+' openings')
    # A narrow terrace stands in front of the lower gallery and turns around
    # its near corner. Both the upper level and the terrace have actual openings.
    b.box((7.44,ymid,2.29),(3.12,length,.185),P,label='terrace/projecting floor above the three arches')
    b.box((6.66,ymid,5.17),(1.54,length,.205),P,label='upper gallery/projecting floor')
    for i,(a,c) in enumerate(zip(col,col[1:])):
        for floor,base,x in [('terrace',2.387,edge-.055),('upper gallery',5.28,face-.115)]:
            rail=box(a+.012,base,c-.012,base+.565)
            left=a+.15;right=c-.15
            for j in range(7):
                y=left+(j+.5)*(right-left)/7
                rail=rail.difference(box(y-.046,base+.229,y+.046,base+.457))
            side(rail,x-.105,x+.045,P,f'{floor}/pierced balustrade bay {i+1}')
            b.box((x-.020,(a+c)/2,base+.601),(.235,c-a-.014,.082),P,label=f'{floor}/coping bay {i+1}')
    for label,base,x,span in [('terrace lower edge',2.13,edge-.065,.18),('terrace supporting edge',2.31,edge-.045,.13),('upper parapet sill',5.24,face-.075,.17)]:
        b.box((x,ymid,base),(span,length,.075),P,label='terrace/'+label)
    # At the near end, the photographed terrace parapet turns back to the
    # downpipe. The two narrow openings beside that corner are separately cut.
    return_slab=box(7.39,2.36,9.00,2.97)
    for x in [8.19,8.46]:return_slab=return_slab.difference(box(x-.047,2.61,x+.047,2.84))
    b.prism(return_slab,-.075,.075,lambda x,z,d:(x,start-d,z),P,'terrace/short front return with two perforations')
    b.box((8.185,start,3.008),(1.72,.24,.078),P,label='terrace/return coping')
    # Three semicircular brick arches under the raised terrace appear in the
    # independent portrait. Set the intrados back to give the arcade open depth.
    arcade=box(.12,0,L+.13,2.205);nx=9 if lod else 23
    for i,(a,c) in enumerate(zip(col,col[1:])):
        mid=(a+c)*.5;half=(c-a-.52)/2;opening=arch(mid,half,.93,.73,nx);arcade=arcade.difference(opening)
        outer=arch(mid,half+.145,.93,.885,nx)
        voussoirs=outer.difference(opening).intersection(box(a,.92,c,2))
        side(voussoirs,edge-.018,edge+.025,B,f'arcade/arch ring {i+1}')
        if not lod:
            for j,theta in enumerate(np.linspace(.16,math.pi-.16,11)):
                p0=(mid+half*math.cos(theta),.93+.73*math.sin(theta));p1=(mid+(half+.14)*math.cos(theta),.93+.878*math.sin(theta))
                cut=LineString([p0,p1]).buffer(.003,cap_style='flat')
                side(cut,edge+.0254,edge+.0271,P,f'arcade {i+1}/radial mortar joint {j+1:02}')
    side(arcade,edge-.36,edge-.021,B,'arcade/three brick arches and returns')
    b.box((7.33,.17,1.06),(3.12,.286,2.12),B,label='arcade/near end wall')
    b.box((6.25,ymid,.035),(5.00,length,.07),P,label='arcade/floor behind the arches')
    # Continue the visible eaves along the inside row of brick piers.
    for j,(x,z,span,hh,mat)in enumerate([(7.51,8.15,.64,.22,P),(7.55,8.27,.79,.075,D),(7.48,8.345,.67,.072,T)]):
        b.box((x,ymid,z),(span,length+.38,hh),mat,label=f'gallery eaves/long edge {j+1}')
    # The roof behind the long eaves is a short visible pitch. Both photographed
    # dormer heads rise above it, and the end gable is visible beyond the last bay.
    roof=Polygon([(5.20,9.36),(7.75,8.34),(7.73,8.24),(5.18,9.26)])
    b.prism(roof,-L-.08,-start+.09,lambda x,z,d:(x,-d,z),T,'garden roof/visible pitched surface')
    for i,y in enumerate([2.50,5.62]):
        b.box((6.71,y,8.94),(.50,1.16,.62),M,label=f'garden dormer {i+1}/cheeks')
        b.box((6.978,y,8.98),(.055,.91,.42),W,label=f'garden dormer {i+1}/green face')
        for k in range(3):
            b.box((7.009,y+(k-1)*.278,8.99),(.021,.239,.35),G,label=f'garden dormer {i+1}/light {k+1}')
        b.box((6.77,y,9.293),(.87,1.39,.093),D,label=f'garden dormer {i+1}/projecting head')
    rear=Polygon([(L,2.38),(L+3.58,2.38),(L+3.58,7.42),(10.05,9.62),(L,7.42)])
    for label,ends in [('near',[(L-.13,7.39),(10.05,9.66)]),('far',[(10.05,9.66),(L+3.68,7.39)])]:
        pitch=LineString(ends).buffer(.079,cap_style='flat',join_style='mitre')
        side(pitch,5.48,7.47,T,'garden return/'+label+' sloping tile roof')
        verge=LineString(ends).buffer(.097,cap_style='flat',join_style='mitre')
        side(verge,7.47,7.55,B,'garden return/'+label+' gable edging')
        n=7 if lod else 15
        for j in range(1,n):
            y,z=np.asarray(ends[0])*(1-j/n)+np.asarray(ends[1])*(j/n)
            b.tube([(5.51,y,z+.094),(7.455,y,z+.094)],.020,T,5 if lod else 8,f'garden return {label}/tile course {j:02}')
    opening=box(L+.36,5.8,L+1.83,7.06);side(rear.difference(opening),7.07,7.36,M,'garden return/far gable around green window')
    side(opening.difference(opening.buffer(-.055,join_style='mitre')),7.13,7.28,W,'garden return/far green frame')
    side(opening.buffer(-.054,join_style='mitre'),7.12,7.14,G,'garden return/far glazing')
    for k in [1,2,3]:
        b.box((7.27,L+.36+1.47*k/4,6.43),(.048,.032,1.18),W,label=f'garden return/far mullion {k}')
    return b
