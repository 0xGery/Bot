from web3 import Web3
import os
from dotenv import load_dotenv

# Load PK on .env
load_dotenv()

# Connect to the Apechain network using RPCs
w3 = Web3(Web3.HTTPProvider('https://rpc.apechain.com/http'))  

# APE Chain ID
CHAIN_ID = 33139

# Contract address for WAPE
WAPE_CONTRACT_ADDRESS = '0x48b62137EdfA95a428D35C09E44256a739F6B557'

# ABI for WAPE contract 
WAPE_ABI = [
    {
        "constant": False,
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "wad", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "type": "function"
    }
]

# Load Account PK
private_key = os.getenv('PRIVATE_KEY')
account = w3.eth.account.from_key(private_key)

# Create contract instance
wape_contract = w3.eth.contract(address=WAPE_CONTRACT_ADDRESS, abi=WAPE_ABI)

def wrap_ape(amount_in_ape):
    # Convert APE to Wei 
    amount_in_wei = w3.to_wei(amount_in_ape, 'ether')

    transaction = wape_contract.functions.deposit().build_transaction({
        'chainId': CHAIN_ID,
        'from': account.address,
        'value': amount_in_wei,
        'gas': 100000, 
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(account.address),
    })

    # Sign and send the transaction
    signed_txn = account.sign_transaction(transaction)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    
    # Wait for the transaction to be mined
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    tx_hash_hex = f"0x{tx_receipt.transactionHash.hex()}"
    tx_url = f"https://apescan.io/tx/{tx_hash_hex}"
    print(f"Wrapped {amount_in_ape} APE to WAPE. Transaction hash: {tx_url}")

def unwrap_wape(amount_in_wape):
    # Convert WAPE to Wei
    amount_in_wei = w3.to_wei(amount_in_wape, 'ether')

    # Prepare the transaction
    transaction = wape_contract.functions.withdraw(amount_in_wei).build_transaction({
        'chainId': CHAIN_ID,
        'from': account.address,
        'gas': 100000, 
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(account.address),
    })

    # Sign and send the transaction
    signed_txn = account.sign_transaction(transaction)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    
    # Wait for the transaction to be mined
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    tx_hash_hex = f"0x{tx_receipt.transactionHash.hex()}"
    tx_url = f"https://apescan.io/tx/{tx_hash_hex}"
    print(f"Unwrapped {amount_in_wape} WAPE to APE. Transaction hash: {tx_url}")

def run_bundle(amount, bundle_number):
    print(f"\nExecuting bundle {bundle_number}:")
    wrap_ape(amount)
    unwrap_wape(amount)

# Usage
# 1 bundles consist of 2 tx which is 1 tx wrap and 1 unwrap
if __name__ == "__main__":
    num_bundles = int(input("Enter the number of bundles to run: "))
    amount_per_bundle = float(input("Enter the amount of APE per bundle: "))
    
    for i in range(num_bundles):
        run_bundle(amount_per_bundle, i+1)
