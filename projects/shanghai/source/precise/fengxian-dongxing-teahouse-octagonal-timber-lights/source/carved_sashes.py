"""Four adjacent upper leaves of the Dongxing teahouse on Zhuanghang East Street."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon
ID='fengxian-dongxing-teahouse-octagonal-timber-lights'
POST='Polished dark red outer frame'; BAR='Smaller brown lattice mouldings'; PANE='Reflected daylight in octagonal glass'; MORTISE='Recesses between joined bars'; SILL='Weathered sill rail and carved drops'
PALETTE={name:dict(color=c,roughness=r)for name,c,r in [(POST,[1,1,1],.80),(BAR,[1,1,1],.72),(PANE,[.69,.78,.77],.30),(MORTISE,[.115,.089,.074],.97),(SILL,[1,1,1],.83)]}
CENTRES=(-.78,-.26,.26,.78)
def texture():
    dest=Path(__file__).with_name('timber-grain.png')
    if not dest.exists():
        rng=np.random.default_rng(899);h,w=260,230;y,x=np.indices((h,w));long=np.array(Image.fromarray(rng.integers(0,255,(7,79),dtype='uint8')).resize((w,h),Image.Resampling.BICUBIC),float)-128
        grain=.19*long+2*np.sin(x*.64+.21*np.sin(y*.037))+rng.normal(0,2.3,(h,w))
        colors=([100,69,56],[128,93,73],[105,86,71])
        Image.fromarray(np.concatenate([np.array(c)+grain[:,:,None]for c in colors],axis=1).clip(0,255).astype('uint8')).quantize(192).save(dest)
    for mat in (POST,BAR,SILL):PALETTE[mat]['texture']=str(dest)
def light(cx,low,top):
    h=.173;cut=.057
    return Polygon([(cx-h+cut,low),(cx+h-cut,low),(cx+h,low+cut),(cx+h,top-cut),(cx+h-cut,top),(cx-h+cut,top),(cx-h,top-cut),(cx-h,low+cut)])
def add_building(b,far=False):
    texture()
    def piece(shape,face,back,mat,name):
        start=len(b.parts);b.prism(shape,-back,-face,lambda x,z,d:(x,-d,z),mat,name)
        if mat in (POST,BAR,SILL):
            band=(POST,BAR,SILL).index(mat)
            for part in b.parts[start:]:
                part['texcoords']=[((band+.015+.97*((x+1.24)/2.48))/3,.995-.988*z/2.18)for x,d,z in part['vertices']]
    def block(x,z,r,t,face,back,mat,name):piece(box(x,z,r,t),face,back,mat,name)
    for i,c in enumerate(CENTRES):
        for side in (-1,1):
            j=c+side*.223;block(j-.029,.337,j+.029,2.012,-.017,.084,POST,'Wide vertical stile of leaf '+str(i+1))
        block(c-.195,.336,c+.195,.385,-.015,.084,POST,'Lower rail of leaf '+str(i+1))
        block(c-.195,1.97,c+.195,2.013,-.015,.084,POST,'Top rail of leaf '+str(i+1))
        block(c-.197,.383,c+.197,1.973,.085,.10,MORTISE,'Dark reveal behind the lattice intersections')
        for label,z,t in [('lower',.444,1.07),('upper',1.278,1.906)]:
            polygon=light(c,z,t);piece(polygon,.026,.045,PANE,label+' glass with clipped corners')
            piece(polygon.buffer(.015,join_style=2).difference(polygon),-.016,.047,BAR,'Eight-sided wood lip of '+label+' glass')
            for s in (-1,1):
                for end,direction in [(z,1),(t,-1)]:
                    xx=c+s*.161;ec=end+direction*.016
                    block(min(xx,c+s*.196),ec-.008,max(xx,c+s*.196),ec+.008,-.018,.05,BAR,'Short return into the corner of the sash')
                    block(xx-.007,ec-.048,xx+.007,ec+.048,-.020,.05,BAR,'Short vertical at a clipped corner')
        for z in (1.126,1.199):
            block(c-.195,z-.011,c+.195,z+.011,-.020,.057,BAR,'Pair of full-width rails through the central lattice')
        for x in (c-.111,c+.111):block(x-.008,1.083,x+.008,1.261,-.020,.054,BAR,'Small upright connecting the centre rails')
        if not far:
            for z in (.412,1.946):
                for s in (-1,1):
                    xx=c+s*.124;block(xx-.007,z-.025,xx+.007,z+.027,-.021,.040,BAR,'Small bottom or top block in the return')
    for x in (-1.080,1.080):block(x-.045,.24,x+.045,2.059,-.048,.142,POST,'Outside jamb of the excerpt')
    for z,h,depth,mat,name in [(.305,.049,.105,POST,'Continuous sill above the pierced apron'),(.079,.053,.157,SILL,'Lower rail through the slot course'),(.035,.046,.173,SILL,'Broad moulded lower edge'),(2.008,.094,.110,POST,'Upper lintel and shadow')]:
        block(-1.14,z,1.14,z+h,-depth,.145,mat,name)
    for x in np.linspace(-1.070,1.070,15):
        pts=[(x-.045,.30),(x+.045,.30),(x+.045,.245),(x+.031,.225),(x+.024,.139),(x-.030,.139),(x-.034,.229),(x-.045,.252)]
        piece(Polygon(pts),-.072,.074,SILL,'Shaped wood drop between vertical slots underneath the sill')
    if not far:
        for z in (.063,.093,2.027):block(-1.14,z,1.14,z+.009,-.178 if z<1 else -.116,.02,SILL,'Fine projecting edge on the sill and lintel')
