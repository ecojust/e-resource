# 东大名路378号街面与塔亭验收

Blender重开包含151个可编辑网格和17种原创材质的文件后渲染了下列预览。第三稿修正塔身和退台连接处的重叠墙面；前稿和同角度最终预览都保留。原始与网页近景各149,604个三角面，远景63,480个。[Blender预览](hongkou-east-daming-road-378-preview.png) · [原生文件与三种GLB](geometry-native.json) · [塔侧接缝修订前](preflight/before-tower-link-seam.png)

177项射线检查逐档覆盖七开间、六窗与四窗退台、栏板穿孔及实缘、塔身窗扇、亭窗、绿瓦屋面和封合处。地图保留原红砖楼后部和同门牌现代30层总部。初步相机在桌面和手机尺寸各对6131个采样点测量实物，可见街面和塔亭的首个交点都落在本栋。[射线记录](street-checks.json) · [地块核验](placement-geometry.json) · [相机测量](camera-preflight.json)

桌面和手机均在独立页完成近远档切换。四个下载实际取得并按清单校验。[桌面](viewer-desktop-full.png) · [手机](viewer-mobile-full.png) · [浏览器收据](viewer.json)

在160处版本实取745个发布输入和5个底图文件，合计750个HTTP请求、670,253,289字节均匹配。两种矢量来源均只裁切569号；近景组新增10个裁切三角，保留925号现代总部和同组其他楼。[HTTP收据](frozen-http.json) · [运行时核验](runtime-placement.json)

正式地图的159处前版在同一机位可见原灰色楼体。160处版本从390像素手机目录打开，在870像素桌面默认视角可辨七开间红砖街墙、两次退台及右侧绿顶塔亭。专项街面图中标签经过塔亭，俯视图可见亭顶。原楼后部、925号现代总部以及周边建筑继续显示。[前态](formal-map-23122/map-before.png) · [手机](formal-map-23122/map-mobile.png) · [桌面](formal-map-23122/map-desktop.png) · [街面](formal-map-23122/map-street-facade.png) · [屋顶](formal-map-23122/map-roof.png) · [城市远景](formal-map-23122/map-distant.png)

首次近景请求外部 Overture 数据服务失败，5处邻楼地面返回空。重新请求取得HTTP 206瓦片与HTTP 200索引；同一组坐标在实际加载 2,321 项建筑要素后，18 项地面探针全部符合预期。两轮浏览器的原始记录分别留存，建筑几何与配准未变。最终网页逐件实取四个下载，城市远景实际切换到 63,480 个三角面的模型。全站753份签名合计668,355,463字节。[首次记录](formal-map-23122/initial-browser.json) · [恢复实测](formal-map-23122/recovered-browser.json) · [两代签名](formal-map-23122/pair-http.json) · [全站HTTP](formal-map-23122/all-http.json) · [汇总](formal-map-23122/acceptance.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/9207ce553efbc4e9acb7254ab4f2b0f55f744412/projects/shanghai/index.html#landmark=hongkou-east-daming-road-378&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
