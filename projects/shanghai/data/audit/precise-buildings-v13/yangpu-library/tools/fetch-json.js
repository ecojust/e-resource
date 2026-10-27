async files=>{
 const out={};for(const [key,file]of Object.entries(files)){
   const url=new URL(file,document.baseURI).href,r=await fetch(url);if(!r.ok)throw Error(url+': HTTP '+r.status);
   const b=await r.arrayBuffer(),sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(x=>x.toString(16).padStart(2,'0')).join('');
   out[key]={url,bytes:b.byteLength,sha256,data:JSON.parse(new TextDecoder().decode(b))};
 }return out;
}
