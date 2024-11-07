import random
import time
from web3 import Web3
from eth_account import Account
from config import w3, PRIVATE_KEY

account = Account.from_key(PRIVATE_KEY)
address = account.address

def random_delay(min_secs=5, max_secs=10):
    delay = random.randint(min_secs, max_secs)
    print(f"Waiting {delay} seconds...")
    time.sleep(delay)

def check_connection():
    if w3.is_connected():
        print(f"Connected to Berachain")
        print(f"Current block number: {w3.eth.block_number}")
        print(f"Your wallet address: {address}")
        balance = w3.eth.get_balance(address)
        print(f"Wallet balance: {w3.from_wei(balance, 'ether')} BERA")
        return True
    return False