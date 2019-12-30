#!/usr/bin/python
# encoding=utf-8
import time

from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ms.v20180408 import ms_client, models


class Jiagu(object):

    def __init__(self):

        print("加固工具")

    def jiagu(self, secretId, secretKey, file_path, file_md5):
        try:
            # 实例化一个认证对象，入参需要传入腾讯云账户secretId，secretKey
            cred = credential.Credential(secretId, secretKey)

            # 实例化要请求产品(以cvm为例)的client对象
            client = ms_client.MsClient(cred, "ap-shanghai")

            # 实例化一个请求对象
            item_id = self.create_shield_instance(client, file_path, file_md5)
            sleep_time = 5
            while True:
                result = self.describe_shield_result(client, item_id)
                if result.TaskStatus == 1:
                    return result.ShieldInfo.AppUrl
                elif result.TaskStatus == 3 or result.TaskStatus == 4:
                    return None
                else:
                    print("加固中," + str(sleep_time) + "s 后再检查")
                    time.sleep(sleep_time)

        except TencentCloudSDKException as err:
            print(err)

    def create_shield_instance(self, client, file_path, file_md5):
        req = models.CreateShieldInstanceRequest()
        req.AppInfo = models.AppInfo()
        req.AppInfo.AppUrl = file_path
        req.AppInfo.AppMd5 = file_md5
        req.ServiceInfo = models.ServiceInfo()
        req.ServiceInfo.ServiceEdition = "basic"
        req.ServiceInfo.SubmitSource = "MC"
        # 通过client对象调用想要访问的接口，需要传入请求对象
        resp = client.CreateShieldInstance(req)
        # 输出json格式的字符串回包
        print(resp.to_json_string())
        return resp.ItemId

    def describe_shield_result(self, client, item_id):
        req = models.DescribeShieldResultRequest()
        req.ItemId = item_id
        resp = client.DescribeShieldResult(req)
        # 输出json格式的字符串回包
        print(resp.to_json_string())

        return resp
