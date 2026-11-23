const {spawnSync} = require('node:child_process');
globalThis.self = globalThis;
globalThis.createImageBitmap = async blob => {
 const bytes = Buffer.from(await blob.arrayBuffer());
 const p = spawnSync('python', ['-B','-c', 'from PIL import Image; import io,sys,json; image=Image.open(io.BytesIO(sys.stdin.buffer.read())); image.load(); print(json.dumps(list(image.size)))'], {input:bytes,encoding:'utf8'});
 if (p.status !== 0) throw Error(p.stderr);
 const [width,height] = JSON.parse(p.stdout);
 return {width,height,close() {}};
};
