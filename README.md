# ReleaseMe
自动化apk打包脚本，再也不用手动去打包、加固、输出渠道包了，时间都省下来优化代码吧

## CHANGELOG

### 2018-08-01
添加了更多的可配置项，使用更为灵活
### 2018-05-11
使用python重构了脚本，支持更多操作的自动化
### 2017-10-26
shell脚本实现从git拉取代码、编译、输出渠道包等工序的自动化

## USAGE
    python /your-path-to-ReleaseMe/release.py -b BRANCH/TAG [-c]

-b 后为需要打包的分支名<br>
-c 为最后要生成的渠道名，不配置则读取[markets.txt](/markets.txt)文件

## IMPORTANT

1. 使用前请修改[config.properties.sample](/config.properties,sample)中的配置，并重命名删除文件名中的.sample
2. 本项目默认使用[walle](https://github.com/Meituan-Dianping/walle)作为渠道包输出工具，请在app中添加相关依赖以获取渠道信息
3. 如需使用[AndResGuard](https://github.com/shwenzhang/AndResGuard),请按照官方文档配置好app/build.gradle


## TODO
- [ ] checkout源码前判断工作目录是否已有相同版本的源码，有则不重新拉取
- [x] 支持[packer-ng-plugin](https://github.com/mcxiaoke/packer-ng-plugin)输出渠道包
- [ ] 支持给各ProductFlavor使用不同的签名文件、输出不同的渠道包
- [ ] 支持使用给定的config.xml进行资源混淆
- [ ] 给特定渠道重设application name
- [ ] 可视化界面配置config.properties
