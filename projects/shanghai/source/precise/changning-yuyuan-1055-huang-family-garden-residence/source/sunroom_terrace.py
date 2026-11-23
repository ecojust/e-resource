"""Two-storey glazed garden room and the pierced eight-spoke terrace parapet."""
from shapely.geometry import box, LineString, Polygon
from shapely.ops import unary_union
from house_fabric import Wall, STONE, CONCRETE, PLINTH, STAIR, STUCCO

def balustrade(w,n,z,name):
    span=w.length/n
    w.rect(-.05,z,w.length+.05,z+.118,-.10,.098,CONCRETE,name+' foot')
    w.rect(-.082,z+.855,w.length+.082,z+.97,-.116,.12,STONE,name+' coping')
    for i in range(n):
        l=i*span;r=l+span
        face=box(l,z+.102,r,z+.878)
        center=(l+r)*.5;zz=z+.49
        segments=[[(l,z+.102),(r,z+.878)],[(l,z+.878),(r,z+.102)],[(l,zz),(r,zz)],[(center,z+.102),(center,z+.878)]]
        lattice=unary_union([face.difference(face.buffer(-.064,join_style=2))]+[LineString(seg).buffer(.037,cap_style=2) for seg in segments]).intersection(face)
        w.prism(lattice,-.075,.077,STONE,name+' pierced star '+str(i+1))

def add_sunroom(b,lod,layout):
    x0,y0,x1,y1=layout['terrace_rectangle'];z=layout['terrace_slab_z']
    floor=box(x0,y0,x1,y1)
    for j,(lo,hi) in enumerate([(0,.29),(3.68,3.915),(z-.19,z),(z,z+.09)]):
        b.plan_prism(floor.buffer(.075 if j else .10,join_style=2),lo,hi,CONCRETE,'Sunroom | horizontal slab '+str(j+1))
    for name,wall,count,piercing in [('South',Wall(b,(x0,y0),(x1,y0)),3,5),('East',Wall(b,(x1,y0),(x1,y1)),2,3)]:
        spacing=wall.length/count
        ground=[(i*spacing+.16,.82,(i+1)*spacing-.16,3.13) for i in range(count)]
        upper=[(i*spacing+.165,4.3,(i+1)*spacing-.165,6.73) for i in range(count)]
        wall.masonry(.29,z-.15,ground+upper,name+' sunroom | outer piers')
        for j,opening in enumerate(ground+upper):
            wall.sash(opening,2,3,f'{name} sunroom | sash {j+1}',lod)
        wall.rect(-.04,3.48,wall.length+.04,3.68,-.14,.075,STONE,name+' sunroom | belt')
        balustrade(wall,piercing,z+.087,name+' terrace |')
    w=Wall(b,(.15,1.27),(x0,1.27))
    ops=[(.49,.82,2.06,3.02),(.65,4.44,2.20,6.59),(2.88,4.39,4.59,6.53)]
    w.masonry(.25,7.45,ops,'South | recessed garden wall')
    for j,h in enumerate(ops):
        w.sash(h,2,3,'South | garden window '+str(j+1),lod)
    b.plan_prism(box(.15,-.035,x0,1.37),3.60,3.89,CONCRETE,'South | straight terrace')
    for wall in [Wall(b,(.15,0),(x0,0)),Wall(b,(.15,1.27),(.15,0))]:
        wall.rect(0,3.87,wall.length,4.66,-.10,.065,STUCCO,'South | rendered balcony parapet')
        wall.rect(-.055,4.65,wall.length+.055,4.74,-.135,.105,STONE,'South | terrace coping')
