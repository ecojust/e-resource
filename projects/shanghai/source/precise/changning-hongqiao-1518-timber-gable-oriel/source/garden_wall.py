"""Clipped timber gable with four measured lights and a lower shallow five-sided bow."""
import numpy as np
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union
from scipy.interpolate import PchipInterpolator
from photo_architecture import Facade
from photograph import CALIBRATION,wall_coordinates,wall_shape,face_coordinates
from material_names import CREAM
TIMBER='Dark exposed garden timbers'
END='Dark wood on the eaves'
SASH='Deep brown painted window sash'
EDGE='Light on the joinery bead'
GLASS=['Blue reflected attic glass','Cool reflected attic glass','Dark garden glass','Garden glass pale reflection','Garden glass shadow']
PLINTH='Cream dressed stone sill'
FIELD='Plaster in window reveal'
# The plane ends at the neighbouring central verandah to the left and the lower balustrade to the right.
OUTLINE=[[500,438],[661,449],[663,243],[675,226],[603,101],[525,111],[462,226],[478,239],[478,257],[500,279]]
APER=box(-.91,-.08,.91,CALIBRATION['fitted_glass_height_m']+.085)

def lower_bow(b):
    samples=[(518.2,391),(532.0,391),(550.,391),(570.7,391),(591.8,391),(613.0,391)]
    t=np.linspace(-1,1,6);depth=-.048-.219*(1-t*t);xs=[wall_coordinates([p],y)[0,0]for p,y in zip(samples,depth)]
    base=np.mean([wall_coordinates([[u,z]],d)[0,1]for u,z,d in [(518.2,421.4,depth[0]),(551.,425.2,depth[2]),(592.,429.,depth[4]),(613.,429.,depth[-1])]])
    head=np.mean([wall_coordinates([[u,z]],d)[0,1]for u,z,d in [(518.2,357.8,depth[0]),(551.,359.2,depth[2]),(592.,360.8,depth[4]),(613.,361.0,depth[-1])]])
    axes=list(zip(xs,depth));frames=[]
    for i,(a,c)in enumerate(zip(axes,axes[1:])):
        f=Facade(b,a,c,'Lower garden bow '+str(i+1));ww=f.length/2;low=base+.028;hi=head-.031;bar=low+(hi-low)*.735
        # Every glazed light and the short top lights have their own slightly different reflection.
        for j,(bottom,top)in enumerate([(low,bar-.025),(bar+.025,hi)]):
            f.prism(box(-ww+.029,bottom,ww-.029,top),-.043,-.027,GLASS[2+(i+(j==0))%3],'glass lower' if j==0 else 'transom glass')
        f.prism(box(-ww,base,ww,head).difference(unary_union([box(-ww+.030,low,ww-.030,bar-.026),box(-ww+.030,bar+.026,ww-.030,hi)])),-.055,.013,SASH,'timber jambs and transom')
        f.prism(box(-ww-.017,base-.105,ww+.017,base),-.082,.074,PLINTH,'sloping sill segment')
        f.prism(box(-ww-.023,head,ww+.023,head+.117),-.069,.058,PLINTH,'projecting upper surround')
    ring=Polygon([(xs[0]-.092,.16),(xs[-1]+.09,.16),*[(x,y-.056)for x,y in reversed(axes)]])
    b.plan_prism(ring,base-.103,base-.03,PLINTH,'Lower garden bow/continuous curved sill top')
    return (xs[0]-.028,base-.060,xs[-1]+.025,head+.031)

def gable(b,lod):
    wall=Facade(b,[-.5,0],[.5,0],'Southern gable');low=lower_bow(b);field=wall_shape(OUTLINE)
    wall.prism(field.difference(unary_union([APER,box(*low)])),-.33,-.030,CREAM,'plastered plane with window openings')
    attheight=CALIBRATION['fitted_glass_height_m'];pitch=CALIBRATION['nominal_spacing_m'];wide=CALIBRATION['nominal_glass_width_m'];holes=[]
    for i in range(4):
        x=(i-1.5)*pitch;pane=box(x-wide/2,0,x+wide/2,attheight);holes.append(pane)
        wall.prism(pane,-.080,-.062,GLASS[i%2],'attic reflected pane '+str(i+1))
        wall.prism(pane.buffer(.015,join_style=2).difference(pane),-.046,-.003,EDGE,'pane perimeter bead '+str(i+1))
    wall.prism(APER.difference(unary_union(holes)),-.097,-.015,SASH,'four light attic frame')
    wall.prism(APER.buffer(.047,join_style=2).difference(APER),-.064,.008,PLINTH,'slender plaster reveal')
    # Timber silhouettes are drawn separately from the infill. Their outlines follow the Fayhoo garden photograph.
    polygons={'upper lintel':[[523,111],[604,101],[607,110],[526,119]],'left main verge':[[459,224],[520,112],[530,112],[471,226]],
              'right main verge':[[598,103],[606,100],[678,223],[666,226]],'slender inner head':[[534,124],[599,117],[599,122],[537,130]],
              'left outer strut':[[474,213],[529,120],[538,119],[484,211]],'right outer strut':[[596,118],[605,118],[654,207],[646,207]],
              'left attic post':[[534,126],[540,126],[539,187],[533,188]],'right attic post':[[595,122],[602,121],[602,183],[596,183]],
              'interrupted tie':[[483,176],[648,164],[651,170],[480,181]],'lower sill tie':[[468,214],[653,201],[656,207],[468,220]],
              'left short upright':[[506,175],[512,175],[511,211],[505,212]],'right short upright':[[624,166],[630,166],[630,203],[624,204]]}
    roofmask=wall_shape([[504,208],[514,199],[539,181],[546,170],[583,167],[592,183],[615,196],[623,203],[622,223],[503,224]])
    # Crop behind the projecting oriel cap and keep all four blue lights visible.
    for name,loop in polygons.items():
        shape=wall_shape(loop).intersection(field).difference(roofmask).difference(APER.buffer(.005,join_style=2))
        if shape.area>.0001:wall.prism(shape,-.032,.053,TIMBER,name)
    braces=[[[506,177],[518,185],[527,194],[531,201]],[[483,204],[488,197],[493,194],[498,201]],[[600,187],[607,179],[614,173],[625,168]],[[631,198],[636,187],[643,179],[646,178]]]
    for i,stroke in enumerate(braces,1):
        q=wall_coordinates(stroke);tt=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))];arc=PchipInterpolator(tt,q)(np.linspace(0,tt[-1],10 if lod else 24));shape=LineString(arc).buffer(.078 if i in [1,3]else .061,cap_style=2).difference(roofmask).intersection(field)
        if not shape.is_empty:wall.prism(shape,-.026,.058,TIMBER,'curved knee brace '+str(i))
    for i,pts in enumerate(([[461,227],[478,227],[479,235],[465,236]],[[658,222],[676,218],[675,228],[659,230]])):
        wall.prism(wall_shape(pts),-.050,.082,END,'eaves return '+str(i+1))
