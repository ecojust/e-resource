"""Three cheeked and pedimented dormers on the south mansard of Dongping Road 11."""
from math import cos, pi
from shapely.geometry import Polygon, box

AXES = (-3.80, 0.0, 3.80)
HALF_WIDTH = .635
EXTENT = 5.48
DEPTH = .86
RISE = 1.55
SILL = .15
WINDOW_TOP = 1.04
TYMPANUM = 1.453
APEX = 1.89
PALETTE = {
    'lime render': {'color': [.63,.545,.423], 'roughness': .86},
    'raised cream moulding': {'color': [.76,.677,.535], 'roughness': .81},
    'shaded cream fillet': {'color': [.48,.395,.283], 'roughness': .94},
    'stained casement timber': {'color': [.31,.167,.080], 'roughness': .71},
    'weathered glazing': {'color': [.135,.17,.178], 'roughness': .32},
    'tile shadow': {'color': [.195,.097,.059], 'roughness': .92},
    'terracotta': {'color': [.47,.242,.139], 'roughness': .88},
    'pale terracotta': {'color': [.55,.295,.183], 'roughness': .91},
    'burnt terracotta': {'color': [.397,.182,.105], 'roughness': .90},
    'ridge cover': {'color': [.252,.151,.102], 'roughness': .89},
}

def slope(y):
    return .02 + (y + .08) * RISE

def front(b, shape, x, near, far, material, name):
    b.prism(shape, -far, -near, lambda u,z,d: (x+u,-d,z), material, name)

def rectangular_ring(b, x, width, z0,z1, rim, near, far, material, name):
    opening=box(-width/2+rim,z0+rim,width/2-rim,z1-rim)
    front(b,box(-width/2,z0,width/2,z1).difference(opening),x,near,far,material,name)

def pediment(b, x, name):
    # Each course turns through the peak and comes forward from the recessed tympanum.
    for j,(half,zbase,apex,ledge,near,finish) in enumerate([
        (.676,1.278,1.702,.055,-.137,'shaded cream fillet'),
        (.709,1.335,1.766,.048,-.171,'raised cream moulding'),
        (.729,1.390,1.821,.043,-.190,'shaded cream fillet'),
        (.753,1.444,APEX,.056,-.208,'raised cream moulding')
    ]):
        course=Polygon([(-half,zbase),(0,apex),(half,zbase),(half,zbase-ledge),(0,apex-ledge),(-half,zbase-ledge)])
        front(b,course,x,near,.075,finish,name+' raking course '+str(j+1))
    back=Polygon([(-.748,1.28),(.748,1.28),(.748,1.437),(0,1.878),(-.748,1.437)])
    front(b,back,x,-.083,.33,'lime render',name+' projecting pediment body')
    for z,h,w,near,mat in [(1.18,.04,1.34,-.146,'shaded cream fillet'),
            (1.22,.065,1.42,-.164,'raised cream moulding'),(1.285,.042,1.451,-.17,'shaded cream fillet'),
            (1.328,.046,1.472,-.179,'raised cream moulding')]:
        b.box((x,(near+.09)/2,z+h/2),(w,.09-near,h),mat,label=name+' pediment bed moulds')

def dormer(b,x,i):
    name='South dormer '+str(i)
    # The sash is set behind its masonry opening. Two leaves meet at the wide center stile.
    hw=.443
    top=1.085
    front(b,box(-HALF_WIDTH,.045,HALF_WIDTH,1.30).difference(box(-hw,SILL,hw,top)),
          x,-.071,.20,'lime render',name+' plastered jambs and lintel')
    rectangular_ring(b,x,1.06,.095,1.16,.033,-.096,-.066,'raised cream moulding',name+' raised exterior architrave')
    rectangular_ring(b,x,.913,.137,1.102,.027,-.086,-.020,'shaded cream fillet',name+' recessed jamb bead')
    rectangular_ring(b,x,.881,.155,1.079,.034,-.038,.024,'stained casement timber',name+' timber frame')
    b.box((x,-.006,.616),(.049,.058,.883),'stained casement timber',label=name+' meeting stile')
    for sign in (-1,1):
        center=x+sign*.216
        b.box((center,.047,.617),(.389,.012,.845),'weathered glazing',label=name+' glazing')
        b.box((center,-.008,.617),(.020,.028,.857),'stained casement timber',label=name+' fine vertical glazing bars')
        for z in (.425,.679,.902):
            b.box((center,-.024,z),(.389,.021,.019),'stained casement timber',label=name+' horizontal glazing bars')
    b.box((x,-.018,.139),(1.01,.193,.047),'raised cream moulding',label=name+' sill')
    # The cheeks end on the incline. Only visible masonry above the existing roof is reconstructed.
    cheek=Polygon([(-.048,.088),(.797,slope(.797)),(.797,1.403),(-.048,1.403)])
    for side in (-1,1):
        lo,hi=sorted((side*(HALF_WIDTH-.068),side*HALF_WIDTH))
        b.prism(cheek,lo,hi,lambda y,z,d:(x+d,y,z),'lime render',name+' side cheek')
    pediment(b,x,name)
    # The small pitched cover meets the upper mansard. Its back edge follows the true intersection.
    for side in (-1,1):
        eave_x=x+side*.724
        eave_z=1.417
        ridge_z=1.873
        y1=(eave_z-.02)/RISE-.08
        y2=min(DEPTH,(ridge_z-.02)/RISE-.08)
        verts=[(x,.268,ridge_z),(eave_x,.268,eave_z),(eave_x,y1,eave_z),(x,y2,ridge_z)]
        # A low thickness at the flashing is enough; the closed cap lip remains editable.
        faces=[(0,1,2,3)] if side>0 else [(3,2,1,0)]
        back=[(a,yy,z-.028) for a,yy,z in verts]
        b.add(verts+back,[*faces,tuple(k+4 for k in reversed(faces[0])),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'ridge cover',name+' sloping hood')

def roof_piece(b,left,right,nrows,small,segment):
    """A bounded roof strip with concave pans and course noses drawn from the side photograph."""
    front_y=-.08
    pitch=(DEPTH-front_y)/nrows
    count=max(1,round((right-left)/.17))
    width=(right-left)/count
    cuts=3 if small else 7
    for row in range(nrows):
        y0=front_y+row*pitch
        y1=y0+pitch
        colour=[([],[]) for _ in range(3)]
        for k in range(count):
            x=left+k*width
            index=(k*7+row*2+segment*5)%13
            vertices,faces=colour[1 if index in (2,8,10) else 2 if index in (5,9) else 0]
            offset=len(vertices)
            for y,step in [(y0,-.018),(y0,.034),(y1,.006)]:
                for s in range(cuts+1):
                    u=s/cuts
                    z=slope(y)+step+.019*cos(2*pi*u)
                    vertices.append((x+u*width,y,z))
            for j in (0,1):
                for col in range(cuts):
                    a=offset+j*(cuts+1)+col;faces.append((a,a+1,a+cuts+2,a+cuts+1))
        materials=('terracotta','pale terracotta','burnt terracotta')
        for material,(v,f) in zip(materials,colour):
            if v:b.add(v,f,material,'Mansard roof strip '+str(segment)+' tile course '+str(row+1))
    base=box(left,front_y,right,DEPTH)
    b.prism(base,-.046,-.025,lambda x,y,d:(x,y,slope(y)+d),'tile shadow','Mansard underlay '+str(segment))
    b.box(((left+right)/2,DEPTH,slope(DEPTH)+.025),(right-left,.105,.092),'ridge cover',label='Horizontal upper slope break')

def add_dormers(b,lod=False):
    nrows=6
    starts=[-EXTENT]+[x+HALF_WIDTH for x in AXES]
    ends=[x-HALF_WIDTH for x in AXES]+[EXTENT]
    for j,(l,r) in enumerate(zip(starts,ends)):
        roof_piece(b,l,r,nrows,lod,j+1)
    for i,x in enumerate(AXES,1):
        dormer(b,x,i)
        # Visible triangular roof shoulders close the two sides of each hood beyond its pitched flank.
        for side in (-1,1):
            offset=.726
            x0=x+side*HALF_WIDTH
            y0=(1.873-.02)/RISE-.08
            y1=(1.417-.02)/RISE-.08
            crossing=offset*(y0-DEPTH)/(y0-y1)
            outline=Polygon([(x+side*crossing,DEPTH),(x+side*offset,y1),(x+side*offset,DEPTH)])
            clip=outline.intersection(box(min(x,x0),-.08,max(x,x0),DEPTH))
            if clip.is_empty or clip.area<1e-8:
                continue
            b.prism(clip,-.025,.022,lambda a,y,d:(a,y,slope(y)+d),'terracotta','Shoulder above dormer '+str(i))
