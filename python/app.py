import shelve
from uuid import uuid4
from socket import gethostname
import json
import pyqrcode
from .secret import generate_secret_key

class App:
    def __init__(self, identity_file, name):  
        self.config = shelve.open(identity_file)
        self.__init_config_default("deviceName",  lambda: name)
        self.__init_config_default("deviceUUID",  lambda: str(uuid4()))
        self.__init_config_default("accountUUID",  lambda: None)
    
    def __init_config_default(self, key, default_value_lambda):
        try:
            self.config[key]
        except KeyError:
            self.config[key] = default_value_lambda()

    def paired(self):
        return self.config["accountUUID"] != None

    def gen_pair_info(self):
        pairing = {}
        pairing["secret"] = generate_secret_key()
        pairing["uuid"] = self.config["deviceUUID"]
        self.config["deviceSecret"] = pairing["secret"]
        url = pyqrcode.create(json.dumps(pairing))
        print(url.terminal(quiet_zone=1))

if __name__ == "__main__":
    app = App("secureput_identity.shelve")
    print(app.config["deviceName"])
    print(app.config["deviceUUID"])
    print(app.gen_pair_info())