# 常德路195号爱登公寓

东立面施工范围有四处中央浅阳台、两端圆角长阳台、两级退台及一层带题字的深条纹门廊。上部中央大块实墙、两侧四条连续砖带和层层收窄的屋顶冠饰按2020年高位正面照片修正。2013年独立入口照片记录了三片雨篷、题字和门牌。[首版](draft-review/first-east-front.jpg) · [修订版](draft-review/revised-east-front.jpg) · [修订与照片出处](draft-review/front-revision.json) · [身份与史料](../../../source/precise/jingan-eddington-house/README.md)

原始版与网页近景各47,000个三角面，远景35,200面，可编辑工程重开后有96个网格，逐面与原始版对应。三档分别以144道射线检验阳台实墙和滴水、窗框后的玻璃、横纹门柱、遮檐、每个汉字及门牌数字、四级冠饰和两端退台后墙。[三档几何复核](surface-checks.json) · [原生复核](geometry-native.json)

原底图实名建筑1912距相邻964的地块约7.58米。对近景组完整的457,368个顶点和重心位置，分别用矢量轮廓与带分栋ID的远景三角面比对，确认本栋近景24,022面、远景16面。新模型与同组邻楼三角网的最近间距，近景8.06米、远景8.14米。地面检查覆盖18个门檐、窗面、人行道和后院点位，并独立核对8个相邻来源。[位置与通行](placement-geometry.json) · [地图合同](final-placement-contract.json) · [桌面及手机视线](../../../source/precise/jingan-eddington-house/camera-preflight.json)

独立查看页、脚本与交付件均已按HTTP实取。[独立页](../../../eddington-house.html) · [文件大小与SHA256](standalone-http.json)

正式地图从228处增至229处。对照两个服务实际返回的目录，原来的188个候选模型记录逐行一致。新增的3个三角形只裁剪1912号原楼的模型范围，同组其他楼体保留。两套矢量源共核18项，门廊、人行道及原邻楼共核26个地面位置。[前后版本比较](renderer-parent-controls.json) · [地面与源模型](renderer-runtime-placement.json)

通过正式独立页查看常德路入口，桌面与390像素手机都能切换47,000面近景和35,200面远景，四种文件实际下载并与原清单校验。按钮按实际镜头分别标明常德路入口正面、圆角阳台与退台、上方俯视。正式服务的1,335个输入合计1,136,688,555字节，逐件通过HTTP校验。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [四项下载](viewer.json) · [正式站逐件结果](renderer-release-http.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/50f8bb2706f97e883fef25dd23b01990e0d37eca/projects/shanghai/index.html#landmark=jingan-eddington-house&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
