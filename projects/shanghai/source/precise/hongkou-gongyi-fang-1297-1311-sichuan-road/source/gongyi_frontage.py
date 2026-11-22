"""Repaired street walls, true openings, projecting galleries, glazing and the two roof forms."""
from pathlib import Path
import json
import math
import numpy as np
from shapely.geometry import Polygon, box as rect
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE.parent/'measurements/frontage-measurements.json').read_text())
N=DATA['north_width']; S=DATA['south_width']; DEPTH=DATA['south_windows']['model_depth']
COURSE='1号楼 | 红褐清水砖'; LIGHT='1号楼 | 浅褐窗间面砖'; RENDER='1号楼 | 灰白粉刷面'
STONE='1号楼 | 米灰汰石子'; LIGHTSTONE='1号楼 | 石饰凸线'; SHADE='1号楼 | 廊下暗灰'
TIMBER='1号楼 | 红褐漆木'; WROUGHT='1号楼 | 黑漆铁花'; METAL='1号楼 | 深色金属'
GLASS='1号楼 | 窗玻璃'; BLUE='1号楼 | 窗玻璃冷色'; SHOP='1号楼 | 商铺暗玻璃'; TILE='1号楼 | 坡屋面陶瓦'
SCREEN='1号楼 | 浅绿透光屏'; SCREENBAR='1号楼 | 屋顶青灰框'; NORTHSTONE='1号楼 | 北端暖灰框架'; CAPCASE='1号楼 | 屋面浅褐外壳';
COPING='1号楼 | 平顶及铅皮'; TILELINE='1号楼 | 陶瓦脊缘'
def material(color,rough=.78,metal=0):return {'color':color,'roughness':rough,'metallic':metal}
PALETTE={SCREEN:material([.16,.43,.40],.26,.07),SCREENBAR:material([.21,.37,.40],.48,.35),NORTHSTONE:material([.48,.40,.27]),CAPCASE:material([.58,.53,.39]),COURSE:material([.47,.22,.13]), LIGHT:material([.68,.55,.42]), RENDER:material([.69,.665,.595]),
 STONE:material([.51,.478,.397]),LIGHTSTONE:material([.674,.635,.53]),SHADE:material([.248,.242,.21]),
 TIMBER:material([.155,.059,.049],.56),WROUGHT:material([.066,.067,.057],.55,.28),METAL:material([.078,.092,.079],.47,.30),
 GLASS:material([.182,.270,.275],.24,.19),BLUE:material([.135,.204,.23],.26,.13),SHOP:material([.076,.124,.118],.27,.24),
 TILE:material([.395,.214,.155]),COPING:material([.357,.358,.331]),TILELINE:material([.40,.24,.18])}
def box(b,x0,x1,y0,y1,z0,z1,m,label):
 b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),m,label=label)
def plane(u,z,out):return (u,-out,z)
def skin(b,poly,y0,y1,m,label):
 b.prism(poly,-y1,-y0,plane,m,label)
def wall(b,x0,x1,y0,y1,z0,z1,openings,m,label):
 holes=[rect(xa,za,xb,zb) for xa,xb,za,zb in openings]
 skin(b,rect(x0,z0,x1,z1).difference(unary_union(holes)),y0,y1,m,label)
def surround(b,x0,x1,z0,z1,y,w,d,m,label,sill=True):
 shape=rect(x0-w,z0-(w if sill else 0),x1+w,z1+w).difference(rect(x0,z0-.0001,x1,z1))
 skin(b,shape,y-d,y+.012,m,label)
def timber_leaf(b,a,c,z0,z1,y,mat,label,pair=True,kick=False):
 mid=(a+c)/2; width=c-a; high=z1-z0
 transom=z1-min(.44,.27*high);j=.046 if pair else .039
 pane=BLUE if int((a+S)*10)%3==1 else GLASS
 box(b,a+.012,c-.012,y+.066,y+.092,z0+.014,z1-.014,pane,label+' glass')
 surround(b,a+j,c-j,z0+j,z1-j,y,j,.037,mat,label+' fixed frame')
 box(b,a+j,c-j,y-.023,y+.066,transom-.032,transom+.031,mat,label+' transom')
 for frac in ((.25,.5,.75) if kick else (.5,)):
  x=a+width*frac
  box(b,x-.014,x+.014,y+.006,y+.058,transom+.032,z1-j,mat,label+' upper lights')
 box(b,mid-.027,mid+.027,y-.025,y+.06,z0+j,transom-.031,mat,label+' meeting stile')
 # North balcony leaves have a solid panel below the glazed part and a narrow moulding on it.
 base=z0
 if kick:
  kicktop=z0+.27*high
  for lo,hi in [(a+j,mid-.027),(mid+.027,c-j)]:
   box(b,lo,hi,y+.013,y+.064,z0+j,kicktop,TIMBER,label+' timber panels')
   surround(b,lo+.04,hi-.04,z0+.11,kicktop-.068,y,.018,.02,TIMBER,label+' panel moulding')
  box(b,a+j,c-j,y-.016,y+.06,kicktop-.028,kicktop+.028,mat,label+' lower rails')
  base=kicktop
 for frac in ([.52] if kick else [.5]):
  z=base+(transom-base)*frac;box(b,a+j,c-j,y+.008,y+.044,z-.013,z+.013,mat,label+' muntins')
 if kick:
  # Top and bottom glass carry fine straight glazing bars, visible behind the freer balcony ironwork.
  for lo,hi in [(a+j,mid-.027),(mid+.027,c-j)]:
   cen=(lo+hi)/2
   box(b,cen-.009,cen+.009,y+.021,y+.047,base+.025,transom-.03,mat,label+' glazing bars')
def curve(points,thick,closed=False):
 from shapely.geometry import LineString
 coords=list(points)
 if closed:coords.append(coords[0])
 return LineString(coords).buffer(thick/2,cap_style=2,join_style=2)
def iron_tile(b,x0,x1,z0,z1,y,lod,label,wheel):
 # Flat-wrought sections at three depths retain clear holes and identifiable units.
 wid=x1-x0; hei=z1-z0;cx=(x0+x1)/2;cz=z0+.56*hei
 from shapely.geometry import LineString
 parts=[]
 def path(pts,w=.018,closed=False):parts.append(curve(pts,w,closed))
 for frac in [0,1]:
  v=x0+wid*frac;path([(v,z0),(v,z1)])
 for z in [z0+.075,z1-.108]:path([(x0,z),(x1,z)])
 seg=24 if not lod else 12
 def ring(x,z,rx,rz):
  path([(x+rx*math.cos(t),z+rz*math.sin(t)) for t in np.linspace(0,math.tau,seg,endpoint=False)],.018,True)
 if wheel:
  # Figure 17 shows six straight spokes, four square scrolls, and shallow hoops to the sides.
  radius=.198*hei;ring(cx,cz,radius,radius)
  for theta in [0,math.pi/3,2*math.pi/3]:
   dx=radius*math.cos(theta);dz=radius*math.sin(theta)
   path([(cx-dx,cz-dz),(cx+dx,cz+dz)],.021)
  for sign in [-1,1]:
   for up in [-1,1]:
    root=cx+sign*.345*wid;tip=cz+up*.302*hei;inside=root-sign*.135*wid
    path([(root,cz),(root,tip),(inside,tip),(inside,tip-up*.117),(inside+sign*.069,tip-up*.117),(inside+sign*.069,tip-up*.059)],.020)
  for frac in [.11,.89]:
   v=x0+frac*wid;path([(v,z0+.075),(v,z1-.107)])
  if not lod:
   ring(cx,z1-.045,.050,.042);path([(cx,z0+.035),(cx,z0+.235)])
 else:
  for frac in [.08,.27,.44,.55,.72,.92]:
   v=x0+frac*wid;path([(v,z0+.076),(v,z1-.17)])
  for side in [-1,1]:
   vx=cx+side*.40*wid
   for iz in [z0+.18,z1-.23]:
    path([(vx,iz),(vx-side*.095,iz),(vx-side*.095,iz+.065),(vx-side*.043,iz+.065),(vx-side*.043,iz+.027)],.02)
  ring(cx,z1-.188,hei*.060,hei*.082)
  if not lod:
   for s in [-1,1]:ring(cx+s*.082,z1-.206,.057,.074)
 shape=unary_union(parts)
 skin(b,shape,y-.012,y+.012,WROUGHT,label)
def pier(b,x,z,top,lab,wide=.39):
 # Front faces of the two tiers differ. Each central pier has a projecting square low plinth and stepped head.
 body=.43 if top else .45
 box(b,x-wide/2,x+wide/2,-.07,.40,z,z+body*2.1,STONE,lab+' square stem')
 box(b,x-wide*.61,x+wide*.61,-.103,.42,z,z+.20,LIGHTSTONE,lab+' base')
 box(b,x-wide*.66,x+wide*.66,-.141,.44,z+.85,z+.99,LIGHTSTONE,lab+' cap')
 for off in [-.082,.082]:
  box(b,x+off-.03,x+off+.03,-.115,-.065,z+.49,z+.69,LIGHTSTONE,lab+' low relief')
def north(b,lod):
 photo=DATA['north_photo'];px=lambda u:(u-162)*(N/(659-162));z=lambda v:(410.8-v)*(N/(659-162));y_back=1.39
 axes=[px(u) for u in photo['corner_axes_u']]
 groups=[(px(x),px(y)) for x,y in photo['leaf_u_intervals']]
 deck=[z(269.9),z(144.3)];caps=[z(189),z(70)];par=z(15.8);eave=z(43.5)
 holes=[(x0,x1,low+.038,high) for low,high in zip(deck,caps) for x0,x1 in groups]
 wall(b,0,N,y_back,y_back+.27,deck[0]-.24,eave,holes,COURSE,'North | brick with twelve real holes')
 # Ground-floor three modern shop openings behind the stone supports.
 shops=[(axes[i]+.25,axes[i+1]-.25,.08,deck[0]-.52) for i in range(3)]
 wall(b,0,N,.15,.48,0,deck[0]+.05,shops,STONE,'North | three shop surrounds')
 for i,(a,c,z0,z1) in enumerate(shops):store_glazing(b,a,c,z0,z1,.21,'North shop '+str(i+1))
 for li,(low,head) in enumerate(zip(deck,caps),2):
  for i,(a,c) in enumerate(groups,1):
   lab=f'North L{li} leaf {i}'
   surround(b,a,c,low+.038,head,y_back,.17,.10,STONE,lab+' stone architrave')
   box(b,a-.22,c+.22,y_back-.14,y_back+.04,head+.14,head+.19,LIGHTSTONE,lab+' head drip')
   timber_leaf(b,a,c,low+.038,head,y_back+.09,TIMBER,lab,True,True)
  box(b,0,N,-.18,y_back+.48,low-.26,low,SHADE,f'Gallery L{li} slab')
  box(b,-.044,N+.044,-.222,-.11,low-.18,low-.086,LIGHTSTONE,f'Gallery L{li} front fascia')
  box(b,-.035,N+.035,-.205,-.123,low-.037,low+.025,LIGHTSTONE,f'Gallery L{li} nosing')
  for i,x in enumerate(axes):
   x=max(.18,min(N-.18,x));lab=f'Gallery L{li} pier {i+1}';pier(b,x,low,li==3,lab)
   # paired faceted brackets built out toward the front rail
   brace=Polygon([(0,0),(.25,0),(.65,.18),(1.30,.26),(1.30,.40),(0,.40)])
   for offset in [-.105,.105]:
    b.prism(brace,x+offset-.047,x+offset+.047,lambda y,h,d:(d,y,low-.64+h),STONE,lab+' paired corbels')
  for i,(x0,x1) in enumerate(zip(axes,axes[1:]),1):
   left=x0+.245;right=x1-.245;lab=f'Gallery L{li} bay {i}'
   box(b,left,right,-.118,-.065,low+.065,low+.105,WROUGHT,lab+' bottom rail')
   box(b,left,right,-.14,-.06,low+1.035,low+1.094,LIGHTSTONE,lab+' handrail')
   for col,(lo,hi) in enumerate(((0,.35),(.35,.65),(.65,1))):
    a=left+(right-left)*lo;c=left+(right-left)*hi
    iron_tile(b,a,c,low+.11,low+1.035,-.084,lod,lab+f' iron panel {col+1}',col==1)
  for x in [.05,N-.05]:
   box(b,x-.035,x+.035,.01,y_back,low+1.023,low+1.092,STONE,f'Gallery L{li} return rail')
   for y in np.arange(.10,y_back,.175):
    box(b,x-.016,x+.016,y-.011,y+.011,low+.085,low+1.032,WROUGHT,f'Gallery L{li} return bars')
 for i,x in enumerate(axes):
  x=max(.20,min(N-.20,x))
  for row,(base,hi) in enumerate(zip(deck,[deck[1]-.29,eave]),2):
   label=f'North pier L{row} axis {i+1}'
   box(b,x-.165,x+.165,y_back-.105,y_back+.085,base,hi,STONE,label+' shaft')
   box(b,x-.222,x+.222,y_back-.182,y_back+.08,hi-.58,hi-.12,LIGHTSTONE,label+' capital')
   if not lod:
    for d in [-.085,.085]:
     skin(b,curve([(x+d-.04,hi-.24),(x+d+.04,hi-.24),(x+d+.04,hi-.39),(x+d,hi-.39)],.018),y_back-.20,y_back-.178,STONE,label+' Greek key')
 # Cantilevered cornice and repaired solid roof parapet, distinct from the pre-repair pierced screen.
 box(b,-.04,N+.04,-.18,y_back+.46,eave-.15,eave+.06,SHADE,'North | deep cornice soffit')
 for i in range(38 if not lod else 19):
  x=(i+.5)*N/(38 if not lod else 19)
  box(b,x-.07,x+.07,-.04,.27,eave-.27,eave-.095,STONE,'North | cornice blocks')
 box(b,-.065,N+.065,-.23,.28,eave+.006,eave+.19,LIGHTSTONE,'North | cornice front lip')
 box(b,0,N,-.006,.22,eave+.16,par,RENDER,'North | repaired solid parapet')
 for x in axes:
  a=max(.02,min(N-.02,x))
  box(b,a-.075,a+.075,-.054,.25,eave+.17,par+.068,LIGHTSTONE,'North | parapet joints')
 box(b,-.02,N+.02,-.09,.27,par-.014,par+.057,STONE,'North | parapet coping')
 flat=eave-.24
 box(b,.003,N-.003,y_back+.05,DEPTH,flat-.17,flat,COPING,'North | flat roof')
 box(b,.015,N-.015,DEPTH-.24,DEPTH,flat-.10,flat+.34,RENDER,'North | rear parapet')

 box(b,0,N,DEPTH-.176,DEPTH,.0,flat,RENDER,'North | rear cut plane')
 north_end(b,lod,flat,par)
def north_end(b,lod,flat,par):
 cols=[(.39,4.3),(4.76,8.70),(9.15,DEPTH-.35)]
 levels=[(4.42,7.45),(8.13,11.0)]
 relief=[rect(y0,z0,y1,z1) for y0,y1 in cols for z0,z1 in levels]
 shops=[(5.02,8.45,.09,3.57),(9.29,12.79,.09,3.56)]
 wall=rect(.16,0,DEPTH,par-.013).difference(unary_union(relief+[rect(a,l,c,h) for a,c,l,h in shops]))
 mapper=lambda y,z,d:(d,y,z)
 b.prism(wall,N-.21,N+.018,mapper,NORTHSTONE,'North end | two floors of buff masonry grid')
 for i,(y0,y1) in enumerate(cols,1):
  for level,(z0,z1) in enumerate(levels,2):
   b.prism(rect(y0,z0,y1,z1),N-.175,N-.043,mapper,COURSE,f'North end L{level} brick panel {i}')
 for i,(y0,y1,z0,z1) in enumerate(shops,1):
  b.prism(rect(y0,z0,y1,z1),N-.19,N-.16,mapper,SHOP,f'North end shop {i} glass')
  for div in [0,.36,.67,1]:
   yc=y0+(y1-y0)*div;box(b,N-.14,N-.08,yc-.033,yc+.033,z0,z1,METAL,f'North end shop {i} posts')
  box(b,N-.14,N-.08,y0,y1,z1-.58,z1-.53,METAL,f'North end shop {i} head')
 box(b,N-.26,N+.061,.09,DEPTH+.06,par-.08,par+.035,LIGHTSTONE,'North end | coping')
 # The 2024 published image shows a glazed screen with a metal grid above it.
 # Model visible screens and housings; machinery behind glass is represented only by its low silhouette.
 xa,xb=1.93,N-2.65;ya,yb=1.34,8.64
 low,high=flat+.31,flat+2.02
 for side,y in [('east',ya),('west',yb)]:
  for i in range(7):
   a=xa+(xb-xa)*i/7;c=xa+(xb-xa)*(i+1)/7
   box(b,a+.032,c-.032,y-.020,y+.020,low,high-.11,SCREEN,'Roof screen | '+side+' glass')
   box(b,a-.031,a+.031,y-.037,y+.037,flat+.045,high,SCREENBAR,'Roof screen | '+side+' posts')
  box(b,xa-.05,xb+.05,y-.063,y+.063,high-.105,high,SCREENBAR,'Roof screen | perimeter beam')
  box(b,xa-.03,xb+.03,y-.051,y+.051,low-.060,low+.025,SCREENBAR,'Roof screen | lower rail')
 for side,x in [('south',xa),('north',xb)]:
  for i in range(4):
   a=ya+(yb-ya)*i/4;c=ya+(yb-ya)*(i+1)/4
   box(b,x-.021,x+.021,a+.033,c-.033,low,high-.105,SCREEN,'Roof screen | '+side+' glass')
   box(b,x-.039,x+.039,a-.037,a+.037,flat+.045,high,SCREENBAR,'Roof screen | '+side+' posts')
  box(b,x-.065,x+.065,ya-.056,yb+.056,high-.105,high,SCREENBAR,'Roof screen | end beams')
 for i in range(1,7):
  x=xa+(xb-xa)*i/7;box(b,x-.038,x+.038,ya,yb,high-.087,high-.01,SCREENBAR,'Roof screen | transverse beams')
 for i in range(1,4):
  y=ya+(yb-ya)*i/4;box(b,xa,xb,y-.032,y+.032,high-.106,high-.035,SCREENBAR,'Roof screen | longitudinal beams')
 for i,(a,c,hh) in enumerate([(2.3,4.05,.92),(4.32,6.95,1.09),(7.24,9.68,.96),(9.93,12.47,.79)]):
  box(b,N-2.33,N-.48,a,c,flat+.015,flat+hh,CAPCASE,f'Roof | north low housing {i+1}')
  box(b,N-2.39,N-.43,a-.04,c+.04,flat+hh,flat+hh+.06,COPING,f'Roof | housing cap {i+1}')
def store_glazing(b,a,c,z0,z1,y,label):
 box(b,a+.009,c-.009,y+.105,y+.134,z0+.006,z1-.006,SHOP,label+' glass')
 surround(b,a+.063,c-.063,z0+.06,z1-.066,y,.06,.043,METAL,label+' outer frame')
 mid=z1-.75
 box(b,a+.06,c-.06,y-.016,y+.08,mid-.034,mid+.032,METAL,label+' shop head')
 for i in [1,2,3]:
  x=a+(c-a)*i/4
  box(b,x-.025,x+.025,y-.015,y+.08,z0+.060,z1-.055,METAL,label+' verticals')
def south(b,lod):
 # South first shop was wider on the 1931 plan. Existing window positions are read independently.
 grid=[-S+(x-42)/(489-42)*S for x in [42,199,298,395,489]]
 widths=[[(.08,.245),(.37,.535),(.67,.835)],[(.13,.34),(.57,.78)],[(.17,.36),(.61,.80)],[(.16,.37),(.57,.78)]]
 levels=[(5.18,7.30),(9.02,11.09)];body_top=12.68
 holes=[];panels=[]
 for i,(a,c) in enumerate(zip(grid,grid[1:])):
  for floor,(z0,z1) in enumerate(levels,2):
   for k,(l,r) in enumerate(widths[i]):holes.append((a+(c-a)*l,a+(c-a)*r,z0,z1))
   if i!=2:panels.append((a+.30,c-.30,z0-.04,z1+.045))
 # Structural wall with all real openings; pale field tile occupies a shallow rebate at the window band.
 y=.058;wall(b,-S,0,y+.075,y+.34,4.06,body_top,holes,RENDER,'South | eighteen openings')
 skin(b,rect(-S,4.06,0,body_top).difference(unary_union([rect(a,z,c,h) for a,c,z,h in panels+holes])),y-.03,y+.08,RENDER,'South | plaster facing')
 for i,(a,c,z0,z1) in enumerate(panels):
  cut=[rect(u,z,v,h)for u,v,z,h in holes if a-.02<u<c+.02 and z0<=z<=z1]
  skin(b,rect(a,z0,c,z1).difference(unary_union(cut)),y+.008,y+.08,LIGHT,'South | tile panel '+str(i+1))
  box(b,a-.035,c+.035,y-.095,y+.078,z0-.055,z0+.022,LIGHTSTONE,'South | sill band '+str(i+1))
  box(b,a-.03,c+.03,y-.055,y+.075,z1-.01,z1+.064,STONE,'South | lintel band '+str(i+1))
 for i,(u,v,z,h) in enumerate(holes):
  timber_leaf(b,u,v,z,h,y+.155,METAL,'South opening '+str(i+1),pair=True)
 for i,(a,c) in enumerate(zip(grid,grid[1:])):
  ci=(a+c)/2;lab=f'South roof bay {i+1}'
  # Rounded outer shoulder on the last bay and fluted stepped coping on the third are separately legible.
  profile=[(a,body_top-.01),(c,body_top-.01)]
  if i==2:
   seq=[(1,12.81),(.91,12.81),(.91,13.15),(.81,13.15),(.81,12.95),(.71,12.95),(.71,13.33),(.57,13.33),(.57,13.52),(.35,13.52),(.35,13.36),(.23,13.36),(.23,13.15),(.11,13.15),(.11,12.92),(0,12.92)]
  elif i==3:
   seq=[(1,12.85),(.971,13.06),(.938,13.15),(.071,13.15),(.035,13.09),(0,12.91)]
  else:seq=[(1,12.82),(.88,12.82),(.86,12.92),(.19,12.92),(.17,12.82),(0,12.82)]
  profile += [(a+(c-a)*f,h) for f,h in seq]
  skin(b,Polygon(profile),y-.033,y+.33,RENDER,lab+' crest')
  if i==2:
   for pct,upper in [(.12,13.13),(.405,13.34),(.49,13.51),(.565,13.32),(.86,13.12)]:
    x=a+(c-a)*pct
    box(b,x-.027,x+.027,y-.073,y+.007,7.95,upper-.018,LIGHTSTONE,lab+' vertical ribs')
 shops=[(a+.21,c-.21,.08,3.94)for a,c in zip(grid,grid[1:])]
 wall(b,-S,0,y,y+.40,.0,4.065,shops,STONE,'South | four shop openings')
 for i,(a,c,z,h) in enumerate(shops):store_glazing(b,a,c,z,h,y+.08,f'South shop {i+1}')
 box(b,-S,0,y-.115,y+.35,4.026,4.125,LIGHTSTONE,'South | shop canopy lip')
 low=11.85; ridge=14.02;yp=6.4
 for i,(a,c) in enumerate(zip(grid,grid[1:])):
  lab=f'South roof lot {i+1}'
  section=Polygon([(0.29,low-.16),(yp,ridge-.16),(DEPTH,low-.16),(DEPTH,low),(yp,ridge),(.29,low)])
  b.prism(section,a+.003,c-.003,lambda y,h,d:(d,y,h),TILE,lab+' intersecting pitches')
  box(b,a+.006,c-.006,yp-.09,yp+.09,ridge-.02,ridge+.065,TILELINE,lab+' ridge')
  # Distinct brick party-wall copings between the four shops.
  if i:
   b.prism(Polygon([(.29,low-.015),(yp,ridge-.015),(DEPTH,low-.015),(DEPTH,low+.085),(yp,ridge+.085),(.29,low+.085)]),a-.046,a+.046,lambda y,h,d:(d,y,h),STONE,lab+' party coping')
 for boundary,thickness,side in [(-S,.16,'southern end'),(-.16,.16,'section boundary')]:
  b.prism(Polygon([(.29,low-.025),(DEPTH,low-.025),(yp,ridge-.16)]),boundary,boundary+thickness,lambda y,h,d:(d,y,h),RENDER,'South | gable infill '+side)
 box(b,-S,-S+.18,.27,DEPTH,0,low,RENDER,'South | outside cut plane')
 box(b,-S,0,DEPTH-.18,DEPTH,.0,low,RENDER,'South | rear cut plane')
def add_building(builder,lod=False):
 north(builder,lod);south(builder,lod)
