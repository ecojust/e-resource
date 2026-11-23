/* Read a native X11 TrueColor display through Xlib. The PNG has one RGB row filter (None).
   With four integer crop arguments, decode an earlier complete capture and copy its rows. */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <zlib.h>
typedef struct _XDisplay Display;
typedef struct _XImage XImage;
extern Display *XOpenDisplay(const char *);
extern int XDefaultScreen(Display *), XDisplayWidth(Display *,int), XDisplayHeight(Display *,int);
extern unsigned long XRootWindow(Display *,int), XGetPixel(XImage *,int,int);
extern XImage *XGetImage(Display *,unsigned long,int,int,unsigned,unsigned,unsigned long,int);
extern int XDestroyImage(XImage *), XCloseDisplay(Display *);
static void require(int ok) {if(!ok){fputs("Invalid X11 display or capture\n",stderr);exit(1);}}
static unsigned unpack(const unsigned char *p){return ((unsigned)p[0]<<24)|((unsigned)p[1]<<16)|((unsigned)p[2]<<8)|p[3];}
static void pack(unsigned char *p,unsigned v){p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static void chunk(const char *name,const unsigned char *buf,unsigned n){
    unsigned char q[4];pack(q,n);require(fwrite(q,1,4,stdout)==4);require(fwrite(name,1,4,stdout)==4);
    if(n)require(fwrite(buf,1,n,stdout)==n);
    unsigned long c=crc32(0,(const Bytef*)name,4);
    if(n)c=crc32(c,buf,n);pack(q,(unsigned)c);require(fwrite(q,1,4,stdout)==4);
}
static unsigned char *rows(unsigned w,unsigned h){require(w>0 && w<=8000 && h>0 && h<=8000);unsigned char *p=calloc(h,3*w+1);require(p!=NULL);return p;}
static void encode(const unsigned char *img,unsigned w,unsigned h){
    unsigned char hdr[13]={0};pack(hdr,w);pack(hdr+4,h);hdr[8]=8;hdr[9]=2;
    require(fwrite("\x89PNG\r\n\x1a\n",1,8,stdout)==8);chunk("IHDR",hdr,13);
    unsigned long size=(3*w+1)*h, len=compressBound(size);unsigned char *zip=malloc(len);require(zip!=NULL);
    require(compress2(zip,&len,img,size,4)==Z_OK);chunk("IDAT",zip,len);free(zip);chunk("IEND",NULL,0);
}
int main(int argc,char **argv){
    if(argc==1){
        Display *d=XOpenDisplay(NULL);require(d!=NULL);int s=XDefaultScreen(d);
        unsigned w=XDisplayWidth(d,s),h=XDisplayHeight(d,s);unsigned char *img=rows(w,h);
        XImage *im=XGetImage(d,XRootWindow(d,s),0,0,w,h,~0UL,2);require(im!=NULL);
        for(unsigned y=0;y<h;y++){unsigned char *p=img+y*(3*w+1)+1;for(unsigned x=0;x<w;x++){
            unsigned long c=XGetPixel(im,x,y);*p++=(c>>16)&255;*p++=(c>>8)&255;*p++=c&255;}}
        XDestroyImage(im);XCloseDisplay(d);encode(img,w,h);free(img);
    } else {
        require(argc==6);FILE *f=fopen(argv[1],"rb");require(f!=NULL);unsigned char header[33],key[8];
        require(fread(header,1,33,f)==33 && !memcmp(header,"\x89PNG\r\n\x1a\n",8) && header[24]==8 && header[25]==2);
        unsigned w=unpack(header+16),h=unpack(header+20);unsigned char *img=rows(w,h);
        require(fread(key,1,8,f)==8 && !memcmp(key+4,"IDAT",4));unsigned len=unpack(key);
        require(len<=compressBound((3*w+1)*h));unsigned char *zip=malloc(len);require(zip!=NULL && fread(zip,1,len,f)==len);
        fclose(f);unsigned long size=(3*w+1)*h;require(uncompress(img,&size,zip,len)==Z_OK && size==(3*w+1)*h);free(zip);
        unsigned x=strtoul(argv[2],NULL,10),y=strtoul(argv[3],NULL,10),cw=strtoul(argv[4],NULL,10),ch=strtoul(argv[5],NULL,10);
        require(x<w && y<h && cw<=w-x && ch<=h-y);unsigned char *cut=rows(cw,ch);
        for(unsigned r=0;r<ch;r++){unsigned char *scan=img+(y+r)*(3*w+1);require(scan[0]==0);memcpy(cut+r*(3*cw+1)+1,scan+3*x+1,3*cw);}
        free(img);encode(cut,cw,ch);free(cut);
    }
    return ferror(stdout)?1:0;
}
