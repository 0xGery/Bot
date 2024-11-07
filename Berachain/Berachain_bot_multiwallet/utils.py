import random
import time
from web3 import Web3
from eth_account import Account
from config import w3, PRIVATE_KEYS

class WalletManager:
    def __init__(self):
        self.accounts = []
        self.addresses = []
        
        # Create account objects for each private key
        for pk in PRIVATE_KEYS:
            account = Account.from_key(pk)
            self.accounts.append(account)
            self.addresses.append(account.address)
            
    def get_account(self, index):
        return self.accounts[index]
        
    def get_address(self, index):
        return self.addresses[index]
        
    def total_wallets(self):
        return len(self.accounts)

# Initialize wallet manager
wallet_manager = WalletManager()

def random_delay(min_secs=5, max_secs=10):
    delay = random.randint(min_secs, max_secs)
    print(f"Waiting {delay} seconds...")
    time.sleep(delay)

def check_connection():
    if w3.is_connected():
        print(f"Connected to Berachain")
        print(f"Current block number: {w3.eth.block_number}")
        print(f"Total wallets loaded: {wallet_manager.total_wallets()}")
        
        # Print balance for each wallet
        for i, address in enumerate(wallet_manager.addresses):
            balance = w3.eth.get_balance(address)
            print(f"Wallet {i+1} ({address}): {w3.from_wei(balance, 'ether')} BERA")
        return True
    return False