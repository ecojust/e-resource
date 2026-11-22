"""Two glazed sashes, a transom, stained beads and the painted brick pier."""
from pathlib import Path
import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union
from photo_architecture import Facade
from window_photo import WIDTH,HEIGHT,EYE,front_shape,wall_coordinates,project
from grille import to_plane
WOOD='Weathered red timber frame';DARK='Dark wood in the glazing rebate';INNER='Light on rubbed window beads'
GLASS=['Smoked umber window glass','Dull grey blue window glass']
BRICK='Painted ivory courtyard brick';PINK='Pale pink whitewash';CAP='Buff limestone stringcourse';RED='Exposed red band on courtyard brick';MORTAR='Fine pale joints in the garden wall'
REFLECT='Timber seen through the opening'
def panel_bounds(pixels,depth):
    q=to_plane(pixels,depth)
    return box(q[:,0].min(),q[:,1].min(),q[:,0].max(),q[:,1].max())
def woodwork(b,lod):
    plane=Facade(b,[-.5,0],[.5,0],'Liang window')
    outer=box(-WIDTH/2,0,WIDTH/2,HEIGHT)
    tall=panel_bounds([[37.5,35.2],[442.0,625.7]],.015)
    lower=panel_bounds([[37.6,658.5],[442.,846.0]],.015)
    holes=unary_union([tall,lower])
    plane.prism(outer.difference(holes),-.075,-.003,WOOD,'wooden double panel surround')
    plane.prism(outer.buffer(.011,join_style=2).difference(outer.buffer(-.008,join_style=2)),-.044,.009,DARK,'outer red shadow molding')
    plane.prism(outer.buffer(-.020,join_style=2).difference(outer.buffer(-.036,join_style=2)),-.015,.008,WOOD,'outer raised bead')
    for name,area in [('upper',tall),('lower',lower)]:
        plane.prism(area.buffer(.014,join_style=2).difference(area),-.038,-.004,INNER,name+' narrow yellowed bead')
        plane.prism(area.buffer(.008,join_style=2).difference(area.buffer(-.009,join_style=2)),-.077,-.036,DARK,name+' inside rebate')
        x0,z0,x1,z1=area.bounds;cx=(x0+x1)*.5
        # A vertical timber meeting rail is visible behind each grille. The
        # bottom of both decorative panels leaves an open arch in front of it.
        middle=panel_bounds([[215,36 if name=='upper'else 660],[263,624 if name=='upper'else 844]],.096)
        plane.prism(middle.intersection(area),-.122,-.089,WOOD,name+' meeting rail behind grille')
        for j,(l,r)in enumerate([(x0,cx),(cx,x1)]):
            # The photograph looks up at the sash. Overlap the hidden glass edges
            # behind all four timber rebates to retain the full oblique sightline.
            side_left=l-.056 if j==0 else l-.003
            side_right=r+.056 if j==1 else r+.003
            plane.prism(box(side_left,z0-.104,side_right,z1+.131),-.128,-.120,
                        GLASS[(j+(name=='lower'))%2],name+' tinted glazing '+str(j+1))
        if name=='upper':
            for i,y in enumerate([235.5,415.1]):
                section=panel_bounds([[37,y-2.4],[441,y+2.4]],.102)
                plane.prism(section.intersection(area),-.113,-.101,REFLECT,'glazed sash horizontal '+str(i+1))
    # The arch and sill project from one continuous wall. Keep the study edges
    # vertical in building space and continue the masonry behind the upper hood.
    left=wall_coordinates([[48.0,136]],.071)[0,0]
    right=wall_coordinates([[461.0,136]],.071)[0,0]
    zmin=wall_coordinates([[256,675]],.071)[0,1];zmax=wall_coordinates([[254,3]],.071)[0,1]
    span=box(left,zmin,right,zmax)
    clearance=outer.buffer(-.005,join_style=2);base=span.difference(clearance)
    plane.prism(base,-.19,-.074,MORTAR,'painted brick backing with true opening')
    course=.063;unit=.222
    for k in range(int(np.floor(zmin/course)),int(np.ceil(zmax/course))):
        z=k*course
        pix=project([[0,.066,z+course/2]])[0,1]
        for i in range(int(np.floor(left/unit))-2,int(np.ceil(right/unit))+2):
            x=(i+(k%2)/2)*unit
            geom=box(x+.0023,z+.0020,x+unit-.0023,z+course-.0021).intersection(base)
            if geom.is_empty or geom.area<.00004:continue
            red=(pix<22 or 173<pix<220 or 568<pix<598)
            material=RED if red else PINK if (k*13+i*7)%11<2 else BRICK
            plane.prism(geom,-.077,-.066,material,'painted wall/course '+str(k+15))
    # The light-coloured stretcher over the wooden head is visibly separate
    # from the brick hood. A second projecting belt runs above its small key.
    for name,upper,lower,front in [('plain timber head lintel',149.5,162.4,.004),('upper stone belt',26.5,48.2,-.008)]:
        zz=wall_coordinates([[255,upper],[255,lower]],.034)[:,1]
        shape=box(left,min(zz),right,max(zz))
        plane.prism(shape,-.102,front,CAP,name)
        plane.prism(box(left,min(zz)-.012,right,min(zz)+.006),-.074,front+.010,INNER if upper>100 else CAP,name+' drip')
