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
}, {
    "inputs": [
        {"type": "address", "name": "account"},
        {"type": "uint256", "name": "block"}
    ],
    "name": "queuedBoost",
    "outputs": [{"type": "uint256"}],
    "stateMutability": "view",
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
        """Initialize wallet data if not exists"""
        if wallet_index not in self.wallet_data:
            self.wallet_data[wallet_index] = {
                'total_claimed': 0,
                'pending_amount': 0,
                'total_delegated': 0,
                'last_known_balance': 0,
                'first_delegation': True,
                'last_delegation_time': None,
                'last_claim_time': None,
                'claim_amounts': [],
                'queued_boosts': {}
            }

    def update_balance(self, wallet_index, new_balance):
        """Update the last known balance"""
        self._init_wallet(str(wallet_index))
        self.wallet_data[str(wallet_index)]['last_known_balance'] = new_balance
        self._save_data()

    def add_claim(self, claimed_amount, wallet_index=0):
        """Track BGT claims per wallet with validation"""
        try:
            if claimed_amount <= 0:
                print("❌ Invalid claim amount")
                return False
                
            self._init_wallet(str(wallet_index))
            data = self.wallet_data[str(wallet_index)]
            
            # Verify claim doesn't exceed possible amounts
            max_possible_claim = w3.to_wei(100, 'ether')  # Example maximum
            if claimed_amount > max_possible_claim:
                print(f"❌ Suspicious claim amount: {w3.from_wei(claimed_amount, 'ether')} BGT")
                return False
                
            # Update amounts with validation
            new_total = data['total_claimed'] + claimed_amount
            new_pending = data['pending_amount'] + claimed_amount
            
            if new_total < data['total_claimed'] or new_pending < data['pending_amount']:
                print("❌ Integer overflow detected in claim amounts")
                return False
                
            # Update if validation passed
            data['total_claimed'] = new_total
            data['pending_amount'] = new_pending
            data['last_claim_time'] = datetime.now().isoformat()
            data['claim_amounts'].append({
                'amount': claimed_amount,
                'timestamp': data['last_claim_time']
            })
            
            self._save_data()
            print(f"✅ Claim tracked successfully:")
            print(f"├─ Amount: {w3.from_wei(claimed_amount, 'ether')} BGT")
            print(f"├─ Total Claimed: {w3.from_wei(new_total, 'ether')} BGT")
            print(f"└─ Pending Amount: {w3.from_wei(new_pending, 'ether')} BGT")
            
            return True
            
        except Exception as e:
            print(f"❌ Error tracking claim: {str(e)}")
            return False

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

# Add new function to check queued boosts
def check_queued_boost(wallet_index=0):
    """Check queued boost status for wallet"""
    try:
        address = wallet_manager.get_address(wallet_index)
        contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        
        # Get current block number
        current_block = w3.eth.block_number
        
        # Call queuedBoost with address and block number
        queued = contract.functions.queuedBoost(
            address,
            current_block  # 'latest' block
        ).call()
        
        print(f"\n🔍 Queued Boost Status for Wallet {wallet_index + 1}:")
        print(f"├─ Address: {address}")
        print(f"├─ Current Block: {current_block}")
        print(f"├─ Queued Amount: {w3.from_wei(queued, 'ether')} BGT")
        
        return queued

    except Exception as e:
        print(f"❌ Error checking queued boost: {str(e)}")
        return 0

def validate_bgt_amounts(wallet_index, current_balance, pending_amount, total_delegated):
    """Validate BGT amounts before delegation"""
    try:
        # Check for negative values
        if current_balance < 0 or pending_amount < 0 or total_delegated < 0:
            print("❌ Invalid negative values detected:")
            print(f"├─ Current Balance: {w3.from_wei(current_balance, 'ether')} BGT")
            print(f"├─ Pending Amount: {w3.from_wei(pending_amount, 'ether')} BGT")
            print(f"└─ Total Delegated: {w3.from_wei(total_delegated, 'ether')} BGT")
            return False

        # Verify total_delegated doesn't exceed current_balance
        if total_delegated > current_balance:
            print("��� Total delegated exceeds current balance:")
            print(f"├─ Current Balance: {w3.from_wei(current_balance, 'ether')} BGT")
            print(f"└─ Total Delegated: {w3.from_wei(total_delegated, 'ether')} BGT")
            return False

        # Verify amounts against on-chain data
        actual_balance = get_bgt_balance(wallet_index)
        if actual_balance is None:
            print("❌ Failed to verify on-chain balance")
            return False
            
        if abs(actual_balance - current_balance) > w3.to_wei(0.0001, 'ether'):  # Small tolerance for rounding
            print("❌ Balance mismatch detected:")
            print(f"├─ Tracked Balance: {w3.from_wei(current_balance, 'ether')} BGT")
            print(f"└─ Actual Balance: {w3.from_wei(actual_balance, 'ether')} BGT")
            bgt_tracker.update_balance(wallet_index, actual_balance)  # Update tracker
            return False

        print("\n✅ BGT Amount Validation:")
        print(f"├─ Current Balance: {w3.from_wei(current_balance, 'ether')} BGT")
        print(f"├─ Pending Amount: {w3.from_wei(pending_amount, 'ether')} BGT")
        print(f"├─ Total Delegated: {w3.from_wei(total_delegated, 'ether')} BGT")
        print(f"└─ Available to Delegate: {w3.from_wei(pending_amount + (current_balance - total_delegated), 'ether')} BGT")
        
        return True

    except Exception as e:
        print(f"❌ Validation error: {str(e)}")
        return False

def validate_json_structure(data):
    """Validate BGT tracker JSON structure"""
    required_fields = {
        'total_claimed': int,
        'pending_amount': int,
        'total_delegated': int,
        'last_known_balance': int,
        'first_delegation': bool,
        'queued_boosts': dict,
        'last_delegation_time': (str, type(None)),
        'last_claim_time': (str, type(None)),
        'claim_amounts': list
    }
    
    try:
        for wallet_id, wallet_data in data.items():
            if not isinstance(wallet_data, dict):
                print(f"❌ Invalid wallet data structure for wallet {wallet_id}")
                return False
                
            # Check required fields and types
            for field, field_type in required_fields.items():
                if field not in wallet_data:
                    print(f"❌ Missing required field '{field}' in wallet {wallet_id}")
                    return False
                    
                if not isinstance(wallet_data[field], field_type):
                    if isinstance(field_type, tuple):
                        if not any(isinstance(wallet_data[field], t) for t in field_type):
                            print(f"❌ Invalid type for field '{field}' in wallet {wallet_id}")
                            return False
                    else:
                        print(f"❌ Invalid type for field '{field}' in wallet {wallet_id}")
                        return False
            
            # Validate queued_boosts structure
            for block, boost_data in wallet_data['queued_boosts'].items():
                required_boost_fields = {
                    'amount': int,
                    'queue_block': int,
                    'timestamp': str
                }
                
                for field, field_type in required_boost_fields.items():
                    if field not in boost_data:
                        print(f"❌ Missing required field '{field}' in boost data for wallet {wallet_id}")
                        return False
                    if not isinstance(boost_data[field], field_type):
                        print(f"❌ Invalid type for field '{field}' in boost data for wallet {wallet_id}")
                        return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating JSON structure: {str(e)}")
        return False

def delegate_bgt(wallet_index=0, retry_count=0):
    """Delegate BGT to validator"""
    MAX_RETRIES = 3
    if retry_count >= MAX_RETRIES:
        print(f"❌ Max retries ({MAX_RETRIES}) reached. Aborting delegation.")
        return False
        
    try:
        # Initialize and validate wallet data
        bgt_tracker._init_wallet(str(wallet_index))
        if not validate_json_structure(bgt_tracker.wallet_data):
            print("❌ Invalid tracker data structure. Aborting delegation.")
            return False
            
        wallet_data = bgt_tracker.wallet_data[str(wallet_index)]
        
        # Get current BGT balance and pending amount
        current_balance = wallet_data.get('last_known_balance', 0)
        pending_amount = wallet_data.get('pending_amount', 0)
        total_delegated = wallet_data.get('total_delegated', 0)
        
        # Calculate available amount to delegate
        available_to_delegate = pending_amount + (current_balance - total_delegated)
        
        if available_to_delegate <= 0:
            print("❌ No BGT available to delegate")
            return False
            
        # Minimum delegation amount (0.01 BGT)
        MIN_DELEGATION = w3.to_wei(0.01, 'ether')
        if available_to_delegate < MIN_DELEGATION:
            print(f"❌ Available amount ({w3.from_wei(available_to_delegate, 'ether')} BGT) below minimum")
            return False
            
        print(f"\n💎 Delegating BGT:")
        print(f"├─ Available: {w3.from_wei(available_to_delegate, 'ether')} BGT")
        print(f"├─ Pending: {w3.from_wei(pending_amount, 'ether')} BGT")
        print(f"└─ Already Delegated: {w3.from_wei(total_delegated, 'ether')} BGT")
        
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
        contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        
        # Queue the boost transaction
        transaction = contract.functions.queueBoost(
            VALIDATOR_ADDRESS,
            available_to_delegate
        ).build_transaction({
            'from': address,
            'nonce': w3.eth.get_transaction_count(address),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 80084
        })
        
        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"\n🔄 Queueing boost...")
        print(f"📝 Tx Hash: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] != 1:
            print("❌ Transaction failed")
            return False
            
        print(f"✅ Boost queued successfully! Gas used: {receipt['gasUsed']}")
        
        # Get the block number when boost was queued
        queue_block = receipt['blockNumber']
        print(f"📦 Queued at block: {queue_block}")
        
        # Update tracker data
        wallet_data['total_delegated'] += available_to_delegate
        wallet_data['pending_amount'] = 0
        wallet_data['first_delegation'] = False
        wallet_data['last_delegation_time'] = datetime.now().isoformat()
        
        # Add to queued boosts with block number
        wallet_data['queued_boosts'][str(queue_block)] = {
            'amount': available_to_delegate,
            'queue_block': queue_block,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save updated data
        bgt_tracker._save_data()
        
        print(f"\n📊 Delegation Summary:")
        print(f"├─ Amount Queued: {w3.from_wei(available_to_delegate, 'ether')} BGT")
        print(f"├─ Queue Block: {queue_block}")
        print(f"├─ Required Blocks: 8186 + 5")
        print(f"└─ Activation Available: Block {queue_block + 8191}")
        
        return True
            
    except Exception as e:
        print(f"❌ Delegate error: {str(e)}")
        if rotate_rpc():
            print("🔄 Retrying with new RPC...")
            return delegate_bgt(wallet_index, retry_count + 1)
        return False

def check_boost_queue(wallet_index=0):
    """Check queued boost details for the wallet"""
    try:
        address = wallet_manager.get_address(wallet_index)
        contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        
        # Get queue details for this wallet and validator
        queue_info = contract.functions.queuedBoost(
            address,
            w3.eth.block_number
        ).call()
        
        current_block = w3.eth.block_number
        blocks_passed = current_block - queue_info[0]
        
        print("\n🔍 Boost Queue Status:")
        print(f"Queued Amount: {w3.from_wei(queue_info[1], 'ether')} BGT")
        print(f"Queue Block: {queue_info[0]}")
        print(f"Current Block: {current_block}")
        print(f"Blocks Passed: {blocks_passed}")
        
        # Usually there's a minimum block delay before activation
        # Return both the block info and balance for decision making
        return {
            'block_number': queue_info[0],
            'current_block': current_block,
            'blocks_passed': blocks_passed,
            'queued_balance': queue_info[1]
        }
        
    except Exception as e:
        print(f"Error checking boost queue: {str(e)}")
        return None

def should_activate_boost(wallet_index=0):
    """Check if boost can and should be activated"""
    try:
        address = wallet_manager.get_address(wallet_index)
        contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        current_block = w3.eth.block_number
        
        # Get queued amount at current block
        queued_amount = contract.functions.queuedBoost(
            address,
            current_block
        ).call()
        
        if queued_amount == 0:
            print("ℹ️ No queued boost to activate")
            return False
            
        # Get queue block from tracker
        wallet_data = bgt_tracker.wallet_data[str(wallet_index)]
        queued_boosts = wallet_data.get('queued_boosts', {})
        
        if not queued_boosts:
            print("ℹ️ No queued boosts found in tracker")
            return False
            
        # Check oldest queued boost
        oldest_queue_block = min(int(block) for block in queued_boosts.keys())
        blocks_passed = current_block - oldest_queue_block
        
        # Required blocks: 8186 + 5 blocks buffer
        REQUIRED_BLOCKS = 8186 + 5
        
        can_activate = blocks_passed >= REQUIRED_BLOCKS
        
        print(f"\n🔍 Boost Activation Check for Wallet {wallet_index + 1}:")
        print(f"├─ Address: {address}")
        print(f"├─ Queued Amount: {w3.from_wei(queued_amount, 'ether')} BGT")
        print(f"├─ Queue Block: {oldest_queue_block}")
        print(f"├─ Current Block: {current_block}")
        print(f"├─ Blocks Passed: {blocks_passed}/{REQUIRED_BLOCKS}")
        print(f"└─ Can Activate: {'✅' if can_activate else '❌'}")
        
        return can_activate
            
    except Exception as e:
        print(f"❌ Error checking boost activation: {str(e)}")
        return False

def activate_boost(wallet_index=0, retry_count=0):
    """Activate queued boost if conditions are met"""
    if not should_activate_boost(wallet_index):
        return False
        
    try:
        # Get wallet data from tracker
        bgt_tracker._init_wallet(str(wallet_index))
        wallet_data = bgt_tracker.wallet_data[str(wallet_index)]
        
        # Check cooldown period (12 hours)
        last_activation = wallet_data.get('last_activation_time')
        if last_activation:
            last_activation_time = datetime.fromisoformat(last_activation)
            time_since_activation = datetime.now() - last_activation_time
            if time_since_activation < timedelta(hours=12):
                remaining_time = timedelta(hours=12) - time_since_activation
                print(f"⏳ Boost activation cooldown: {remaining_time} remaining")
                return False

        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
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
        print(f"\n🔄 Activating boost...")
        print(f"📝 Tx Hash: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Boost activation successful! Gas used: {receipt['gasUsed']}")
        
        # Update tracker data
        wallet_data['total_activated'] += 1
        wallet_data['last_activation_time'] = datetime.now().isoformat()
        
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
