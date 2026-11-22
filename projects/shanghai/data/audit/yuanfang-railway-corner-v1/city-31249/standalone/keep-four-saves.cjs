// Copy only the assigned inspector's completed saveAs paths, immediately before its original cleanup.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const base=__dirname, out=path.join(base,'viewer-31249','saved');
const expected=JSON.parse(fs.readFileSync(path.join(base,'two-transitions.json')))[249].downloads;
const byName=new Map(Object.values(expected).map(row=>[path.basename(row.file),row]));
const original=fs.rmSync;
fs.rmSync=function(file,...options){
  if(typeof file==='string' && path.dirname(file)===process.env.TMPDIR && byName.has(path.basename(file)) && fs.existsSync(file)){
    const row=byName.get(path.basename(file));
    fs.mkdirSync(out,{recursive:true});
    const retained=path.join(out,path.basename(file));
    fs.copyFileSync(file,retained,fs.constants.COPYFILE_EXCL);
    const contents=fs.readFileSync(retained);
    assert.equal(contents.length,row.bytes);assert.equal(crypto.createHash('sha256').update(contents).digest('hex'),row.sha256);
  }
  return original.call(fs,file,...options);
};
