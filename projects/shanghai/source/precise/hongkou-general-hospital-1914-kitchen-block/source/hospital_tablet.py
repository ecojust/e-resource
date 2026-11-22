"""Stone cartouche on the north street elevation of the former Shanghai General Hospital.

Outlines use native 940×627 photograph coordinates. Registration to the 940×705
street view, uncertainty and original image credits are in the measurements folder.
"""
from math import cos, hypot, pi, sin, sqrt
from shapely.geometry import Polygon

STONE = 'Cartouche | warm grey architectural stone'
CARVING = 'Cartouche | carved limestone'
FACE = 'Cartouche | weathered tablet face'
BACK = 'Cartouche | recessed stone'

def _stone(rgb):
    rgb = [v / 255 for v in rgb]
    return {'color': [(v / 12.92 if v < .04045 else ((v+.055)/1.055)**2.4) for v in rgb],
            'roughness': .91, 'metallic': 0.0}

PALETTE = {STONE: _stone((172,156,138)), CARVING: _stone((182,165,145)),
           FACE: _stone((178,161,139)), BACK: _stone((147,133,116))}
DEFAULT = {'x0':20.307531866985414,'x1':22.749335214412355,
           'z0':10.06368237773435,'z1':13.437647726593296}

def _curve(start, segments, steps):
    result=[start]
    for a,b,end in segments:
        x,y=result[-1]
        for i in range(1,steps+1):
            t=i/steps;q=1-t
            result.append((q**3*x+3*q*q*t*a[0]+3*q*t*t*b[0]+t**3*end[0],
                           q**3*y+3*q*q*t*a[1]+3*q*t*t*b[1]+t**3*end[1]))
    return result

def add_tablet(builder,lod=False,layout=None):
    limits={**DEFAULT,**(layout or {}).get('tablet',{})}
    x0,x1,z0,z1=(limits[k] for k in ('x0','x1','z0','z1'))
    sx=(x1-x0)/271;sz=(z1-z0)/384
    def xyz(u,v,d):
        return (x0+(u-490)*sx,-d,z0+(512-v)*sz)
    builder.palette.update(PALETTE)
    steps=4 if lod else 8
    sides=6 if lod else 10
    def slab(points,back,front,mat,name):
        polygon=Polygon([(u,-v) for u,v in points])
        if not polygon.is_valid:raise ValueError(name)
        builder.prism(polygon,back,front,lambda u,z,d:xyz(u,-z,d),mat,'Cartouche / '+name)
    def rect(l,t,r,b,d0,d1,mat,name):
        slab([(l,t),(r,t),(r,b),(l,b)],d0,d1,mat,name)
    def wreath(path,width,d,height,name,material=CARVING,taper=False):
        """Convex carved band swept along an observed centreline, with a solid end on each side."""
        verts=[];faces=[];n=len(path)
        for j,(u,v) in enumerate(path):
            a=path[max(0,j-1)];b=path[min(n-1,j+1)]
            dx,dy=b[0]-a[0],b[1]-a[1];length=hypot(dx,dy)
            nx,ny=-dy/length,dx/length
            scale=(.25+.75*sin(pi*(j+.5)/n)**.44) if taper else 1.
            for k in range(sides):
                theta=2*pi*k/sides;radius=width*scale*cos(theta)
                verts.append(xyz(u+nx*radius,v+ny*radius,d+height*scale*sin(theta)))
            if j:
                for k in range(sides):
                    a=(j-1)*sides+k;b=(j-1)*sides+(k+1)%sides
                    faces.append((a,b,b+sides,a+sides))
        faces+=[tuple(reversed(range(sides))),tuple(range((n-1)*sides,n*sides))]
        # The photographic v axis increases downwards and the outward physical axis is -Y.
        builder.add(verts,[tuple(reversed(f)) for f in faces],material,'Cartouche / '+name)
    def leaf(u,v,rx,ry,angle,d,thickness,name):
        """Lenticular leaf or pendant with pointed tips and a rising central vein."""
        verts=[];faces=[];rings=4 if lod else 7
        turn=angle*pi/180.;ca,sa=cos(turn),sin(turn)
        for j in range(rings+1):
            s=j/rings;local_y=(2*s-1)*ry
            if j in (0,rings):span=0.;indices=1
            else:span=sin(pi*s)**.72;indices=sides
            for k in range(indices):
                theta=2*pi*k/sides;local_x=rx*span*cos(theta)
                verts.append(xyz(u+ca*local_x-sa*local_y,
                                 v+sa*local_x+ca*local_y,
                                 d+thickness*span*sin(theta)))
        for k in range(sides):faces.append((0,1+(k+1)%sides,1+k))
        for j in range(rings-2):
            for k in range(sides):
                a=1+j*sides+k;b=1+j*sides+(k+1)%sides
                faces.append((a,b,b+sides,a+sides))
        last=1+(rings-2)*sides
        for k in range(sides):faces.append((last+k,last+(k+1)%sides,len(verts)-1))
        builder.add(verts,faces,CARVING,'Cartouche / '+name)

    # Flat cheeks lie against the brick. The centre of the field is a single unlettered surface.
    rect(504,163,750,480,-.008,.035,BACK,'backboard')
    slab([(505,464),(748,464),(745,509),(507,510)],-.008,.055,STONE,'bracket backing')
    field=[(553,242),(546,240),(542,236),(549,231),(549,221),(594,220),
           (594,196),(574,196),(574,182),(683,182),(683,196),(660,196),
           (660,220),(705,220),(705,231),(715,237),(712,248),(702,253),
           (702,372),(710,375),(711,385),(704,390),(698,405),(554,405),
           (549,391),(538,383),(539,373),(553,369)]
    slab(field,.031,.145,FACE,'blank shield and neck')
    rect(555,436,701,459,.034,.109,STONE,'apron bearing')
    for top,left,right,bottom,depth,name in [
        (174,568,687,181,.171,'upper hood roll'),(180,570,686,187,.177,'upper hood fascia'),
        (187,575,680,195,.142,'upper neck sill'),(212,541,597,218,.181,'left ear lintel'),
        (218,545,592,228,.156,'left ear fillet'),(213,657,711,219,.181,'right ear lintel'),
        (219,661,706,228,.156,'right ear fillet')]:
        slab([(left,top),(right,top),(right-2,bottom),(left+2,bottom)],.079,depth,STONE,name)
    def mirror(path,side):
        # The right garland is slightly farther from the field than the left.
        return [(u if side==0 else 1252-u, v if side==0 else v+1) for u,v in path]
    for side,sideword in enumerate(('left','right')):
        def traced(start,segments):
            return mirror(_curve(start,segments,steps),side)
        def ornament(start,segments,width,d,height,label,taper=False):
            wreath(traced(start,segments),width,d,height,sideword+' '+label,taper=taper)
        def lobe(u,v,rx,ry,angle,d,height,label):
            a,b=mirror([(u,v)],side)[0];leaf(a,b,rx,ry,angle if side==0 else -angle,d,height,sideword+' '+label)
        cheek=mirror([(491,182),(527,181),(527,458),(491,465)],side)
        slab(cheek,-.004,.089,STONE,sideword+' outer upright')
        # Crown foliage is a solid carved mass below its fluted eye and its folded edge.
        crown=_curve((492,181),[
          ((489,156),(501,145),(513,147)),((525,146),(525,158),(536,151)),
          ((550,145),(559,137),(571,130)),((579,124),(590,129),(592,137)),
          ((598,152),(591,175),(578,177)),((570,177),(562,174),(559,188)),
          ((564,181),(574,183),(574,194)),((573,207),(561,210),(553,203)),
          ((543,211),(533,200),(536,183)),((514,192),(499,186),(492,181))],steps)
        slab(mirror(crown,side),.031,.126,STONE,sideword+' crown acanthus ground')
        ornament((577,134),[((566,139),(556,160),(535,174)),((522,182),(504,185),(497,175)),
                            ((489,161),(500,148),(513,150)),((531,150),(527,172),(514,172)),
                            ((503,172),(502,159),(512,157)),((518,155),(521,162),(516,165))],
                 4.1,.147,.032,'outer curled volute',True)
        ornament((570,168),[((583,172),(594,143),(584,133)),((578,126),(571,132),(570,144)),
                            ((567,161),(575,163),(577,151)),((579,142),(581,142),(581,148))],
                 3.5,.177,.034,'inner crown volute',True)
        ornament((563,155),[((553,168),(547,183),(551,195)),((554,207),(570,202),(564,192))],
                 4.2,.143,.033,'turned-under crown leaf',True)
        # The visible fruits hang from a carved continuous vine, with small side stems between clusters.
        ornament((507,184),[((511,205),(504,219),(509,239)),((515,261),(507,281),(508,312)),
                             ((503,341),(509,367),(508,388)),((509,408),(506,441),(510,459))],
                 3.2,.106,.025,'central garland stem')
        for j,v in enumerate((210,260,280,302,339,360,379,412,434)):
            for direction in (-1,1):
                u=508+direction*5
                lobe(u,v,4.6,9.8,-direction*(18+4*(j%2)),.114,.032,'layered hanging leaf '+str(j)+' '+str(direction))
        # Red-brown shadows between the hanging fruits in the source are not painted into the stone.
        for idx,v in enumerate((199,225,251,274,298,327,351,374,403,430,450)):
            lobe(508,v,4.9,8.9,0,.129,.035,'garland bud '+str(idx))
            lobe(500,v+3.8,4.0,7.7,27,.117,.029,'garland outer leaf '+str(idx))
            lobe(518,v+4.7,3.8,7.6,-26,.118,.029,'garland inner leaf '+str(idx))
        for i,v in enumerate((237,318,391)):
            ornament((492,v),[((498,v+6),(511,v+11),(523,v+25))],2.8,.134,.019,'ribbon descending '+str(i))
            ornament((523,v+1),[((511,v+10),(498,v+19),(495,v+34))],2.5,.128,.019,'ribbon return '+str(i))
        ornament((551,238),[((539,231),(532,241),(535,251)),((538,260),(551,257),(551,246)),
                             ((551,238),(542,238),(541,246)),((541,251),(546,250),(546,246))],
                 2.7,.176,.022,'upper shield scroll',True)
        ornament((544,252),[((545,265),(529,281),(535,291)),((538,300),(547,297),(545,289))],
                 3.2,.155,.019,'upper shield tail',True)
        for i,v in enumerate((307,324,343,356)):
            lobe(544,v,3.5 if i<3 else 2.6,6.2,4,.115,.022,'tassel '+str(i))
        ornament((584,433),[((552,437),(533,417),(535,391)),((534,380),(536,371),(543,372)),
                             ((553,370),(554,387),(544,388)),((540,388),(539,382),(544,379))],
                 3.6,.166,.031,'lower shield volute',True)
        ornament((539,393),[((541,413),(553,430),(574,434)),((558,426),(551,415),(554,405)),
                             ((559,389),(570,400),(566,408))],3.4,.157,.029,'lower acanthus leaf',True)
        ornament((543,436),[((549,425),(557,435),(573,435)),((587,435),(606,436),(604,418)),
                             ((602,407),(591,408),(590,418)),((589,424),(596,425),(598,419))],
                 3.1,.155,.030,'apron spiral',True)
        ornament((603,457),[((610,448),(610,429),(609,417)),((611,407),(622,413),(620,423)),
                             ((620,438),(618,449),(612,456))],4.3,.178,.038,'folded lower tongue')
    # Short lobed barrel unites the two ends of the upper pair of volutes.
    rect(586,134,667,166,.06,.135,STONE,'crown barrel bearing')
    # A continuous rounded barrel backs the five beaded/fluted divisions at the crown.
    ring=[];ends=[];count=12 if lod else 24
    for u,vheight in ((582,15.5),(590,18.2),(608,16.7),(628,17.2),(647,16.7),(664,18.0),(672,15.3)):
        for k in range(count):
            angle=2*pi*k/count
            ring.append(xyz(u,149.7+vheight*sin(angle),.147+.044*cos(angle)))
    for j in range(6):
        for k in range(count):
            a=j*count+k;b=j*count+(k+1)%count
            ends.append((a,b,b+count,a+count))
    ends.extend([tuple(reversed(range(count))),tuple(range(count*6,count*7))])
    builder.add(ring,ends,STONE,'Cartouche / continuous fluted crown barrel')
    for i,u in enumerate((590,598,609,619,627,636,646,656,664)):
        w=3.6 if i in (0,8) else 2.7
        wreath(_curve((u,131.1),[((u+3.4,139),(u+2.1,157),(u-1.5,167))],steps),
               w,.164,.045,'crown barrel flute '+str(i),STONE)
    for i,v in enumerate((136,143,150,157,164)):
        leaf(627,v,2.0,2.7,0,.211,.009,'central bead '+str(i))
    # The original foot has four separate, short stepped corbels.
    for i,u in enumerate((540,600,658,717)):
        slab([(u-13,481),(u+13,481),(u+12,505),(u+7,511),(u-12,511)],
             .021,.149,STONE,'corbel base '+str(i+1))
        slab([(u-14,482),(u+14,482),(u+12,502),(u-12,502)],
             .115,.198,STONE,'corbel face '+str(i+1))
    for u,v,r,b,d,name in [(507,458,751,465,.226,'top bead'),(505,465,750,471,.245,'projecting shelf'),
                             (509,471,745,479,.222,'shelf fascia'),(515,479,742,485,.193,'lower shelf ledge'),
                             (519,485,735,489,.148,'shelf throat')]:
        slab([(u,v),(r,v+1),(r-2,b+1),(u+2,b)],.008,d,STONE,name)
