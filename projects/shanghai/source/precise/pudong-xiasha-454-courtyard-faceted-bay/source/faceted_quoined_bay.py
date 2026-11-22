"""Visible three planes of the west bay photographed inside the Xiasha courtyard."""
from pathlib import Path
import math,numpy as np
from PIL import Image
from shapely.geometry import box
ID='pudong-xiasha-454-courtyard-faceted-bay'
BRICK='Coursed grey brick';STONE='Rusticated corner blocks';WOOD='Weathered red casement';GLASS='Clouded blue glazing';DARK='Deep open casement';SOFFIT='Shadowed plank eaves';CAP='Mottled coping'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(BRICK,[1,1,1],.9),(STONE,[1,1,1],.92),(WOOD,[1,1,1],.78),(GLASS,[.39,.48,.50],.37),(DARK,[.075,.066,.056],.96),(SOFFIT,[.25,.22,.17],.88),(CAP,[.43,.45,.38],.91)]}
POINTS=[(-1.52,.74),(-.75,0),(.75,0),(1.52,.74)]
def texture():
    f=Path(__file__).with_name('grey-brick-quoin-and-red-sash.png')
    if not f.exists():
        rng=np.random.default_rng(883);h,w=360,256;y,x=np.indices((h,w))
        def broad(c,r):return np.asarray(Image.fromarray(rng.integers(0,255,(c,r),dtype='uint8')).resize((w,h),Image.Resampling.BILINEAR),float)-127
        row=y//14;bx=(x+(row%2)*17)//35
        diff=rng.integers(-20,17,(33,12))[row,bx];seams=(y%14<1)|((x+(row%2)*17)%35<1)
        brick=np.array([146,143,132])+(diff+.12*broad(18,40)+rng.normal(0,5.5,(h,w))-14*seams)[:,:,None]
        stone=np.array([176,170,151])+(.21*broad(14,18)+rng.normal(0,6.4,(h,w)))[:,:,None]
        wood=np.array([113,64,54])+(.16*broad(10,85)+.10*broad(6,10)+rng.normal(0,2.9,(h,w)))[:,:,None]
        Image.fromarray(np.concatenate((brick,stone,wood),axis=1).clip(0,255).astype('uint8')).quantize(224).save(f)
    for m in (BRICK,STONE,WOOD):PALETTE[m]['texture']=str(f)
def frame(i):
    x,y=POINTS[i];u,v=POINTS[i+1];length=math.hypot(u-x,v-y);return x,y,(u-x)/length,(v-y)/length,length
def position(i,s,depth,z):
    x,y,ux,uy,width=frame(i);return x+ux*s-uy*depth,y+uy*s+ux*depth,z
def add_building(b,far=False):
    texture()
    for i in range(3):
        x,y,ux,uy,width=frame(i);mid=width/2;half=(.447 if i==1 else .321)
        def part(shape,front,back,mat,label):
            start=len(b.parts);b.prism(shape,-back,-front,lambda s,z,d:position(i,s,-d,z),mat,label)
            if mat in (BRICK,STONE,WOOD):
                stripe=(BRICK,STONE,WOOD).index(mat)
                for p in b.parts[start:]:
                    p['texcoords']=[((stripe+.01+.98*min(1,max(0,((px-x)*ux+(py-y)*uy)/width)))/3,.99-.98*min(1,max(0,pz/2.81)))for px,py,pz in p['vertices']]
        def block(a,z,c,t,front,back,mat,label):part(box(a,z,c,t),front,back,mat,label)
        lower,upper=.78,2.21
        part(box(0,.045,width,2.62).difference(box(mid-half,lower,mid+half,upper)),.018,.21,BRICK,'Faceted grey wall pierced for the rectangular sash')
        for level in range(12):
            z=.056+level*.212
            for side in (0,1):
                ext=.147 if (side+i+level)%2 else .215
                a=0 if side==0 else width-ext
                block(a,z,a+ext,z+.196,-.048,.06,STONE,'Alternating long and short quoin return')
        block(mid-half-.072,.703,mid+half+.072,.787,-.119,.11,STONE,'Pale projecting window sill')
        block(mid-half-.021,upper-.016,mid+half+.021,upper+.067,-.031,.12,STONE,'Upper lintel facing')
        for side in (-1,1):
            c=mid+side*(half-.026);block(c-.025,lower,c+.025,upper,-.008,.11,WOOD,'Red timber outer jamb')
        for z in (lower+.035,upper-.034):block(mid-half,z-.029,mid+half,z+.029,-.012,.11,WOOD,'Red sill or head rail')
        block(mid-.022,lower,mid+.022,upper,-.016,.11,WOOD,'Vertical meeting stile')
        for leaf in (0,1):
            a=mid-half+.049 if leaf==0 else mid+.023;c=mid-.022 if leaf==0 else mid+half-.049
            if leaf==1 and i==1:
                block(a,lower+.065,c,upper-.060,.17,.18,DARK,'Shadow behind the open right half')
            else:
                block(a,lower+.065,c,upper-.061,.063,.076,GLASS,'Blue or grey timber sash glazing')
                for ind in (1,2,3):
                    z=lower+.06+(upper-lower-.12)*ind/4
                    block(a,z-.012,c,z+.012,.018,.075,WOOD,'Slender horizontal sash bar')
        for z,depth,h,mat in ((2.59,.15,.086,STONE),(2.678,.235,.068,SOFFIT),(2.744,.258,.055,CAP)):
            block(-.06,z,width+.06,z+h,-depth,.21,mat,'Stepped projecting eave above the bay')
        if not far:
            # Closely spaced rafter ends make a broken dark line under the projecting fascia.
            for s in np.linspace(.06,width-.06,round(width/.10)):
                block(s-.017,2.615,s+.017,2.671,-.228,-.103,SOFFIT,'Small underside rafter below the edge of the eaves')
            for origin in (.028,width-.126):
                for level in range(1,11):
                    z=.056+.212*level
                    block(origin,z-.011,origin+.096,z+.002,-.047,-.023,STONE,'Thin recessed return of the alternating stone course')
