from config import transaction_folder, transaction_lifetime
import json
import os
import time
import hashlib


class Transaction(object):
    def __init__(self, dictionary, signature):
        for key, value in dictionary.items():
            setattr(self, key, value)
        setattr(self, "signature", signature)
        setattr(self, "creation_time", time.time())
        sha = hashlib.sha256()
        value = self.sender + self.receiver + str(self.amount) + str(self.creation_time)
        sha.update(value.encode())
        self.comment = sha.hexdigest()
    
    def to_dict(self):
        return {
            "sender" : self.sender,
            "receiver" : self.receiver,
            "amount" : self.amount,
            "comment" : self.comment
        }

    def to_list(self):
        return [self.to_dict(), {"signature" : self.signature}]

    # def save(self):
    #     try: os.mkdir(transaction_folder)
    #     except: pass
    #         files = os.listdir(path=transaction_folder)
    #         index = len(files)
    #         with open(transaction_folder + str(index)+".json", "w+") as filepath:
    #             json.dump(self.to_list(), filepath)
            
    def check_lifetime(self):
        if self.creation_time + transaction_lifetime < time.time(): return False
        return True

    def __str__(self):
        return str(self.to_list())