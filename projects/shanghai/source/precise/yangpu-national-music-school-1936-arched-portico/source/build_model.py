"""A local 1936 study of the National Music School's photographed central portal and roof."""
import argparse,hashlib,json,math,os,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box

SOURCE=Path(__file__).absolute().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as MetricBuilder
from photo_architecture import Facade
from plaster import CAST,TEXTURE,apply_metric_uv
from pavilion_roof import TILE,PALE,FASCIA,LIP,build as build_roof

META=dict(id='yangpu-national-music-school-1936-arched-portico',name='国立音乐专科学校正校舍中央券门与四坡顶（1936年特刊）',
          heritage_group='4G012',viewer_page='national-music-school-1936-arched-portico.html',scope='1936年落成特刊所见的正校舍中央券门、上部方亭四坡顶和紧贴券门的檐口截段。')
D=json.loads((SOURCE/'dimensions.json').read_bytes())
R=json.loads((SOURCE.parent/'measurements/joint-camera-and-roof.json').read_bytes())
STONE='Pale entrance surround';BASE='Low plinth stone';SHADOW='Neutral photographic shadow';WALL='Upper pavilion in shade'
WOOD='Gallery post in shade';LIGHT='Eave trim';SOFFIT='Gallery soffit';TREAD='Honed threshold'
def pigment(g,rough=.85):
    c=g/255;return dict(color=[((c+.055)/1.055)**2.4]*3,roughness=rough)
PALETTE={CAST:dict(color=[1.,1.,1.],roughness=.94,texture=str(TEXTURE)),STONE:pigment(214),BASE:pigment(177),
         SHADOW:pigment(49),WALL:pigment(96),WOOD:pigment(77),LIGHT:pigment(159),SOFFIT:pigment(112),
         TREAD:pigment(169),TILE:pigment(105,.9),PALE:pigment(117),FASCIA:pigment(77),LIP:pigment(122)}
class AggregateBuilder(MetricBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        p=Path(path);f=p.with_suffix('.geometry.json')
        if f.is_file():
            r=json.loads(f.read_bytes())
            with p.open('rb')as stream:r['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            r['bytes']=p.stat().st_size;f.write_text(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')

def arch(rad,spring,bottom,n):
    pts=[(-rad,bottom),(rad,bottom),(rad,spring)]
    pts.extend((rad*math.cos(i*math.pi/n),spring+rad*math.sin(i*math.pi/n))for i in range(1,n+1))
    return Polygon(pts)

def portal(builder,face,lod):
    l=D['wall_left'];r=D['wall_right'];h=D['wall_top'];s=D['spring'];rad=D['clear_width']/2;base=D['ground'];n=28 if lod else 68
    hole=arch(rad,s,base-.01,n)
    face.prism(box(l,base,r,h).difference(hole),-.60,0,CAST,'pale portal with arch reveal')
    rim=arch(rad+.135,s,base-.01,n).difference(hole)
    face.prism(rim,.002,.071,STONE,'continuous round archivolt and jamb')
    # The low inward shoulders beneath the spring have a separate return.
    for i,side in enumerate([-1,1]):
        label='Jamb '+str(i+1);cx=side*(rad-.045)
        face.box(cx,(base+s-.065)/2,.09,s-.065-base,.41,-.24,BASE,label+' inset reveal stop')
        face.box(side*(rad+.052),s-.030,.18,.075,.22,-.035,STONE,label+' spring shoulder')
    for i,(a,b)in enumerate([(l,-rad-.01),(rad+.01,r)]):
        out='Foot '+str(i+1)
        for z0,z1,prot,w,mat,name in [(base,-.12,.085,.03,BASE,'plinth'),(-.12,-.045,.112,.05,STONE,'plinth bead'),
                                       (-.045,.055,.078,.03,BASE,'cap')]:
            face.box((a+b)/2,(z0+z1)/2,b-a+w,z1-z0,.60+prot,(prot-.60)/2,mat,out+' '+name)
    for name,z0,z1,p,mat in [('upper mould',h-.11,h-.065,.067,BASE),('upper cornice',h-.065,h+.023,.094,STONE)]:
        face.box((l+r)/2,(z0+z1)/2,r-l+.085,z1-z0,.67+p,(p-.67)/2,mat,name)
    # Studio backing is separate from the actual vault. It represents an
    # unresolved dark opening on the printed plate, with no inferred doors.
    face.prism(arch(rad+.28,s,base+.009,n),-1.47,-1.445,SHADOW,'archival shadow backing')
    builder.box((0,.31,base+.036),(rad*2-.08,1.27,.072),TREAD,label='Entry/threshold')
    for side in [-1,1]:
        x=side*(rad+.14)
        builder.box((x,.92,(base+s)/2),(.29,.74,s-base),BASE,label='Entry/deep jamb return')
    shell=arch(rad+.17,s,s-.015,n).difference(arch(rad,s,s-.025,n))
    face.prism(shell,-1.45,-.595,BASE,'curved inner soffit')

def gallery(builder,face,lod):
    l=D['wall_left'];r=D['wall_right'];h=D['wall_top'];base=D['ground'];rz=R['left_front_eave_xyz'][2]
    x0,y0,_=R['left_front_eave_xyz'];x1,y1,_=R['right_rear_eave_xyz']
    # The pale front projects in front of the adjacent eave; only its neighbouring short sections are shown.
    for i,(a,b) in enumerate([(l-2.02,l+.02),(r-.02,r+2.38)]):
        cx=(a+b)/2;span=b-a;prefix='Gallery '+str(i+1)
        builder.box((cx,.65,base+.045),(span,1.9,.09),BASE,label=prefix+'/section floor')
        for za,zb,depth,y,mat,name in [(h-.77,h-.70,1.72,.63,SOFFIT,'deep soffit'),(h-.70,h-.49,1.72,.63,WOOD,'fascia'),
                    (h-.49,h-.43,1.77,.625,LIGHT,'drip return')]:
            builder.box((cx,y,(za+zb)/2),(span,depth,zb-za),mat,label=prefix+'/'+name)
        for j,xx in enumerate([a+.16,b-.16]):
            for z0,z1,wid,mat,name in [(base,base+.23,.32,BASE,'shoe'),(base+.23,h-.97,.20,WOOD,'post'),(h-.97,h-.76,.31,WOOD,'post head')]:
                builder.box((xx,.42,(z0+z1)/2),(wid,wid,z1-z0),mat,label=prefix+'/'+name+' '+str(j+1))
        # Single horizontal strip where the roof of each adjacent wing meets the tower.
        front=Facade(builder,(a,.19),(b,.19),prefix)
        for j in range(2 if i==0 else 3):
            w=span/(2 if i==0 else 3);x=-span/2+(j+.5)*w
            front.box(x,h-.025,w-.07,.66,.115,-.11,SHADOW,'dark upper gallery bay')
            front.box(x-w*.48,h-.02,.046,.75,.125,-.008,LIGHT,'bay division')
        builder.box((cx,.27,h+.34),(span,.30,.065),FASCIA,label=prefix+'/upper band')
    # Continuous upper enclosure, limited to the walls directly below the archived roof.
    bounds=box(x0+.79,y0+.76,x1-.77,y1-.67)
    builder.plan_prism(bounds,h+.025,rz-.17,WALL,'Upper pavilion/shaded wall envelope')
    # Below the photographed upper block, neutral vertical cuts close the
    # cropped volume behind the gallery and support the rear roof silhouette.
    section_left=x0+.82;section_right=x1-.81;back=y1-.70
    builder.box(((section_left+section_right)/2,back-.08,(h+base)/2),
                (section_right-section_left,.16,h-base),SOFFIT,label='Section/rear vertical cut')
    for j,xx in enumerate([section_left+.07,section_right-.07]):
        builder.box((xx,(1.52+back)/2,(h+base)/2),(.14,back-1.52,h-base),SOFFIT,label='Section/side cut '+str(j+1))
    for i,(a,b) in enumerate([(l-2.02,l),(r,r+2.38)]):
        builder.box(((a+b)/2,1.51,(h-.74+base)/2),(b-a,.105,h-.74-base),SOFFIT,label='Gallery '+str(i+1)+'/shadow section')
        builder.box(((a+b)/2,1.447,base+.24),(b-a,.055,.48),BASE,label='Gallery '+str(i+1)+'/low backing plinth')
    for k,drop in enumerate([.31,.19]):
        builder.plan_prism(bounds.buffer(.08+k*.06,join_style=2),rz-drop,rz-drop+.043,FASCIA,'Upper pavilion/eaves bedding '+str(k+1))
    # Exposed brackets at the two lateral eave returns. The heavily shaded
    # upper wall is left free of unverified window joinery.
    for side,x,y in [('left',x0+.85,y0+.76),('right',x1-.80,y1-.68)]:
        for j in range(3 if lod else 5):
            yy=y+(j-2)*.14
            builder.tube([(x,yy,rz-.51),(x+(-.48 if side=='left' else .48),yy,rz-.16)],.033,WOOD,6 if lod else 8,label='Upper pavilion/'+side+' eave brackets')
def add_building(builder,lod):
    face=Facade(builder,(-.5,0),(.5,0),'Portico')
    portal(builder,face,lod);gallery(builder,face,lod);build_roof(builder,R,lod);apply_metric_uv(builder)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender');args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for a raw mesh')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['HISTORIC_MUSIC_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
