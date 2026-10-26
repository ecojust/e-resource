# 照片玻璃的网页显示

网页对**带实际照片map、名称明确为 `PhotoFacade_…Glass…` 或 `PhotoFacade_…Glazing…`** 的玻璃使用 `MeshBasicMaterial`。照片已记录现场的照明和反射，继续用场景PBR受光、投影或额外HDR会重复改变该信息。此处理取消这几项重复贡献；它不是从照片反推材质，也不声称获得去光照的PBR纹理。

显示仍保留原材质颜色系数、透明度、侧面/深度/混合设置、雾及应用统一色调映射，不能等同于屏幕像素与照片像素逐值一致。GLB、照片字节、几何及原始UV缓冲均不变；继续使用同一个贴图对象与既有EXIF方向补偿。

Bund12/17采用旧 `Glazing` 名称，其余登记通常采用 `Glass`。Bund18的 `PhotoFacade_Limestone_*` 照片石墙保持原材质；没有该明确前缀/名称或没有照片map的普通玻璃、窗框和边缘构件均不转换。

`src/photographic-glass.js` 在每个导入group内按原材质身份缓存一次转换，先替换所有该group引用，再释放旧材质程序。贴图和Bitmap不会在转换时释放；不再采样的旧PBR附加贴图也保留明确资源归属，到模型卸载时由 `model-resources.js` 去重清理。viewer共享贴图及其仍共享的Bitmap不由该模型关闭。纯照片玻璃mesh不投影、不接收场景阴影，也不会在HDR稍后载入时再次接入反射；普通玻璃继续使用原反射系统。

依据：本地同相机A/B的 `04-photo-captured-radiance` 已由主代理目视确认；生产设置沿用该实验的 `source.toneMapped`。自动验证见 `tests/photographic-glass.test.mjs`、`photographic-texture.test.mjs`、`photographic-reflection.test.mjs` 和 `model-resources.test.mjs`。浏览器最终复验由主代理统一执行。
