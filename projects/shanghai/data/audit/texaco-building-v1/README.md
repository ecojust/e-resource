# 德士古大楼2020年的弧形街墙

上海市人民政府铭牌、市房管局二批2A051和实名门牌均指向延安东路110号。1994年铭牌记载英商会德丰后转美商德士古，1943年竣工，1986年加层。2020年东、南两面的独立街景可数中央及东北侧六层、南段五层。2015照片中的额外窗列和空调机、历史照中央高起的女儿墙分别记入来源。原生底图按八层估高25.6米，著录与不同时期外观分开。[年代及名字](../../../source/precise/huangpu-texaco-building/README.md) · [实拍与市政府铭牌](../../../source/precise/huangpu-texaco-building/reference-review.json)

原创模型沿东南边的约72.2米弧线，制作延安东路一侧九组窗、入口上两列短窗及四川中路一侧十一组窗。两扇门的外墙开口一直抵到人行道，门后玻璃和中柱各有实际进深。完整模型保留釉面砖拼缝、转角纵向壁棱、挑窗台和窗格；简化档保留两侧不同的檐高、双窗、白窗带和中柱。[制作代码](../../../source/precise/huangpu-texaco-building/source/street_front.py) · [四件实物](../../../assets/models/candidates/huangpu-texaco-building/manifest.json)

原始与网页近景各54,596个三角面，远景21,920个。Blender重新打开231个可编辑网格核对，重新打开后渲染的街墙可辨右段上层窗带和中央两列短窗。对三份GLB各测28次表面或天空；南翼上方为空，东翼同一标高有窗；中央门玻璃较普通窗更深，门中圆柱向外凸出。[原生核验](geometry-native.json) · [表面及透空检验](opening-rays.json) · [原生正面](huangpu-texaco-building-preview.png)

固定底图中仅处理1848弧形街墙。近景保留其原生屋顶投影76.25%，远景保留76.61%，同近景组另六个所有者与裁剪均无交叠。源近远几何在截面两处终点略有差异，最大28.37厘米，共用截面取中，距任一档实际端点最大14.19厘米。七处地面探针包括门前人行道、中柱、门后的墙角及门扇之前的凹入空间。[底图及各边道路关系](../../../source/precise/huangpu-texaco-building/footprint-review.json) · [七点与实际三角面检验](footprint-review.json) · [接入合同](final-placement-contract.json) · [两种视高下的视线](overview-sightlines.json)

独立页已实测桌面与390×844手机两档，核对四种文件下载。[浏览器报告](viewer.json) · [桌面](viewer-desktop-full.png) · [手机](viewer-mobile-full.png)

已在第140处前项与第141处城市场景比较全部候选记录，第141处新登记此街墙。[前后HTTP](predecessor-controls.json) · [发布输入](production-snapshot.json)

从上海项目目录复核，其中MACRO为固定底图文件目录，WORK为空目录。

    python -B data/audit/texaco-building-v1/verify-placement.py --macro "$MACRO" --work "$WORK" --out /tmp/texaco-review
    python -B data/audit/texaco-building-v1/check-openings.py --work "$WORK" --report /tmp/texaco-review/opening-rays.json

桌面与手机单体图可分别辨认转角双门和延安东路一翼较低的檐线。[画面观察](visual-review.json)

实际从黄浦目录进入20099的141处城市地图，桌面和390×844手机均能选中德士古大楼。桌面可辨弧形街墙、两段不同高度的女儿墙和中央短窗；手机的两块灯牌遮住底层中央门洞。收起侧栏后的近景可见并排的门、中央圆柱和凹入的玻璃，转至东翼可见连贯的浅色窗带。另在同一会话拍摄保留的后部屋面及21,920面远景模型。[桌面](main-desktop.png) · [手机](main-mobile.png) · [中央双门](central-double-door.png) · [东翼窗带](east-ribbon-windows.png) · [保留屋面](retained-source.png) · [远景](distant.png)

该会话从20098取得前项140处目录，核对原有100个候选条目、四种交付物的字节及摘要，并确认底图1848所在的近景瓦片与远景瓦片均实际加载。七个地面点分别检查门前人行道、门侧的凹处、门槛后方、中柱和两翼墙体；网页、控制台与资源请求错误均为零。182个HTTP输入和4个登记生成文件已逐项对照。前项公开版本另从固定提交下载25项共35,794,962字节。[完整浏览器记录](main-map-browser.json) · [本次实取文件](main-map-inputs.json) · [工作树核对](project-comparison.json) · [140处公开版本取件](predecessor-public-downloads-140.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/8f2798fc89817c592dd627182d528d19782a0fec/projects/shanghai/index.html#landmark=huangpu-texaco-building&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
