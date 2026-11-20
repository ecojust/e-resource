# 原上海犹太人总会南京西路722号南楼

上海市房屋管理局的第二批优秀历史建筑表在2B001同列两处，南京西路722号犹太人总会与702号黄河皮鞋店。2013年庭院入口保护牌明确写722号，春兰公司存档办公地址也记722号。上海近代文献馆记载，叶贻铨原拟建体育会、赛马总会，先建两层，抗战时期售予犹商，后曾用作市政协办公处及联谊俱乐部。[正式名录与建筑史料](reference-review.json)

本模型取2013年12月12日庭院的三幅地面实拍及2020年2月2日俯拍可证的南楼。入口设双柱拱券门廊，两侧有圆窗；东西各五座券窗，楼上露台以汰石子式瓶状栏杆围合。端翼窗面转折，檐后红瓦坡顶沿两翼与端部相连。北侧垂直翼和院内平屋顶附建继续沿用城市原体，院墙、树、车道、室内与702号另列。窗框分格、雕饰和标高均有估算。[六幅参考照片与许可](reference-review.json) · [底图、地面定位与航片](footprint-review.json)

[独立查看器](../../../jewish-club.html) · [网页近景](../../../assets/models/candidates/jingan-jewish-club/jingan-jewish-club-web.glb) · [网页远景](../../../assets/models/candidates/jingan-jewish-club/jingan-jewish-club-lod.glb) · [原始 GLB](../../../assets/models/candidates/jingan-jewish-club/jingan-jewish-club-raw.glb) · [Blender 原生](../../../assets/models/candidates/jingan-jewish-club/jingan-jewish-club.blend) · [清单](../../../assets/models/candidates/jingan-jewish-club/manifest.json)

## 重建

在 `projects/shanghai` 下执行。需要 Python、NumPy、Shapely 2.1、Node.js、Blender 4.3、gltfpack、ImageMagick 与 Open Image Denoise。局部X沿院侧立面向东稍偏北，Y向楼内，Z向上；GLB使用标准Y向上。源程序按门廊、拱廊、石材、栏杆与屋顶分别命名。

```sh
python source/precise/jingan-jewish-club/source/build_model.py \
  --out /tmp/jewish-club-assets --audit /tmp/jewish-club-audit \
  --gltfpack gltfpack --oidn oidnDenoise
python data/audit/jewish-club-v1/check-surfaces.py \
  --manifest /tmp/jewish-club-assets/manifest.json --out /tmp/jewish-club-audit/surface-probes.json
python data/audit/jewish-club-v1/verify-placement.py \
  --manifest /tmp/jewish-club-assets/manifest.json --work /tmp/jewish-club-sources --output /tmp/jewish-club-audit
```

原生、两级网页几何、底模近远景和院地碰撞有独立检测记录。可在固定Git对象不可用时将底图的四个清单文件以原文件名预放入工作目录。[几何、地面与邻楼核验](../../../data/audit/jewish-club-v1/README.md)
