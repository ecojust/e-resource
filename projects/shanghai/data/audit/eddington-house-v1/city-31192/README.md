# 爱登公寓（常德公寓）的正式城市地图复核

从常德路195号的已建目录打开地标。旧站有228处，交付后有229处。桌面使用820×600独立鼠标点击，手机使用390×844独立触控。两端默认画面都将中央砖窗带、两翼圆角阳台和顶部两级退台放在导览卡上方。手机放大后能看清东入口和窗框。[旧城原位](before/map-before.png) · [桌面默认](desktop/map-desktop.png) · [手机默认](phone/map-mobile.png) · [手机放大](phone-zoom/map-mobile-zoom.png)

街面全图能辨入口条纹门框与四字门楣。入口近图可直接读到「常德公寓」，灯牌在上层窗前，位置卡压住人行道一角。右侧阳台近图能分出圆角栏板、各层退进和后面的玻璃窗，最上方一小段栏板受到地标牌遮挡。屋顶图能辨双翼顶层与原生街坊的高差；左下层由信息卡部分遮住。[街面](desktop/map-street-facade.png) · [门楣和条纹门框](architecture/map-striped-jambs-and-name.png) · [右侧退台](architecture/map-balconies-and-setbacks.png) · [屋顶与邻楼](architecture/map-roof.png)

在真实地图上检查门洞、踏步、楼体和邻屋的26个地面点。远档由实际页面载入，再从目录上的独立模型入口逐项点击并保存四份下载，合计4,633,831字节，各文件与清单的SHA-256一致。[地面与街景状态](desktop/main-browser.json) · [真实远档及四次保存](distant/main-browser.json) · [模型远景](distant/map-distant.png) · [六段进程退出](map-process-outcomes.json)

旧城首次请求的六份街区资产和新城手机首次请求的区界文件曾返回502。分别按原Git对象恢复后，新旧站逐件获取200响应。另一次手机默认图成功后，放大时渲染进程中止。完整的失败报告和日志按原字节归档，默认触控和放大随后由两次短会话重验成功。[首轮街区请求](first-control-network-failure) · [首次手机区界请求](first-phone-source-failure) · [首次手机放大及默认图](first-phone-zoom-interruption)
