# ReleaseMe
自动化apk打包脚本，再也不用手动去打包、加固、输出渠道包了，时间都省下来优化代码吧

## CHANGELOG

### 2018-05-11
使用python重构了脚本，支持更多操作的自动化
### 2017-10-26
shell脚本实现从git拉取代码、编译、输出渠道包等工序的自动化

## USAGE
    python /your-path-to-ReleaseMe/release.py -s git_url -b BRANCH/TAG -c all(或者指定的渠道名)
    
## IMPORTANT

1. 请在[config.properties](/config.properties)中配置以下信息(斜体字为可选项，仅在需要使用时配置)<br>
STORE_FILE<br>
MARKET_FILE<br>
KEY_ALIAS<br>
STORE_PASSWORD<br>
KEY_PASSWORD<br>
*360_ACCOUNT="YOUR_ACCOUNT_FOR_DEV_360"*<br>
*360_PASSWORD="YOUR_PASSWORD_FOR_DEV_360"*<br>
*USE_RES_GUARD=false*<br>

2. 本项目默认使用[walle](https://github.com/Meituan-Dianping/walle)作为渠道包输出工具，请在app中添加相关依赖以获取渠道信息