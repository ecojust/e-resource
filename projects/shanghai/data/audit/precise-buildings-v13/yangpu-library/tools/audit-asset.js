async ({record,variant})=>{
 const hash=async b=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(x=>x.toString(16).padStart(2,'0')).join('');
 const file=variant==='full'?record.model:record.lod_model,url=new URL(file,document.baseURI).href;
 const response=await fetch(url);if(!response.ok)throw Error('GLB '+response.status+': '+url);
 const buffer=await response.arrayBuffer(),v=new DataView(buffer);
 if(buffer.byteLength<28||v.getUint32(0,true)!==0x46546c67||v.getUint32(4,true)!==2||v.getUint32(8,true)!==buffer.byteLength)throw Error('Invalid GLB header');
 const length=v.getUint32(12,true),doc=JSON.parse(new TextDecoder().decode(new Uint8Array(buffer,20,length))),bin=28+length;
 const images=await Promise.all((doc.images||[]).map(async image=>{
   if(image.uri||!Number.isInteger(image.bufferView))throw Error('Expected embedded image');
   const view=doc.bufferViews[image.bufferView],start=bin+(view.byteOffset||0);
   return {bytes:view.byteLength,mimeType:image.mimeType,sha256:await hash(buffer.slice(start,start+view.byteLength))};
 }));
 const photo=(doc.materials||[]).filter(m=>/^PhotoFacade_/i.test(m.name||'')&&m.pbrMetallicRoughness?.baseColorTexture);
 return {file,url,bytes:buffer.byteLength,sha256:await hash(buffer),images,mappedPhotoMaterials:photo.map(m=>m.name),
   triangles:(doc.meshes||[]).reduce((n,m)=>n+m.primitives.reduce((n,p)=>n+(doc.accessors[p.indices]?.count||0)/3,0),0),
   modelMaterials:doc.materials||[],extensionsUsed:doc.extensionsUsed||[],extensionsRequired:doc.extensionsRequired||[],
   copyright:doc.asset.copyright||'',externalResources:(doc.buffers||[]).some(b=>b.uri&&!b.uri.startsWith('data:'))};
}
