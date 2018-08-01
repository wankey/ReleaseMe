# encoding=utf-8
import getopt
import os
import shutil
import subprocess
import sys
from Properties import Properties


class ReleaseMe(object):

    def __init__(self, branch_name, channel_name):
        self.branch_name = branch_name
        self.channel_name = channel_name

    def read_properties(self):
        prop = Properties(os.path.join('.', 'config.properties')).get_properties()

        gitProtocol = prop["GIT_PROTOCOL"]
        self.server_path = prop["GIT_PATH"]
        self.gitAccount = prop["GIT_USERNAME"]
        self.gitPassword = prop["GIT_PASSWORD"]

        if gitProtocol != 'git':
            self.server_path = self.server_path.replace("//","//"+self.gitAccount+":"+self.gitPassword+"@")

        project_name = (self.server_path.split('/')[1]).split('.')[0]
        self.workspace = os.path.join(os.path.abspath('.'), 'workspace', project_name, self.branch_name)
        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace)

        self.market_file = os.path.abspath(prop["MARKET_FILE"])
        self.sign_file = os.path.abspath(prop["STORE_FILE"])
        self.key_alias = prop["KEY_ALIAS"]
        self.store_password = prop["STORE_PASSWORD"]
        self.key_password = prop["KEY_PASSWORD"]
        self.useResguard = prop["USE_RES_GUARD"]
        self.channelNameFor360 = prop["CHANNEL_NAME_FOR_360"]
        self.accout360 = prop["360_ACCOUNT"]
        self.password360 = prop["360_PASSWORD"]

    def checkout(self):
        return subprocess.check_call(['git', 'clone', '-b', self.branch_name, self.server_path, self.workspace])

    def build(self):
        os.chdir(self.workspace)
        if os.path.exists(os.path.join(self.workspace, 'gradlew')):
            cmd = './gradlew'
        else:
            cmd = 'gradle'
        if self.useResguard=="true":
            arg="resguardRelease"
        else:
            arg="assembleRelease"
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

    def jiagu(self):
        if self.channel_name == "360" or self.channel_name == "all".lower() or self.channel_name == "":
            dir_360_jiagu = os.path.join(os.getcwd(), '360jiagu')
            java_360_jiagu = os.path.join(dir_360_jiagu, 'java/bin/java')
            subprocess.check_call(['chmod', 'a+x', java_360_jiagu])
            ret = subprocess.check_call([java_360_jiagu, '-jar', dir_360_jiagu + '/jiagu.jar', '-login', self.accout360, self.password360])
            if ret != 0:
                print("360开发者中心登录失败")
                exit()
            ret = subprocess.check_call([java_360_jiagu, '-jar', dir_360_jiagu + '/jiagu.jar', '-config', 'null'])
            if ret != 0:
                print("360加固宝设置失败")
                exit()

            out_puts = os.path.join(self.workspace, 'outputs')
            for name in os.listdir(out_puts):
                ret = self.jiagu_apk(java_360_jiagu, dir_360_jiagu, out_puts, name)
        else:
            ret = 0
        return ret

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

    def make_channels(self):
        if self.channel_name == "":
            out_puts = os.path.join(self.workspace, 'outputs')
            file = open(self.market_file,'r')
            lines = file.readlines()
            for line in lines:
                if self.channelNameFor360 !="" and line == self.channelNameFor360 :
                    ret = self.jiagu()
                    if ret != 0:
                        print("加固失败")
                        pass

                for name in os.listdir(out_puts):
                    src_file = os.path.join(out_puts, name)
                    if name.endswith("-release-360.apk"):
                        ret = subprocess.check_call(
                            ["java", "-jar", "walle-cli-all.jar", "batch", '-c', line, src_file])
                        if ret == 0:
                            os.remove(src_file)
                    elif name.endswith('-release.apk'):
                        ret = subprocess.check_call(["java", "-jar", "walle-cli-all.jar", "batch", '-c', line, src_file])
        else:
            for name in os.listdir(out_puts):
                src_file = os.path.join(out_puts, name)
                if name.endswith('-release.apk'):
                    ret = subprocess.check_call(["java", "-jar", "walle-cli-all.jar", "batch", '-c', self.channel_name, src_file])

def main(argv):
    try:
        opts, args = getopt.getopt(argv[1:], 'b:c:', ['branch=', 'channel='])
        branch_name = ""
        channel = ""
        for opt, arg in opts:
            if opt in ['-b', '--branch']:
                branch_name = arg
            elif opt in ['-c', '--channel']:
                channel = arg
            else:
                print("参数错误")
        root_dir = os.getcwd()
        release = ReleaseMe(branch_name, channel)
        release.read_properties()
        ret = release.checkout()
        if ret != 0:
            print('代码拉取错误，请重试')
            exit()

        ret = release.build()
        if ret != 0:
            print('编译失败')
            exit()

        release.copy_product_to_outputs(os.path.join(release.workspace, "app/build/outputs/apk/"))
        os.chdir(root_dir)

        release.make_channels()
        subprocess.check_call(['open', os.path.join(release.workspace, 'outputs')])
    except getopt.GetoptError:
        sys.exit()


if __name__ == '__main__':
    main(sys.argv)
