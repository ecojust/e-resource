# 永嘉路501号住宅核验

作者依据2014年街照、天平街道档案中的西端和庭园照，以及图书馆所存塔楼照片，制作北面、西北圆塔、西端及南院一面。第二轮根据塔楼照片调整金属尖顶下砖饰和窄长窗；预览可辨三只老虎窗、街面小檐和西侧低附间。[照片、年代和范围](../../../source/precise/xuhui-yongjia-road-501-residence/README.md) · [终版原生预览](xuhui-yongjia-road-501-residence-preview.png)

Blender重开后检查79个可编辑网格、14种材质和64,700个近景三角面。远景为16,088面，三个序列化模型各有56处射线检查，覆盖窗框、砖圈、尖塔和屋面。[原生复核](geometry-native.json) · [三档168次射线](surface-checks.json)

340号源体东端保留近景10.94平方米、远景10.15平方米。另五座房屋逐栋检查，最近一组近景三角离裁切约9.83米，岳阳路院内的2048号楼约13.00米。桌面及手机默认139°／51°分别对10,787个北立面与圆塔采样作视线核验。[配准与15处地面实测](placement-geometry.json) · [镜头预检](camera-preflight.json)

在22167正式独立模型页，桌面与390像素手机均从近景切到远景，实际下载三个GLB与Blender文件，四份正文散列按清单核对。该版地图204处、1,129个签名输入，运行时在20个宏块纹理中验证1,119个裁切三角，最大单纹理322，目标源新增27个裁切三角。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [四件实际下载](viewer.json) · [运行时与地面结果](runtime-placement.json)

31166与31167两代主地图实拍包含桌面和触屏手机默认视角、地面近景、屋顶及远景。住宅浅色窗格、三只老虎窗、尖顶圆塔在街面相机中可辨，另五座原建筑保留原地碰撞。[主地图对比与六张原图](city-31167/README.md)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/56a06d911a6422f841fb5a9ea72fa63d4b654ce5/projects/shanghai/index.html#landmark=xuhui-yongjia-road-501-residence&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
