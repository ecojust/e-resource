"""Build House 12's photographed numbered gable, three green casements and recessed side landing."""
from pathlib import Path
import argparse,json,sys
import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
ID='changning-xinhuacun-12-numbered-gable'
META=dict(id=ID,heritage_id='sh-historic-b3-101',protection_number='3M003',name='新华村12号题号山墙',address='愚园路1320号新华村12号',scope='12号有数字的主山墙，三樘绿色小格窗、粗砂面与红砖交牙、窄凹廊、檐口、瓦面及两处可见烟囱。',geometry_license='MIT',photos_embedded=False,viewer_page='xinhuacun-12-numbered-gable.html')
M='coarse grey-brown pebble dash';B='warm red facing brick';T='terracotta roof';P='pale precast cement';W='deep green window joinery';G='dark casement glass';D='dark cast rainwater iron';I='ivory cast house numerals'
PALETTE={n:dict(color=c,roughness=r)for n,c,r in [(M,[.344,.319,.271],.95),(B,[.65,.356,.224],.89),(T,[.523,.257,.177],.87),(P,[.64,.593,.492],.82),(W,[.14,.225,.181],.59),(G,[.188,.251,.227],.29),(D,[.144,.145,.128],.64),(I,[.851,.767,.565],.59)]}
reg=json.loads((HERE/'registered-gable.json').read_bytes());H=np.array(reg['image_to_xz'])
def xz(u,v):
    q=H@[u,v,1.]
    return q[:2]/q[2]
def rect(left,top,right,bottom):
    return Polygon([xz(*p)for p in [(left,top),(right,top),(right,bottom),(left,bottom)]])
def build(lod=False):
    b=Builder(PALETTE)
    def solid(poly,back,front,mat,name):
        if poly.is_empty:return
        if poly.geom_type!='Polygon':
            for i,q in enumerate(poly.geoms):
                if q.geom_type=='Polygon':solid(q,back,front,mat,name+'/'+str(i+1))
            return
        b.prism(poly,back,front,lambda x,z,d:(x,-d,z),mat,name)
    def face(uv,back,front,mat,name):
        solid(Polygon([xz(*p)for p in uv]),back,front,mat,name)
    def strip(uv,width,back,front,mat,name):
        solid(LineString([xz(*p)for p in uv]).buffer(width/2,cap_style='flat',join_style='mitre'),back,front,mat,name)
    # The main face ends at the dark right-hand recess. It is backed with real
    # reveals at the windows, and its lowest visible opening sits below the sill.
    openings={'lower':rect(506,353,560,394),'upper':rect(507,244,559,284),'attic':rect(550,150,603,189)}
    surface=rect(450,230,640,452).difference(unary_union([openings['lower'],openings['upper']]))
    left=rect(448,232,476,452);right=rect(613,228,641,449)
    for j in range(12):
        y=236+17.2*j
        left=left.union(rect(471,y,481,y+8.3))
        right=right.union(rect(607.5,y-4,616,y+4.3))
    brick=left.union(right).intersection(surface)
    solid(surface,-.31,-.027,M,'numbered face/back and window reveals')
    solid(surface.difference(brick).buffer(-.00045,join_style="mitre").simplify(.00021,preserve_topology=True),-.026,.001,M,'numbered face/roughcast central field')
    solid(brick,-.025,.009,B,'numbered face/interlocking brick quoins')
    attic=Polygon([xz(*p)for p in [(461,209),(575,89),(695,202)]]).difference(openings['attic'])
    solid(attic,-.36,.003,M,'attic/triangular gable with casement opening')
    # Casements have three vertical lights. Each pane sits behind the rails and
    # has a shallow frame return; the glazing never fills the thickness of the wall.
    for name,poly in openings.items():
        xmin,zmin,xmax,zmax=poly.bounds;w=xmax-xmin;h=zmax-zmin
        frame=poly.difference(box(xmin+.049,zmin+.049,xmax-.049,zmax-.049))
        solid(frame,-.228,-.093,W,'casement '+name+'/recessed outer frame')
        for j in (1,2):
            x=xmin+j*w/3
            b.box((x,.144,(zmin+zmax)/2),(.036,.070,h-.055),W,label=f'casement {name}/stile {j}')
        cells=4 if name=='attic'else 3
        for j in range(1,cells):
            z=zmin+j*h/cells
            b.box(((xmin+xmax)/2,.153,z),(w-.065,.037,.027),W,label=f'casement {name}/rail {j}')
        for j in range(3):
            for k in range(cells):
                a=xmin+j*w/3+.023;c=xmin+(j+1)*w/3-.023
                lo=zmin+k*h/cells+.016;hi=zmin+(k+1)*h/cells-.016
                solid(poly.intersection(box(a,lo,c,hi)),-.242,-.221,G,f'casement {name}/pane {j+1}-{k+1}')
        for part,z,hh,depth in [('lintel',zmax+.051,.105,.071),('sill',zmin-.045,.081,.099)]:
            b.box(((xmin+xmax)/2,-depth/3,z),(w+.156,depth*1.33,hh),P,label=f'casement {name}/{part}')
    for d in reg['digit_outlines']:
        for i,(shell,*holes)in enumerate(d['rings']):
            solid(Polygon(shell,holes).buffer(-.0015,join_style='mitre'),-.0004,.037,I,'house number/'+d['number']+' stroke '+str(i+1))
    # Three edges run independently along the two sloping verges and the lower fascia.
    for label,coords in [('left',[(452,212),(574,86)]),('right',[(575,86),(702,203)])]:
        strip(coords,.135,-.32,.102,P,'gable verge/'+label+' moulding')
        strip(coords,.220,-.29,.018,T,'gable verge/'+label+' underlying tile edge')
    for j,(uv,thick,depth,mat)in enumerate([([(424,222),(730,204)],.143,.42,D), ([(430,229),(725,212)],.100,.31,P), ([(447,215),(705,201)],.089,.20,T)]):
        strip(uv,thick,-.40,depth,mat,'eaves/horizontal band '+str(j+1))
    # The part of both pitched planes immediately behind the gable is visible in oblique views.
    # The study closes these short roof strips without extrapolating the full plan of the house.
    for label,ends in [('left',[(449,212),(575,87)]),('right',[(575,87),(706,202)])]:
        strip(ends,.109,-1.98,-.30,T,'roof/'+label+' clay tile strip')
        n=12 if lod else 24
        for j in range(1,n+1):
            t=(j-.5)/n;p=xz(*(np.asarray(ends[0])*(1-t)+np.asarray(ends[1])*t))
            b.tube([(p[0],.39,p[1]+.067),(p[0],1.94,p[1]+.067)],.021,T,5 if lod else 7,f'roof {label}/tile roll {j:02}')
    # Right pier and the two dark landings can be seen through the slot.
    corner=rect(669,224,702,450);solid(corner,-.56,.007,B,'side landing/outer brick pier')
    for j in range(8):
        y=247+j*25.3;solid(rect(669,y,702,y+2.2),.009,.018,P,f'side landing/recessed course {j+1}')
    for k,y in enumerate([294,397]):
        solid(rect(638,y,670,y+5),-.94,.013,P,f'side landing/edge beam {k+1}')
        guard=rect(639,y+4,669,y+26)
        for x in [644,653,662]:guard=guard.difference(rect(x,y+6,x+3,y+15))
        solid(guard,-.09,-.009,P,f'side landing/short pierced parapet {k+1}')
    solid(rect(640,233,668,443),-1.19,-1.07,M,'side landing/rear wall')
    for name,uv in [('left',[(451,450),(485,449),(484,510),(449,511)]),('right',[(614,446),(643,446),(645,508),(614,508)])]:
        face(uv,-.62,.002,B,'ground opening/'+name+' jamb')
    solid(rect(481,433,615,454),-.54,.111,P,'ground opening/lintel and projecting hood')
    # The rainwater head and downpipe appear in both the older and numbered photographs.
    p=xz(685,228);q=xz(688,451);d=8 if lod else 14
    b.tube([(p[0],-.125,p[1]),(q[0],-.125,q[1])],.054,D,d,'drain/iron downpipe')
    for label,u,v,r in [('upper collar',685,261,.080),('hopper rim',686,275,.145),('lower collar',687,386,.070)]:
        x,z=xz(u,v);b.tube([(x,-.125,z-.052),(x,-.125,z+.052)],r,D,d,'drain/'+label)
    for label,u,v,width,height,depth in [('ridge stack',547,112,.77,.91,1.50),('west stack',448,171,.49,.94,1.90)]:
        x,z=xz(u,v);b.box((x,depth,z),(width,.56,height),B,label='chimney/'+label)
        b.box((x,depth,z+height/2), (width+.061,.620,.074),P,label='chimney/'+label+' coping')
    return b
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args()
    print(build(a.lod).save(a.output,META)['sha256'])
