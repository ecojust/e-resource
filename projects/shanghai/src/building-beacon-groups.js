/** Divide projected anchors into latitude bands then nearby longitude groups.
 * Group buttons occupy distinct cells inside the map's visible control insets.
 */
export function groupBeaconLabels(items,{left,top,width,height}){
  const columns=Math.min(5,Math.max(1,Math.floor(width/76)));
  const rows=Math.min(4,Math.max(1,Math.floor(height/46)));
  const groups=[];
  const northToSouth=[...items].sort((a,b)=>a.y-b.y||a.x-b.x||a.number-b.number);
  for(let row=0;row<rows;row++){
    const band=northToSouth.slice(Math.floor(row*items.length/rows),Math.floor((row+1)*items.length/rows));
    band.sort((a,b)=>a.x-b.x||a.y-b.y||a.number-b.number);
    for(let column=0;column<columns;column++){
      const members=band.slice(Math.floor(column*band.length/columns),Math.floor((column+1)*band.length/columns));
      if(!members.length)continue;
      const center=members.reduce((s,m)=>({x:s.x+m.x/members.length,y:s.y+m.y/members.length}),{x:0,y:0});
      const closest=members.reduce((a,b)=>Math.hypot(a.x-center.x,a.y-center.y)<=Math.hypot(b.x-center.x,b.y-center.y)?a:b);
      groups.push({id:'beacon-group:'+row+'-'+column,representative:closest.id,
        memberIds:members.sort((a,b)=>a.number-b.number).map(m=>m.id),
        labelX:left+(column+.5)*width/columns,labelY:top+(row+.5)*height/rows,
        width:Math.min(72,width/columns),height:Math.min(44,height/rows)});
    }
  }
  return groups;
}

const pickerStyle=`
.beacon-group-buttons{position:absolute;inset:0;z-index:2;pointer-events:none}
.beacon-group-buttons>button{position:absolute;transform:translate(-50%,-50%);pointer-events:auto;
  border:1px solid #ffd58b;border-radius:8px;background:#173e42f5;color:#fff1cd;
  font:600 13px/1.2 system-ui,sans-serif;padding:0 4px;cursor:pointer;touch-action:manipulation}
.beacon-group-buttons>button:focus-visible,.beacon-group-picker :focus-visible{outline:3px solid #c58c35;outline-offset:1px}
dialog.beacon-group-picker{box-sizing:border-box;inset:0;margin:auto;padding:16px;width:min(400px,calc(100% - 24px));
  max-width:none;height:auto;max-height:min(78dvh,540px);border:1px solid #a78e64;border-radius:12px;
  background:#fffaf0;color:#183d3e;box-shadow:0 8px 35px #18282c55;font:14px/1.4 system-ui,sans-serif}
dialog.beacon-group-picker[open]{display:flex;flex-direction:column;gap:10px}
dialog.beacon-group-picker::backdrop{background:#102d35a8}
.beacon-group-picker header{position:static;display:flex;align-items:center;justify-content:space-between;gap:8px;padding:0;color:inherit;background:transparent}
.beacon-group-picker h2{margin:0;font-size:17px}
.beacon-group-picker button,.beacon-group-picker input{color:inherit;font:inherit}
.beacon-group-picker .close-picker{min-height:42px;padding:4px 10px;border:1px solid #a89677;border-radius:5px;background:transparent;cursor:pointer}
.beacon-group-picker input{box-sizing:border-box;width:100%;min-height:42px;border:1px solid #aa9a7f;border-radius:5px;padding:7px 9px;background:#fff}
.beacon-group-picker .building-options{min-height:0;overflow:auto;overscroll-behavior:contain}
.beacon-group-picker .building-options button{display:flex;width:100%;align-items:baseline;gap:10px;min-height:44px;padding:9px 4px;text-align:left;
  background:transparent;border:0;border-bottom:1px solid #d9cdb6;cursor:pointer}
.beacon-group-picker .building-options button:hover{background:#f2eadb}
.beacon-group-picker .building-options span{flex:0 0 3ch;color:#755a32;font-variant-numeric:tabular-nums}
.beacon-group-picker .building-options strong{font-weight:500}
`;

export function createBeaconGroupPicker({documentObject,container,byId,numbers,onSelect}){
  const make=(tag,cls)=>{
    const node=documentObject.createElement(tag);
    if(cls)node.className=cls;
    return node;
  };
  const style=make('style');style.textContent=pickerStyle;
  const overlay=make('div','beacon-group-buttons');
  const dialog=make('dialog','beacon-group-picker');
  dialog.setAttribute('aria-label','选择分组中的建筑');
  const header=make('header'),heading=make('h2'),close=make('button','close-picker');
  close.type='button';close.textContent='关闭';
  header.append(heading,close);
  const search=make('input');search.type='search';search.placeholder='按建筑名称或编号筛选';
  search.setAttribute('aria-label',search.placeholder);
  const options=make('div','building-options');
  const empty=make('p');empty.textContent='本组没有匹配的建筑。';empty.hidden=true;
  dialog.append(header,search,options,empty);container.append(style,overlay,dialog);
  const buttons=new Map();
  let groups=new Map(),invoker=null;
  function open(id){
    const group=groups.get(id);
    if(!group)return;
    invoker=buttons.get(id);heading.textContent='本组 '+group.memberIds.length+' 处建筑';
    search.value='';empty.hidden=true;
    const rows=group.memberIds.map(id=>{
      const row=byId.get(id),number=String(numbers.get(id));
      const button=make('button');button.type='button';button.dataset.landmark=id;
      const index=make('span');index.textContent=number;
      const text=make('strong');text.textContent=row.name;
      button.append(index,text);
      button.addEventListener('click',()=>{dialog.close();onSelect(row);});
      return button;
    });
    options.replaceChildren(...rows);options.scrollTop=0;
    if(!dialog.open)dialog.showModal();
    // Do not raise a soft keyboard over a short list on touch devices.
    close.focus({preventScroll:true});
  }
  search.addEventListener('input',()=>{
    const query=search.value.trim().toLocaleLowerCase();
    let count=0;
    for(const option of options.children){
      const id=option.dataset.landmark;
      const match=(numbers.get(id)+' '+byId.get(id).name).toLocaleLowerCase().includes(query);
      option.style.display=match?'':'none';
      if(match)count++;
    }
    empty.hidden=count!==0;
  });
  close.addEventListener('click',()=>dialog.close());
  dialog.addEventListener('close',()=>{if(invoker?.isConnected)invoker.focus({preventScroll:true});});
  function update(layout){
    groups=new Map(layout.map(g=>[g.id,g]));
    for(const [id,button] of buttons)if(!groups.has(id)){button.remove();buttons.delete(id);}
    for(const group of layout){
      let button=buttons.get(group.id);
      if(!button){
        button=make('button');button.type='button';button.dataset.beaconGroup=group.id;
        button.setAttribute('aria-haspopup','dialog');
        button.addEventListener('click',event=>{event.stopPropagation();open(group.id);});
        overlay.appendChild(button);buttons.set(group.id,button);
      }
      button.textContent=group.memberIds.length+' 处';
      button.setAttribute('aria-label',byId.get(group.representative).name+'附近的'+group.memberIds.length+'处建筑');
      Object.assign(button.style,{left:group.labelX+'px',top:group.labelY+'px',width:group.width+'px',height:group.height+'px'});
    }
  }
  return {update,open,destroy(){if(dialog.open)dialog.close();overlay.remove();dialog.remove();style.remove();}};
}
