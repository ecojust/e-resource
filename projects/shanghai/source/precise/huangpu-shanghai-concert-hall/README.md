# 上海音乐厅（原南京大戏院）

模型展示黄浦区延安东路523号上海音乐厅迁建后的外观。2003年，原建筑向东南平移66.46米。原有保护建筑与迁建后的新增部分共同构成现址建筑。西北三联拱窗入口和倒角、东北长边与东南三开间入口分别参照已查看的实景照片。东南入口另有台阶，中央红色双坡屋顶及浅色端山墙分别有航片和地面远景可参照。[资料核对](reference-review.json)

西南立面缺少可辨认逐窗的照片，使用素面墙体和檐线表达其体量。屋面分段、开间、门窗、柱头、栏杆、简化浮雕、设施与台阶尺寸为估计。未建室内、场地、周边楼宇和搬迁前旧址。网页仅开放俯瞰。光照与材料为日间表达。

从仓库根目录执行以下命令可重建四个模型文件和预览图。依赖 Python、NumPy、Shapely 2.1+、Blender 和 gltfpack。文件名和大小以交付清单为准。

```sh
python projects/shanghai/source/precise/huangpu-shanghai-concert-hall/source/build_concert_hall.py \
  --out /tmp/concert-hall/assets --audit /tmp/concert-hall/audit \
  --gltfpack gltfpack --blender blender
```

建模程序和原创外观构件采用 MIT 许可。底层平面轮廓与地理要素来自 © OpenStreetMap contributors 和 Overture Maps Foundation，适用 ODbL 1.0。原源高度使用2020年 CNBH 10米栅格，见资料记录中的 CC BY 4.0 署名，不能当作建筑测高。第三方照片和航片仅用于研究，交付不含照片、航片图像及纹理。

[模型清单](../../../assets/models/candidates/huangpu-shanghai-concert-hall/manifest.json) · [定位、裁剪和碰撞检查](../../../data/audit/concert-hall-v1/footprint-review.json)
