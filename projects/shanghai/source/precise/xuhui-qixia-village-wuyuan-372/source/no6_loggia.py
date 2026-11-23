"""No. 6's white sliding sash, ochre-red open loggia and narrow sloping canopy, photo 42504417."""
import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union
from no7_enclosure import finish, IRON, SLAB

WHITE='Qixia 6 | weathered ivory sliding metal'
GLASS='Qixia 6 | grey transparent sliding glass'
OCHRE='Qixia 6 | pale ochre balcony apron'
ROSE='Qixia 6 | muted terracotta loggia render'
ROOF='Qixia 6 | narrow oxide red canopy'
PALETTE={WHITE:finish((193,190,177),.67,.12), GLASS:finish((127,138,132),.32,.07,.48),
         OCHRE:finish((173,159,111),.94), ROSE:finish((151,104,88),.94),
         ROOF:finish((127,76,61),.83,.06), IRON:finish((43,45,43),.76,.28), SLAB:finish((148,162,169),.92)}


def layout(cam,face_y,rear_y):
    def measure(uv,axis,y=face_y):
        return float(cam.wall(uv,y)[axis])
    # The rightmost narrow white strip is the return of the glazing. Its rearward width
    # is not an extra full sash on the photographed courtyard plane.
    left=measure((156,285),0);right=measure((289,265),0)
    low=float(np.mean([measure(p,2)for p in [(154,351),(221,344),(291,338)]]))
    middle=float(np.mean([measure(p,2)for p in [(162,240),(222,228),(289,216)]]))
    awning_front=face_y-.21
    eave=float(np.mean([measure(p,2,awning_front)for p in [(166,153),(211,141),(258,128)]]))
    # The dark rear opening's top left corner sits at (209,182). The upper right is obscured.
    return dict(left=left,right=right,low=low,middle=middle,eave=eave,awning_front=awning_front,
                rear_door_left=measure((209,183),0,rear_y), rear_door_head=measure((213,180),2,rear_y),
                glass_sill=float(np.mean([measure(p,2)for p in [(156,311),(223,303),(287,295)]])),
                glass_transom=float(np.mean([measure(p,2)for p in [(160,268),(220,257),(287,246)]])),
                glass_head=float(np.mean([measure(p,2)for p in [(159,247),(218,236),(288,222)]])))


def no6_openings(cam,face_y,rear_y):
    """XZ cut-outs to subtract from the main courtyard wall before installing the loggia."""
    a=layout(cam,face_y,rear_y)
    return [box(a['left'],a['low']-.01,a['right'],a['middle']),
            box(a['left'],a['middle'],a['right'],a['eave']+.20)]


def no6_rear_opening(cam,face_y,rear_y):
    """Measured dark opening in the rose-coloured upper wall at rear_y."""
    a=layout(cam,face_y,rear_y)
    left=max(a['left']+.10,min(a['right']-.65,a['rear_door_left']))
    return box(left,a['middle'],a['right']-.18,a['rear_door_head'])


def add_no6_loggia(builder,cam,face_y,rear_y,lod=False):
    if rear_y<=face_y:
        raise ValueError('No. 6 rear face must be behind the enclosure')
    for name,material in PALETTE.items():
        builder.palette.setdefault(name,material)
    a=layout(cam,face_y,rear_y);l,r=a['left'],a['right'];mid=a['middle'];d=rear_y-face_y
    front=face_y-.045
    def block(name,x0,y0,z0,x1,y1,z1,material):
        builder.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label='No 6 / '+name)
    def panel(shape,y_front,y_back,material,name):
        builder.prism(shape,-y_back,-y_front,lambda x,z,depth:(x,-depth,z),material,'No 6 / '+name)
    for label,z in [('middle',a['low']),('upper',mid)]:
        block(label+' terrace floor',l-.035,front-.025,z-.097,r+.055,rear_y+.02,z,SLAB)
    block('ochre solid apron below sliding window',l,face_y,a['low'],r,face_y+.09,a['glass_sill'],OCHRE)
    block('ochre apron right return',r-.075,face_y+.09,a['low'],r,rear_y,a['glass_sill'],OCHRE)
    sill,transom,head=a['glass_sill'],a['glass_transom'],a['glass_head']
    frontglass=face_y+.018;frontframe=face_y-.012
    def axis(u,v):return float(cam.wall((u,v),frontframe)[0])
    # Three large transom lights surmount six narrow lower sliding leaves. Two lower
    # lights have been slid aside, exposing a comparatively dark room in this photograph.
    edges=[l,*[axis(u,274) for u in (177,196,218,241,264)],r]
    edges=[max(l,min(r,v))for v in edges]; glass=[];frames=[]
    for group,(bottom,top,xs,open_slots) in enumerate(((sill,transom,edges,{2,4}),
                                                       (transom,head,[l,axis(198,239),axis(241,230),r],set()))):
        for i,(x0,x1) in enumerate(zip(xs,xs[1:])):
            outer=box(x0,bottom,x1,top)
            inside=box(x0+.022,bottom+.021,x1-.022,top-.021)
            if group==0 and i in open_slots:
                continue
            frames.append(outer.difference(inside));glass.append(inside)
    # Fixed meeting stiles remain alongside the two open leaves.
    frames.extend(box(u-.024,sill,u+.024,transom) for u in (edges[2],edges[3],edges[4],edges[5]))
    frames.append(box(l,transom-.023,r,transom+.023))
    panel(unary_union(frames),frontframe,face_y+.024,WHITE,'ivory sliding frames and transoms')
    panel(unary_union(glass),frontglass,frontglass+.008,GLASS,'sliding glazing with two open bays')
    # The foreshortened right strip is a separate short glazed return. The return is visible
    # in the photograph between the frontal outer post and the opaque yellow jamb.
    return_depth=min(.27,d*.37)
    block('sliding enclosure right side glass',r-.013,face_y+.034,sill,r,face_y+return_depth,head,GLASS)
    for z in (sill,transom,head):
        block('sliding enclosure return rail',r-.02,face_y,z-.014,r+.012,face_y+return_depth,z+.014,WHITE)
    block('sliding enclosure return jamb',r-.02,face_y+return_depth-.025,sill,r+.012,face_y+return_depth,head,WHITE)
    h=a['eave'];front_y=a['awning_front'];rise=min(.29,(rear_y-front_y)*.23)
    def ceiling(y):return h+(y-front_y)*rise/(rear_y-front_y)
    top=ceiling(rear_y)
    # Dark multi-light French door set into the red rear face. Neither of the two pale party walls is modeled here.
    door_shape=no6_rear_opening(cam,face_y,rear_y)
    back=box(l,mid,r,top).difference(door_shape)
    panel(back,rear_y-.020,rear_y-.004,ROSE,'red rear wall surrounding the dark opening')
    # The shared party wall is 160 mm wide and centred on l, making its inner face l + 80 mm.
    block('red left inner cheek',l+.081,face_y+.042,mid,l+.096,rear_y,ceiling(face_y+.042),ROSE)
    # The awning is a thin sloping sheet, with a contrasting red soffit and closely spaced
    # ribs exposed along its leading edge. End return is the measured front to rear projection.
    az0,az1=l-.047,r+.034;corners=[(az0,front_y),(az1,front_y),(az1,rear_y),(az0,rear_y)]
    for material,base,thickness,name in ((ROSE,-.054,.026,'rose soffit'),(ROOF,-.028,.047,'oxide red sheet')):
        vs=[(x,y,ceiling(y)+base+dz)for dz in (0,thickness)for x,y in corners]
        builder.add(vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material,'No 6 / '+name)
    block('thin red fascia at canopy nose',az0,front_y-.006,h-.055,az1,front_y+.004,h+.019,ROOF)
    # Visible repeat estimated from the clear left half of the source (about 6–8 source pixels).
    pitch=.145
    for x in np.arange(az0+.06,az1-.02,pitch):
        reach=min(.27,(rear_y-front_y)*.30)
        builder.tube([(x,front_y,h+.026),(x,front_y+reach,ceiling(front_y+reach)+.026)],.014,ROOF,4 if lod else 8,'No 6 / visible red canopy flute')
    # Slender straight upper rail, distinct from the dark interior glazing behind it.
    rail_y=face_y-.08
    rail_h=float(np.median([cam.wall(uv,rail_y)[2]for uv in [(171,211),(200,204),(234,195),(267,187)]]))
    for zz,radius,tag in ((rail_h,.015,'handrail'),(rail_h-.095,.010,'second horizontal rail'),(mid+.065,.009,'bottom rail')):
        if lod:block(tag,l,rail_y-radius,zz-radius,r,rail_y+radius,zz+radius,IRON)
        else:builder.tube([(l,rail_y,zz),(r,rail_y,zz)],radius,IRON,8,'No 6 / '+tag)
    for u in (164,178,196,210,223,239,253,270,283,295):
        x=float(cam.wall((u,213),rail_y)[0]);x=max(l+.009,min(r-.009,x));weight=.014 if u in (164,210,253,295)else .008
        if lod: block('upper upright',x-weight,rail_y-weight,mid,x+weight,rail_y+weight,rail_h,IRON)
        else:builder.tube([(x,rail_y,mid),(x,rail_y,rail_h)],weight,IRON,8,'No 6 / upper upright')
    return no6_openings(cam,face_y,rear_y)
