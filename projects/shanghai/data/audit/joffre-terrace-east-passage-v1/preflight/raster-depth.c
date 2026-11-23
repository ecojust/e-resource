#include <math.h>
#include <stdbool.h>
#include <stdint.h>
/* Orthographic per-pixel barycentric depth test. The greatest dot product
   with the eye direction corresponds to the closest surface. */
void raster(int n, int width, int height, const double *xy, const double *depth,
            const uint8_t *visible, const uint8_t *rgb, double *buffer, uint8_t *image) {
    for (int k=0;k<n;k++) {
        if (!visible[k]) continue;
        const double *v=xy+6*k, *z=depth+3*k;
        const uint8_t *color=rgb+3*k;
        double ax=v[0],ay=v[1],bx=v[2]-ax,by=v[3]-ay,cx=v[4]-ax,cy=v[5]-ay;
        double den=bx*cy-by*cx;
        if(fabs(den)<1e-10)continue;
        int x0=(int)fmax(0,floor(fmin(v[0],fmin(v[2],v[4]))));
        int x1=(int)fmin(width-1,ceil(fmax(v[0],fmax(v[2],v[4]))));
        int y0=(int)fmax(0,floor(fmin(v[1],fmin(v[3],v[5]))));
        int y1=(int)fmin(height-1,ceil(fmax(v[1],fmax(v[3],v[5]))));
        for(int y=y0;y<=y1;y++){
            double dy=y+.5-ay;
            for(int x=x0;x<=x1;x++){
                double dx=x+.5-ax,u=(dx*cy-dy*cx)/den,vv=(bx*dy-by*dx)/den;
                if(u<0||vv<0||u+vv>1)continue;
                const int i=y*width+x;
                double zz=z[0]+u*(z[1]-z[0])+vv*(z[2]-z[0]);
                if(zz>buffer[i]){
                    buffer[i]=zz;
                    for(int ch=0;ch<3;ch++)image[3*i+ch]=color[ch];
                }
            }
        }
    }
}
