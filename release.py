# encoding=utf-8
import getopt
import os
import shutil
import subprocess
import sys

from Properties import Properties


class ReleaseMe(object):
    git_protocol = None
    server_path = None
    workspace = None
    sign_file = None
    key_alias = None
    store_password = None
    key_password = None
    use_resguard = None
    account360 = None
    password360 = None
    use_tinker = None
    module_app = None
    market_tool_type = None
    toolDir = os.path.join(os.getcwd(), "tool")

    def read_properties(self):
        prop = Properties(os.path.join(os.getcwd(), "config", 'config.properties')).get_properties()

        self.git_protocol = prop["GIT_PROTOCOL"]
        self.server_path = prop["GIT_PATH"]
        self.sign_file = os.path.abspath(prop["STORE_FILE"])
        self.key_alias = prop["KEY_ALIAS"]
        self.store_password = prop["STORE_PASSWORD"]
        self.key_password = prop["KEY_PASSWORD"]
        self.use_resguard = prop["USE_RES_GUARD"]
        self.account360 = prop["360_ACCOUNT"]
        self.password360 = prop["360_PASSWORD"]
        self.use_tinker = prop["USE_TINKER"]
        self.module_app = prop["MODULE_APP"]
        self.market_tool_type = prop["MARKET_TOOL_TYPE"]

    def checkout(self,project_name, branch_name):
        project_path = os.path.join(self.server_path, project_name + ".git")
        self.workspace = os.path.join(os.path.abspath('.'), 'workspace', project_name, branch_name)

        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace)
        ret = subprocess.check_call(['git', 'clone', '-b', branch_name, project_path, self.workspace])
        if ret != 0:
            print('代码拉取错误，请重试')
            exit()
        else:
            return ret

    def build(self, product_flavor):
        os.chdir(self.workspace)
        gradlew_file = os.path.join(self.workspace, 'gradlew')
        if os.path.exists(gradlew_file):
            cmd = 'sh gradlew'
        else:
            cmd = 'gradle'
        if self.use_resguard == "true":
            if product_flavor != "":
                arg = "assemble" + product_flavor.capitalize() + "Release"
            else:
                arg = "resguard" + product_flavor.capitalize() + "Release"
        else:
            if product_flavor != "":
                arg = "assemble" + product_flavor.capitalize() + "Release"
            else:
                arg = "assembleRelease"
        return subprocess.check_call([cmd, arg])

    def copy_product_to_outputs(self, folder):
        for name in os.listdir(folder):
            if os.path.isdir(os.path.join(folder, name)):
                self.copy_product_to_outputs(os.path.join(folder, name))
            elif name.endswith("-release.apk"):
                dst = os.path.join(self.workspace, "outputs")
                if not os.path.exists(dst):
                    os.makedirs(dst)
                shutil.copy(os.path.join(folder, name), os.path.join(dst, name))

    def backup_apk_for_tinker(self, folder):
        dst = os.path.join(self.workspace, "outputs")
        for name in os.listdir(folder):
            shutil.copytree(os.path.join(folder, name), os.path.join(dst, name))

    def jiagu(self):
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

        out_puts = os.path.join(self.workspace, 'outputs')
        for name in os.listdir(out_puts):
            if name.endswith("-release.apk"):
                self.jiagu_apk(java, dir_360_jiagu, out_puts, name)

    def jiagu_apk(self, java, jiagu_dir, out_puts, file):
        base_file = os.path.join(out_puts, file)
        dst_file = base_file.replace('.apk', '-360.apk')

        ret = subprocess.check_call(
            [java, '-jar', jiagu_dir + '/jiagu.jar', '-jiagu', base_file, out_puts])
        if ret == 0:

            for name in os.listdir(out_puts):
                if name.endswith("_jiagu.apk"):
                    src_file = os.path.join(out_puts, name)
                    ret = subprocess.check_call(
                        ["java", '-jar', self.toolDir + '/apksigner.jar', 'sign', "--ks", self.sign_file,
                         '--ks-key-alias',
                         self.key_alias, '--ks-pass', 'pass:' + self.key_password, '--key-pass',
                         "pass:" + self.key_password, '--out',
                         dst_file, src_file])
                    if ret == 0:
                        os.remove(src_file)
        return ret

    def call_packer_tool(self, file_name, src_file, channel_name, extra_info, dst_file):
        print("===========================================================")
        print("当前正在输出的渠道是：" + channel_name)
        channel_name = channel_name.strip().replace('\n', '')
        if self.market_tool_type == "1":
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
                        , os.path.join(dst_file, file_name.replace("-360.apk", "_" + channel_name + ".apk"))])
        elif self.market_tool_type == "2":
            tmpFile = os.path.join(dst_file, "tmp")
            subprocess.check_call(
                ["java", "-jar", self.toolDir + "/packer-ng-2.0.1.jar", "generate",
                 "--channels=" + channel_name
                    , "--output=" + tmpFile
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

    def prepare_market_list(self, channel_name):
        out_puts = os.path.join(self.workspace, 'outputs')
        for file in os.listdir(out_puts):
            if file.endswith("-360.apk"):
                product = file.split("-")[1]
                if channel_name == "all":
                    market_file_path = os.path.join('.', 'config')
                    market_file_path = os.path.join(market_file_path, '{0}_markets.txt'.format(product))
                    if os.path.exists(market_file_path):
                        market_file = open(market_file_path, 'r')
                        lines = market_file.readlines()
                        for line in lines:
                            self.make_channel(out_puts, file, line, product)
                    else:
                        print("没有找到对应的渠道配置文件")
                else:
                    self.make_channel(out_puts, file, channel_name, product)


def main(argv):
    try:
        project_name = ""
        branch_name = ""
        channel = ""
        product_flavor = ""

        opts, args = getopt.getopt(argv[1:], 'p:b:c:f:', ['project=', 'branch=', 'channel=', 'flavor='])

        for opt, arg in opts:
            if opt in ['-p', '--project']:
                project_name = arg
            elif opt in ['-b', '--branch']:
                branch_name = arg
            elif opt in ['-c', '--channel']:
                channel = arg
            elif opt in ['-f', '--flavor']:
                product_flavor = arg
            else:
                print("参数错误")

        root_dir = os.getcwd()
        release = ReleaseMe()
        release.read_properties()
        ret = release.checkout(project_name, branch_name)
        if ret != 0:
            print('代码拉取错误，请重试')
            exit()

        ret = release.build(product_flavor)
        if ret != 0:
            print('编译失败')
            exit()

        tmp_build_folder = os.path.join(release.workspace, release.module_app, "build")

        if release.use_tinker == "true":
            release.backup_apk_for_tinker(os.path.join(tmp_build_folder, "bakApk/"))

        release.copy_product_to_outputs(os.path.join(tmp_build_folder, "outputs/apk/"))
        os.chdir(root_dir)
        release.jiagu()

        if channel != "":
            release.prepare_market_list(channel)

        outputs = os.path.join(release.workspace, 'outputs')
        subprocess.check_call(['open', outputs])
    except getopt.GetoptError:
        sys.exit()


if __name__ == '__main__':
    main(sys.argv)
