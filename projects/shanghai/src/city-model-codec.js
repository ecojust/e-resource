/** Near-model transport decoding. Geometry stays in its original GLB precision. */
export const CITY_MODEL_BYTE_LIMIT=100000000;
const SHA256=/^[0-9a-f]{64}$/i;

function checkAborted(signal) {
  if(signal?.aborted)throw new DOMException('City model request aborted','AbortError');
}

/** Validate compressed index fields before a far parent acquires a near owner. */
export function cityModelCodecMetadata(item) {
  const encoding=item.content_encoding??'identity';
  if(encoding!=='identity'&&encoding!=='gzip')throw Error('Unsupported city model content encoding');
  const fileBytes=Number(item.size_bytes),sha256=item.sha256;
  if(sha256!=null&&(typeof sha256!=='string'||!SHA256.test(sha256)))throw Error('Invalid city model SHA-256');
  if(encoding==='identity')return {encoding,fileBytes,sha256:sha256?.toLowerCase()};
  const decodedBytes=Number(item.decoded_size_bytes),decodedSha256=item.decoded_sha256;
  if(!Number.isInteger(fileBytes)||fileBytes<1||fileBytes>=CITY_MODEL_BYTE_LIMIT
    ||!Number.isInteger(decodedBytes)||decodedBytes<12||decodedBytes>=CITY_MODEL_BYTE_LIMIT
    ||typeof sha256!=='string'||!SHA256.test(sha256)
    ||typeof decodedSha256!=='string'||!SHA256.test(decodedSha256))throw Error('Invalid gzip city model size or SHA-256');
  return {encoding,fileBytes,sha256:sha256.toLowerCase(),decodedBytes,decodedSha256:decodedSha256.toLowerCase()};
}

async function boundedRead(stream,{signal,maximum,byteLimit,label}) {
  checkAborted(signal);
  const reader=stream.getReader(),chunks=[];let length=0;
  const abort=()=>{reader.cancel(signal.reason).catch(()=>{});};
  signal?.addEventListener('abort',abort,{once:true});
  try {
    checkAborted(signal);
    for(;;) {
      const {value,done}=await reader.read();checkAborted(signal);
      if(done)break;
      const bytes=value instanceof Uint8Array?value:new Uint8Array(value);
      length+=bytes.byteLength;
      if(length>=byteLimit||length>maximum)throw Error(`${label} exceeds the declared size or file limit`);
      chunks.push(bytes);
    }
    const output=new Uint8Array(length);let offset=0;
    for(const chunk of chunks){output.set(chunk,offset);offset+=chunk.byteLength;}
    return output;
  } catch(error) {
    // A decompressor can emit a large chunk before its trailer is read. Cancel
    // immediately on overflow instead of first assembling the complete output.
    try {await reader.cancel(error);} catch {}
    checkAborted(signal);throw error;
  } finally {
    signal?.removeEventListener('abort',abort);reader.releaseLock();
  }
}

function assertSize(bytes,expected,label) {
  if(bytes.byteLength!==expected)throw Error(`${label} size does not match the city index`);
}
async function assertHash(bytes,expected,signal,label) {
  if(!expected)return;
  checkAborted(signal);
  if(!globalThis.crypto?.subtle)throw Error('City model SHA-256 verification is unavailable');
  const digest=await globalThis.crypto.subtle.digest('SHA-256',bytes);checkAborted(signal);
  const actual=Array.from(new Uint8Array(digest),value=>value.toString(16).padStart(2,'0')).join('');
  if(actual!==expected)throw Error(`${label} SHA-256 does not match the city index`);
}
const isGLB=bytes=>bytes.byteLength>=4&&bytes[0]===0x67&&bytes[1]===0x6c&&bytes[2]===0x54&&bytes[3]===0x46;
function assertGLB(bytes) {
  if(!isGLB(bytes)||bytes.byteLength<12)throw Error('Decoded city model is not a GLB');
  const header=new DataView(bytes.buffer,bytes.byteOffset,12);
  if(header.getUint32(4,true)!==2||header.getUint32(8,true)!==bytes.byteLength)throw Error('Invalid decoded city GLB header');
}

/**
 * Fetch normally exposes bytes after HTTP Content-Encoding. A gzip transport
 * index can therefore receive gzip magic OR already-decoded GLB magic. Never
 * decompress twice; decoded size/hash are mandatory in both cases.
 * byteLimit is injectable downward for bounded-output fixtures, never upward.
 */
export async function decodeCityModelResponse(response,codec,{signal,byteLimit=CITY_MODEL_BYTE_LIMIT}={}) {
  if(!Number.isInteger(byteLimit)||byteLimit<13||byteLimit>CITY_MODEL_BYTE_LIMIT)throw Error('Invalid city model byte limit');
  checkAborted(signal);
  const maximum=codec.encoding==='gzip'?Math.max(codec.fileBytes,codec.decodedBytes):byteLimit-1;
  if(maximum>=byteLimit)throw Error('City model declaration exceeds the file limit');
  // Standard fetch Response always provides a readable body. Keep a bounded
  // fallback for legacy injected responses used by host applications.
  const input=response.body?await boundedRead(response.body,{signal,maximum,byteLimit,label:'City model response'})
    :new Uint8Array(await response.arrayBuffer());
  checkAborted(signal);
  if(input.byteLength>=byteLimit||input.byteLength>maximum)throw Error('City model response exceeds the file limit');
  if(codec.encoding!=='gzip') {
    if(codec.sha256){assertSize(input,codec.fileBytes,'City model');await assertHash(input,codec.sha256,signal,'City model');}
    return input.buffer.slice(input.byteOffset,input.byteOffset+input.byteLength);
  }
  let decoded;
  if(isGLB(input)) {
    // Encoded bytes are unavailable after automatic HTTP decompression. Do not
    // compare their hash/size to this body; verify the decoded contract instead.
    decoded=input;
  } else {
    if(input.byteLength<2||input[0]!==0x1f||input[1]!==0x8b)throw Error('City gzip model has invalid gzip or GLB magic');
    assertSize(input,codec.fileBytes,'Compressed city model');await assertHash(input,codec.sha256,signal,'Compressed city model');
    checkAborted(signal);
    if(typeof DecompressionStream==='undefined')throw Error('This browser cannot decompress gzip city models');
    const encoded=new ReadableStream({start(controller){controller.enqueue(input);controller.close();}});
    decoded=await boundedRead(encoded.pipeThrough(new DecompressionStream('gzip')),
      {signal,maximum:codec.decodedBytes,byteLimit,label:'Decoded city model'});
  }
  checkAborted(signal);assertSize(decoded,codec.decodedBytes,'Decoded city model');assertGLB(decoded);
  await assertHash(decoded,codec.decodedSha256,signal,'Decoded city model');checkAborted(signal);
  return decoded.buffer.slice(decoded.byteOffset,decoded.byteOffset+decoded.byteLength);
}
