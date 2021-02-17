import os
import hashlib
import json
import random
from config import chain_folder, dificulty

class Block(object):
    def __init__(self, dictionary : dict, signature : dict):
        for key, value in dictionary.items():
            setattr(self, key, value)
        setattr(self, "signature", signature["signature"])
        
    def to_dict(self) -> dict:
        res = {
            "index" : self.index,
            "prev_hash" : self.prev_hash,
            "hash" : self.hash,
            "miner" : self.miner,
            "nonce" : self.nonce,
            "transactions" : self.transactions
        }
        if self.index == 0: 
            res.update({"dificulty" : self.dificulty, "coins" : self.coins, "mine_reward" : self.mine_reward, "creator" : self.creator})
        return res

    def to_list(self) -> list:
        return ([self.to_dict(), {"signature" : self.signature}])

    def save(self) -> bool:
        try: os.mkdir(chain_folder)
        except: pass
        with open(f"{chain_folder}/{self.index}.json", "w+") as filepath:
            json.dump([self.to_dict(), {"signature" : self.signature}], filepath)
        return True
    
    def get_hash(self) -> str:
        sha = hashlib.sha256()
        trans = ""
        for i in self.transactions:
            trans += str(i)
        value = str(self.index) + str(self.prev_hash) + str(self.miner) + str(self.nonce) + str(trans) + str(self.signature)
        sha.update(value.encode('UTF-8'))
        new_hash = sha.hexdigest()
        return new_hash

    def update_hash(self) -> str:
        self.hash = self.get_hash()
        return self.hash

    def is_valid(self) -> bool:
        if self.index != 0 and self.hash != "0"*64:
            if self.get_hash() != self.hash: return False
            if self.hash[:dificulty] != "0"*dificulty: return False
        return True

    def __str__(self) -> str:
        return str([self.to_dict(), {"signature":self.signature}])
