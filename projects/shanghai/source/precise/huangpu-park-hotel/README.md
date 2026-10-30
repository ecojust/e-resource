# 国际饭店历史主楼：2007外观参照候选

[模型查看与外围漫游](../../../park-hotel.html) · [资产清单](../../../assets/models/candidates/huangpu-park-hotel/manifest.json) · [检查记录](../../../data/audit/park-hotel-v1/README.md)

参照WiNG的2007年照片，以及国资委2023年介绍和上海地方志，制作前部高塔与相连较低主体。模型表现深色基座、棕褐砖面、连续竖肋、分格矩形窗、第二／三／十四设计层的弧角玻璃带、分组退台和高低砖垛塔冠。未将同框体育大厦、玻璃邻楼、后期3–9层后楼或地下室纳入。

## 来源与尺寸解释

官方2023文章与《名街志》83.8米，施工志与名建筑志83.6米，两种值并列。本件选择83.8米作为最高砖垛点，天线和旗杆未建，文献计高端点未知，不能据模型断言83.8与83.6的差异原因。

地上22层、地下2层有文字依据，本件仅设22个地上设计分层。前三层顶面4.8／9／13.2米；其后多数层高3.65米，最高墙面82.6米、砖垛83.8米。分层不代表照片逐层精确对应。实际照片冠部有不等高侧台阶、较宽砖墩和更连贯的中央竖窗组，本候选四组双层退台与均匀窗网明显简化；这些差异保留为后续细化项。文献“十五层以上四面逐层收进”支持上部阶梯轮廓，但没有每次退距；本件将15–22设计层解释为四组、每组两层，属于明确的候选方案。

基座约30×45米，主体约28×44米，前塔局部中心Y−8米；上部四组宽深26×25、23×22、20×19、16×16米，均为设计估计。地图61.80×29.65米外框没有分出历史主体与后期加建，未整体挤出。1179平方米历史占地、1827平方米后期占地、各时期建筑面积和营业面积未用于反推几何边长。

弧角玻璃带用分段曲面表现，半径、分段、窗数、窗框、墙厚、雨篷、塔冠砖垛与背面全部含估计；侧后窗网尚无完整照片核验。材料采用原创纯色与粗糙度，无照片像素、真实砖缝或扫描风化。未复原模糊招牌、字样及屋顶设备。内部楼板只支撑外观结构，不表示开放室内。

[来源及短引](source-register.json) · [逐层设计参数](design-input.json)。WiNG照片CC BY3.0（https://creativecommons.org/licenses/by/3.0/），仅本地参考，未重新发布图片或采样贴图。官方和地方志未确认开放许可，仅列事实、短引和出处。原创代码与几何MIT。1934年6月交付与12月1日开业分别保留，不合并为同一事件。

## 复跑

仓库根目录执行；Python依赖见`source/requirements.txt`，Blender4.3.2、gltfpack1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/huangpu-park-hotel/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/huangpu-park-hotel/source/build_model.py --out /tmp/park
python projects/shanghai/source/precise/huangpu-park-hotel/source/build_model.py --out /tmp/park --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/huangpu-park-hotel/source/build_native.py -- --raw /tmp/park/huangpu-park-hotel-raw.glb --out /tmp/park/huangpu-park-hotel.blend --previews /tmp/park-previews
python projects/shanghai/source/precise/huangpu-park-hotel/source/package_assets.py --raw /tmp/park/huangpu-park-hotel-raw.glb --lod /tmp/park/huangpu-park-hotel-lod.glb --native /tmp/park/huangpu-park-hotel.blend --out projects/shanghai/assets/models/candidates/huangpu-park-hotel --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/huangpu-park-hotel/source/verify_geometry.py --assets projects/shanghai/assets/models/candidates/huangpu-park-hotel --out /tmp/park-geometry.json --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

近远景保持相同体量、窗位、弧角玻璃带与竖肋；远景保留窗台并简化窗框。墙端按内侧斜接，避免转角重叠端面；作者构件独立闭合，相接构件未作整楼布尔并集。原生保存后重开比较建筑几何哈希，预览地面不计入建筑。

网页复验需Playwright和Chromium：启动`python -m http.server 8782 --directory projects/shanghai`，运行`node projects/shanghai/data/audit/park-hotel-v1/qa-browser.cjs`。输出`/workspace/park-browser*`；可用`MODEL_URL`指定页面地址。场景只允许整个楼体外包之外平地行走，不支持室内、登台或楼梯。没有城市原址配准或源替换，40处原址入口数量不变。
