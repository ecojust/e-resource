"""Upper corner of the two-storey Yuanpei Building, Lane 865 Changning Road."""
from math import cos,sin,pi
from shapely.geometry import box, Polygon
from shapely.ops import unary_union, orient
from shapely import constrained_delaunay_triangles

def finish(rgb,roughness=.88,metallic=0):
    def linear(channel):
        v=channel/255
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return dict(color=[linear(x) for x in rgb],roughness=roughness,metallic=metallic)
PALETTE={'lime joint':finish((151,126,105)),'brick russet':finish((147,91,64)),
 'brick burnt':finish((134,80,57)),'brick ochre':finish((157,101,75)),
 'pale masonry':finish((199,190,158)), 'cornice shadow':finish((159,150,125)),
 'roof fascia':finish((91,52,43)), 'gutter and pipe':finish((74,65,55),.64,.24),
 'window metal':finish((77,84,77),.52,.20),'window glass':finish((104,125,130),.29,.18)}

def add_building(b,lod=False):
    xlen,return_len=4.28,2.12
    sill=.59;head=2.45;half=.535
    faces=[('long',-xlen,0,[-3.28,-1.32],lambda u,z,d:(u,-d,z)),
           ('return',0,return_len,[1.08],lambda u,z,d:(d,u,z))]
    for side,lo,hi,window_centres,mapper in faces:
        def face(label,g,front,back,mat):
            if not g.is_empty and g.area>1e-8:
                b.prism(g,-back,-front,mapper,mat,side+' '+label)
        holes=[box(c-half,sill,c+half,head)for c in window_centres]
        # The return's first few centimetres share the front wall's masonry core.
        start=lo+.014 if side=='return' else lo
        shell_end=hi-.014 if side=='long' else hi
        shape=box(start,0,shell_end,2.69).difference(unary_union(holes))
        face('perforated masonry shell',shape,.013,.199,'lime joint')
        for j in range(0,37):
            z=.075*j;left=lo-(.126 if j%2 else 0)
            for i in range(20):
                x=left+i*.253
                a,bound=max(x+.003,lo+.001 if side=='return' else lo),min(x+.249,hi-.001 if side=='long' else hi)
                if a>=bound:continue
                unit=box(a,z+.002,bound,min(2.687,z+.072)).difference(unary_union(holes)) if z<2.685 else None
                if unit is not None:
                    colour=('brick russet','brick burnt','brick ochre')[(i*31+j*17+j//4)%3]
                    label='stretcher bond course '+str(j//5)
                    if lod:
                        # The bed already closes the wall. Keep the joint pattern
                        # on distant brick faces and omit edges below pixel scale.
                        for tri in constrained_delaunay_triangles(unit).geoms:
                            pts=list(orient(tri,sign=1).exterior.coords)[:3]
                            b.add([mapper(u,h,0) for u,h in pts],[(0,1,2)],colour,side+' '+label)
                    else:
                        face(label,unit,0,.018,colour)
        for i,c in enumerate(window_centres):
            label='window '+str(i+1)
            face(label+' pale stone reveal',holes[i].difference(box(c-half+.045,sill+.032,c+half-.045,head-.047)),.012,.174,'pale masonry')
            opening=box(c-half+.044,sill+.032,c+half-.044,head-.047)
            face(label+' sash perimeter',opening.difference(box(c-half+.074,sill+.062,c+half-.074,head-.077)),.099,.182,'window metal')
            face(label+' glazing',box(c-half+.067,sill+.051,c+half-.067,head-.071),.147,.171,'window glass')
            face(label+' paired central stile',box(c-.018,sill+.047,c+.018,head-.06),.092,.174,'window metal')
            face(label+' upper horizontal transom',box(c-half+.049,1.991,c+half-.049,2.034),.080,.165,'window metal')
            face(label+' projecting sill',box(c-half-.048,sill-.085,c+half+.048,sill+.002),-.087,.038,'pale masonry')
            for j,xc in enumerate((c-half-.070,c+half+.070)):
                face(label+' vertical pale strip '+str(j),box(xc-.032,.06,xc+.032,2.695),-.018,.015,'pale masonry')
            if not lod:
                for k in range(3):
                    z=.704+k*.535
                    face(label+' sash fixed tabs',box(c-half+.057,z,c-half+.075,z+.058),.084,.107,'window metal')
    # One connected L in plan per level avoids overlapping end caps at the mitre.
    for title,z0,z1,d,mat in (
          ('lower eaves fillet',2.66,2.715,.080,'cornice shadow'),
          ('pale entablature',2.715,2.88,.112,'pale masonry'),
          ('projecting cap',2.88,2.951,.161,'pale masonry'),
          ('dark tile fascia',2.951,3.09,.196,'roof fascia'),
          ('gutter lip',3.09,3.13,.215,'gutter and pipe')):
        footprint=Polygon([(-xlen,-d),(d,-d),(d,return_len),(-.198,return_len),(-.198,.198),(-xlen,.198)])
        b.plan_prism(footprint,z0,z1,mat,title)
    # Angled rainhead, offset upper pipe and two wall straps are identifiable at the angle.
    def pipe(name,a,c,r):
        import numpy as np
        a=np.array(a);c=np.array(c);axis=(c-a)/np.linalg.norm(c-a)
        left=np.array([1.,0.,0.]); normal=np.cross(axis,left);normal/=np.linalg.norm(normal)
        cross=np.cross(normal,axis)
        n=8 if lod else 24
        verts=[tuple(p+r*(normal*cos(2*pi*i/n)+cross*sin(2*pi*i/n))) for p in (a,c) for i in range(n)]
        triangles=[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        triangles.extend([tuple(reversed(range(n))),tuple(range(n,2*n))]);b.add(verts,triangles,'gutter and pipe',name)
    pipe('vertical downpipe',(-.23,-.112,.009),(-.23,-.112,2.718),.039)
    pipe('sloping junction',(-.23,-.112,2.72),(-.28,-.205,3.02),.044)
    for i,z in enumerate((.44,1.80)):
        pipe('retaining collar '+str(i),(-.23,-.112,z),(-.23,-.112,z+.045),.045)
