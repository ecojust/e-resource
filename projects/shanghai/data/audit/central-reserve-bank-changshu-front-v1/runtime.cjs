const fs=require('node:fs'),path=require('node:path'),raw=fs.readFileSync.bind(fs);
const catalog=raw(0),site=process.env.SHANGHAI_PROJECT_ROOT,work=process.env.CHANGSHU_WORK;
fs.readFileSync=function(file,...args){
 if(file===path.join(site,'data/candidate-city-integrations.json'))return catalog;
 if(file===path.join(site,'source/precise/jingan-central-reserve-bank-changshu-front/footprint-review.json'))return raw(path.join(work,'footprint-review.json'),...args);
 return raw(file,...args);
};
