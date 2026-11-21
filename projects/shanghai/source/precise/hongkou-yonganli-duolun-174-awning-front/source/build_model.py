"""Construct the named gateway, five upper window axes, and individual Dutch awnings of Yong'an Li."""
import argparse,hashlib,json,math,os,sys
from pathlib import Path
import numpy as np
from shapely.geometry import box,LineString,Polygon,Point
from shapely.ops import unary_union

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as RepeatBuilder
from photo_architecture import Facade
from pebbled_stucco import CAST,TEXTURE,apply_metric_uv
from fabric_canopies import CANVAS,STRIPE,LINING,PIPE,IRON,CORD,bonnet,slatted_box
from lane_gate import BLUE,MILK,LETTER,GREEN,SHOP,passage,shop
from lane_windows import STONE,SASH,GLASS,DARK,WARM,RECESS,PANEL,framed_window,spandrel

ID='hongkou-yonganli-duolun-174-awning-front'
META=dict(id=ID,name='永安里多伦路174号题名门与双窗条篷',heritage_group='4F015',
          viewer_page='yonganli-duolun-174-awning-front.html',
          scope='多伦路174号题名门及两侧相邻沿街开间。五个上层窗轴、弧面布篷、门灯、栏箱与店面以2020年街景为准。')
DIM=json.loads((SOURCE/'dimensions.json').read_bytes())


class AggregateBuilder(RepeatBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        file=Path(path);receipt=file.with_suffix('.geometry.json')
        if receipt.is_file():
            data=json.loads(receipt.read_bytes())
            with file.open('rb') as stream:data['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            data['bytes']=file.stat().st_size;receipt.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')


def pigment(rgb,rough=.82,metal=0.):
    v=np.array(rgb)/255.;return dict(color=np.where(v<.04045,v/12.92,((v+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)


PALETTE={CAST:dict(color=[1.,1.,1.],texture=str(TEXTURE),roughness=.93),STONE:pigment([144,145,137]),RECESS:pigment([103,105,101]),
         PANEL:pigment([166,164,151]),CANVAS:pigment([137,133,120],.96),STRIPE:pigment([171,171,158],.93),PIPE:pigment([183,182,167],.70,.10),
         IRON:pigment([70,73,70],.57,.24),CORD:pigment([63,64,60],.81),BLUE:pigment([62,75,82],.37,.10),MILK:pigment([198,207,203],.38),
         SASH:pigment([81,53,46],.66),GLASS:pigment([100,120,125],.28,.19),WARM:pigment([131,140,140],.28,.22),
         DARK:pigment([57,66,65],.56),LETTER:pigment([64,62,55]),GREEN:pigment([42,102,89],.42,.17),SHOP:pigment([122,92,76]),'Paper on street gate':pigment([186,178,171],.92)}


def projecting_course(f,z,thick,depth,mat,label):
    f.box(0,z,f.length,thick,depth+.31,(depth-.31)/2,mat,label)


def upper(f,centre,axes,mid,p,lod):
    cuts=[]
    for n,zkey,hkey in ((2,'sill_second','second_sash_height'),(3,'third_sill','third_sash_height')):
        sill=p[zkey];h=p[hkey]
        for u_global in axes:
            u=u_global-mid;sw=p['central_sash_width']if centre else p['ordinary_sash_width']
            hw=p['central_hood_width']if centre else p['ordinary_hood_width']
            cuts.append(framed_window(f,u,sill,sw,h,centre and n==2,lod))
            rise=.62 if centre else .52
            rim=sill+h-.135
            bonnet(f,u,rim,hw,.84 if centre else .68,rise,lod)
            if not centre:spandrel(f,u,sill-.64,sw+.20)
        if n==3 and not centre:
            # Short, separated parapet panels below the continuous roof coping.
            for u in axes:
                f.box(u-mid,p['parapet']-.21,p['ordinary_sash_width']+.22,.11,.052,.032,PANEL,'Parapet panels')
    f.wall(p['shop_cornice']-.021,p['parapet'],cuts,.31,CAST)
    projecting_course(f,p['shop_cornice']-.087,.169,.18,STONE,'Street cornice')
    projecting_course(f,p['shop_cornice']+.041,.057,.22,PANEL,'Street cornice lip')
    projecting_course(f,p['parapet']-.11,.161,.15,STONE,'Roof edge')
    projecting_course(f,p['parapet']-.019,.055,.185,PANEL,'Roof cap')
    # Separate floor edges behind the front cut are visible through open sashes and from above.
    for z in (p['shop_cornice']+.11,p['third_sill']-.81,p['parapet']-.19):
        f.box(0,z,f.length,.16,p['section_depth']-.30,-(p['section_depth']+.30)/2,STONE,'Floor and roof cut edges')
    if not lod:
        # Period photos distinguish narrow ruled horizontal stucco joints and
        # staggered vertical incisions from the thicker pier and sill mouldings.
        wall=box(-f.length/2,p['shop_cornice']+.19,f.length/2,p['parapet']-.24)
        wall=wall.difference(unary_union([a.buffer(.09,join_style=2)for a in cuts]))
        for k,z in enumerate(np.arange(p['shop_cornice']+.42,p['parapet']-.27,.45)):
            groove=box(-f.length/2,z-.006,f.length/2,z+.006)
            for x in np.arange(-f.length/2+.58+(k%2)*.47,f.length/2,.95):
                groove=groove.union(box(x-.006,z-.43,x+.006,z))
            surface=wall.intersection(groove)
            if not surface.is_empty:f.prism(surface,.001,.004,RECESS,'Ruled stucco joints')


def exposed_service_windows(f,north,axes,mid,p,lod):
    if north:
        for x in (-4.85,-1.38):
            # The inboard box lies beside the central opening, not across it.
            if abs(x-mid)<f.length/2+.55:slatted_box(f,x-mid,4.50,.99,.50,lod)
    else:
        x=axes[0]-mid
        f.box(x,4.87,.75,.37,.36,.252,PIPE,'Air conditioner casing')
        disk=Point(x,4.87).buffer(.143,quad_segs=10 if lod else 22)
        f.prism(disk,.431,.438,IRON,'Air conditioner grille')
        if not lod:
            for y in np.linspace(4.76,4.98,8):
                q=box(x-.142,y-.004,x+.142,y+.005).intersection(disk)
                if not q.is_empty:f.prism(q,.438,.445,PIPE,'Fan grille bars')


def add_building(b,lod):
    p=DIM;edges=p['facade_joints_u'];ax=p['sash_centres_u']
    for j,(a,end) in enumerate(zip(edges,edges[1:])):
        center=j==1;mid=(a+end)/2;name=('North paired shop','Number 174 gateway','South paired shop')[j]
        f=Facade(b,[0.,-a],[0.,-end],name)
        if center:passage(f,p,lod)
        else:shop(f,p,j==0,lod)
        axes=[x for x in ax if a<x<end]
        upper(f,center,axes,mid,p,lod)
        if not center:exposed_service_windows(f,j==0,axes,mid,p,lod)
        if center:slatted_box(f,-1.32,4.62,.99,.52,lod)
    # Wide entrance pilasters and individual narrow end piers below the coping.
    for u in edges:
        f=Facade(b,[0.,-u+.29],[0.,-u-.29],'Street pier')
        lo=p['shop_cornice']+.06;top=p['parapet']-.115;w=.29 if abs(u)<3 else .21
        f.box(0,(lo+top)/2,w,top-lo,.17,.037,CAST,'Full upper pier')
        for z in (p['sill_second']-.26,p['third_sill']-.25):
            f.box(0,z,w+.061,.12,.16,.072,STONE,'Pier band')
    # These end faces show only the requested section depth behind the front.
    for u,side in ((edges[0],-1),(edges[-1],1)):
        a=[0.,-u];end=[p['section_depth'],-u];v=Facade(b,*( (end,a) if side<0 else (a,end) ),'Section ends')
        v.wall(.083,p['parapet']-.03,(),.17,CAST)
    for part in b.parts:
        v=np.asarray(part['vertices']);offset=math.radians(p.get('yaw_enu_deg',0.))
        rot=np.array([[math.cos(offset),-math.sin(offset)],[math.sin(offset),math.cos(offset)]])
        v[:,:2]=v[:,:2]@rot.T;part['vertices']=v.tolist()
    apply_metric_uv(b)


if __name__=='__main__':
    pa=argparse.ArgumentParser(add_help=False);pa.add_argument('--output',type=Path);pa.add_argument('--lod',action='store_true');pa.add_argument('--blender',default='blender')
    args,rest=pa.parse_known_args()
    if args.output:
        if rest:pa.error('Unrecognised raw-export options')
        model=AggregateBuilder(PALETTE);add_building(model,args.lod);model.save(args.output,META)
    else:
        if args.lod:pa.error('--lod requires --output')
        os.environ['YONGANLI_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
