"""Procedural reconstruction of the photographed south loggia, local metres (Z up)."""
from math import sin, cos, pi, sqrt, ceil
from collections import defaultdict

RADIUS = 10.6
HALF_ARC = 6.15
BASE = 2.60
UPPER = 6.94
ROOF = 11.39


def plan(s, depth):
    a = s / RADIUS
    return ((RADIUS - depth) * sin(a),
            RADIUS * cos(HALF_ARC / RADIUS) - (RADIUS - depth) * cos(a))


def vertex(s, depth, z):
    return (*plan(s, depth), z)


def steps(lo, hi, n):
    return [lo + (hi - lo) * i / n for i in range(n + 1)]


class Model:
    def __init__(self, detail):
        self.parts = defaultdict(lambda: defaultdict(list))
        self.detail = detail
        self.rail_newels = set()
        self.arc_samples = {'raw': 26, 'full': 18, 'lod': 8}[detail]

    def quad(self, part, mat, a, b, c, d):
        self.parts[part][mat].extend(((a, b, c), (a, c, d)))

    def wedge(self, part, mat, a, b, front, back, bottom_a, bottom_b, top_a, top_b):
        """Closed radial/tangential element, independently pitched upper/lower edges."""
        A = vertex(a,front,bottom_a); B = vertex(b,front,bottom_b)
        C = vertex(b,front,top_b); D = vertex(a,front,top_a)
        E = vertex(a,back,bottom_a); F = vertex(b,back,bottom_b)
        G = vertex(b,back,top_b); H = vertex(a,back,top_a)
        for face in ((A,B,C,D),(F,E,H,G),(E,A,D,H),(B,F,G,C),(D,C,G,H),(E,F,B,A)):
            self.quad(part,mat,*face)

    def strip(self, part, mat, x0, x1, d0, d1, z0, z1, count=1):
        t = steps(x0,x1,count)
        for a,b in zip(t,t[1:]):
            self.wedge(part, mat,a,b,d0,d1,z0,z0,z1,z1)

    def deck(self, part, z, depth):
        # Chordal rear edge is a deliberate sectional edge of the model.
        arc = steps(-HALF_ARC, HALF_ARC, self.arc_samples * 2)
        for a,b in zip(arc,arc[1:]):
            xa,ya=plan(a,depth); xb,yb=plan(b,depth)
            def ring(h): return [(xa,ya,h),(xb,yb,h),(xb,1.88,h),(xa,1.88,h)]
            bottom,top=ring(z-.15),ring(z)
            self.quad(part,'paving',*top)
            self.quad(part,'shadow',*bottom[::-1])
            for i in range(4):
                k=(i+1)%4
                self.quad(part,'stone',bottom[i],bottom[k],top[k],top[i])

    def arch(self, part, a,b,base,spring,crown,top,front,back,glazed=False,trim=True):
        half=(b-a)/2
        midpoint=(a+b)/2
        def edge(x):
            q=min(1,abs((x-midpoint)/half))
            return spring+(crown-spring)*sqrt(max(0,1-q*q))*(1-.10*q)
        # Equal-angle sampling concentrates vertices around the springing.
        xx=[midpoint-half*cos(pi*i/self.arc_samples) for i in range(self.arc_samples+1)]
        for x,y in zip(xx,xx[1:]):
            ex,ey=edge(x),edge(y)
            self.wedge(part,'stone',x,y,front,back,ex,ey,top,top)
            if trim:
                self.wedge(part+'.archivolt','dressed',x,y,front-.095,front+.012,
                           ex,ey,ex+.145,ey+.145)
                if self.detail!='lod':
                    self.wedge(part+'.fine_bead','reveal',x,y,front-.11,front-.07,
                               ex+.15,ey+.15,ex+.184,ey+.184)
            if glazed:
                self.wedge(part+'.glass','glazing',x,y,front+.205,front+.24,base,base,ex,ey)
        if glazed:
            cols=5 if half>1.45 else 3
            for x in steps(a,b,cols)[1:-1]:
                self.strip(part+'.steel','steel',x-.022,x+.022,front+.144,front+.206,base,edge(x)-.018)
            for z in [base+.54,base+1.11,spring-.12]:
                self.strip(part+'.steel','steel',a,b,front+.141,front+.205,z,z+.038,4)
            self.strip(part+'.sill','dressed',a-.06,b+.06,front-.15,front+.26,base-.10,base+.025,5)

    def pierced_apron(self, part, center, s_width, z, h):
        # A quatrefoil opening is represented by a genuine hole through the spandrel.
        n=16 if self.detail=='lod' else 32
        rings=[]
        for i in range(n):
            t=2*pi*i/n
            u,v=cos(t),sin(t)
            fac=1/max(abs(u),abs(v))
            outline=(center+s_width*.5*u*fac,z+h*.5*v*fac)
            rad=.305+.09*cos(4*t)
            aperture=(center+s_width*rad*u,z+h*rad*v)
            rings.append((outline,aperture))
        def at(q,d):return vertex(q[0],d,q[1])
        for i,(O,I) in enumerate(rings):
            P,J=rings[(i+1)%n]
            self.quad(part,'stone',at(O,.03),at(P,.03),at(J,.03),at(I,.03))
            self.quad(part,'stone',at(P,.27),at(O,.27),at(I,.27),at(J,.27))
            self.quad(part,'reveal',at(I,.03),at(J,.03),at(J,.27),at(I,.27))
            self.quad(part,'stone',at(P,.03),at(O,.03),at(O,.27),at(P,.27))

    def rail(self, part,a,b,depth,z_at,slots):
        # Pierced stone parapet with real openings and a continuous sloping handrail.
        seg = steps(a,b,slots)
        for i,(lo,hi) in enumerate(zip(seg,seg[1:])):
            za,zb=z_at(lo),z_at(hi)
            for mat,base,top,out,inset in [('stone',0,.14,-.09,.15),('dressed',.85,.99,-.13,.18),('stone',.73,.88,-.068,.137)]:
                self.wedge(part+'.rails',mat,lo,hi,depth+out,depth+inset,za+base,zb+base,za+top,zb+top)
            w=hi-lo
            for f0,f1,w0,w1 in [(0,.10,.23,.28),(.10,.18,.28,.15),(.18,.63,.15,.15),(.63,.74,.15,.24)]:
                # Radial baluster taper; one short prism per shoulder, front/rear solid.
                mid=(lo+hi)/2
                zz=z_at(mid)+.085
                ring0=[vertex(mid-w*w0,depth-.048,zz+f0),vertex(mid+w*w0,depth-.048,zz+f0),vertex(mid+w*w0,depth+.125,zz+f0),vertex(mid-w*w0,depth+.125,zz+f0)]
                ring1=[vertex(mid-w*w1,depth-.048,zz+f1),vertex(mid+w*w1,depth-.048,zz+f1),vertex(mid+w*w1,depth+.125,zz+f1),vertex(mid-w*w1,depth+.125,zz+f1)]
                for k in range(4):
                    e=(k+1)%4
                    self.quad(part+'.balusters','dressed',ring0[k],ring0[e],ring1[e],ring1[k])
                self.quad(part+'.balusters','dressed',*ring0[::-1])
                self.quad(part+'.balusters','dressed',*ring1)
        for s in [a,b]:
            # Contiguous panels share their structural end post.
            key=(round(s,6),round(depth,6),round(z_at(s),6))
            if key in self.rail_newels:
                continue
            self.rail_newels.add(key)
            self.strip(part+'.newels','stone',s-.13,s+.13,depth-.11,depth+.18,z_at(s),z_at(s)+.99)
            self.strip(part+'.newels','dressed',s-.17,s+.17,depth-.15,depth+.22,z_at(s)+.93,z_at(s)+1.035)

    def build(self):
        h=HALF_ARC
        self.deck('01_Basement_ceiling_and_arcade_floor',BASE,-.02)
        self.deck('02_Loggia_ceiling_and_upper_floor',UPPER,-.03)
        self.deck('03_Open_roof_terrace',ROOF,-.02)
        # Two recessed basement lights at the central landing. Side stairs shelter the outer bays.
        for i,(a,b) in enumerate([(-1.19,.11),(.37,1.27)]):
            self.arch('04_Landing_basement_light_%02d'%i,a,b,.17,.91,1.12,BASE-.14,-2.63,-2.34)
            self.strip('04_Basement_plinth','plinth',a,b,-2.63,-2.33,0,.17,3)
        for a,b in [(-2.05,-1.19),(.11,.37),(1.27,2.05)]:
            self.strip('04_Basement_front_piers','plinth',a,b,-2.63,-2.33,0,BASE-.14,3)
        self.strip('05_Landing_slab','paving',-2.05,2.05,-2.74,-.02,BASE-.17,BASE,14)
        self.rail('05_Landing_rail',-2.05,2.05,-2.60,lambda s:BASE,15)
        for side,label in [(-1,'west'),(1,'east')]:
            p='06_'+label+'_stair'
            n=15; inner=2.05; end=6.85; tread=(end-inner)/n
            for i in range(n):
                a,b=sorted((side*(inner+i*tread),side*(inner+(i+1)*tread)))
                top=BASE*(1-i/n)
                self.strip(p+'.risers','stone',a,b,-2.67,-.02,0,top-.063,2)
                self.strip(p+'.treads','paving',a,b,-2.718,-.02,top-.063,top,2)
            lo,hi=sorted((side*inner,side*end))
            self.rail(p+'.raking_rail',lo,hi,-2.60,lambda x: BASE*(1-(abs(x)-inner)/(end-inner)),12)
        # Three large open arches on the lower level, four structurally continuous piers.
        low_bounds=[-h,-2.14,2.14,h]
        for i,s in enumerate(low_bounds):
            self.strip('10_Arcade_pier_%02d'%i,'stone',s-.24,s+.24,-.05,.53,BASE-.02,UPPER-.41)
            for z,w,d in [(BASE,.37,.12),(BASE+.17,.31,.095),(UPPER-1.35,.29,.085)]:
                self.strip('10_Arcade_pier_%02d'%i,'dressed',s-w,s+w,-d,.55,z,z+.18)
        for i,(a,b) in enumerate(zip(low_bounds,low_bounds[1:])):
            self.arch('11_Open_arcade_%02d'%i,a+.24,b-.24,BASE,UPPER-1.56,UPPER-.76,UPPER-.22,0,.52)
            if i!=1:self.rail('12_Arcade_side_parapet_%02d'%i,a+.24,b-.24,.07,lambda s:BASE,12)
        # Five true glazed openings. The centre opening is visibly wider than both pairs.
        high_bounds=[-h,-4.05,-2.07,2.07,4.05,h]
        sill=UPPER+1.27
        for i,s in enumerate(high_bounds):
            self.strip('20_Upper_window_pier_%02d'%i,'stone',s-.15,s+.15,.015,.40,UPPER-.04,ROOF-.22)
        for i,(a,b) in enumerate(zip(high_bounds,high_bounds[1:])):
            name='21_Glazed_bay_%02d'%i
            self.arch(name,a+.15,b-.15,sill,ROOF-1.06,ROOF-.57,ROOF-.21,.02,.36,True)
            cells=4 if i==2 else 2
            edges=steps(a+.15,b-.15,cells)
            for j,(s,t) in enumerate(zip(edges,edges[1:])):
                self.pierced_apron(name+'.pierced_apron',(s+t)/2,t-s,UPPER+.765,.71)
            self.strip(name+'.apron_band','stone',a+.15,b-.15,.02,.33,UPPER+.06,UPPER+.410,4)
            self.strip(name+'.apron_band','stone',a+.15,b-.15,.02,.33,UPPER+1.119,sill,4)
        for j,z in enumerate((UPPER,ROOF)):
            for k,(d,bot,top,mat) in enumerate([(-.055,-.40,-.28,'reveal'),(-.110,-.28,-.17,'dressed'),(-.17,-.17,-.08,'stone'),(-.235,-.08,.045,'dressed'),(-.08,.043,.10,'stone')]):
                self.strip('30_String_course_%d.%d'%(j,k),mat,-h-.24,h+.24,d,.49,z+bot,z+top,self.arc_samples*2)
        # Crimson brick step accents directly above photographed upper archivolts.
        for s in high_bounds[1:-1]:
            for row,half in enumerate([.135,.225,.32]):
                self.strip('32_Stepped_red_inlays','red_brick',s-half,s+half,-.001,.018,ROOF-.68+row*.105,ROOF-.58+row*.105,2)
        for i,(a,b) in enumerate(zip([-h,-2.07,2.07,h],[-2.07,2.07,h])):
            self.rail('40_Terrace_parapet_%02d'%i,a,b,-.005,lambda s:ROOF+.075,14)
        return self.parts
