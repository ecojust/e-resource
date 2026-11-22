"""Present-day recessed transom and folded iron grilles at 205 East Beijing Road."""
from pathlib import Path
from profile_tools import cb,bricks_uv,BRICK as STONE
GREEN='Green paint on folded iron slats'
FRAME='Green angle-section frame'
WOOD='Brown painted lintel and window frame'
GLASS='Dark upper window glass'
TRIM='Pale moulded plaster plinth'
PALETTE={}
for key,col in [(STONE,(255,255,255)),(GREEN,(63,105,99)),(FRAME,(54,88,81)),(WOOD,(85,60,57)),(GLASS,(78,74,68)),(TRIM,(162,161,151))]:
    PALETTE[key]=dict(color=[(v/255)**2.2 for v in col],roughness=.43 if key==GLASS else .82)
PALETTE[STONE]['texture']=str(Path(__file__).with_name('finish.png'))
CENTRES=[-.472,-.282,-.092,.098,.288,.478]
BANDS=[(.095,.92),(1.23,1.97)]
def model(b,lod=False):
    for x in (-.866,.866):
        cb(b,x-.129,x+.129,-.04,.24,0,3.53,STONE,'Plastered reveal beside street entrance')
        cb(b,x-.147,x+.147,-.106,.24,0,.415,TRIM,'Broader stone plinth')
        cb(b,x-.153,x+.153,-.121,.24,.415,.455,TRIM,'Lip above plinth')
        if not lod:cb(b,x-.146,x+.146,-.103,.22,.56,.589,TRIM,'Second small relief on lower jamb')
    cb(b,-1.017,1.017,-.063,.24,3.51,3.68,STONE,'Single stone head across the opening')
    cb(b,-1.035,1.035,-.092,.24,3.65,3.71,TRIM,'Projecting upper edge')
    cb(b,-.737,.737,.059,.196,2.4,2.625,WOOD,'Deep horizontal timber below transom')
    cb(b,-.719,.719,.147,.17,2.643,3.485,GLASS,'Transom glazing behind metal bars')
    for x in [-.704+i*1.408/8 for i in range(9)]:
        cb(b,x-.009,x+.009,.107,.151,2.635,3.487,WOOD,'Upright in transom')
    for z in (2.637,3.095,3.48):
        cb(b,-.725,.725,.092,.16,z-.017,z+.017,WOOD,'Transom head, intermediate rail or sill')
    for x in (-.696,.696):
        cb(b,x-.023,x+.023,.015,.082,.04,2.396,FRAME,'Green outer door stile')
    for z in (.050,.951,1.198,2.005,2.376):
        cb(b,-.712,.712,.01,.086,z-.018,z+.018,FRAME,'Horizontal rail across grille')
    cb(b,-.675,.675,.034,.075,.952,1.210,GREEN,'Plain central plate separating the two grilles')
    # Six small rectangular meanders terminate alternately at the lower/upper rail.
    for lo,hi in BANDS:
        for n,x in enumerate(CENTRES):
            for dx in (-.078,.078):
                cb(b,x+dx-.008,x+dx+.008,.024,.061,lo,hi,GREEN,'Outer sides of one folded rectangle')
            zz=hi-.014 if lo<1 else lo+.014
            cb(b,x-.078,x+.078,.023,.062,zz-.008,zz+.008,GREEN,'Short return along the head or foot')
            for dx in (-.038,.038):
                start,end=(lo+.010,hi-.087) if lo<1 else (lo+.087,hi-.010)
                cb(b,x+dx-.007,x+dx+.007,.021,.052,start,end,GREEN,'Pair of short returns inside the folded rectangle')
            if not lod:
                for dx in (-.078,.078):
                    cb(b,x+dx-.003,x+dx+.003,.017,.024,lo+.018,hi-.018,FRAME,'Rolled edge of iron strip')
    for i in range(11):
        x=-.640+i*.128
        cb(b,x-.008,x+.008,.024,.072,2.025,2.36,GREEN,'Straight head bars')
    bricks_uv(b)
