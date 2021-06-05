from flask import Flask, render_template, request, redirect, url_for, jsonify
from blockchain import exchangerates, blockexplorer
import requests
import json
from datetime import datetime
from myblockchain import Blockchain
from uuid import uuid4
import random
import hashlib


app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')

blockchain = Blockchain()


@app.route('/')
@app.route('/home')
@app.route('/index')
def home():
    start_game(20)
    last_block = blockchain.last_block
    pre_blocks = blockchain.chain[:-1]
    gamers_money = {'gamer0':10, 'gamer1':10, 'gamer2':10, 'gamer3':10, 'gamer4':10}
    for i in blockchain.chain:
        for j in i['transactions']:
            gamers_money[j['recipient']] = gamers_money[j['recipient']] + j['amount']
            gamers_money[j['sender']] = gamers_money[j['sender']] - j['amount']
    return render_template("index.html", last_block=last_block, pre_blocks=pre_blocks, datetime=datetime, gamers_money=gamers_money)
	
@app.route('/<string:block_index>/blockinfo', methods=['GET', 'POST'])	
def block_info(block_index):
    for blocks in blockchain.chain:
        if blocks['index'] == int(block_index):
            block = blocks
    return render_template("block_info.html", block=block, datetime=datetime, length = len(block['transactions']))
	



@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


@app.route('/chain/latestblock', methods=['GET'])
def get_last_block():
    response = blockchain.last_block
    return jsonify(response), 200

def start_game(rounds=1, number = 4):
        gamers_account = [10] * number
        active = len(gamers_account)
        zeros = 0
        amount_of_trans = 0
        while rounds!=0:
            winner = random.randint(0, active-1)
            print(winner)
            for i in range(len(gamers_account)):
                if gamers_account[winner] == 0:
                    rounds = rounds + 1
                    break
                if gamers_account[i] != 0:
                    if i == winner:
                        gamers_account[winner] = gamers_account[winner] +  active - 1
                    else:
                        blockchain.new_transaction("gamer" + str(i), "gamer" + str(winner), 1)
                        gamers_account[i] = gamers_account[i] - 1
                        amount_of_trans = amount_of_trans + 1
                        if amount_of_trans == 5:
                            mine()
                            amount_of_trans = 0

            rounds = rounds - 1
            print(gamers_account)
            
            count = 0
            for i in gamers_account:
                if i == 0:
                    count = count + 1
            
            if count > zeros:
                active = active - 1
                zeros = count
        mine()

	
if __name__ == '__main__':
    app.debug = True
    app.run()