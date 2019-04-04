#!/usr/bin/python
# encoding=utf-8
import os
import subprocess


class Channel(object):
    outputs_dir = None
    toolDir = None
    market_tool_type = None

    def __init__(self):
        print("渠道包工具")

    def prepare_market_list(self, channel_name):
        for file in os.listdir(self.outputs_dir):
            if file.endswith("-360.apk"):
                product = file.split("-")[1]
                if channel_name == "all":
                    market_file_path = os.path.join('.', 'config')
                    market_file_path = os.path.join(market_file_path, '{0}_markets.txt'.format(product))
                    if os.path.exists(market_file_path):
                        market_file = open(market_file_path, 'r')
                        lines = market_file.readlines()
                        for line in lines:
                            self.make_channel(self.outputs_dir, file, line, product)
                    else:
                        print("没有找到对应的渠道配置文件")
                else:
                    self.make_channel(self.outputs_dir, file, channel_name, product)

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
            tmp_file = os.path.join(dst_file, "tmp")
            subprocess.check_call(
                ["java", "-jar", self.toolDir + "/packer-ng-2.0.1.jar", "generate",
                 "--channels=" + channel_name
                    , "--outputs=" + tmp_file
                    , src_file
                 ])
        else:
            print("未支持的渠道包工具")
