from config import *
from block import Block
from transaction import Transaction
from crypto_controller import *
import utils as u
import os
import json
import socket
import random
import threading
import requests
import time
import pathlib


class Node(object):
    def __init__(self):
        self.public_key = None
        self.private_key = None
        self.is_miner = False
        self.last_block_index = -1
        self.last_block = ''
        self.world_state = {}
        self.node_pool = []
        self.transactions_pool = []
        self.port = 14000
        self.web = str(socket.gethostbyname(socket.gethostname()))+":5000/"
        threading.Thread(target=self.broadcast_listen, daemon=True).start()
        ip = "192.168.0.255" # use "255.255.255.255" for global broadcast
        self.load_config()
        self.build_world_state()
        time.sleep(1)
        self.broadcast_send(ip)
        self.request_missed_blocks()
        # threading.Thread(target=self.broadcast_always_listen, daemon=True).start()
    
    def load_config(self) -> bool:
        self.private_key, self.public_key = load_keys()
        return self.private_key is not None

    def build_world_state(self) -> None:
        i = 0
        try:
            while True:
                with open(f"{chain_folder}/{i}.json", "r") as filepath:
                    data = json.load(filepath)
                block = Block(data[0], data[1])
                if not block.is_valid(): continue
                new_state = self.calculate_new_state(block)
                if not new_state: continue
                if block.index > self.last_block_index:
                    self.last_block = block.hash
                    self.last_block_index = block.index
                self.world_state.update({block.hash : new_state})
                i += 1
        except FileNotFoundError: pass  
    
    def calculate_new_state(self, block : Block) -> dict or None:
        prev_hash = block.prev_hash
        if block.index == 0:
            amount = block.coins
            return {creator : amount}
        elif prev_hash not in self.world_state: return None # unknown prev block

        new_world_state = self.world_state[prev_hash].copy()
        for i in block.transactions:
            sender = i[0]["sender"]
            receiver = i[0]["receiver"]
            amount = i[0]["amount"]
            if amount < 0: return None
            new_world_state[sender] = new_world_state.get(sender, 0) - amount
            new_world_state[receiver] = new_world_state.get(receiver, 0) + amount
            if new_world_state[sender] < 0: return None

        new_world_state[block.miner] = new_world_state.get(block.miner, 0) + reward
        return new_world_state

    def get_balance(self):
        curr_state = self.world_state[self.last_block]
        return curr_state.get(self.public_key)

    def add_new_block(self, block : Block) -> bool:
        if block.index == 0 and self.last_block_index >= 0: return False

        if not block.is_valid(): return False

        new_state = self.calculate_new_state(block)
        if not new_state: return False

        curr_block = block
        while curr_block.index != 0:
            with open(f"{chain_folder}/{curr_block.index-1}.json", "r") as filepath:
                curr_block = json.load(filepath)
                curr_block = Block(curr_block[0], curr_block[1])
                for i in curr_block.transactions:
                    if i in block.transactions: return False
        
        if block.index <= self.last_block_index: return False
        if block.index > self.last_block_index + 1: self.request_missed_blocks() 

        for i in block.transactions:
            for j in self.transactions_pool:
                if j.to_list() == i: 
                    self.transactions_pool.remove(j)

        block.save()
        self.world_state[block.hash] = new_state
        self.last_block_index = block.index
        self.last_block = block.hash
        return True

    def request_missed_blocks(self) -> bool:
        if self.node_pool == []: return False
        while True:
            address = random.random(self.node_pool)
            try:
                data = requests.get(f"http://{address}/get_blocks/{self.last_block_index + 1}")
                data = data.json()
                for block in data:
                    self.add_new_block(Block(block[0], block[1]))
            except: self.node_pool.remove(address)

        for i in data: 
            res = self.add_new_block(Block(i[0], i[1]))
            if not res: return False
            
        print("Missed blocks revived!")
        return True

    def mine_block(self, data : dict = {}) -> Block or None:
        data["nonce"] = random.randint(0, 1e9)
        while True:
            if len(self.transactions_pool) == 0: return None # nothing to mine
            data["miner"] = self.public_key
            data["prev_hash"] = self.last_block
            data["index"] = self.last_block_index+1
            data["transactions"] = [i.to_list() for i in self.transactions_pool[:max_transactions_in_block]]
            block = Block(data, {"signature" : sign_data(data, self.private_key)})
            block.update_hash()
            if block.hash[:dificulty] == "0"*dificulty: 
                return block
            else: data["nonce"] += 1

    def mine_procedure(self) -> None:
        while self.is_miner:
            for i in self.transactions_pool: 
                if not i.check_lifetime(): self.transactions_pool.remove(i)
            new_block = self.mine_block()
            if  not new_block: continue
            self.add_new_block(new_block)
            self.send_block_to_nodes(new_block)

    def send_block_to_nodes(self, block : Block):
        if self.node_pool == []: return False
        block = json.dumps(block.to_list())
        for i in self.node_pool:
            try:
                requests.get(f"http://{i}/get_new_block/{block}")
            except: self.node_pool.remove(i)
        return True

    def make_transaction(self, transaction_data) -> Transaction:
        transaction = Transaction(transaction_data, sign_data(transaction_data, self.private_key))
        self.transactions_pool.append(transaction)
        self.send_transaction_to_nodes(transaction)
        return(transaction)

    def send_transaction_to_nodes(self, transaction):
        if self.node_pool == []: return False
        transaction = json.dumps(transaction.to_list())
        for i in self.node_pool:
            try:
                requests.post(f"http://{i}/get_new_transaction/<{transaction}>", data = transaction)
            except: self.node_pool.remove(i)
        return True

    def reset(self) -> Block:
        u.clear_directory(chain_folder)
        self.last_block_index = -1
        self.last_block = None
        dictionary = {
            "index" : 0,
            "miner" : creator,
            "prev_hash" : "",
            "hash" : "0"*64,
            "mine_reward" : reward,
            "coins" : 1000,
            "dificulty" : dificulty,
            "nonce": 0,
            "creator" : creator,
            "transactions":[]
        }
        genesis = Block(dictionary, {"signature" : sign_data(dictionary, self.private_key)})
        genesis.save()
        self.build_world_state()
        return genesis


        

    # connection
    def broadcast_send(self, ip):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        udp_socket.sendto(b'CONNECTION_REQUEST'+bytes(self.web.encode()), (ip, self.port))
        udp_socket.close()

    def broadcast_listen(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(("", self.port))
        while True:
            data, ip = udp_socket.recvfrom(45)
            if data[:18] == b"CONNECTION_REQUEST":
                client = data[18:]
                if client.decode() != self.web:
                    if not client in self.node_pool: 
                        self.node_pool.append(client)
                    self.broadcast_send(ip[0])

    # def broadcast_always_listen(self):
    #     tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #     tcp_server.bind(('', self.port))
    #     tcp_server.listen()
    #     while True:
    #         conn, ip = tcp_server.accept()