"""Convert the panorama coordinate frame used by the source stations to WGS84."""
from math import cos, sin, pi, radians, hypot, atan2, sqrt

def gcj(lon,lat):
 x=lon-105;y=lat-35;m=sqrt(abs(x))
 dy=-100+2*x+3*y+.2*y*y+.1*x*y+.2*m+(20*sin(6*x*pi)+20*sin(2*x*pi))*2/3+(20*sin(y*pi)+40*sin(y/3*pi))*2/3+(160*sin(y/12*pi)+320*sin(y*pi/30))*2/3
 dx=300+x+2*y+.1*x*x+.1*x*y+.1*m+(20*sin(6*x*pi)+20*sin(2*x*pi))*2/3+(20*sin(x*pi)+40*sin(x/3*pi))*2/3+(150*sin(x/12*pi)+300*sin(x/30*pi))*2/3
 a=6378245.;e=.006693421622965943;rad=radians(lat);magic=1-e*sin(rad)**2;s=sqrt(magic);return lon+dx*180/(a/s*cos(rad)*pi),lat+dy*180/(a*(1-e)/(magic*s)*pi)

def wgs(X,Y):
 v=Y/4482777.06;co=[.03278182852591,40.31678527705744,.65659298677277,-4.44255534477492,.85341911805263,.12923347998204,-.04625736007561];blon=-1.981981304930552e-8+8.983055099779535e-6*X;blat=sum(c*v**i for i,c in enumerate(co));xx=blon-.0065;yy=blat-.006;xp=pi*3000/180;z=hypot(xx,yy)-.00002*sin(yy*xp);t=atan2(yy,xx)-.000003*cos(xx*xp);gx=z*cos(t);gy=z*sin(t);lx,ly=gx,gy
 for i in range(5):
  rx,ry=gcj(lx,ly);lx-=rx-gx;ly-=ry-gy
 return lx,ly
