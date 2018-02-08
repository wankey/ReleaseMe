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
    elif [ "$key" = "PROJECT_NAME" ];then
        PROJECT_NAME=$value
    elif [ "$key" = "KEY_ALIAS" ];then
        KEY_ALIAS=$value
    elif [ "$key" = "STORE_PASSWORD" ];then
        STORE_PASSWORD=$value
    elif [ "$key" = "KEY_PASSWORD" ];then
        KEY_PASSWORD=$value
    elif [ "$key" = "USE_360JIAGU" ];then
        USE_360JIAGU=$value
    elif [ "$key" = "360_ACCOUNT" ];then
        ACCOUNT_360=$value
    elif [ "$key" = "360_PASSWORD" ];then
        PASSWORD_360=$value
    elif [ "$key" = "USE_ANDRESPROGUARD" ];then
        USE_ANDRESPROGUARD=$value
    fi
done <  config.properties

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
JIAGU_DIR=$PROJECT_DIR/360jiagu
JAVA_DIR=$PROJECT_DIR/360jiagu/java/bin
APP_DIR=$PROJECT_DIR/$PROJECT_NAME/$version
BUILD_TOOL_DIR=$ANDROID_HOME/build-tools/26.0.2/
CHANNEL_FILE=$APP_DIR/config/markets.txt


echo "开始下载源代码"
rm -rf $APP_DIR/
git clone -b $version $SERVER_PATH $APP_DIR
cd $APP_DIR

echo "开始编译"
rm -rf out/ ;
mkdir out/ ;

sh gradle clean;
if [ "$USE_ANDRESPROGUARD" = "true" ];then
  sh gradle resguardRelease;
  cp $APP_DIR/app/build/outputs/apk/release/AndResGuard_app-release/app-release_7zip_aligned_unsigned.apk $APP_DIR/out/app-release_unsigned.apk
else
  sh gradle assembleRelease;
fi

echo "编译完成"
echo "====================================="

if [ "$USE_360JIAGU" = "true" ];then
  echo "开始加固360渠道包"
  java -jar $JIAGU_DIR/jiagu.jar -login $ACCOUNT_360 $PASSWORD_360;
  java -jar $JIAGU_DIR/jiagu.jar -config null;

  java -jar $JIAGU_DIR/jiagu.jar -jiagu $APP_DIR/out/app-release_unsigned.apk out/

  echo "加固完成"
  echo "====================================="
fi

echo "开始签名"
  $BUILD_TOOL_DIR/apksigner sign --ks $APP_DIR/config/android.jks --ks-key-alias $KEY_ALIAS --ks-pass pass:$KEY_PASSWORD --key-pass pass:$KEY_PASSWORD --out $APP_DIR/out/app-release.apk $APP_DIR/out/app-release_unsigned.apk
  $BUILD_TOOL_DIR/apksigner sign --ks $APP_DIR/config/android.jks --ks-key-alias $KEY_ALIAS --ks-pass pass:$KEY_PASSWORD --key-pass pass:$KEY_PASSWORD --out $APP_DIR/out/app-release_signed_110_jiagu.apk $APP_DIR/out/app-release_unsigned_110_jiagu.apk
  java -jar $PROJECT_DIR/CheckAndroidV2Signature.jar $APP_DIR/out/app-release.apk;
  java -jar $PROJECT_DIR/CheckAndroidV2Signature.jar $APP_DIR/out/app-release_signed_110_jiagu.apk;
  rm -rf $APP_DIR/out/app-release_unsigned.apk
  rm -rf $APP_DIR/out/app-release_unsigned_110_jiagu.apk
echo "签名完成"

echo "开始生成渠道包"
  java -jar $PROJECT_DIR/walle-cli-all.jar batch -c T360 $APP_DIR/out/app-release_signed_110_jiagu.apk
  java -jar $PROJECT_DIR/walle-cli-all.jar batch -f $APP_DIR/config/markets.txt $APP_DIR/out/app-release.apk
  java -jar $PROJECT_DIR/walle-cli-all.jar show $APP_DIR/out/app-release_360.apk
  rm $APP_DIR/out/app-release_signed_110_jiagu.apk
  mv $APP_DIR/out/app-release_signed_110_jiagu_T360.apk $APP_DIR/out/app-release_360.apk
  rm $APP_DIR/out/app-release.apk

  java -jar $PROJECT_DIR/walle-cli-all.jar show -c $APP_DIR/out/app-release_self.apk
  java -jar $PROJECT_DIR/walle-cli-all.jar show -c $APP_DIR/out/app-release_360.apk
echo "渠道包生成完毕"

echo "打包渠道包"
cd out; zip $version.zip *;
echo "====================================="

if [ "$USE_FTP" = "true" ];then
  echo "开始上传到FTP"
  updir=$pwd/out/    #要上传的文件夹
  echo "将要上传的文件目录："${updir}
  todir=$FTP_PATH         #目标文件夹
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
