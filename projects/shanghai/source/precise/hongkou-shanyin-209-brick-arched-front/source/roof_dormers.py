"""No. 3, Lane 209 Shanyin Road. Two roof windows traced in Fayhoo's April 2015 photograph."""
import math
import numpy as np

PREFIX = 'Shanyin dormer | '
RENDER = PREFIX + 'warm pale roughcast'
CHEEK = PREFIX + 'side return render'
RED = PREFIX + 'aged oxblood paint'
CAP = PREFIX + 'pale verge flashing'
WHITE = PREFIX + 'warm white sash'
GLASS = PREFIX + 'glazing'
DARK = PREFIX + 'shadowed reveal'
LEAD = PREFIX + 'weathered grey apron'
CLAY = PREFIX + 'burnt clay'
RIDGE = PREFIX + 'terracotta tile roll'
GUTTER = PREFIX + 'dark eaves gutter'
RAKE = PREFIX + 'pale raking edge'
PALETTE = {
    GUTTER: {'color':[.039,.041,.038],'roughness':.76},
    RAKE: {'color':[.34,.30,.27],'roughness':.88},
    RENDER: {'color':[.54,.49,.42],'roughness':.93},
    CHEEK: {'color':[.28,.26,.24],'roughness':.94},
    RED: {'color':[.28,.050,.029],'roughness':.72},
    CAP: {'color':[.41,.39,.33],'roughness':.8},
    WHITE: {'color':[.70,.65,.52],'roughness':.66},
    GLASS: {'color':[.23,.32,.36],'roughness':.27,'alpha':.47},
    DARK: {'color':[.045,.050,.047],'roughness':.91},
    LEAD: {'color':[.23,.22,.19],'roughness':.78,'metallic':.16},
    CLAY: {'color':[.36,.119,.055],'roughness':.89},
    RIDGE: {'color':[.46,.163,.074],'roughness':.87},
}

class Survey:
    def __init__(self, layout):
        self.P = np.asarray(layout['camera_P'],float)
        self.W = layout['middle_window_width']
        self.ey, self.ez = layout['eave_y'], layout['eave_z']
        self.slope = (layout['ridge_z']-self.ez)/(layout['ridge_y']-self.ey)

    def intersect(self, u, v, plane):
        system = np.array([self.P[0]-u*self.P[2], self.P[1]-v*self.P[2], plane])
        return np.linalg.solve(system[:,:3], -system[:,3])

    def at_roof(self,u,v):
        return self.intersect(u,v,[0,-self.slope,1,self.slope*self.ey-self.ez])

    def at_y(self,u,v,y):
        return self.intersect(u,v,[0,1,0,-y])

    def roof_z(self,y):
        return self.ez+self.slope*(y-self.ey)

    def roof_y(self,z):
        return self.ey+(z-self.ez)/self.slope


def dimensions(layout):
    s=Survey(layout)
    # Two independently captioned photographs constrain the projecting eaves
    # separately from the dormer walls. The actual flashing is seen only in 2015.
    unit=s.W/2.38
    left_y,right_y=2.365*unit,1.245*unit
    left_barge_y,right_eaves_y=2.01*unit,.895*unit
    def xy(u,v,y):
        q=s.at_y(u,v,y)
        return [float(q[0]),float(q[2])]
    left=dict(y=left_y,front_y=left_barge_y,sides=[xy(631,324,left_y)[0],xy(759,323,left_y)[0]],
              eave=xy(697,193,left_barge_y)[1],peak=xy(689,141,left_barge_y)[1],
              peak_x=xy(689,141,left_barge_y)[0],eave_x=[xy(591,193,left_barge_y)[0],xy(783,188,left_barge_y)[0]])
    # The 2015 picture resolves roughly six foreground tile laps near the right
    # wall between eave and raking verge. The second view cannot see the end.
    tail_y=right_eaves_y+2.18*unit
    right=dict(y=right_y,front_y=right_eaves_y,sides=[xy(861,348,right_y)[0],xy(998,348,right_y)[0]],
               eave=xy(914,186,right_eaves_y)[1],eave_x=[xy(828,186,right_eaves_y)[0],xy(998,186,right_eaves_y)[0]],
               join=s.at_y(997,130,tail_y).tolist())
    return s,left,right


def roof_openings(layout):
    """Footprints in XY for subtracting the parent tile skin below the two visible recesses."""
    s,left,right=dimensions(layout)
    polygons=[]
    for d in [left,right]:
        x0,x1=d['sides'];y=d['y'];back=s.roof_y(d['eave']-.06*s.W)
        polygons.append([(x0,y),(x1,y),(x1,back),(x0,back)])
    return polygons


def add_dormers(b, lod, layout):
    """Append the gabled pale sash and the red opening casement at the adjoining roof."""
    s,left,right=dimensions(layout);w=s.W
    far=lod is True or lod=='lod'
    b.palette.update(PALETTE)

    def prism(side,delta,mat,label):
        a=np.asarray(side,dtype=float);dv=np.asarray(delta,dtype=float)
        if np.dot(np.cross(a[1]-a[0],a[2]-a[0]),dv)<0:a=a[::-1]
        n=len(a)
        faces=[list(range(n-1,-1,-1)),list(range(n,2*n))]
        faces.extend([i,(i+1)%n,(i+1)%n+n,i+n]for i in range(n))
        b.add(np.vstack((a,a+dv)),faces,mat,label)

    def box(x0,x1,y0,y1,z0,z1,mat,label):
        assert x0<x1 and y0<y1 and z0<z1,label
        b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)

    def beam(a,z,width,height,mat,label):
        a,z=np.array(a),np.array(z);vec=z-a;length=np.linalg.norm(vec);u=vec/length
        side=np.cross(u,[0.,0.,1.]);side/=np.linalg.norm(side);up=np.cross(u,side)
        corner=[a+ms*width/2*side+mu*height/2*up for ms,mu in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        prism(corner,vec,mat,label)

    def shell(points,mat,label,thickness=.019):
        prism(points,[0,0,-thickness*w],mat,label)

    def cheeks(d,label):
        x0,x1=d['sides'];y=d['y'];top=d['eave']-.043*w;back=s.roof_y(top);floor=s.roof_z(y)-.024*w
        for x,dx,side in [(x0,.043*w,'left'),(x1,-.043*w,'right')]:
            prism([(x,y,floor),(x,y,top),(x,back,top)],(dx,0,0),CHEEK,label+' '+side+' triangular return')
            # The visible metal strip turns up the side then overlaps the tile.
            a=y-.034*w;end=back-.012*w;outside=-1 if dx>0 else 1
            lip=x+outside*.052*w
            shell([(x,a,s.roof_z(a)+.020*w),(lip,a,s.roof_z(a)+.020*w),
                   (lip,end,s.roof_z(end)+.020*w),(x,end,s.roof_z(end)+.020*w)],LEAD,label+' '+side+' stepped side flashing',.012)
        apron=y-.066*w;outer=y+.034*w;left_edge=x0-.035*w;right_edge=x1+.035*w
        clearance=.025*w
        if d is left:
            # In the front photograph the left metal sheet extends past both
            # jambs. Its toe is visible across the interlocking tile ribs.
            clearance=.031*w
            contact=[0,-s.slope,1,s.slope*s.ey-s.ez-clearance]
            toe=s.intersect(690,337,contact)
            apron=float(toe[1])
            left_edge=s.at_y(611,335,apron)[0];right_edge=s.at_y(771,335,apron)[0]
            box(x0,x1,y-.007*w,y+.005*w,s.roof_z(y)+.010*w,s.roof_z(y)+.065*w,
                LEAD,label+' grey metal counterflashing at the front wall')
        shell([(left_edge,apron,s.roof_z(apron)+clearance),(right_edge,apron,s.roof_z(apron)+clearance),
               (right_edge,outer,s.roof_z(outer)+clearance),(left_edge,outer,s.roof_z(outer)+clearance)],LEAD,label+' forward drainage apron',.010)

    def front(d,outer,label):
        x0,x1=d['sides'];y=d['y'];floor=s.roof_z(y)-.023*w;top=d['eave']-.038*w
        u0,v0,u1,v1=outer;l,_,high=s.at_y(u0,v0,y);r,_,low=s.at_y(u1,v1,y)
        low=max(low,floor+.040*w); high=min(high,top-.016*w)
        for nm,a,z in [('left jamb',x0,l),('right jamb',r,x1)]:
            box(a,z,y,y+.075*w,floor,top,RENDER,label+' '+nm)
        box(l,r,y,y+.075*w,high,top,RENDER,label+' lintel')
        box(l,r,y-.008*w,y+.080*w,floor,low,RENDER,label+' sill')
        return l,r,low,high

    cheeks(left,'Gabled dormer');cheeks(right,'Red casement dormer')
    x0,x1=left['sides'];y=left['y'];e=left['eave'];peak=left['peak'];cx=left['peak_x'];edge0,edge1=left['eave_x']
    l,r,bot,top=front(left,(650,214,735,323),'Gabled dormer')
    prism([(edge0,left['front_y']+.013*w,e),(edge1,left['front_y']+.013*w,e),(cx,left['front_y']+.013*w,peak)],(0,.052*w,0),RED,'Gabled dormer | oxblood bargeboard and tympanum')
    front_y=left['front_y']
    for side,a,k in [('left',edge0,cx),('right',cx,edge1)]:
        def roof_height(x):
            return e+(peak-e)*((x-edge0)/(cx-edge0) if side=='left'else (edge1-x)/(edge1-cx))
        za,zk=roof_height(a),roof_height(k)
        quad=[(a,front_y,za),(k,front_y,zk),(k,s.roof_y(zk)-.012*w,zk),(a,s.roof_y(za)-.012*w,za)]
        shell(quad,CLAY,'Gabled dormer | '+side+' clay roof')
        verge=[(592,190),(689,136),(689,150),(592,201)] if side=='left' else [(689,136),(783,185),(783,197),(689,150)]
        cap=[s.at_y(u,v,front_y-.006*w) for u,v in verge]
        prism(cap,[0,.035*w,0],CAP,'Gabled dormer | '+side+' folded pale verge face')
        # Each pan runs down its own slope. Successive exposed rows stop at the house roof.
        count=5 if far else 10
        for i in range(1,count):
            x=a+(k-a)*i/count;z=roof_height(x)+.006*w;end=s.roof_y(z)-.046*w
            if end>front_y:
                beam((x,front_y,z),(x,end,z),.015*w,.015*w,RIDGE,'Gabled dormer | '+side+' fired clay lap '+str(i))
    beam((cx,front_y,peak+.010*w),(cx,s.roof_y(peak),peak+.010*w),.085*w,.044*w,CAP,'Gabled dormer | capped ridge')
    # Front glazing is physically behind the casing, divided by the visible vertical members.
    rebate=y+.019*w;bar=.021*w;depth=.021*w
    for left_u,right_u,nm in [(l,l+bar,'left outer'),(r-bar,r,'right outer')]:
        box(left_u,right_u,rebate,rebate+depth,bot,top,WHITE,'Gabled dormer | '+nm)
    for a,z,nm in [(bot,bot+bar,'lower rail'),(top-bar,top,'head rail')]:
        box(l+bar,r-bar,rebate,rebate+depth,a,z,WHITE,'Gabled dormer | '+nm)
    internal=[s.at_y(u,280,y)[0] for u in (674,698,714)]
    for i,x in enumerate(internal):
        thick=.015*w if i!=1 else .019*w
        box(x-thick/2,x+thick/2,rebate,rebate+depth,bot+bar,top-bar,WHITE,'Gabled dormer | vertical division '+str(i+1))
    for i,(a,z) in enumerate(zip([l+bar,*internal],[*internal,r-bar])):
        box(a+.001*w,z-.001*w,rebate+depth,rebate+depth+.004*w,bot+bar,top-bar,GLASS,'Gabled dormer | light '+str(i+1))
    # A dim reveal is recessed far enough to read separately through the translucent glazing.
    box(l,r,y+.12*w,y+.126*w,bot,top,DARK,'Gabled dormer | inner reveal shadow')

    y=right['y'];e=right['eave'];edge0,edge1=right['eave_x'];ax,ay,az=right['join']
    l,r,bot,top=front(right,(869,218,992,343),'Red casement dormer')
    front_y=right['front_y']
    def uv(u,v,yy):
        return s.at_y(u,v,yy)
    near_cap=uv(838,172,front_y)
    far_cap=np.array([ax,ay,az])
    near_roof=uv(839,185,front_y)
    far_roof=uv(997,143,ay)
    eaves_right=uv(998,186,front_y)
    shell([near_roof,eaves_right,far_roof],CLAY,'Red casement dormer | triangular tiled slope')
    end_y=s.roof_y(far_roof[2])
    shell([near_roof,far_roof,(far_roof[0],end_y,far_roof[2]),(near_roof[0],s.roof_y(near_roof[2]),near_roof[2])],
          CLAY,'Red casement dormer | visible return to house pitch')
    # Pale mortar cheek below the continuous raking clay coping. It is
    # distinctly visible between the orange coping and triangular field of tiles.
    corner=np.array([near_roof,far_roof,far_cap,near_cap])
    axis=far_cap-near_cap
    lateral=np.array([-axis[1],axis[0],0.]);lateral/=np.linalg.norm(lateral)
    prism(corner,lateral*.047*w,RAKE,'Red casement dormer | pale cheek below raking coping')
    for i in range(8):
        a=near_cap+axis*(i/8)
        z=near_cap+axis*min(1,(i+1.08)/8)
        # The cap has a small folded shoulder and lower skirts.
        verts=[a+lateral*ac*w+np.array([0,0,az0*w]) for ac,az0 in [(-.040,-.019),(-.037,.005),(-.023,.017),(.023,.017),(.037,.005),(.040,-.019)]]
        prism(verts,z-a,RIDGE,'Red casement dormer | independent lapped coping tile '+str(i+1))
    front_board=[uv(u,v,front_y+.014*w) for u,v in [(830,192),(998,192),(998,205),(830,205)]]
    prism(front_board,[0,.060*w,0],RED,'Red casement dormer | red eaves fascia')
    gutter=[uv(u,v,front_y) for u,v in [(827,185),(997,185),(997,194),(830,194)]]
    prism(gutter,[0,.041*w,0],GUTTER,'Red casement dormer | dark projecting gutter and drip')
    soffit=[uv(u,v,front_y+.060*w) for u,v in [(835,205),(997,205),(997,212),(835,212)]]
    prism(soffit,[0,.070*w,0],RENDER,'Red casement dormer | pale lower eaves soffit')
    # Six exposed fore-aft tile laps can be counted by the neighbour at the
    # high end. Individual pan joints stagger between full-detail courses.
    for i in range(1,7):
        t=i/7
        pa=near_roof*(1-t)+far_roof*t
        pb=eaves_right*(1-t)+far_roof*t
        delta=np.array([0,0,.006*w]);pa+=delta;pb+=delta
        beam(pa,pb,.024*w,.014*w,CLAY,'Red casement dormer | transverse tile lap '+str(i))
    if not far:
        for i in range(7):
            t=(i+.08)/7;tt=(i+.93)/7
            for j in range(1,9):
                xfrac=(j+.42*(i%2))/9
                # The shrinking row clips joints at the raking edge.
                if xfrac<=t or xfrac<=tt:continue
                pos=lambda q:near_roof*(1-xfrac)+eaves_right*(xfrac-q)+far_roof*q+np.array([0,0,.007*w])
                beam(pos(t),pos(tt),.013*w,.012*w,CLAY,'Red casement dormer | tile pan '+str(i+1)+'-'+str(j))
    box(l,r,y+.27*w,y+.279*w,bot,top,DARK,'Red casement dormer | deep unlit recess')
    # The red leaf on the viewer's left is turned outward; its world-space direction
    # is constrained by the two separately visible upright edges, with full extent approximate.
    def casement(origin,tip,low,high,label):
        a=np.array(origin,float);end=np.array(tip,float);dxy=end-a;length=np.linalg.norm(dxy)
        u=dxy/length;n=np.array([-u[1],u[0]])
        def block(v0,v1,z0,z1,mat,name,thick):
            q=[[*((a+u*t)-n*thick/2),z] for t,z in [(v0,z0),(v1,z0),(v1,z1),(v0,z1)]]
            prism(q,[*(n*thick),0],mat,label+' '+name)
        st=.025*w;br=.020*w
        block(0,st,low,high,RED,'hinge stile',.023*w);block(length-st,length,low,high,RED,'closing stile',.023*w)
        rails=[low,low+(high-low)*.34,low+(high-low)*.67,high]
        for i,level in enumerate(rails):
            z0=max(level-br/2,low);z1=min(level+br/2,high);block(st,length-st,z0,z1,RED,'horizontal rail '+str(i+1),.023*w)
        for i,(za,zb) in enumerate(zip(rails,rails[1:])):
            block(st,length-st,za+br/2,zb-br/2,GLASS,'glazed light '+str(i+1),.006*w)
    lo=s.at_y(982,340,y)[2];hi=s.at_y(960,237,y)[2]
    ra=s.at_y(943,300,y)[0];rb=s.at_y(982,300,y)[0]
    casement((ra,y+.017*w),(rb,y+.013*w),lo,hi,'Red dormer | frontal red leaf')
    hinge_x=s.at_y(893,270,y)[0]; free_y=y-.18*w
    free_x=s.at_y(906,270,free_y)[0]
    casement((hinge_x,y+.010*w),(free_x,free_y),lo,hi,'Red dormer | outward red leaf')
