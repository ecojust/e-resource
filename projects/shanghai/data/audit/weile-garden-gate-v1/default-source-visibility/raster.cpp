#include <algorithm>
#include <cmath>
#include <limits>
struct P {double x,y,z,e,n;};
extern "C" void draw(int w,int h, double cx,double cy,double f,int count,const double* vertices,const int* labels, const int* clipped,const double* mask,int m,float* depth,int* color){
 for(int t=0;t<count;t++){
  P orig[6],out[6];int num=0;for(int j=0;j<3;j++){auto v=vertices+((t*3+j)*5); orig[j]={v[0],v[1],v[2],v[3],v[4]}; }
  for(int j=0;j<3;j++){auto a=orig[j],b=orig[(j+1)%3];if(a.z>=.4)out[num++]=a;if((a.z<.4)!=(b.z<.4)){double s=(.4-a.z)/(b.z-a.z);out[num++]={a.x+s*(b.x-a.x),a.y+s*(b.y-a.y),.4,a.e+s*(b.e-a.e),a.n+s*(b.n-a.n)};}}
  for(int i=1;i+1<num;i++){
   P v[3]={out[0],out[i],out[i+1]};double x[3],y[3],z[3];
   for(int j=0;j<3;j++){z[j]=1/v[j].z;x[j]=cx+f*v[j].x*z[j];y[j]=cy-f*v[j].y*z[j];}
   double det=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2]);if(std::abs(det)<1e-10)continue;
   int l=std::max(0,int(std::floor(std::min({x[0],x[1],x[2]})))),r=std::min(w-1,int(std::ceil(std::max({x[0],x[1],x[2]}))));int top=std::max(0,int(std::floor(std::min({y[0],y[1],y[2]})))),bot=std::min(h-1,int(std::ceil(std::max({y[0],y[1],y[2]}))));
   for(int py=top;py<=bot;py++)for(int px=l;px<=r;px++){double a=((y[1]-y[2])*(px+.5-x[2])+(x[2]-x[1])*(py+.5-y[2]))/det,b=((y[2]-y[0])*(px+.5-x[2])+(x[0]-x[2])*(py+.5-y[2]))/det,c=1-a-b;if(a<0||b<0||c<0)continue;
    int p=py*w+px;double d=a*z[0]+b*z[1]+c*z[2];if(d<=depth[p]+1e-9)continue;
    if(clipped[t]&&m){double E=(a*z[0]*v[0].e+b*z[1]*v[1].e+c*z[2]*v[2].e)/d,N=(a*z[0]*v[0].n+b*z[1]*v[1].n+c*z[2]*v[2].n)/d;bool inside=false;for(int j=0,k=m-1;j<m;k=j++){double ex=mask[j*2],ey=mask[j*2+1],fx=mask[k*2],fy=mask[k*2+1];if(((ey>N)!=(fy>N))&&(E<(fx-ex)*(N-ey)/(fy-ey)+ex))inside=!inside;}if(inside)continue;}
    depth[p]=d;color[p]=labels[t];
   }
  }
 }
}
