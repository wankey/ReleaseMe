# encoding=utf-8
import getopt
import os
import shutil
import subprocess
import sys
from Properties import Properties


class ReleaseMe(object):
    workspace = ""
    sign_file = ""
    key_alias = ""
    store_password = ""
    key_password = ""

    def __init__(self, server_path, branch_name, channel_name):
        self.server_path = server_path
        self.branch_name = branch_name
        self.channel_name = channel_name
        project_name = (self.server_path.split('/')[1]).split('.')[0]
        self.workspace = os.path.join(os.path.abspath('.'), 'workspace', project_name, branch_name)
        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace)

    def checkout(self):
        return subprocess.check_call(['git', 'clone', '-b', self.branch_name, self.server_path, self.workspace])

    def read_properties(self):
        self.prop = Properties(os.path.join('.', 'config.properties')).get_properties()
        self.accout = prop["360_ACCOUNT"]
        self.password = prop["360_PASSWORD"]
        self.market_file = os.path.abspath(prop["MARKET_FILE"])
        self.sign_file = os.path.abspath(prop["STORE_FILE"])
        self.key_alias = prop["KEY_ALIAS"]
        self.store_password = prop["STORE_PASSWORD"]
        self.key_password = prop["KEY_PASSWORD"]
        self.useResguard = prop["USE_RES_GUARD"]

    def build(self):
        self.read_properties()
        os.chdir(self.workspace)
        if os.path.exists(os.path.join(self.workspace, 'gradlew')):
            cmd = './gradlew'
        else:
            cmd = 'gradle'

        return subprocess.check_call([cmd, "assembleRelease"])

    def copy_product_to_outputs(self, folder):
        for name in os.listdir(folder):
            if os.path.isdir(os.path.join(folder, name)):
                self.copy_product_to_outputs(os.path.join(folder, name))
            elif name.endswith("-release.apk"):
                dst = os.path.join(self.workspace, "outputs")
                if not os.path.exists(dst):
                    os.makedirs(dst)
                shutil.copy(os.path.join(folder, name), os.path.join(dst, name))

    def build_app(self):
        ret = self.checkout()
        if ret != 0:
            print('代码提取错误，请重试')
            exit()

        ret = self.build()
        if ret != 0:
            print('编译失败')
            exit()

        self.copy_product_to_outputs(os.path.join(release.workspace, "app/build/outputs/apk/"))

    def make_channels(self):
        out_puts = os.path.join(self.workspace, 'outputs')
        if self.channel_name == "360" or self.channel_name == "all".lower():
            jiagu_ret = self.jiagu()
            if jiagu_ret != 0:
                print("加固失败")
        for name in os.listdir(out_puts):
            src_file = os.path.join(out_puts, name)
            if name.endswith("-release-360.apk"):
                ret = subprocess.check_call(
                    ["java", "-jar", "walle-cli-all.jar", "batch", '-c', 'T360', src_file])
                if ret == 0:
                    os.remove(src_file)
            elif name.endswith('-release.apk'):
                if self.channel_name == "all".lower():
                    ret = subprocess.check_call(
                        ["java", "-jar", "walle-cli-all.jar", "batch", '-f',
                        self.market_file,
                         src_file])
                else:
                    ret = subprocess.check_call(
                        ["java", "-jar", "walle-cli-all.jar", "batch", '-c', self.channel_name,
                         src_file])

    def jiagu(self):
        dir_360_jiagu = os.path.join(os.getcwd(), '360jiagu')
        java_360_jiagu = os.path.join(dir_360_jiagu, 'java/bin/java')
        subprocess.check_call(['chmod', 'a+x', java_360_jiagu])
        ret = subprocess.check_call([java_360_jiagu, '-jar', dir_360_jiagu + '/jiagu.jar', '-login', self.accout, self.password])
        if ret != 0:
            print("360开发者中心登录失败")
            exit()
        ret = subprocess.check_call([java_360_jiagu, '-jar', dir_360_jiagu + '/jiagu.jar', '-config', 'null'])
        if ret != 0:
            print("360加固宝设置失败")
            exit()

        jiagu_ret = 0
        out_puts = os.path.join(self.workspace, 'outputs')
        for name in os.listdir(out_puts):
            ret = self.jiagu_apk(java_360_jiagu, dir_360_jiagu, out_puts, name)
            if ret != 0:
                jiagu_ret = ret

        return jiagu_ret

    def jiagu_apk(self, java, jiagu_dir, out_puts, file):
        base_file = os.path.join(out_puts, file)
        dst_file = base_file.replace('.apk', '-360.apk')

        ret = subprocess.check_call(
            [java, '-jar', jiagu_dir + '/jiagu.jar', '-jiagu', os.path.join(out_puts, file), out_puts])
        if ret == 0:
            for name in os.listdir(out_puts):
                if name.endswith("_jiagu.apk"):
                    src_file = os.path.join(out_puts, name)
                    ret = subprocess.check_call(
                        ["java", '-jar', 'apksigner.jar', 'sign', "--ks", self.sign_file, '--ks-key-alias',
                         self.key_alias, '--ks-pass', 'pass:' + self.key_password, '--key-pass',
                         "pass:" + self.key_password, '--out',
                         dst_file, src_file])
                    if ret == 0:
                        os.remove(src_file)
        return ret


def main(argv):
    try:
        opts, args = getopt.getopt(argv[1:], 's:b:c:', ['server_path=', 'branch_name=', 'channel='])
        print(opts)
        server_path = ""
        branch_name = ""
        channel = ""
        for opt, arg in opts:
            if opt in ['-s', '--server_path']:
                print(arg)
                server_path = arg
            elif opt in ['-b', '--branch_name']:
                print(arg)
                branch_name = arg
            elif opt in ['-c', '--channel']:
                print(arg)
                channel = arg

        if server_path != "" and branch_name != "" and channel != "":
            root_dir = os.getcwd()
            release = ReleaseMe(server_path, branch_name, channel)
            release.build_app()
            os.chdir(root_dir)
            release.make_channels()
            subprocess.check_call(['open', os.path.join(release.workspace, 'outputs')])
        else:
            print("参数错误")
    except getopt.GetoptError:
        sys.exit()


if __name__ == '__main__':
    main(sys.argv)
