#!/usr/bin/env python3
# coil-cli
# A simple CLI for interacting
# with the Coil Network
# github.com/coilcoin/coil-cli

import sys
import json
import time
import hashlib
import requests
import argparse
import binascii
from urllib.parse import urlparse

# Paths
chain_path = "/home/jesse/.config/coil/blockchain/chain.json"
peers_path = "/home/jesse/.config/coil/peers.txt"

# Read In Peers
lines = open(peers_path, "r").readlines()
nodes = [ urlparse(p.strip()) for p in lines ]

def double_hash(input):
    return hashlib.sha256(hashlib.sha256(input).digest()).hexdigest()

def double_hash_encode(input):
    return double_hash(input.encode("utf8"))

def double_hash_encode_JSON(input):
	return double_hash_encode(str(input))

def writeChainToDisk(chainDict):
    f = open(chain_path, "w")
    f.write(json.dumps(chainDict))
    f.close()

    print("[coil] Successfully downloaded chain from peers")

def readChainFromDisk():
    f = open(chain_path, "r")
    chain = json.loads(f.read())
    return chain

def readWallet(wallet_path):
    f = open(wallet_path, "r")
    wallet = f.read()
    return json.loads(wallet)

def getHistory(address, chain):
    history = {
        "address": address,
        "inputs": [],
        "outputs": []
    }

    for blockIndex, block in enumerate(chain):
        for tx in block["transactions"]:
            if tx["address"] == address:
                for o in tx["outputs"]:
                    history["outputs"].append({
                        "amount": o["amount"],
                        "to": o["address"],
                        "time": block["timestamp"]
                    })

            for o in tx["outputs"]:
                if o["address"] == address:
                    amount = o["amount"]
                    fromAddress = tx["address"]
                    time = block["timestamp"]
                    blockHash = double_hash_encode_JSON(block)

                    history["inputs"].append({
                        "amount": amount,
                        "from": fromAddress,
                        "time": time,
                        "previousBlockHash": blockHash,
                        "blockIndex": blockIndex
                    })
    
    return history

def update(args):
    """
    coil.py update
    Read nodes from nodes.txt, attempt to connect
    with a node and then download
    """
    print("[coil] Attempting to fetch chain from node")
    connected = False
    
    for node in nodes:
        response = requests.get("http://" + node.netloc + "/resolve/chain")        
        if response.status_code == 200 and response.headers["Content-Type"] == "application/json":
            print("[coil] Successfully connected to " + node.netloc)
            connected = True
            if readChainFromDisk() != response.json():
                writeChainToDisk(response.json())
            break

    if not connected:
        print("[coil] Could not connect to any nodes")
        sys.exit()
    
    else:
        print("[coil] Coil is up-to-date")

def history(args):
    """
    coil.py history <address>

    Scan through the blockchain and calculate
    UXTO for transaction submission
    """

    address = args.address
    blockchain = readChainFromDisk()["chain"]
    history = getHistory(address, blockchain)

    print(json.dumps(history, indent=2))

def balance(args):
    """
    coil.py balance <address>

    Return balance for particular address
    TODO: Change this to work from local chain
    """

    address = args.address
    connected = False
    
    for node in nodes:
        response = requests.get("http://" + node.netloc + "/balance/" + address)        
        if response.status_code == 200 and response.headers["Content-Type"] == "application/json":
            print("[coil] Successfully connected to " + node.netloc)
            connected = True
            print(json.dumps(response.json(), indent=2))
            break

    if not connected:
        print("[coil] Could not connect to any nodes")
        sys.exit()

def send(args):
    """
    coild.py send <wallet> <address> <amount>
    """
    address = args.address
    amount = args.amount
    wallet = readWallet(args.wallet_path)
    history = getHistory(wallet["address"], readChainFromDisk()["chain"])
    connected = False

    payload = {
        'private': binascii.hexlify(wallet["privateKey"].encode("utf8")).decode("utf8"),
        'public': binascii.hexlify(wallet["publicKey"].encode("utf8")).decode("utf8"),
        'inputs': history["inputs"],
        'outputs': [
            {
                'amount': amount,
                'to': address,
                'time': time.time()
            }
        ]
    }
    
    print("[coil] Attempting to submit transaction node")
    for node in nodes:
        response = requests.post("http://" + node.netloc + "/tx", json.dumps(payload), headers={"Content-Type": "application/json"})        
        if response.status_code == 200 and response.headers["Content-Type"] == "application/json":
            print("[coil] Successfully connected to " + node.netloc)
            connected = True
            print(json.dumps(response.json(), indent=2))
            break

    if not connected:
        print("[coil] Could not connect to any nodes")
        sys.exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    subparsers.required = True

    parser_update = subparsers.add_parser("update")
    parser_update.set_defaults(which="update")

    parser_send = subparsers.add_parser("send")
    parser_send.set_defaults(which="send")
    parser_send.add_argument("wallet_path")
    parser_send.add_argument("address")
    parser_send.add_argument("amount", type=float)

    parser_send = subparsers.add_parser("history")
    parser_send.set_defaults(which="history")
    parser_send.add_argument("address")

    parser_send = subparsers.add_parser("balance")
    parser_send.set_defaults(which="balance")
    parser_send.add_argument("address")

    args = None
    try:
        args = parser.parse_args()
    except:
        parser.print_help()
    else:
        if args.which == "send":
            send(args)
        elif args.which == "update":
            update(args)
        elif args.which == "history":
            history(args)
        elif args.which == "balance":
            balance(args)
        else:
            parser.print_usage()