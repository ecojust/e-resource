/* Orthographic depth map in a plane perpendicular to the light. */
#include <float.h>
#include <math.h>
#include <stddef.h>

void depth_map(const double *tri, size_t count, int width, int height, float *depth) {
    for (size_t i=0; i<(size_t)width*height; ++i) depth[i]=-FLT_MAX;
    for (size_t i=0; i<count; ++i) {
        const double *a=tri+9*i, *b=a+3, *c=b+3;
        const double bu=b[0]-a[0], bv=b[1]-a[1], cu=c[0]-a[0], cv=c[1]-a[1];
        const double det=bu*cv-bv*cu;
        if(fabs(det)<1e-9)continue;
        int x0=fmax(0,floor(fmin(a[0],fmin(b[0],c[0]))));
        int x1=fmin(width-1,ceil(fmax(a[0],fmax(b[0],c[0]))));
        int y0=fmax(0,floor(fmin(a[1],fmin(b[1],c[1]))));
        int y1=fmin(height-1,ceil(fmax(a[1],fmax(b[1],c[1]))));
        for(int y=y0;y<=y1;++y)for(int x=x0;x<=x1;++x){
            const double dx=x+.5-a[0],dy=y+.5-a[1];
            const double u=(dx*cv-dy*cu)/det, v=(bu*dy-bv*dx)/det;
            if(u<0 || v<0 || u+v>1)continue;
            const double z=a[2]+u*(b[2]-a[2])+v*(c[2]-a[2]);
            const size_t k=(size_t)y*width+x;
            if(z>depth[k])depth[k]=(float)z;
        }
    }
}
