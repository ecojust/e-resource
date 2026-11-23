static float emissive[3];
void set_emission(float r,float g,float b){emissive[0]=r;emissive[1]=g;emissive[2]=b;}
/* glTF tangent-space normal mapping for the courtyard daylight rasterizer.
 * back and pixel use the registered camera, including its measured roll. */
static const uint8_t *normal_rgb;
static int normal_w, normal_h, normal_u, normal_v;
static float normal_strength;
void set_normal_map(const uint8_t *rgb, int w, int h, int wrap_u, int wrap_v, float scale) {
    normal_rgb=rgb; normal_w=w; normal_h=h; normal_u=wrap_u; normal_v=wrap_v;
    normal_strength=scale;
}
static void world_vertex(const float *p, float *xyz) {
    float depth=1.f/p[2];
    for(int i=0; i<3; ++i)
        xyz[i]=transform(back+4*i, p[0]*pixel*depth, p[1]*pixel*depth, depth);
}
static int tangent_frame(const float *a,const float *b,const float *c,float *frame) {
    if(!normal_w) return 0;
    float du1=b[3]-a[3], dv1=b[4]-a[4], du2=c[3]-a[3], dv2=c[4]-a[4];
    float det=du1*dv2-dv1*du2, P[3], Q[3], R[3];
    if(fabsf(det)<1.e-12f) return 0;
    world_vertex(a,P);world_vertex(b,Q);world_vertex(c,R);
    for(int i=0;i<3;++i) {
        frame[i]=((Q[i]-P[i])*dv2-(R[i]-P[i])*dv1)/det;
        frame[3+i]=((R[i]-P[i])*du1-(Q[i]-P[i])*du2)/det;
    }
    return 1;
}
static void perturb(float u,float v,const float *frame,float *nx,float *ny,float *nz) {
    float U=u*normal_w-.5f, V=v*normal_h-.5f;
    int X=(int)floorf(U),Y=(int)floorf(V);
    float tx=0,ty=0,tz=0;
    for(int a=0;a<2;++a)for(int b=0;b<2;++b) {
        float wt=(a?U-X:1-U+X)*(b?V-Y:1-V+Y);
        int pos=3*(wrapped(Y+b,normal_h,normal_v)*normal_w+wrapped(X+a,normal_w,normal_u));
        tx+=wt*(normal_rgb[pos]/127.5f-1.f);
        ty+=wt*(normal_rgb[pos+1]/127.5f-1.f);
        tz+=wt*(normal_rgb[pos+2]/127.5f-1.f);
    }
    float dot=frame[0]*(*nx)+frame[1]*(*ny)+frame[2]*(*nz);
    float x=frame[0]-dot*(*nx),y=frame[1]-dot*(*ny),z=frame[2]-dot*(*nz);
    float len=sqrtf(x*x+y*y+z*z); if(len<1.e-8f)return;
    x/=len;y/=len;z/=len;
    float bx=(*ny)*z-(*nz)*y, by=(*nz)*x-(*nx)*z, bz=(*nx)*y-(*ny)*x;
    float hand=(bx*frame[3]+by*frame[4]+bz*frame[5])<0.f?-1.f:1.f;
    tx*=normal_strength;ty*=normal_strength*hand;
    float qx=x*tx+bx*ty+(*nx)*tz,qy=y*tx+by*ty+(*ny)*tz,qz=z*tx+bz*ty+(*nz)*tz;
    len=sqrtf(qx*qx+qy*qy+qz*qz);
    if(len>1.e-8f){*nx=qx/len;*ny=qy/len;*nz=qz/len;}
}
