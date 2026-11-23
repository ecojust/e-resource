// Photographic-camera visibility, short-range diffuse occlusion and finite area lighting in the vestibule.
#include <embree4/rtcore.h>
#include <algorithm>
#include <cmath>
#include <cstring>
struct Vec {
    float x,y,z;
    Vec operator+(Vec p) const {return {x+p.x,y+p.y,z+p.z};}
    Vec operator-(Vec p) const {return {x-p.x,y-p.y,z-p.z};}
    Vec operator*(float k) const {return {x*k,y*k,z*k};}
    float dot(Vec p) const {return x*p.x+y*p.y+z*p.z;}
    Vec cross(Vec p) const {return {y*p.z-z*p.y,z*p.x-x*p.z,x*p.y-y*p.x};}
    Vec unit() const {return (*this)*(1.f/std::max(1e-12f,std::sqrt(dot(*this))));}
};
static RTCRay cast(Vec o,Vec dir,float length) {
    RTCRay ray={};ray.org_x=o.x;ray.org_y=o.y;ray.org_z=o.z;
    ray.dir_x=dir.x;ray.dir_y=dir.y;ray.dir_z=dir.z;ray.tnear=.001f;
    ray.tfar=length;ray.mask=0xffffffff;return ray;
}
static bool reaches(RTCScene scene,Vec at,Vec dir,float length) {
    RTCRay ray=cast(at,dir,length);rtcOccluded1(scene,&ray);return ray.tfar>=0;
}
static RTCDevice device;
static RTCScene scene;
extern "C" int prepare(int n,const Vec *triangle) {
    device=rtcNewDevice("threads=1");if(!device)return 1;
    scene=rtcNewScene(device);RTCGeometry mesh=rtcNewGeometry(device,RTC_GEOMETRY_TYPE_TRIANGLE);
    auto *verts=rtcSetNewGeometryBuffer(mesh,RTC_BUFFER_TYPE_VERTEX,0,RTC_FORMAT_FLOAT3,sizeof(Vec),3ull*n);
    auto *indices=(unsigned*)rtcSetNewGeometryBuffer(mesh,RTC_BUFFER_TYPE_INDEX,0,RTC_FORMAT_UINT3,3*sizeof(unsigned),n);
    if(!verts||!indices)return 2;
    std::memcpy(verts,triangle,3ull*n*sizeof(Vec));for(int i=0;i<3*n;i++)indices[i]=i;
    rtcCommitGeometry(mesh);rtcAttachGeometry(scene,mesh);rtcReleaseGeometry(mesh);rtcCommitScene(scene);
    return (int)rtcGetDeviceError(device);
}
extern "C" void release() {
    rtcReleaseScene(scene);rtcReleaseDevice(device);
}
extern "C" int paint(int rays,const Vec *directions,Vec *eye,int *tri_ids,float *weights,float *ambient,float *door) {
    constexpr int count=20;
    Vec hemi[count];
    for(int i=0;i<count;i++){
        float r=std::sqrt((i+.5f)/count),a=i*2.3999632f;
        hemi[i]={r*std::cos(a),r*std::sin(a),std::sqrt(1-r*r)};
    }
    for(int i=0;i<rays;i++){
        Vec d=directions[i].unit();RTCRayHit hit={};hit.ray=cast(*eye,d,140);
        hit.hit.geomID=RTC_INVALID_GEOMETRY_ID;rtcIntersect1(scene,&hit);
        if(hit.hit.geomID==RTC_INVALID_GEOMETRY_ID){tri_ids[i]=-1;continue;}
        tri_ids[i]=(int)hit.hit.primID;weights[2*i]=hit.hit.u;weights[2*i+1]=hit.hit.v;
        Vec normal=Vec{hit.hit.Ng_x,hit.hit.Ng_y,hit.hit.Ng_z}.unit();if(normal.dot(d)>0)normal=normal*(-1);
        Vec p=*eye+d*hit.ray.tfar+normal*.0015f;
        Vec tangent=normal.cross(std::abs(normal.z)>.96f?Vec{0,1,0}:Vec{0,0,1}).unit();
        Vec up=normal.cross(tangent);float ao=0,illumination=0;
        for(auto h:hemi){
            Vec travel=tangent*h.x+up*h.y+normal*h.z;
            if(reaches(scene,p,travel,1.65f))ao+=1.f/count;
        }
        // Integrate the visible solid angle of the tall south entrance as a diffuse area source.
        for(int v=0;v<3;v++)for(int u=0;u<3;u++){
            Vec sample={-1.70f+1.70f*u,.39f,.95f+2.03f*v};Vec delta=sample-p;
            float ds=delta.dot(delta),length=std::sqrt(std::max(ds,.002f));Vec dir=delta*(1.f/length);
            float cosine=std::max(0.f,dir.dot(normal))*std::max(0.f,-dir.y);
            if(cosine>0&&reaches(scene,p,dir,std::max(.003f,length-.003f)))
                illumination+=cosine*2.8f/std::max(ds,1.f);
        }
        // Indirect light from the south entrance falls away past the gallery
        // and along the partly screened lateral passages.
        float lateral=std::max(0.f,std::abs(p.x)-3.65f)/3.25f;
        float axial=std::max(0.f,p.y-13.2f)/7.2f;
        ambient[i]=ao/(1.f+lateral*lateral+axial*axial);
        door[i]=illumination;
    }
    return (int)rtcGetDeviceError(device);
}
