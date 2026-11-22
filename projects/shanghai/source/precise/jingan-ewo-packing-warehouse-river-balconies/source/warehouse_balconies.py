"""A double gallery on the river wall at 912 North Suzhou Road, after the 2015 photograph."""
import math


def finish(rgb,rough=.9,metal=0):
    return dict(color=[v/3294.6 if v<=10 else ((v/255+.055)/1.055)**2.4 for v in rgb],roughness=rough,metallic=metal)


PALETTE={'brick red':finish((160,79,51)),'burnt red':finish((145,67,43)),'brick highlight':finish((178,91,60)),
         'mortar':finish((153,107,83)),'rebated door':finish((55,51,44)),'shutter':finish((62,57,48)),
         'gallery iron':finish((59,61,54),.75,.24),'edge of deck':finish((55,55,48),.86,.16)}


def box(b,l,r,f,back,z0,z1,material,name):
    b.box(((l+r)/2,(f+back)/2,(z0+z1)/2),(r-l,back-f,z1-z0),material,label=name)


def head(z,x,half):
    return z+.077*(1-(x/half)**2)


def head_brick(b,left,right,half,base,mat,front=-.054):
    outline=[(left,head(base,left,half)),(right,head(base,right,half)),(right,head(base,right,half)+.153),(left,head(base,left,half)+.153)]
    verts=[(x,y,z) for y in (front,.20)for x,z in outline]
    b.add(verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,'segmental red-brick head')


def gallery(b,level,upper,lod):
    half=.48 if upper else .76;base=level;top=level+(2.02 if upper else 2.20);sides=5 if lod else 10
    # Two different door widths are visible above identical iron balcony fronts.
    for l,r in ((-1.32,-half),(half,1.32)):
        box(b,l,r,0,.31,base,top+.23,'mortar','side of brick opening')
        for course in range(math.ceil((top+.23-base)/.129)):
            z=base+course*.129
            if z>=top+.223:continue
            start=l-(.113 if course%2 else 0)
            j=0
            while start<r:
                end=min(start+.275,r);lo=max(start,l)
                if end-lo>.015:
                    mat=('brick red','burnt red','brick highlight','brick red')[(j+course*3+int(upper))%4]
                    box(b,lo+.003,end-.003,-.015,.011,z+.004,min(z+.126,top+.23),mat,'individual face brick')
                j+=1;start+=.275
    box(b,-half,half,.155,.222,base+.02,top,'rebated door','recessed dark gallery doors')
    for x in (-half+.028,0,half-.028):
        box(b,x-.020,x+.020,.119,.165,base+.03,top-.01,'shutter','door side and meeting rail')
    for z in [base+.09,base+.57,base+1.11,top-.07]:
        box(b,-half+.035,half-.035,.126,.158,z-.018,z+.018,'shutter','shallow door rails')
    # Narrow head band is segmented around the shallow rise over the opening.
    for j in range(16):
        l=-half+2*half*j/16;r=-half+2*half*(j+1)/16
        head_brick(b,l,r,half,top,'mortar',front=-.045)
    for i in range(16 if upper else 23):
        count=16 if upper else 23;x0=-half+.001+2*half*i/count;x1=-half-.001+2*half*(i+1)/count
        head_brick(b,x0,x1,half,top,'burnt red' if i%4==0 else 'brick red')
    for z,depth,h in ((base-.12,-.71,.116),(base-.052,-.74,.054)):
        box(b,-1.18,1.18,depth,.12,z,z+h,'edge of deck','two-level balcony fascia')
    for x in (-1.145,1.145):
        for y in (-.68,-.04):
            box(b,x-.022,x+.022,y-.022,y+.022,base-.02,base+.77,'gallery iron','rectangular corner post')
        for z in (base+.06,base+.73):
            b.tube([(x,-.68,z),(x,-.005,z)],.015,'gallery iron',sides,'balcony return rail')
        for y in (-.53,-.38,-.23):
            b.tube([(x,y,base+.06),(x,y,base+.73)],.009,'gallery iron',sides,'side gallery baluster')
    for z,rad in ((base+.057,.014),(base+.73,.020)):
        b.tube([(-1.16,-.68,z),(1.16,-.68,z)],rad,'gallery iron',sides,'street-facing horizontal')
    for i in range(1,21):
        x=-1.145+2.29*i/21
        b.tube([(x,-.68,base+.05),(x,-.68,base+.738)],.009,'gallery iron',sides,'iron baluster')
    for x in (-1.11,0,1.11):
        b.tube([(x,-.60,base-.14),(x,-.04,base-.43)],.026,'gallery iron',sides,'short diagonal gallery bracket')
    return top+.23


def add_building(b,lod=False):
    first=gallery(b,.43,False,lod)
    second=gallery(b,3.19,True,lod)
    for l,r in ((-1.32,1.32),):
        box(b,l,r,0,.31,0,.42,'brick red','street sill course')
        box(b,l,r,.007,.31,first,3.19,'brick red','brick spandrel between balconies')
        box(b,l,r,.007,.31,second,5.58,'brick red','upper brick spandrel')
    for z in (.09,.19,2.91,3.014,5.46):
        box(b,-1.32,1.32,-.033,.032,z,z+.035,'burnt red','projecting brick stringcourse')
