#!/usr/bin/env bash

if [ x$1 != x ]
then
   version=$1
else
   read -p "Enter the version > " version
fi

while read linemsg
do
    key=$(echo $linemsg | cut -d = -f 1)
    value=$(echo $linemsg | cut -d = -f 2)

    if [ "$key" = "TYPE" ];then
        SERVER_TYPE=$value
    elif [ "$key" = "SERVER_PATH" ];then
        SERVER_PATH=$value
    elif [ "$key" = "APP_NAME" ];then
        APP_NAME=$value
    elif [ "$key" = "KEY_ALIAS" ];then
        KEY_ALIAS=$value
    elif [ "$key" = "STORE_PASSWORD" ];then
        STORE_PASSWORD=$value
    elif [ "$key" = "KEY_PASSWORD" ];then
        KEY_PASSWORD=$value
    elif [ "$key" = "USE_360JIAGU" ];then
        USE_360JIAGU=$value
    elif [ "$key" = "360_ACCOUNT" ];then
        360_ACCOUNT=$value
    elif [ "$key" = "360_PASSWORD" ];then
        360_PASSWORD=$value
    fi
done <  config.properties

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
JIAGU_DIR=$PROJECT_DIR/360jiagu
JAVA_DIR=$PROJECT_DIR/360jiagu/java/bin;
APP_DIR=$PROJECT_DIR/$APP_NAME/$version

echo "开始下载源代码"
git clone -b $version $SERVER_PATH $APP_DIR
cd $APP_DIR

echo "开始编译"
rm -rf out/ ;
sh gradlew clean;
sh gradlew assembleReleaseChannels ; #编译普通渠道包，并输出到根目录下的out目录
echo "编译完成"
echo "====================================="

if [ "$USE_360JIAGU" = "true" ];then
  echo "开始加固360渠道包"
  java -jar $JIAGU_DIR/jiagu.jar -login $360_ACCOUNT $360_PASSWORD;
  java -jar $JIAGU_DIR/jiagu.jar -importsign $APP_DIR/key.jks $STORE_PASSWORD $KEY_ALIAS $KEY_PASSWORD ;
  java -jar $JIAGU_DIR/jiagu.jar -config null;
  java -jar $JIAGU_DIR/jiagu.jar -jiagu out/app-360-$version.apk out/ -autosign;
  rm out/app-360-$version.apk
  echo "加固完成"
  echo "====================================="
fi


echo "打包渠道包"
cd out; zip $version.zip *;
echo "====================================="

if [ "$USE_FTP" = "true" ];then
  echo "开始上传到FTP"
  updir=$pwd/out/    #要上传的文件夹
  echo "将要上传的文件目录："${updir}
  todir=/android          #目标文件夹
  echo "远程目录为："${todir}
  ip=$FTP_SERVER      #服务器
  user=$FTP_ACCOUNT          #ftp用户名
  password=$FTP_PASSWORD        #ftp密码
  ftp -nv ${ip}
  user ${user} ${password}
  type binary
  cd ${todir}
  lcd ${updir}
  prompt
  put $version.zip ${todir}/$version.zip
  quit
  EOF
  echo "FTP上传完毕"
  echo "====================================="
fi
