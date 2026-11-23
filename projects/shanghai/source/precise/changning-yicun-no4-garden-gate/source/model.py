"""The gate at No. 4 and the photographed elevation behind it, in local Z-up metres."""
from collections import defaultdict
from math import sin,cos,pi,hypot

HOUSE=8.0
class Model:
    def __init__(self,role):
        self.role=role
        self.parts=defaultdict(lambda:defaultdict(list))
    def quad(self,group,mat,p):
        a,b,c,d=p
        self.parts[group][mat].extend(((a,b,c),(a,c,d)))
    def block(self,g,m,x0,x1,y0,y1,z0,z1):
        self.taper(g,m,(x0,x1,y0,y1),(x0,x1,y0,y1),z0,z1)
    def taper(self,g,m,lo,hi,z0,z1):
        x0,x1,y0,y1=lo; a,b,c,d=hi
        low=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)]
        top=[(a,c,z1),(b,c,z1),(b,d,z1),(a,d,z1)]
        self.quad(g,m,low[::-1]);self.quad(g,m,top)
        for i in range(4):
            j=(i+1)%4;self.quad(g,m,(low[i],low[j],top[j],top[i]))
    def slab(self,g,m,outline,y0,y1):
        # Convex X/Z polygon in counter-clockwise order, viewed from the street.
        a=[(x,y0,z)for x,z in outline];b=[(x,y1,z)for x,z in outline]
        for i in range(1,len(a)-1):
            self.parts[g][m].extend(((a[0],a[i],a[i+1]),(b[0],b[i+1],b[i])))
        for i in range(len(a)):
            j=(i+1)%len(a);self.quad(g,m,(a[i],b[i],b[j],a[j]))
    def beam(self,g,m,x,z,u,v,y,width,dep):
        dx=u-x;dz=v-z;n=hypot(dx,dz); ox=-dz/n*width/2;oz=dx/n*width/2
        self.slab(g,m,[(x-ox,z-oz),(u-ox,v-oz),(u+ox,v+oz),(x+ox,z+oz)],y,y+dep)
    def ring(self,g,m,x,z,r1,r2,y,dep,n):
        for i in range(n):
            pts=[(x+r*cos(k),z+r*sin(k))for r,k in [(r2,2*pi*i/n),(r2,2*pi*(i+1)/n),(r1,2*pi*(i+1)/n),(r1,2*pi*i/n)]]
            self.slab(g,m,pts,y,y+dep)
    def apertures(self,g,m,ext,holes,y,thickness):
        # Partition the complete front and back surface. Only the cutout perimeter
        # has reveal faces; the openings remain open through the section.
        x0,z0,x1,z1=ext;xs=sorted({x0,x1,*[v for h in holes for v in (h[0],h[2])]});zs=sorted({z0,z1,*[v for h in holes for v in (h[1],h[3])]})
        for a,b in zip(xs,xs[1:]):
            for c,d in zip(zs,zs[1:]):
                x=(a+b)/2;z=(c+d)/2
                if any(l<x<r and m<z<n for l,m,r,n in holes):continue
                poly=[(a,c),(b,c),(b,d),(a,d)]
                self.quad(g,m,[(px,y,pz)for px,pz in poly]);self.quad(g,m,[(px,y+thickness,pz)for px,pz in poly[::-1]])
        for i,h in enumerate([ext,*holes]):
            l,b,r,t=h;vs=[(l,b),(r,b),(r,t),(l,t)]
            if i:vs.reverse()
            for k,(x,z) in enumerate(vs):
                a,c=vs[(k+1)%4];self.quad(g,'reveal'if i else m,[(x,y,z),(x,y+thickness,z),(a,y+thickness,c),(a,y,c)])
    def gate(self):
        for side,x in [('West',-1.47),('East',1.47)]:
            g='01.'+side+'-rendered-gatepost'
            self.block(g,'foot',x-.31,x+.31,-.05,.54,0,.21)
            self.block(g,'render',x-.31,x+.31,-.04,.52,.21,2.339)
            self.block(g,'cap',x-.345,x+.345,-.086,.565,2.339,2.374)
            self.taper(g,'render',(x-.36,x+.36,-.10,.58),(x-.255,x+.255,.005,.48),2.374,2.46)
            self.block(g,'cap',x-.257,x+.257,.005,.479,2.459,2.475)
        for suffix,l,r in [('west',-1.141,-.009),('east',.01,1.143)]:
            g='02.'+suffix+'-painted-iron-leaf'
            self.block(g,'paint',l,r,.021,.065,.026,2.087)
            self.block(g+'-edge','edge',l,r,.013,.04,2.07,2.09)
            self.block(g+'-edge','edge',l,l+.018,.012,.043,.025,2.076)
            self.block(g+'-edge','edge',r-.018,r,.013,.042,.025,2.076)
            if self.role!='lod':
                for x in (l+.065,r-.065):
                    for z in (.13,.99,1.94):
                        self.block(g+'-fasteners','oxide',x-.009,x+.009,.009,.023,z-.008,z+.008)
        # A smaller inset access door is visible in the east leaf in both photographs.
        for x in (.105,1.088):
            self.block('02.inset-access-leaf','oxide',x-.008,x+.008,.002,.021,.06,1.73)
        self.block('02.inset-access-leaf','oxide',.103,1.095,.001,.023,1.705,1.724)
        self.block('02.east-hasps','hardware',.589,.965,-.049,.011,1.082,1.119)
        self.block('02.east-hasps','hardware',.91,.96,-.065,.018,1.093,1.146)
        for s,x0,x1 in [('west',-2.72,-1.77),('east',1.78,3.35)]:
            self.block('03.'+s+'-wall','render',x0,x1,.04,.31,.14,2.194)
            self.block('03.'+s+'-wall','foot',x0,x1,.042,.31,0,.14)
            self.block('03.'+s+'-coping','cap',x0,x1,.005,.343,2.193,2.23)
        self.block('03.east-recessed-panel','oxide',1.787,2.636,.019,.05,1.515,2.08)
        self.block('03.east-recessed-panel','cap',1.77,2.65,-.003,.032,1.491,1.519)
        self.block('04.number-four-plaque','plaque',1.331,1.601,-.065,-.037,1.889,2.09)
        # The photographed enamel digit is modelled as four narrow raised strokes.
        g='04.enamel-digit-four'
        for x,z,u,v in [(1.464,2.046,1.422,1.987),(1.422,1.987,1.491,1.987),(1.473,2.046,1.473,1.961)]:
            self.beam(g,'ivory',x,z,u,v,-.0685,.0095,.005)
        if self.role!='lod':
            for x in (1.345,1.587):
                self.block('04.enamel-fixings','fastener',x-.004,x+.004,-.069,-.063,1.989,1.996)
        self.block('00.threshold','cap',-1.16,1.16,-.30,.34,-.045,.026)
    def sash(self,g,l,b,r,t,y,cols,rows):
        self.block(g+'-glass','glass',l+.01,r-.01,y+.077,y+.090,b+.01,t-.01)
        size=.025
        for i in range(cols+1):
            x=l+(r-l)*i/cols;self.block(g+'-stiles','steel',x-size/2,x+size/2,y+.015,y+.077,b,t)
        for f in rows:
            z=b+(t-b)*f;th=size if f in (0,1) or f>.75 else .014
            self.block(g+'-rails','steel',l,r,y+.008,y+.070,z-th/2,z+th/2)
        self.block(g+'-sill','pale',l-.048,r+.048,y-.076,y+.14,b-.06,b+.006)
        if self.role=='raw':
            for i in range(1,cols):
                x=l+(r-l)*i/cols;self.block(g+'-glazing-beads','bead',x+.014,x+.021,y+.043,y+.070,b+.015,t-.015)
    def gable(self):
        l,r=-.67,2.44;eave=4.62;ridge=5.405;cx=.925;y=HOUSE
        holes=[(.291,3.347,1.536,4.433)]
        vents=[(.931,4.985),(.766,4.840),(1.093,4.820)]
        # All three vent holes sit above the eaves, where the roof slopes vary.
        self.apertures('10.front-render-wall','pale',(l,.91,r,eave),holes,y,.31)
        self.sash('11.four-light-steel-window',*holes[0],y,4,[0,.20,.42,.64,.82,1])
        self.slab('10.west-roof-slope','pale',[(l,eave),(cx-.51,eave),(cx-.51,ridge-.247)],y,y+.31)
        self.slab('10.east-roof-slope','pale',[(cx+.51,eave),(r,eave),(cx+.51,ridge-.268)],y,y+.31)
        vl=cx-.51;vr=cx+.51;zt=5.09
        airholes=[(x-.058,z-.025,x+.058,z+.025)for x,z in vents]
        self.apertures('12.three-gable-vents','pale',(vl,eave,vr,zt),airholes,y,.31)
        self.slab('10.upper-gable','pale',[(vl,zt),(vr,zt),(vr,ridge-.268),(cx,ridge),(vl,ridge-.247)],y,y+.31)
        for i,(x,z) in enumerate(vents):
            self.block('12.dark-interior-'+str(i+1),'dark',x-.058,x+.058,y+.34,y+.345,z-.027,z+.027)
        for x,z,u,v in [(l-.028,eave,cx,ridge),(cx,ridge,r+.028,eave)]:
            self.beam('10.gable-edge','pale',x,z,u,v,y-.019,.047,.44)
        # The east and west structural sections stop after the photographed front roof return.
        for x,z,u,v in [(l-.03,eave,cx,ridge),(cx,ridge,r+.03,eave)]:
            self.beam('13.clay-roof-return','clay',x,z,u,v,y+.27,.055,.75)
        self.apertures('15.east-wing','wing',(r,.97,4.82,4.022),[(2.757,3.14,3.277,3.705),(3.666,2.60,4.575,3.825)],y+.32,.25)
        self.sash('15.wing-shaded-window',2.757,3.14,3.277,3.705,y+.32,2,[0,1])
        self.sash('15.wing-tall-window',3.666,2.60,4.575,3.825,y+.32,3,[0,.35,.72,1])
        self.block('15.east-wing-fascia','pale',r,4.84,y+.206,y+.77,3.993,4.052)
        self.slab('15.east-wing-tiled-roof','clay',[(r,4.052),(4.84,4.052),(4.76,4.125),(r,4.125)],y+.20,y+1.0)
        for i in range({'raw':34,'full':22,'lod':6}[self.role]):
            count={'raw':34,'full':22,'lod':6}[self.role];x=r+(4.81-r)*(i+.5)/count
            self.block('15.tiled-edge','clayedge',x-.008,x+.008,y+.20,y+.98,4.117,4.132)
        g='14.window-side-condenser';self.block(g+'-case','case',1.69,2.13,y-.22,y-.006,3.443,3.835)
        self.ring(g+'-fan-opening','hardware',1.908,3.646,.104,.146,y-.235,.018,{'raw':40,'full':28,'lod':12}[self.role])
        if self.role!='lod':
            for i in range(7):
                z=3.535+i*.034;dx=(.108**2-(z-3.646)**2)**.5 if abs(z-3.646)<.108 else .03
                self.block(g+'-guard','bead',1.908-dx,1.908+dx,y-.242,y-.228,z-.004,z+.004)
    def build(self):
        self.gate();self.gable();return self.parts
