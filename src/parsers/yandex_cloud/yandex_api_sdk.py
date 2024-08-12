from yandexcloud import SDK
import requests
from yandex.cloud.organizationmanager.v1 import *
from yandex.cloud.resourcemanager.v1 import *
from yandex.cloud.compute.v1 import *
from yandex.cloud.loadbalancer.v1 import *
from yandex.cloud.k8s.v1 import *
from yandex.cloud.storage.v1 import *

#etc
from yandex.cloud.mdb.redis.v1 import *


class YandexAPISDK:
    def __init__(self, oauth: str, iam_token: str = None):
        self.folder_id = None
        if iam_token is not None:
            self.sdk = SDK(iam_token=iam_token)
        else:
            # Getting iam
            iam_resp = requests.post('https://iam.api.cloud.yandex.net/iam/v1/tokens'
                                          ,json={'yandexPassportOauthToken': self.oauth})

            if iam_resp.ok:
                iam = iam_resp.json()['iamToken']
                self.sdk = SDK(iam_token=iam)
            else:
                raise Exception('Invalid oauth token')

    def set_working_folder(self, org_name: str, cloud_name: str, folder_name: str) -> None:
        pass
