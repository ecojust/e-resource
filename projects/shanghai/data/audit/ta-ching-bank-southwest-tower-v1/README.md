# 大清银行上海分行旧址西南八角塔

模型以2017年修缮后有日期的街照为准，较低铜穹位于四川中路和汉口路的西南转角。汉口路正门上的高穹顶在同一幢楼的另一位置。[史料、摄影署名与制作范围](../../../source/precise/huangpu-ta-ching-bank-southwest-tower/README.md) · [两期街照](preflight/2013-and-2017-west-corner.jpg)

三份试制GLB分别通过89处独立射线，实测街角窗洞的玻璃和窗框进深、两街首间窗墙的石带、山花、小柱、铜皮和顶杆。近景有23,336个三角面，远景有12,816个，模型按各个转角面的展开长度布置原创红砖贴图。三个版本均使用重复采样；原始模型的1,636个带纹理顶点与作者函数的最大UV差约为0.0000018。[立面与试模](preflight/restored-form-review.jpg) · [三档表面](preflight/mesh-surfaces.json) · [纹理实测](preflight/brick-texture-uv.json)

试制模型与宏区14-13720-6694的59号原房两档实网格配准。修剪仅限32.02平方米的转角小段；近档保留98.53%的原房投影，远档保留98.58%，九条截面与两档原网格边界的偏差小于8厘米。十栋邻屋和21处路面、壁体及玻璃内外的位置均经核验。默认桌面和手机各12处受证构件均通过城市体量视线检查。[原房保留量及地面](preflight/corner-scope.json) · [默认取景](preflight/overview-sightlines.json)

两种默认镜头又对网页近、远档的实际三角网格做了48条首个表面求交。四川中路首间上窗按可见玻璃另定位；最终观察点能落在真实窗玻璃、石框、三角山花、铜穹立缝和细杆。相邻窗柱对西侧窗洞形成自然侧向遮挡。[导出网格的镜头求交](preflight/exported-mesh-sightlines.json)

正式包装重新打开Blender工程，并逐个核对可编辑网格上的红砖贴图和UV。三份最终GLB另验267处材质与进深、21处地面和九段截面。[正式三档表面](surface-checks.json) · [工程纹理](native-uv.json) · [最终配准](placement-geometry.json) · [独立预览](../../../ta-ching-bank-southwest-tower.html)

## 西南八角塔在城市主图中的位置

主图收录的建筑由 314 处增至 315 处。四川中路和汉口路交界的转角保留矮铜穹和细顶杆，两条街各自的第一个开间也可在图中辨认。桌面视口用鼠标、手机尺寸视口用触摸输入，各从地图标记选中本栋。21 处地面和墙体检查点、12 处相邻建筑检查点均与预期相符。独立页在桌面和手机尺寸视口取得的六幅视图覆盖正面、斜侧和远景，四份下载实物与模型清单的 SHA-256 一致。

[城市主图](../../../index.html#landmark=huangpu-ta-ching-bank-southwest-tower&mode=overview) · [城市与独立页逐图记录](final-map-31280/visual-review.json) · [导出模型表面、纹理与视线](tower-recheck/README.md)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/cec7cede033b1b659fbeb6b0c903a558dea98c9d/projects/shanghai/index.html#landmark=huangpu-ta-ching-bank-southwest-tower&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，8 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
