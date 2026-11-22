# 潘氏花园南楼柱廊地图复核

第324期城市目录有359个模型，第325期加入南楼柱廊后有360个。南楼对应地块14-13718-6694原建筑2572。柱廊几何仅覆盖朝花园的局部，检查记录包含原楼其余部分的地面读数和18个相邻原建筑。两期各自读取冻结城市近、远网，沿40条相机视线求最先相交的三角面，超过目标点的相交通常不遮挡目标。

在本目录使用支持 registerHooks 的 Node.js 运行以下命令。默认分别访问两个原城市服务。也可以在命令尾加上提供相应版本的站点网址。SHANGHAI_PROJECT_ROOT 可指定包含 vendor 的项目目录。

```sh
node trace-registered-city.mjs source-324-sightlines.json result-324.json
node trace-registered-city.mjs source-325-sightlines.json result-325.json
```
