# ReleaseMe
自动化apk打包脚本，再也不用手动去打包、加固、输出渠道包了，时间都省下来优化代码吧

##CHANGELOG

###2018-05-11
使用python重构了脚本，支持更多操作的自动化
###2017-10-26
shell脚本实现从git拉取代码、编译、输出渠道包等工序的自动化


##USAGE
    python /your-path-to-ReleaseMe/release.py -s git_url -b BRANCH/TAG -c all(或者指定的渠道名)
    
##IMPORTANT
1. 项目根目录的gradle.properties中需要配置签名文件信息<br>
STORE_FILE=""<br>
KEY_ALIAS=""<br>
STORE_PASSWORD=""<br>
KEY_PASSWORD=""<br>
2. 项目根目录下需要有个config文件夹，内含文件markets.txt，文件中每行一个渠道名
3. 如需使用360加固或发布到360应用市场，请在[config.properties](/config.properties)中配置你的360开发者平台的账号和密码