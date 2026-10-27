// Isolated control of the QA expression only. No browser/product traffic is stubbed.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url));
const expressions=JSON.parse(fs.readFileSync(path.join(dir,'runtime-functions.json'),'utf8'));
globalThis.document={baseURI:'https://test.invalid/project/'};
assert.ok(globalThis.crypto?.subtle,'Node with native WebCrypto is required');
const files=[{file:'src/first.js'},{file:'src/second.js'},{file:'src/third.js'}];
const delays={'first.js':24,'second.js':1,'third.js':8};
async function exercise(expression,{badStatus=false,rejectRead=false}={}) {
  const starts=[],ends=[];
  globalThis.fetch=async url=>{
    const name=path.basename(url.pathname);starts.push(name);
    await new Promise(resolve=>setTimeout(resolve,delays[name]));ends.push(name);
    return {ok:!(badStatus&&name==='second.js'),status:badStatus&&name==='second.js'?503:200,
      async arrayBuffer(){if(rejectRead&&name==='second.js')throw Error('synthetic-body-read-failure');return new TextEncoder().encode(name+'\n').buffer;}};
  };
  try{return {rows:await (new Function('return ('+expression+')'))()(files),starts,ends};}
  catch(error){return {error:String(error.message),starts,ends};}
}
const sequential=await exercise(expressions.original);
const parallel=await exercise(expressions.candidate);
assert.deepEqual(sequential.rows,parallel.rows);
assert.deepEqual(parallel.rows.map(row=>row.file),files.map(row=>row.file));
assert.deepEqual(parallel.starts,['first.js','second.js','third.js']);
assert.deepEqual(parallel.ends,['second.js','third.js','first.js']);
const badOld=await exercise(expressions.original,{badStatus:true});
const badNew=await exercise(expressions.candidate,{badStatus:true});
assert.equal(badOld.error,'src/second.js: 503');assert.equal(badNew.error,badOld.error);
// Ensure the first failed Promise.all's remaining requests settle before swapping this test's mock.
await new Promise(resolve=>setTimeout(resolve,30));
const readOld=await exercise(expressions.original,{rejectRead:true});
const readNew=await exercise(expressions.candidate,{rejectRead:true});
assert.equal(readOld.error,'synthetic-body-read-failure');assert.equal(readNew.error,readOld.error);
await new Promise(resolve=>setTimeout(resolve,30));
const report={passed:true,scope:'Synthetic isolated QA-expression equivalence only; no browser, production asset or performance acceptance.',
  unchanged_exact_rows_and_sha:true,baseline_order_preserved:true,out_of_order_completion_exercised:true,
  all_independent_reads_started:true,non_ok_http_rejected:true,body_read_failure_rejected:true,
  rows:parallel.rows,parallel_starts:parallel.starts,parallel_completion_order:parallel.ends};
fs.writeFileSync(path.join(dir,'equivalence-check.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));
