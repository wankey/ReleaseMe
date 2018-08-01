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
        self.toolDir = os.path.join(os.getcwd(), "tool")

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

        self.marketTool=prop["MARKET_TOOL_TYPE"]
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
        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace)
        ret = subprocess.check_call(['git', 'clone', '-b', self.branch_name, self.server_path, self.workspace])
        if ret != 0:
            print('代码拉取错误，请重试')
            exit()

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
        ret = subprocess.check_call([cmd, "clean", arg])
        if ret != 0:
            print("编译失败")
            exit()
        else:
            self.copy_product_to_outputs(os.path.join(self.workspace, "app/build/outputs/apk/"))

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
        dir_360_jiagu = os.path.join(self.toolDir, '360jiagu')
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

        out_puts = os.path.join(self.workspace, "outputs")
        for name in os.listdir(out_puts):
            if name.endswith("-release.apk"):
                ret = self.jiagu_apk(java_360_jiagu, dir_360_jiagu, out_puts, name)
        return ret

    def jiagu_apk(self, java, jiagu_dir, out_puts, file):
        base_file = os.path.join(out_puts, file)
        dst_file = base_file.replace('.apk', '-360_signed.apk')

        if os.path.exists(dst_file):
            return 0

        ret = subprocess.check_call(
            [java, '-jar', jiagu_dir + '/jiagu.jar', '-jiagu', os.path.join(out_puts, file), out_puts])
        if ret == 0:
            for name in os.listdir(out_puts):
                if name.endswith("_jiagu.apk"):
                    src_file = os.path.join(out_puts, name)
                    ret = subprocess.check_call(
                        ["java", '-jar', self.toolDir+'/apksigner.jar', 'sign', "--ks", self.sign_file, '--ks-key-alias',
                         self.key_alias, '--ks-pass', 'pass:' + self.key_password, '--key-pass',
                         "pass:" + self.key_password, '--out',
                         dst_file, src_file])
                    if ret == 0:
                        os.remove(src_file)
        return ret

    def make_channels(self,out_puts):
        destDir=os.path.join(out_puts,"markets")

        if self.channel_name == "":
            file = open(self.market_file,'r')
            lines = file.readlines()
            for line in lines:
                line = line.strip()
                if not len(line) or line.startswith('#'):#判断是否是空行或注释行
                    continue

                if self.channelNameFor360 !="" and line == self.channelNameFor360 :
                    continue
                else:
                    self.channel_name = self.channel_name + line + ","

        print(self.channel_name)

        for name in os.listdir(out_puts):
            src_file = os.path.join(out_puts, name)
            if name.endswith("release.apk"):
                if self.marketTool == "1":
                    ret = subprocess.check_call(["java", "-jar", self.toolDir + "/walle-cli-all.jar", "batch", '-c', self.channel_name, src_file, destDir])
                elif self.marketTool == "2":
                    ret = subprocess.check_call(["java", "-jar", self.toolDir + "/packer-ng-2.0.1.jar", "generate", "--channels="+ self.channel_name, "--output=" + destDir, src_file])
            elif name.endswith("-360_signed.apk"):
                if self.marketTool == "1":
                    ret = subprocess.check_call(["java", "-jar", self.toolDir + "/walle-cli-all.jar", "batch", '-c', self.channelNameFor360, src_file, destDir])
                elif self.marketTool == "2":
                    tmpFile=os.path.join(destDir,"tmp")
                    ret = subprocess.check_call(["java", "-jar", self.toolDir + "/packer-ng-2.0.1.jar", "generate", "--channels="+ self.channelNameFor360, "--output=" + tmpFile, src_file])
                    for name in os.listdir(tmpFile):
                        shutil.copy(os.path.join(tmpFile, name), os.path.join(destDir, name.replace("360_signed-"+self.channelNameFor360+".apk",self.channelNameFor360+".apk")))
                    if os.path.exists(tmpFile):
                        shutil.rmtree(tmpFile)

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

        if branch_name == "":
            branch_name = "master"

        root_dir = os.getcwd()
        release = ReleaseMe(branch_name, channel)
        release.read_properties()
        ret = release.checkout()
        ret = release.build()
        if release.channelNameFor360 !="":
            ret = release.jiagu()
            if ret != 0:
                print("加固失败")

        os.chdir(root_dir)
        out_puts = os.path.join(release.workspace, "outputs")
        release.make_channels(out_puts)
        subprocess.check_call(['open', out_puts])
    except getopt.GetoptError:
        sys.exit()


if __name__ == '__main__':
    main(sys.argv)
