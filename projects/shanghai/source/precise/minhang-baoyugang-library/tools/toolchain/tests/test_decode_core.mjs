/** Small CPU controls of preservation policy; these are not building model proofs. */
import assert from 'node:assert/strict';
import {triangleKey,addTriangle,compareTriangles,compareValues,compareProtectedGroups,glbTriplesToENU,materialState} from '../decode_core.mjs';
const p=[[0,0,0],[1,0,0],[0,1,0]],n=[0,0,1,0,0,1,0,0,1];
function map(points=p,material='Glass',normals=n,copies=1){const t=new Map(),k=triangleKey(points,material).key;for(let i=0;i<copies;i++)addTriangle(t,k,normals);return t;}
const tests=[];function test(name,run){run();tests.push({name,passed:true});}
test('Actual GLB coordinates rotate to ENU, without axis mirroring',()=>assert.deepEqual(glbTriplesToENU([2,5,-7,1,0,-1]),[2,7,5,1,1,0]));
test('Nonfinite decoded array rejected',()=>assert.throws(()=>glbTriplesToENU([0,0,Infinity])));
test('Empty triangle equivalence rejected',()=>assert.throws(()=>compareTriangles(new Map(),new Map())));
test('Invalid material scalar rejected',()=>assert.throws(()=>materialState({name:'Glass',opacity:NaN})));
test('Default infinite attenuation distance preserved explicitly',()=>assert.equal(materialState({name:'Glass',attenuationDistance:Infinity}).attenuationDistance,'Infinity'));
test('Cyclic winding preserved',()=>assert.equal(triangleKey(p,'Glass').key,triangleKey([p[1],p[2],p[0]],'Glass').key));
test('Reversed winding rejected',()=>assert.throws(()=>compareTriangles(map(),map([p[0],p[2],p[1]]))));
test('Position drift rejected without rounding',()=>assert.throws(()=>compareTriangles(map(),map([[0,0,0],[1.00000001,0,0],[0,1,0]]))));
test('Triangle material reassignment rejected',()=>assert.throws(()=>compareTriangles(map(),map(p,'Frame'))));
test('Duplicate triangle multiplicity checked',()=>assert.throws(()=>compareTriangles(map(),map(p,'Glass',n,2))));
test('Normals below policy tolerated',()=>{const a=.04*Math.PI/180;compareTriangles(map(),map(p,'Glass',[Math.sin(a),0,Math.cos(a),...n.slice(3)]));});
test('Normals above policy rejected',()=>{const a=.06*Math.PI/180;assert.throws(()=>compareTriangles(map(),map(p,'Glass',[Math.sin(a),0,Math.cos(a),...n.slice(3)])));});
const glass={transmission:.8,ior:1.46,thickness:.065,attenuationColor:[.9,.97,.96],attenuationDistance:12,transparent:false,side:0};
test('Unchanged modern glass accepted',()=>compareValues(glass,structuredClone(glass)));
for(const key of ['transmission','ior','thickness','attenuationDistance'])test('Changed '+key+' rejected',()=>assert.throws(()=>compareValues(glass,{...glass,[key]:glass[key]+.01})));
test('Changed attenuation color rejected',()=>assert.throws(()=>compareValues(glass,{...glass,attenuationColor:[.8,.97,.96]})));
test('Lost glass property rejected',()=>{const b={...glass};delete b.transmission;assert.throws(()=>compareValues(glass,b));});
test('Glass opacity mode unchanged',()=>assert.throws(()=>compareValues(glass,{...glass,transparent:true})));
const group=(label)=>({label,material:'Glass',count:1,triangles:map()});
const raw=new Map([['window|Glass',group('window')],['wall/fine-tile-joints-0|Glass',group('wall/fine-tile-joints-0')]]);
const authored=new Map([['window|Glass',group('window')]]),allow=['(?:^|/)fine-tile-joints-[0-9]+$'];
test('Only allowlisted joints can disappear',()=>assert.equal(compareProtectedGroups(raw,authored,allow).removed_groups.length,1));
test('Protected window removal fails',()=>assert.throws(()=>compareProtectedGroups(raw,new Map(),allow)));
test('New LOD geometry fails',()=>{const b=new Map(authored);b.set('wall|Glass',group('wall'));assert.throws(()=>compareProtectedGroups(raw,b,allow));});
test('Changed protected LOD position fails',()=>{const b=new Map(authored);b.set('window|Glass',{...group('window'),triangles:map([[0,0,0],[2,0,0],[0,1,0]])});assert.throws(()=>compareProtectedGroups(raw,b,allow));});
console.log(JSON.stringify({schema:'modern-decoder-policy-cpu-controls-v11',passed:true,building_model_test:false,control_count:tests.length,tests},null,2));
