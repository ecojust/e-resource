/* Daylight variant of the project northwest_raster.c. The fragment shader also
 * tests the full building against eighteen equal-solid-angle sky samples.
 * Perspective-correct glTF rasterization. One sun depth buffer and a camera
 * depth buffer are shared across every material, including the textured brick. */
#include <stdint.h>
#include <math.h>
#include <stdlib.h>
static inline int mini(int x,int y){return x<y?x:y;}
static inline int maxi(int x,int y){return x>y?x:y;}
static inline float limited(float v,float lo,float hi){return fminf(hi,fmaxf(v,lo));}
static inline int wrapped(int k,int n,int mode){if(mode==10497){k%=n;return k<0?k+n:k;}return mini(n-1,maxi(0,k));}
static inline void bounds(const float *a,const float *b,const float *c,int w,int h,int *box){
 box[0]=maxi(0,(int)floorf(fminf(a[0],fminf(b[0],c[0]))));box[1]=mini(w-1,(int)ceilf(fmaxf(a[0],fmaxf(b[0],c[0]))));
 box[2]=maxi(0,(int)floorf(fminf(a[1],fminf(b[1],c[1]))));box[3]=mini(h-1,(int)ceilf(fmaxf(a[1],fmaxf(b[1],c[1]))));
}
void shadow_depth(int n,const uint32_t *ids,const float *p,int dim,float *depth){
 for(int i=0;i<n;i++){const float *a=p+3*ids[3*i],*b=p+3*ids[3*i+1],*c=p+3*ids[3*i+2];
  float ux=b[0]-a[0],uy=b[1]-a[1],vx=c[0]-a[0],vy=c[1]-a[1],D=ux*vy-uy*vx;if(fabsf(D)<1.e-7f)continue;
  int box[4];bounds(a,b,c,dim,dim,box);
  for(int y=box[2];y<=box[3];y++)for(int x=box[0];x<=box[1];x++){
   float dx=x+.5f-a[0],dy=y+.5f-a[1],s=(dx*vy-dy*vx)/D,t=(ux*dy-uy*dx)/D,r=1.f-s-t;
   if(s<0||t<0||r<0)continue;float z=r*a[2]+s*b[2]+t*c[2];int k=y*dim+x;if(z>depth[k])depth[k]=z;
  }
 }
}
/* Vertex payload [pixel x, pixel y, inverse eye depth, u, v, sun x, sun y,
 * sun z, normal x, normal y, normal z]; metals use a restrained sky response. */
/* All matrices use model coordinates in metres. Invert the surveyed camera at
 * the stored eye depth to test each visible fragment against the full building. */
static int count,dim,timed;
static float *xform,*dirs,*maps,*back,*fraction,pixel;
void set_sky(int n,int size,float *t,float *d,float *m){count=n;dim=size;xform=t;dirs=d;maps=m;}
void set_photo(float *b,float p,int direct,float *f){back=b;pixel=p;timed=direct;fraction=f;}
static float transform(const float *m,float x,float y,float z){return m[0]*x+m[1]*y+m[2]*z+m[3];}
static float visibility(float x,float y,float z,float nx,float ny,float nz){
    float total=0,open=0;
    for(int i=0;i<count;i++){
        const float *d=dirs+3*i;
        float dot=nx*d[0]+ny*d[1]+nz*d[2];
        if(dot<=0)continue;
        const float *t=xform+i*12;
        float u=transform(t,x,y,z)-.5f,v=transform(t+4,x,y,z)-.5f;
        int a=floorf(u),b=floorf(v);
        float depth=transform(t+8,x,y,z)+.045f+.02f*(1.f-dot);
        float visible=0;
        for(int j=0;j<2;j++)for(int k=0;k<2;k++){
            int col=a+k,row=b+j;
            if(col<0||row<0||col>=dim||row>=dim||maps[(i*dim+row)*dim+col]<=depth){
                visible+=(k?u-a:1-(u-a))*(j?v-b:1-(v-b));
            }
        }
        total+=dot;open+=dot*visible;
    }
    return total>1.e-5f?open/total:0.f;
}

void paint(int n,const uint32_t *ids,const float *p,int w,int h,float *zb,uint16_t *labels,
 uint8_t *image,int material,const float *base,float metallic,float rough,const uint8_t *tex,
 int tw,int th,int wrapu,int wrapv,const float *linear,const uint8_t *srgb,
 int sd,const float *shadow,const float *sun){
 for(int i=0;i<n;i++){const float *a=p+11*ids[3*i],*b=p+11*ids[3*i+1],*c=p+11*ids[3*i+2];
  float ux=b[0]-a[0],uy=b[1]-a[1],vx=c[0]-a[0],vy=c[1]-a[1],D=ux*vy-uy*vx;
  if(fabsf(D)<1.e-7f||a[2]<=0||b[2]<=0||c[2]<=0)continue;
  int box[4];bounds(a,b,c,w,h,box);
  for(int y=box[2];y<=box[3];y++)for(int x=box[0];x<=box[1];x++){
   float dx=x+.5f-a[0],dy=y+.5f-a[1],s=(dx*vy-dy*vx)/D,t=(ux*dy-uy*dx)/D,r=1.f-s-t;
   if(s<0||t<0||r<0)continue;float z=r*a[2]+s*b[2]+t*c[2];int k=y*w+x;if(z<=zb[k])continue;
   zb[k]=z;labels[k]=(uint16_t)(material+1);r*=a[2]/z;s*=b[2]/z;t*=c[2]/z;
   float attr[11];for(int j=3;j<11;j++)attr[j]=r*a[j]+s*b[j]+t*c[j];
   float nx=attr[8],ny=attr[9],nz=attr[10];float L=sqrtf(nx*nx+ny*ny+nz*nz);if(L>0){nx/=L;ny/=L;nz/=L;}
   float dl=fmaxf(0,nx*sun[0]+ny*sun[1]+nz*sun[2]),vis=0;
   int sx=(int)floorf(attr[5]),sy=(int)floorf(attr[6]);float bias=.032f+.018f*(1.f-dl);
   for(int sy0=-1;sy0<=1;sy0++)for(int sx0=-1;sx0<=1;sx0++){
    int xx=sx+sx0,yy=sy+sy0;
    if(xx<0||yy<0||xx>=sd||yy>=sd||attr[7]+bias>=shadow[yy*sd+xx])vis+=1.f/9.f;
   }
   
float zz=1.f/z,uu=(x+.5f)*pixel*zz,vv=(y+.5f)*pixel*zz;
float wx=transform(back,uu,vv,zz),wy=transform(back+4,uu,vv,zz),wz=transform(back+8,uu,vv,zz);
float exposure=fraction[k]=visibility(wx+.012f*nx,wy+.012f*ny,wz+.012f*nz,nx,ny,nz);
float sky=exposure*(.70f+.15f*(.5f+.5f*nz))+.16f;
if(!timed)vis=0;

   float tx=attr[3]*tw-.5f,ty=attr[4]*th-.5f;int ix=floorf(tx),iy=floorf(ty);float fx=tx-ix,fy=ty-iy;
   for(int ch=0;ch<3;ch++){
    float al=base[ch];
    if(tw>0){
     int x0=wrapped(ix,tw,wrapu),x1=wrapped(ix+1,tw,wrapu),y0=wrapped(iy,th,wrapv),y1=wrapped(iy+1,th,wrapv);
     al*=((1.f-fx)*linear[tex[3*(y0*tw+x0)+ch]]+fx*linear[tex[3*(y0*tw+x1)+ch]])*(1.f-fy)
        +((1.f-fx)*linear[tex[3*(y1*tw+x0)+ch]]+fx*linear[tex[3*(y1*tw+x1)+ch]])*fy;
    }
    float daylight=sky*(.98f+.02f*ch)+vis*dl*(.49f-.025f*ch);
    float reflect=(.0065f+.008f*ch)*metallic*(1.f-rough)*(.55f+.45f*nz);
    float result=limited(al*daylight+reflect,0,1);
    image[k*3+ch]=srgb[(int)(result*65535.f+.5f)];
   }
  }
 }
}
