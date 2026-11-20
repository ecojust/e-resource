# 徐汇公学崇思楼修复后立面与屋面核验

模型坐落在徐汇中学的实名崇思楼地块，分别依据修缮项目报告、设计单位的南北立面照片和2010年独立拍摄的斜照。施工项目部记录了1917年奠基、1918年竣工和两方向的轴线尺寸。楼体采用66.140×25.144米，屋面、石饰及门窗的进深取照片估计。[模型范围和建筑来源](../../../source/precise/xuhui-chongsi-building/README.md) · [原始照片与政府名录](../../../source/precise/xuhui-chongsi-building/reference-review.json)

原始及网页近景各有239,342个三角面，远景有56,422个。建模文件以Blender重新打开，核实411个可编辑网格、材质名与原始GLB的带方向三角面。网页近远模型采用Meshopt压缩，并分别独立解码与源网格对照。三份GLB的78条外向射线分别检查了砖柱与柱头、中央门扇、错层塔窗、三种屋顶窗及东西端坡面等实际表面。[模型和完整签名](geometry-native.json) · [三档外立面和屋面射线](opening-rays.json) · [完整交付清单绑定](delivery-manifest-binding.json) · [原生渲染](xuhui-chongsi-building-preview.png)

冻结宏区14-13718-6696的实名楼体316在近、远景均完全由本模型接替。同图组其他九栋与裁剪面重叠为零；全区最近相邻原生建筑1627与裁剪边界相距7.46米。底层地面轮廓自台阶、通柱、外墙和梯塔实物几何提取。每0.85米分段包络保留全部行人高度投影，包含221个边界点，额外包围25.64平方米。八个地面探针区分前庭、步道、踏步和梯塔。固定的南面接近方向−7°、俯角38°，在650及844像素高度下从源轮廓测算均能看见入口、窗列、山花与屋脊。[近远源和地面探针](footprint-review.json) · [安置及碰撞几何](final-placement-contract.json) · [两组取景视线](overview-sightlines.json)

在上海项目目录下使用来源收据指定的宏区文件和空工作目录，可重新执行核验。

    python -B data/audit/chongsi-building-v1/verify-placement.py --macro "$MACRO" --work "$WORK" --out /tmp/chongsi-review
    python -B data/audit/chongsi-building-v1/check-openings.py --work "$WORK" --report /tmp/chongsi-review/opening-rays.json
    python -B data/audit/chongsi-building-v1/check-overview-sightlines.py --feature-table "$MACRO/feature-table.json.gz" --contract /tmp/chongsi-review/final-placement-contract.json --report /tmp/chongsi-review/overview-sightlines.json

160处前态与161处本版的目录均经实际HTTP读取。原有120行接入模型保持一致，崇思楼是本次增加的校园入口。生产快照绑定753项输入。[前后版本HTTP核对](predecessor-controls.json) · [生产输入签名](production-snapshot.json)

独立查看页在1250×820桌面和390×844手机分别加载近景与远景，四次截屏及四个文件下载签名通过，页面错误为零。手机视口将整幅南立面留在控制面板上方，桌面能分辨中央入口、砖柱、百叶窗和屋顶天窗。[逐项浏览器结果](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png) · [影像核对](visual-review.json)

## 正式城市地图

23122前态有160个地点。通过目录进入相邻的徐家汇藏书楼北楼后，在崇思楼位置记录了原始街景。23123目录新增崇思楼后有161个地点。900×650桌面和390×844手机均从正式城市入口载入了近景模型和含316号源的原瓦片组。默认视角完整呈现南立面和孟莎屋顶，名称牌位于建筑上方，发光定位点覆盖南面中央的一小处。 另取南门砖柱、屋面老虎窗、北侧楼梯以及远景。8个街面和墙体样点完成碰撞复核，四件下载按实际响应校验。北侧视角的西端楼梯局部被原有邻楼遮挡。远景截图主要呈现街区位置，运行记录另行确认远景网格已加载。

[前态与原瓦片](control-browser-23122.json) · [前态画面](map-before-23122.png) · [桌面实图](main-desktop.png) · [手机实图](main-mobile.png) · [后态实际操作](main-map-browser-23123.json) · [南门与砖柱](south-door-and-piers.png) · [屋面与老虎窗](mansard-and-dormers.png) · [北侧原邻楼与楼梯](north-stair-towers.png) · [街区远景](distant.png)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/6ca543f4ae326c5e7ffc6c3f08cdd6b5d8f024bd/projects/shanghai/index.html#landmark=xuhui-chongsi-building&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 8 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
