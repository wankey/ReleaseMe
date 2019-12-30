#!/usr/bin/python
# encoding=utf-8
import fnmatch
import getopt
import glob
import os
import shutil
import subprocess
import sys

import requests

import Util
from FtpUtil import FtpUtil
from Properties import Properties
from jiagu import Jiagu


class Release(object):
    git_server_path = None

    module_app = None

    use_resguard = None
    use_tinker = None

    sign_file = None
    key_alias = None
    store_password = None
    key_password = None

    market_tool_type = None
    jiagu_type = None

    account360 = None
    password360 = None

    tencent_cloud_api = None
    tencent_cloud_secret = None

    toolDir = os.path.join(os.getcwd(), "tool")
    project_dir = None
    branch_dir = None
    outputs_dir = None

    # FTP服务器配置
    ftpServer = None
    ftpPort = None
    ftpAccount = None
    ftpPassword = None
    ftpDir = None

    def read_properties(self):
        prop = Properties(os.path.join(os.path.abspath('.'), "config", 'config.properties')).get_properties()

        self.git_server_path = prop["GIT_SERVER"]
        self.sign_file = os.path.abspath(prop["STORE_FILE"])
        self.key_alias = prop["KEY_ALIAS"]
        self.store_password = prop["STORE_PASSWORD"]
        self.key_password = prop["KEY_PASSWORD"]
        self.use_resguard = prop["USE_RES_GUARD"] == "true"
        self.account360 = prop["360_ACCOUNT"]
        self.password360 = prop["360_PASSWORD"]
        self.use_tinker = prop["USE_TINKER"] == "true"
        self.module_app = prop["MODULE_APP"]
        self.jiagu_type = int(prop["JIAGU_TYPE"])
        self.market_tool_type = int(prop["MARKET_TOOL_TYPE"])
        self.ftpServer = prop["FTP_SERVER"]
        self.ftpPort = int(prop["FTP_PORT"])
        self.ftpAccount = prop["FTP_ACCOUNT"]
        self.ftpPassword = prop["FTP_PASSWORD"]
        self.ftpDir = prop["FTP_DIR"]
        self.tencent_cloud_api = prop["t_cloud_api"]
        self.tencent_cloud_secret = prop["t_cloud_secret"]

    def config_workspace(self, project_name, branch_name):
        self.project_dir = os.path.join(os.path.abspath('.'), 'workspace', project_name)
        if not os.path.exists(self.project_dir):
            os.makedirs(self.project_dir)
        self.branch_dir = os.path.join(self.project_dir, branch_name)

        if os.path.exists(os.path.join(self.project_dir, "outputs")):
            shutil.rmtree(os.path.join(self.project_dir, "outputs"))
            pass

        self.outputs_dir = os.path.join(self.project_dir, "outputs", branch_name)
        if not os.path.exists(self.outputs_dir):
            os.makedirs(self.outputs_dir)

    # 从git拉取源码
    def checkout(self, project_name, branch_name):
        if os.path.exists(self.branch_dir):
            shutil.rmtree(self.branch_dir)
        return subprocess.check_call(
            ['git', 'clone', '-b', branch_name, os.path.join(self.git_server_path, project_name + ".git"),
             self.branch_dir])

    # 编译
    def build(self, flavor_name, build_type):
        os.chdir(self.branch_dir)
        gradle_wrapper = os.path.join(self.branch_dir, 'gradlew')

        if os.path.exists(gradle_wrapper):
            cmd = './gradlew'
        else:
            cmd = 'gradle'
        if self.use_resguard:
            arg = "resguard" + flavor_name.capitalize() + build_type.capitalize()
        else:
            arg = "assemble" + flavor_name.capitalize() + build_type.capitalize()

        return subprocess.check_call([cmd, arg])

    def copy_product_to_outputs(self, src_dir):
        file = None
        for name in os.listdir(src_dir):
            current_file = os.path.join(src_dir, name)
            if os.path.isdir(current_file):
                file = self.copy_product_to_outputs(current_file)
            elif name.endswith(".apk"):
                file = shutil.copy(current_file, self.outputs_dir)
            else:
                pass
        return file

    def recursiveSearchFiles(self, dirpath, keywords):
        fileList = []
        pathList = glob.glob(os.path.join(dirpath, '*'))
        for mPath in pathList:
            # fnmatch 用于匹配后缀
            if fnmatch.fnmatch(mPath, keywords):
                print(mPath)
                fileList.append(mPath)  # 符合条件条件加到列表
            elif os.path.isdir(mPath):
                if os.path.basename(mPath).startswith("AndResGuard"):
                    pass
                else:
                    fileList += self.recursiveSearchFiles(mPath, keywords)  # 将返回的符合文件列表追加到上层
            else:
                pass
        return fileList

    def find_and_copy_apk(self):
        src_dir = os.path.join(self.branch_dir, self.module_app, "build", "outputs", "apk")
        return self.recursiveSearchFiles(src_dir, "*.apk")

    def upload_to_ftp(self, local_file):
        print("上传 %s 到 %s" % (local_file, self.ftpServer))
        ftp = FtpUtil(self.ftpServer, self.ftpPort)
        ftp.login(self.ftpAccount, self.ftpPassword)

        if os.path.isfile(local_file):
            ftp.upload_file(local_file, self.ftpDir)
        else:
            ftp.upload_file_tree(local_file, self.ftpDir)

    def jiagu_by_legu(self, file):
        if not self.tencent_cloud_api:
            print("未配置腾讯云Api")
        else:
            self.upload_to_ftp(file)
            remote_file = os.path.join("http://", self.ftpServer, self.ftpDir, os.path.basename(file))
            self.call_legu(remote_file, Util.getFileMD5(file))

    def call_legu(self, src_file, file_md5):
        print("使用腾讯乐固进行加固")
        jiagu = Jiagu()
        result_url = jiagu.jiagu(self.tencent_cloud_api, self.tencent_cloud_secret, src_file, file_md5)
        if result_url is not None:
            file_name = os.path.join(self.outputs_dir, os.path.basename(src_file))
            self.download_file(result_url, file_name)
            self.sign_apk(file_name)
        else:
            print("加固失败")

    def jiagu_by_360(self, file):
        print("使用360加固宝进行加固")
        dir_360_jiagu = os.path.join(self.toolDir, '360jiagu')
        java = os.path.join(dir_360_jiagu, 'java/bin/java')
        subprocess.check_call(['chmod', 'a+x', java])
        ret = subprocess.check_call(
            [java, '-jar', dir_360_jiagu + '/jiagu.jar', '-login', self.account360, self.password360])
        if ret != 0:
            print("360开发者中心登录失败")
            exit()
        ret = subprocess.check_call([java, '-jar', dir_360_jiagu + '/jiagu.jar', '-config', 'null'])
        if ret != 0:
            print("360加固宝设置失败")
            exit()
        self.jiagu_apk(java, dir_360_jiagu, file)

    def jiagu_apk(self, java, jiagu_dir, file):
        ret = subprocess.check_call(
            [java, '-jar', jiagu_dir + '/jiagu.jar', '-jiagu', file, self.outputs_dir])
        if ret == 0:
            for name in os.listdir(self.outputs_dir):
                if name.endswith("_jiagu.apk"):
                    src_file = os.path.join(self.outputs_dir, name)
                    self.sign_apk(src_file)
        return ret

    def jiagu(self, file):
        if self.jiagu_type == 1:
            self.jiagu_by_360(file)
        elif self.jiagu_type == 2:
            self.jiagu_by_legu(file)
        else:
            return

    def sign_apk(self, src_file):
        print("重新签名：" + src_file)
        ret = subprocess.check_call(
            ["java", '-jar', self.toolDir + '/apksigner.jar', 'sign', "--ks", self.sign_file,
             '--ks-key-alias',
             self.key_alias, '--ks-pass', 'pass:' + self.key_password, '--key-pass',
             "pass:" + self.key_password, '--out',
             os.path.join(os.path.dirname(src_file), os.path.basename(src_file).replace(".apk", "_signed.apk")),
             src_file])
        os.remove(src_file)

    def download_file(self, url, file_name):
        print("开始下载：" + url)
        r = requests.get(url, stream=True)

        with open(file_name, "wb") as pdf:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    pdf.write(chunk)
        print("下载完成：" + file_name)

    def call_packer_tool(self, file_name, src_file, channel_name, extra_info, dst_file):
        print("===========================================================")
        print("当前正在输出的渠道是：" + channel_name)
        channel_name = channel_name.strip().replace('\n', '')
        if self.market_tool_type == 1:
            if extra_info == "":
                subprocess.check_call(
                    ["java", "-jar", self.toolDir + "/walle-cli-all.jar", "batch"
                        , '-c', channel_name
                        , src_file
                        , dst_file])
            else:
                extra_info = extra_info.strip().replace('\n', '')
                subprocess.check_call(
                    ["java", "-jar", self.toolDir + "/walle-cli-all.jar", "put"
                        , '-c', channel_name
                        , '-e', extra_info
                        , src_file
                        , os.path.join(dst_file, file_name.replace("-signed.apk", "_" + channel_name + ".apk"))])
        elif self.market_tool_type == 2:
            tmpFile = os.path.join(dst_file, "tmp")
            subprocess.check_call(
                ["java", "-jar", self.toolDir + "/packer-ng-2.0.1.jar", "generate",
                 "--channels=" + channel_name
                    , "--outputs=" + tmpFile
                    , src_file
                 ])
        else:
            print("未支持的渠道包工具")

    def make_channel(self, out_puts, file_name, channel_name, product):
        dst_file = os.path.join(out_puts, "channelApk")
        if product != "":
            dst_file = os.path.join(dst_file, product)

        if not os.path.exists(dst_file):
            os.makedirs(dst_file)

        src_file = os.path.join(out_puts, file_name)

        if os.path.isfile(src_file):
            if "!" in channel_name:
                channel = channel_name.split("!")[0]
                extra_info = channel_name.split("!")[1]
                self.call_packer_tool(file_name, src_file, channel, extra_info, dst_file)
            else:
                self.call_packer_tool(file_name, src_file, channel_name, "", dst_file)

    def prepare_market_list(self,flavor_nname, channel_name):
        for file in os.listdir(self.outputs_dir):
            if file.endswith("_signed.apk"):
                if channel_name == "all":
                    market_file_path = os.path.join('.', 'config')
                    market_file_path = os.path.join(market_file_path, '{0}_markets.txt'.format(flavor_nname))
                    if os.path.exists(market_file_path):
                        market_file = open(market_file_path, 'r')
                        lines = market_file.readlines()
                        for line in lines:
                            self.make_channel(self.outputs_dir, file, line, flavor_nname)
                    else:
                        print("没有找到对应的渠道配置文件")
                else:
                    self.make_channel(self.outputs_dir, file, channel_name, flavor_nname)


def main(argv):
    try:
        opts, args = getopt.getopt(argv[1:], 'p:b:f:t:c:', ['product=', 'branch=', 'flavor=', 'buildType=', 'channel='])
        branch_name = "master"
        channel = ""
        project_name = ""
        flavor_name = ""
        build_type = "release"
        for opt, arg in opts:
            if opt in ['-b', '--branch']:
                branch_name = arg
            elif opt in ['-c', '--channel']:
                channel = arg
            elif opt in ['-p', '--project']:
                project_name = arg
            elif opt in ['-f', '--flavor']:
                flavor_name = arg
            elif opt in ['-t', '--buildType=']:
                build_type = arg
            else:
                print("不支持的参数:" + opt)

        root_dir = os.getcwd()

        release = Release()
        release.read_properties()
        release.config_workspace(project_name, branch_name)
        ret = release.checkout(project_name, branch_name)
        if ret != 0:
            print('代码拉取错误，请重试')
            exit()

        ret = release.build(flavor_name, build_type)
        if ret != 0:
            print('编译失败')
            exit()

        os.chdir(root_dir)
        files = release.find_and_copy_apk()

        if files is None:
            print("文件未找到")
            return

        if build_type == "release":
            for file in files:
                # 加固apk
                release.jiagu(file)

                # 生成渠道包
                if channel != "":
                    release.prepare_market_list(flavor_name,channel)

                if release.use_tinker:
                    src_dir = os.path.join(release.branch_dir, release.module_app, "build", "bakApk")
                    for name in os.listdir(src_dir):
                        current_file = os.path.join(src_dir, name)
                        dst_file = os.path.join(release.outputs_dir, name)
                        shutil.copytree(current_file, dst_file)
        else:
            for file in files:
                shutil.copy(file, release.outputs_dir)

        subprocess.check_call(['open', release.outputs_dir])
    except getopt.GetoptError:
        sys.exit()


if __name__ == '__main__':
    main(sys.argv)
