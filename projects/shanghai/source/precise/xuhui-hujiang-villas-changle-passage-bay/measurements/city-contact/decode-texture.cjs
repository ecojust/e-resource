// Decode the embedded material when the geometry review runs Three.js outside a browser.
const {execFileSync} = require('node:child_process');

globalThis.self = globalThis;
globalThis.createImageBitmap = async blob => {
  const source = Buffer.from(await blob.arrayBuffer());
  const decoder = [
    'import io,struct,sys',
    'from PIL import Image',
    "with Image.open(io.BytesIO(sys.stdin.buffer.read())) as im:",
    " image=im.convert('RGBA')",
    " sys.stdout.buffer.write(struct.pack('<II',*image.size)+image.tobytes())",
  ].join('\n');
  const rgba = execFileSync(process.env.PYTHON || 'python', ['-c',decoder], {
    input: source, maxBuffer: 16 * 1024 * 1024,
  });
  const width = rgba.readUInt32LE(0);
  const height = rgba.readUInt32LE(4);
  if (rgba.length !== 8 + width * height * 4) throw new Error('Incomplete bitmap');
  return {width, height, data: new Uint8Array(rgba.subarray(8)), close(){}};
};
