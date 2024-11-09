import sys
import os
import time
import json
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import w3, rotate_rpc
from utils import wallet_manager, random_delay
from eth_abi import encode

# Contract addresses
BGT_CONTRACT = "0xbDa130737BDd9618301681329bF2e46A016ff9Ad"
VALIDATOR_ADDRESS = "0x40495A781095932e2FC8dccA69F5e358711Fdd41"

# ABI for BGT contract
BGT_ABI = [{
    "inputs": [
        {"type": "address", "name": "validator"},
        {"type": "uint128", "name": "amount"}
    ],
    "name": "queueBoost",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
}, {
    "inputs": [
        {"type": "address", "name": "validator"}
    ],
    "name": "activateBoost",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
}, {
    "constant": True,
    "inputs": [{"name": "account", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"name": "", "type": "uint256"}],
    "type": "function"
}]

class BGTTracker:
    def __init__(self):
        self.wallet_data = {}
        self.data_file = 'data/bgt_tracker.json'
        self._load_data()
        
    def _load_data(self):
        """Load data from JSON file"""
        try:
            os.makedirs('data', exist_ok=True)
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.wallet_data = json.load(f)
        except Exception as e:
            print(f"Error loading BGT tracker data: {e}")
            
    def _save_data(self):
        """Save data to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.wallet_data, f, indent=4)
        except Exception as e:
            print(f"Error saving BGT tracker data: {e}")
    
    def _init_wallet(self, wallet_index):
        """Initialize data structure for a new wallet"""
        if str(wallet_index) not in self.wallet_data:
            self.wallet_data[str(wallet_index)] = {
                'total_claimed': 0,
                'total_delegated': 0,
                'total_activated': 0,
                'first_delegation': True,
                'queued_boosts': {},
                'pending_amount': 0,
                'last_delegation_time': None,
                'last_activation_time': None,
                'last_claim_time': None,
                'claim_amounts': [],
                'last_known_balance': 0
            }
            self._save_data()

    def update_balance(self, wallet_index, balance):
        """Update last known balance for wallet"""
        self._init_wallet(str(wallet_index))
        self.wallet_data[str(wallet_index)]['last_known_balance'] = balance
        self._save_data()

    def add_claim(self, claimed_amount, wallet_index=0):
        """Track BGT claims per wallet"""
        self._init_wallet(str(wallet_index))
        data = self.wallet_data[str(wallet_index)]
        data['total_claimed'] += claimed_amount
        data['pending_amount'] += claimed_amount
        data['last_claim_time'] = datetime.now().isoformat()
        data['claim_amounts'].append({
            'amount': claimed_amount,
            'timestamp': data['last_claim_time']
        })
        self._save_data()
        print(f"📊 Total BGT claimed for wallet {wallet_index + 1}: {w3.from_wei(data['total_claimed'], 'ether')} BGT")

    def add_activation(self):
        """Track boost activations"""
        self.total_activated += 1
        self._save_data()

    def get_oldest_boost_time(self):
        """Get the oldest queued boost time"""
        if not self.queued_boosts:
            return None
        return min(self.queued_boosts.keys())

# Initialize BGT tracker
bgt_tracker = BGTTracker()

def get_bgt_balance(wallet_index=0):
    """Get BGT balance for the wallet"""
    try:
        address = wallet_manager.get_address(wallet_index)
        bgt_contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        balance_wei = bgt_contract.functions.balanceOf(address).call()
        balance_bgt = w3.from_wei(balance_wei, 'ether')
        print(f"Current BGT balance: {balance_bgt} BGT")
        return balance_wei
    except Exception as e:
        print(f"Error checking BGT balance: {str(e)}")
        if rotate_rpc():
            return get_bgt_balance(wallet_index)
        return None

def delegate_bgt(wallet_index=0, retry_count=0):
    """Delegate BGT to validator"""
    MAX_RETRIES = 3
    
    if retry_count >= MAX_RETRIES:
        print(f"❌ Max retries ({MAX_RETRIES}) reached. Aborting operation.")
        return False
        
    try:
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
        
        print("\n📥 DELEGATING BGT:")
        print("-"*30)
        print(f"Wallet {wallet_index + 1}: {address}")
        
        # Get current BGT balance
        print("\n💎 BGT Balance Check:")
        balance = get_bgt_balance(wallet_index)
        if balance is None:
            return False
            
        if balance == 0:
            print("❌ No BGT balance to delegate")
            return False
            
        # Get wallet data from tracker
        bgt_tracker._init_wallet(str(wallet_index))
        wallet_data = bgt_tracker.wallet_data[str(wallet_index)]
        
        # Calculate total amount to delegate
        total_delegated = wallet_data['total_delegated']
        undelegated_balance = balance - total_delegated
        pending_amount = wallet_data['pending_amount']
        total_to_delegate = undelegated_balance + pending_amount
        
        if total_to_delegate == 0:
            print("ℹ️  No BGT to delegate")
            return False
            
        print(f"🔄 Delegating total of {w3.from_wei(total_to_delegate, 'ether')} BGT")
        
        contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        
        transaction = contract.functions.queueBoost(
            VALIDATOR_ADDRESS,
            total_to_delegate
        ).build_transaction({
            'from': address,
            'nonce': w3.eth.get_transaction_count(address),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 80084
        })

        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"📝 Tx Hash: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Delegation successful! Gas used: {receipt['gasUsed']}")
        
        # Update tracker data
        wallet_data['total_delegated'] += total_to_delegate
        wallet_data['pending_amount'] = 0
        wallet_data['last_delegation_time'] = datetime.now().isoformat()
        wallet_data['first_delegation'] = False
        
        # Add to queued boosts
        queue_time = datetime.now().isoformat()
        wallet_data['queued_boosts'][queue_time] = total_to_delegate
        
        # Save updated data
        bgt_tracker._save_data()
        
        return True
            
    except Exception as e:
        print(f"❌ Delegate error: {str(e)}")
        if rotate_rpc():
            return delegate_bgt(wallet_index, retry_count + 1)
        return False

def activate_boost(wallet_index=0, retry_count=0):
    """Activate queued boost"""
    MAX_RETRIES = 3
    
    if retry_count >= MAX_RETRIES:
        print(f"❌ Max retries ({MAX_RETRIES}) reached. Aborting operation.")
        return False
        
    try:
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
        
        print("\n🚀 ACTIVATING BOOST:")
        print("-"*30)
        
        # Get wallet data
        bgt_tracker._init_wallet(str(wallet_index))
        wallet_data = bgt_tracker.wallet_data[str(wallet_index)]
        
        # Check if there are any queued boosts
        if not wallet_data['queued_boosts']:
            print("ℹ️  No queued boosts to activate")
            return False
            
        contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        
        transaction = contract.functions.activateBoost(
            VALIDATOR_ADDRESS
        ).build_transaction({
            'from': address,
            'nonce': w3.eth.get_transaction_count(address),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 80084
        })

        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"🔄 Activating boost...")
        print(f"📝 Tx Hash: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Boost activation successful! Gas used: {receipt['gasUsed']}")
        
        # Update tracker data
        wallet_data['total_activated'] += 1
        wallet_data['last_activation_time'] = datetime.now().isoformat()
        
        # Remove oldest queued boost
        oldest_time = min(wallet_data['queued_boosts'].keys())
        del wallet_data['queued_boosts'][oldest_time]
        
        # Save updated data
        bgt_tracker._save_data()
        
        return True
            
    except Exception as e:
        print(f"❌ Activation error: {str(e)}")
        if rotate_rpc():
            return activate_boost(wallet_index, retry_count + 1)
        return False

# Test execution
if __name__ == "__main__":
    print("Testing BGT delegation functionality...")
    try:
        if w3 and w3.is_connected():
            print(f"✅ Connected to Berachain")
            print(f"📦 Current block: {w3.eth.block_number}")
            wallet_index = 0
            address = wallet_manager.get_address(wallet_index)
            print(f"Testing with wallet {wallet_index + 1} ({address})")
            
            # Test BGT balance
            balance = get_bgt_balance(wallet_index)
            if balance > 0:
                # Test delegation
                delegate_bgt(wallet_index)
                time.sleep(5)
                # Test activation
                activate_boost(wallet_index)
        else:
            print("❌ Failed to connect to Berachain")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
