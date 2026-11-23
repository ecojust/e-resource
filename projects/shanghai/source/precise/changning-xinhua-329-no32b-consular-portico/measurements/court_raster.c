/* Small, single-threaded triangle rasterizer for the measured court views.
 * Input is a compact conversion of the authored GLB and its embedded images. */
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { double x,y,z; } V;
typedef struct { uint32_t w,h; unsigned char *rgb; } Texture;
typedef struct { float base[4]; int32_t colour,normal; } Material;
typedef struct { V point; double u,v; } Vertex;
typedef struct { double x,y,z; } Screen;
static V sub(V a,V b){return (V){a.x-b.x,a.y-b.y,a.z-b.z};}
static V add(V a,V b){return (V){a.x+b.x,a.y+b.y,a.z+b.z};}
static V times(V a,double s){return (V){a.x*s,a.y*s,a.z*s};}
static double dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
static V cross(V a,V b){return (V){a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
static V unit(V a){double n=sqrt(dot(a,a));return n>1e-12?times(a,1/n):(V){0,0,0};}
static void fail(const char *s){fprintf(stderr,"%s\n",s);exit(1);}
static void take(FILE *f,void *p,size_t n){if(fread(p,1,n,f)!=n)fail("Incomplete triangle stream");}
static double linear(unsigned char x){double s=x/255.;return s<=.04045?s/12.92:pow((s+.055)/1.055,2.4);}
static unsigned char srgb(double x){x=fmax(0,fmin(1,x));return (unsigned char)lrint(255*(x<=.0031308?12.92*x:1.055*pow(x,1/2.4)-.055));}
static const unsigned char *sample(const Texture *t,double u,double v){
    uint32_t x=(uint32_t)((u-floor(u))*t->w)%t->w,y=(uint32_t)((v-floor(v))*t->h)%t->h;
    return t->rgb+3*((size_t)y*t->w+x);
}
int main(int argc,char **argv){
    if(argc!=4)fail("Expected scene, camera and output PPM");
    FILE *scene=fopen(argv[1],"rb"),*cam=fopen(argv[2],"r");
    if(!scene||!cam)fail("Could not open scene or camera");
    unsigned width,height;double cropx,cropy,scale,fx,fy,cx,cy;
    if(fscanf(cam,"%u%u%lf%lf%lf%lf%lf%lf%lf",&width,&height,&cropx,&cropy,&scale,&fx,&fy,&cx,&cy)!=9 || !width||!height||width>4096||height>4096)fail("Bad camera frame");
    V R[3],eye;
    for(int i=0;i<3;i++)if(fscanf(cam,"%lf%lf%lf",&R[i].x,&R[i].y,&R[i].z)!=3)fail("Bad camera rotation");
    if(fscanf(cam,"%lf%lf%lf",&eye.x,&eye.y,&eye.z)!=3)fail("Bad camera origin");
    fclose(cam);
    char magic[8];uint32_t nm,nt,nf;take(scene,magic,8);if(memcmp(magic,"COURT003",8))fail("Bad scene signature");
    take(scene,&nm,4);take(scene,&nt,4);take(scene,&nf,4);
    if(nm>256 || nt>256 || nf>10000000)fail("Bad scene size");
    Material *mats=calloc(nm,sizeof(*mats));Texture *textures=calloc(nt?nt:1,sizeof(*textures));
    if(!mats||!textures)fail("Insufficient scene memory");
    for(uint32_t i=0;i<nm;i++){
        take(scene,mats[i].base,16);take(scene,&mats[i].colour,4);take(scene,&mats[i].normal,4);
        if(mats[i].colour>=(int)nt || mats[i].normal>=(int)nt)fail("Bad texture index");
    }
    for(uint32_t i=0;i<nt;i++){
        Texture *t=&textures[i];take(scene,&t->w,4);take(scene,&t->h,4);
        if(!t->w||!t->h||t->w>4096||t->h>4096)fail("Bad texture size");
        size_t bytes=(size_t)t->w*t->h*3;t->rgb=malloc(bytes);if(!t->rgb)fail("Insufficient texture memory");take(scene,t->rgb,bytes);
    }
    size_t count=(size_t)width*height;float *depth=malloc(count*sizeof(float));unsigned char *rgb=malloc(count*3);
    if(!depth||!rgb)fail("Insufficient image memory");
    for(size_t i=0;i<count;i++){depth[i]=INFINITY;rgb[3*i]=rgb[3*i+1]=229;rgb[3*i+2]=224;}
    V sun=unit((V){.19,-.61,.77});double lut[256];for(int i=0;i<256;i++)lut[i]=linear((unsigned char)i);
    for(uint32_t k=0;k<nf;k++){
        uint32_t mid;float source[15];Vertex v[3];Screen p[3];int clipped=0;
        take(scene,&mid,4);take(scene,source,sizeof(source));if(mid>=nm)fail("Bad material index");
        Material *mat=&mats[mid];
        for(int j=0;j<3;j++){
            float *a=source+5*j;v[j]=(Vertex){{a[0],a[1],a[2]},a[3],a[4]};
            V rel=sub(v[j].point,eye);double z=dot(rel,R[2]);
            if(z<=.01){clipped=1;continue;}
            p[j]=(Screen){(fx*dot(rel,R[0])/z+cx-cropx)*scale,(fy*dot(rel,R[1])/z+cy-cropy)*scale,z};
        }
        if(clipped)continue;
        V e1=sub(v[1].point,v[0].point),e2=sub(v[2].point,v[0].point);
        V n=unit(cross(e1,e2)),view=unit(sub(eye,times(add(add(v[0].point,v[1].point),v[2].point),1./3)));
        if(dot(view,n)<=0)continue;
        double ax=p[1].x-p[0].x,ay=p[1].y-p[0].y,bx=p[2].x-p[0].x,by=p[2].y-p[0].y,det=ax*by-ay*bx;
        if(fabs(det)<1e-8)continue;
        int x0=(int)fmax(0,floor(fmin(p[0].x,fmin(p[1].x,p[2].x)))),x1=(int)fmin(width-1,ceil(fmax(p[0].x,fmax(p[1].x,p[2].x))));
        int y0=(int)fmax(0,floor(fmin(p[0].y,fmin(p[1].y,p[2].y)))),y1=(int)fmin(height-1,ceil(fmax(p[0].y,fmax(p[1].y,p[2].y))));
        if(x1<x0||y1<y0)continue;
        double du1=v[1].u-v[0].u,dv1=v[1].v-v[0].v,du2=v[2].u-v[0].u,dv2=v[2].v-v[0].v,uvdet=du1*dv2-du2*dv1;
        V tan={0},bitan={0};
        if(mat->normal>=0 && fabs(uvdet)>1e-12){
            tan=unit(times(sub(times(e1,dv2),times(e2,dv1)),1/uvdet));
            bitan=unit(times(sub(times(e2,du1),times(e1,du2)),1/uvdet));
        }
        for(int j=y0;j<=y1;j++)for(int i=x0;i<=x1;i++){
            double x=i+.5-p[0].x,y=j+.5-p[0].y,b=(x*by-y*bx)/det,c=(ax*y-ay*x)/det,a=1-b-c;
            if(a<0||b<0||c<0)continue;
            a/=p[0].z;b/=p[1].z;c/=p[2].z;double z=1/(a+b+c);size_t ix=(size_t)j*width+i;
            if(z>=depth[ix])continue;
            double u=(a*v[0].u+b*v[1].u+c*v[2].u)*z,vv=(a*v[0].v+b*v[1].v+c*v[2].v)*z;
            V normal=n;
            if(mat->normal>=0 && fabs(uvdet)>1e-12){
                const unsigned char *m=sample(&textures[mat->normal],u,vv);
                normal=unit(add(add(times(tan,2*m[0]/255.-1),times(bitan,2*m[1]/255.-1)),times(n,2*m[2]/255.-1)));
            }
            double light=.56+.31*fmax(0,dot(normal,sun))+.12*dot(normal,view);
            const unsigned char *albedo=mat->colour>=0?sample(&textures[mat->colour],u,vv):NULL;
            for(int q=0;q<3;q++)rgb[3*ix+q]=srgb(mat->base[q]*light*(albedo?lut[albedo[q]]:1));
            depth[ix]=(float)z;
        }
    }
    if(fgetc(scene)!=EOF)fail("Extra data after last triangle");fclose(scene);
    FILE *out=fopen(argv[3],"wb");if(!out)fail("Cannot create image");
    fprintf(out,"P6\n%u %u\n255\n",width,height);if(fwrite(rgb,3,count,out)!=count)fail("Incomplete image write");
    if(fclose(out))fail("Image close failed");return 0;
}
