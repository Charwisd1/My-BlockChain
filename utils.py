import os
import datetime
import requests

def clear_directory(path):
    i = 0
    while True:
        try:
            os.remove(f"{path}/{i}.json")
            i += 1
        except: break


# data = requests.get("http://127.0.0.1:5000/get_blocks/0")
# print(data)
