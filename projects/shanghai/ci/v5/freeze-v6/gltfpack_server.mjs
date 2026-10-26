/** Serial JSON-lines adapter around the unmodified gltfpack WASM library.
 * One process / one WASM instance. No queue concurrency, shell or geometry edits.
 */
import fs from 'node:fs';
import readline from 'node:readline';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {performance} from 'node:perf_hooks';

const library=path.resolve(process.argv[2]||'/workspace/shanghai_tools/node_modules/gltfpack/library.js');
const {pack}=await import(pathToFileURL(library).href);
const iface={read:filename=>fs.readFileSync(filename),write:(filename,data)=>fs.writeFileSync(filename,data)};
const usage=()=>({rssBytes:process.memoryUsage().rss,maxRssBytes:process.resourceUsage().maxRSS*1024,
  heapUsedBytes:process.memoryUsage().heapUsed,externalBytes:process.memoryUsage().external});
const send=message=>process.stdout.write(JSON.stringify(message)+'\n');
const version=(await pack(['-v'],iface)).trim();
send({type:'ready',protocol:1,pid:process.pid,version,library,...usage()});
const lines=readline.createInterface({input:process.stdin,crlfDelay:Infinity});
for await (const line of lines) {
  const started=performance.now();let request;
  try {
    request=JSON.parse(line);
    if(!request||!Array.isArray(request.args)||!request.args.length||!request.args.every(v=>typeof v==='string'))
      throw new Error('Expected {id, args: nonempty string array}');
    const log=await pack(request.args,iface);
    send({id:request.id,ok:true,log,packMs:performance.now()-started,...usage()});
  } catch(error) {
    // A normal gltfpack error rejects only this request. The next request uses
    // the same instance; recovery from missing-input errors is benchmarked.
    send({id:request?.id??null,ok:false,error:String(error?.message||error),
      packMs:performance.now()-started,...usage()});
  }
}
