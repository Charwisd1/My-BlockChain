from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from base64 import b64encode, b64decode
import json
import os
from config import config_folder


def generate_keys() -> tuple:
    private_key = ECC.generate(curve='P-256')
    public_key = private_key.public_key()

    try: os.mkdir("config")
    except: pass
    with open(f"{config_folder}/private_key.json", "w+") as filepath:
        json.dump(key2str(private_key), filepath)
    with open(f"{config_folder}/public_key.json", "w+") as filepath:
        json.dump(key2str(public_key), filepath)

    return private_key, public_key

def load_keys() -> tuple:
    try:
        with open(f"{config_folder}/private_key.json", "r") as filepath:
            private_key = json.load(filepath)
        with open(f"{config_folder}/public_key.json", "r") as filepath:
            public_key = json.load(filepath)
        return private_key, public_key
    except:
        return None, None


def key2str(key):
    return b64encode(key.export_key(format="DER")).decode()

def str2key(s: str):
    return ECC.import_key(b64decode(s))

def sign_data(data, private_key):
    data = str(data).encode()
    signer = DSS.new(str2key(private_key), 'fips-186-3')
    data = SHA256.new(data)
    signature = signer.sign(data)
    return b64encode(signature).decode()