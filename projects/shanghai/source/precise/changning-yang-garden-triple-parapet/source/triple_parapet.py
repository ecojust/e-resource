"""Model the three scalloped heads above the double casements on the garden front."""
from math import cos, sin, pi
from shapely.geometry import box, Polygon
from shapely.ops import unary_union

def finish(rgb,roughness,metal=0):
    def linear(q):
        v=q/255
        return v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4
    return {'color':[linear(x) for x in rgb],'roughness':roughness,'metallic':metal}
PALETTE={'warm render':finish((181,177,154),.92),'cast stone':finish((211,207,187),.85),
         'drip edge':finish((187,185,169),.82),'sash metal':finish((65,69,66),.5,.28),
         'window glass':finish((106,137,147),.24,.22),'panel face':finish((177,172,150),.93),
         'reveal shade':finish((142,143,130),.91),'recessed joint':finish((158,155,136),.94)}
CENTRES=(-2.13,0,2.13)
HALF=3.37
H=.744
SHOULDER=2.975
def crest_path(radius,n):
    path=[(-HALF,SHOULDER)]
    for c in CENTRES:
        path.extend((c+radius*cos(pi-pi*i/n),SHOULDER+radius*sin(pi-pi*i/n)) for i in range(n+1))
    path.append((HALF,SHOULDER))
    return path

def add_building(b,lod=False):
    n=14 if lod else 44
    def face(name,shape,front,back,material):
        if shape.area:
            b.prism(shape,-back,-front,lambda u,z,v:(u,-v,z),material,name)
    def up(name,x0,x1,z0,z1,front,back,material):
        face(name,box(x0,z0,x1,z1),front,back,material)
    # The long wall remains open behind all three pairs, including their deep jambs.
    sill=.865;head=2.335;win=.785
    outline=Polygon([(-HALF,0),(HALF,0)]+list(reversed(crest_path(H,n))))
    windows=[box(c-win,sill,c+win,head) for c in CENTRES]
    face('three parapet lobes and pierced wall',outline.difference(unary_union(windows)),0,.30,'warm render')
    # Follow the same semicircles into the short horizontal ledges between heads.
    for title,r,dz,height,front,back,mat in [
        ('hood lower shadow',H+.014,-.053,.044,-.064,.035,'drip edge'),
        ('hood projecting crown',H+.024,-.012,.073,-.112,.034,'cast stone'),
        ('cap narrow weathering strip',H+.018,.049,.029,-.080,.07,'drip edge')]:
        line=crest_path(r,n)
        strip=Polygon([(x,z+dz) for x,z in line]+[(x,z+dz+height)for x,z in reversed(line)])
        face(title,strip,front,back,mat)
    for i,c in enumerate(CENTRES):
        label=['west','middle','east'][i]
        openbox=windows[i]
        lining=openbox.difference(box(c-win+.018,sill+.018,c+win-.018,head-.018))
        face(label+' shaded reveal',lining,.027,.151,'reveal shade')
        frame=openbox.difference(box(c-win+.047,sill+.05,c+win-.047,head-.052))
        face(label+' inner sash',frame,.10,.166,'sash metal')
        for j,xc in enumerate((c-win/2,c+win/2)):
            up(label+' glass leaf '+str(j+1),xc-win/2+.029,xc+win/2-.029,sill+.031,head-.032,.158,.178,'window glass')
        up(label+' centre meeting stile',c-.028,c+.028,sill+.032,head-.038,.086,.175,'sash metal')
        for j,x in enumerate((c-win,c+win)):
            ext=(-.086,0) if j==0 else (0,.086)
            up(label+' pale jamb '+str(j+1),x+ext[0],x+ext[1],sill-.015,head+.112,-.043,.13,'cast stone')
        up(label+' flat lintel',c-win-.086,c+win+.086,head,head+.112,-.046,.13,'cast stone')
        panel=box(c-.797,.267,c+.797,.727)
        raised=box(c-.745,.31,c+.745,.685)
        face(label+' inset rectangular spandrel',panel,-.008,.012,'recessed joint')
        face(label+' raised spandrel field',raised,-.038,.009,'panel face')
    for i,x in enumerate((-1.065,1.065)):
        up('pier shaft '+str(i),x-.095,x+.095,.119,2.806,-.047,.05,'cast stone')
        up('pier neck '+str(i),x-.13,x+.13,2.789,2.938,-.068,.053,'drip edge')
    for label,z0,z1,front,mat in [('base projecting lip',.010,.089,-.14,'cast stone'),('base stepped crown',.089,.147,-.087,'drip edge'),('continuous window sill',.755,.827,-.105,'drip edge'),('window sill top',.823,.867,-.141,'cast stone')]:
        up(label,-HALF,HALF,z0,z1,front,.045,mat)
    for i,sign in enumerate((-1,1)):
        x=sign*3.24
        for j in range(6):
            z=1.08+.303*j
            up('flank course '+str(i)+' '+str(j),x-.122,x+.122,z,z+.014,-.003,.007,'recessed joint')
