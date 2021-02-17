from node import Node
from block import Block
from transaction import Transaction
from flask import Flask, jsonify, request, render_template, make_response
from config import *
import threading
import json
import os
import time
from crypto_controller import generate_keys, key2str
import requests



class active_Node(Node):
    # def __init__(self):
    #     super().__init__()
    def init(self):
        self.app = app
        threading.Thread(target = self.CLI).start()
        threading.Thread(target = self.app.run(), daemon=True, args=(self,)).start()

    def get_chain(self) -> dict:
        data = []
        for i in range(self.last_block_index, -1, -1):
            data.append(self.get_block(i))
        return data
    
    def get_block(self, id) -> Block or None:
        try:
            with open(f"{chain_folder}/{id}.json", "r") as filepath:
                block = json.load(filepath)
            block = Block(block[0], block[1])
            return block
        except: return None


    def CLI(self):
        os.system("cls")
        print("Welcome to CLI application")
        while True:
            command = input("-> ")
            if command == "help": 
                for comm, text in (self.c_help()).items():
                    print(comm, "-", text)
            elif command == "genesis": 
                try: print(self.reset())
                except: print("Register first!")
            elif command == "register": self.c_register()
            elif command == "transfer":
                amount = int(input("Amount: "))
                receiver = input("Receiver: ")
                transaction = self.make_transaction({
                    "sender" : self.public_key,
                    "amount" : amount,
                    "receiver" : receiver
                })
                print(transaction)
            elif command == "miner start":
                self.is_miner = True
                threading.Thread(target = self.mine_procedure, daemon=True).start()
                print("Miner started!")
            elif command == "miner stop":
                self.is_miner = False
                print("Miner stoped!")
            elif command == "balance":
                print(f"Current balance: {self.get_balance()} rafaellas")
            elif command == "state":
                for i in self.node_pool:
                    print(self.world_state[self.last_block].get([i], 0))
            elif command == "pool":
                for i in self.transactions_pool: print(str(i))
            elif command == "nodes":
                for i in self.node_pool: print(i)
            elif command == "dump":
                for i in self.get_chain():
                    print(i)
            elif command == "dump trx":
                for i in self.get_chain():
                    for j in i.transactions:
                        print(j)
            elif command == "invalid block":
                data = list(input("Input invalid list of values: "))
                try: block = Block(data[0], data[1])
                except: print("Fault! Incorrect structure of block!")
                try:
                    result = self.add_new_block(block)
                except: print("Fault! Invalid block data")
                if result: print("Correct block!")
                else: print("Fault! Incorrect block!")
            elif command == "invalid trx":
                data = list(input("Input invalid list of values: "))
                try: trx = Transaction(data[0], data[1])
                except: print("Fault! Incorrect structure of transaction!")
                self.make_transaction(trx)
                print("Invalid trx was added to pool")

    def c_help(self) -> dict:
        return {"genesis": "start new blockchain network",
                "register": "make new keys",
                "transfer": "transfer money to specific account",
                "miner start": "start mining new blocks",
                "miner stop": "stop mining new blocks",
                "balance": "show current address and balance",
                "state": "show all addresses in network and their balances",
                "pool": "show transaction pool",
                "nodes": "show network nodes",
                "dump": "show all blocks and transactions",
                "dump trx": "show all data of specific transaction",
                "dump block": "show all data of specific block",
                "invalid trx": "send invalid transaction to network",
                "invalid block": "send invalid block to network",
                "exit": "kill current node"}

    def c_register(self):
        self.private_key, self.public_key = generate_keys()
        print("Public key: ", key2str(self.public_key), "\nPrivate key: ", key2str(self.private_key))


new = active_Node()
app = Flask(__name__)
app.config["threaded"] = True
app.config["DEBUG"] = True
app.config["host"] = new.web.split(":")[0]
app.config["port"] = new.web.split(":")[1]

@app.route("/")
def start():
    return render_template("chain.html", chain = new.get_chain(), transactions =  new.transactions_pool)

@app.route("/get_blocks/<fromid>", methods=["GET"])
def w_get_blocks(fromid):
    data = []
    fromid = int(fromid)
    for i in range(fromid, new.last_block_index+1):
        data.append(new.get_block(i).to_list())
    return jsonify(data)

@app.route("/get_new_block/<block>", methods=["GET"])
def w_get_new_block(block):
    block = json.loads(block)
    print(block[0], block[1])
    new.add_new_block(Block(block[0], block[1]))
    return jsonify(True)

@app.route("/get_new_transaction/<transaction>", methods=["GET"])
def w_get_new_transaction(transaction):
    transaction = json.loads(transaction)
    print(transaction)
    if not transaction in new.transactions_pool:
        new.make_transaction(Transaction(transaction[0], transaction[1]))


new.init()

