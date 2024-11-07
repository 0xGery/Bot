import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import w3
from utils import account, address, random_delay
from eth_abi import encode

# Contract addresses 
BGT_CONTRACT = "0xbDa130737BDd9618301681329bF2e46A016ff9Ad"  # BGT contract
VALIDATOR_ADDRESS = w3.to_checksum_address("0x40495A781095932e2FC8dccA69F5e358711Fdd41")

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
        self.total_claimed = 0  # in Wei
        self.total_delegated = 0  # in Wei
        self.total_activated = 0  # in Wei
        self.first_delegation = True
        self.queued_boosts = {}  # Dictionary to track {timestamp: amount in Wei}
        
    def log_status(self, action="STATUS_UPDATE"):
        """Log current BGT status to file"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Get current balance in Wei
            current_balance = get_bgt_balance()
            
            # Calculate queued amount in Wei
            queued_amount = sum(self.queued_boosts.values())
            
            # Calculate not delegated amount in Wei
            not_delegated = max(0, self.total_claimed - self.total_delegated)
            
            log_entry = (
                f"\n=== {action} at {current_time} ===\n"
                f"Original BGT Balance: {w3.from_wei(current_balance, 'ether')} BGT\n"
                f"Total BGT Claimed: {w3.from_wei(self.total_claimed, 'ether')} BGT\n"
                f"Total BGT Queued for Boost: {w3.from_wei(self.total_delegated, 'ether')} BGT\n"
                f"Total BGT Activated: {w3.from_wei(self.total_activated, 'ether')} BGT\n"
                f"Current Queue Amount: {w3.from_wei(queued_amount, 'ether')} BGT\n"
                f"BGT Not Yet Delegated: {w3.from_wei(not_delegated, 'ether')} BGT\n"
                f"Number of Pending Boosts: {len(self.queued_boosts)}\n"
                "Queued Boosts Details:\n"
            )
            
            # Add details for each queued boost
            for timestamp, amount in self.queued_boosts.items():
                queue_time = datetime.fromtimestamp(timestamp)
                hours_queued = (datetime.now() - queue_time).total_seconds() / 3600
                log_entry += (
                    f"- {w3.from_wei(amount, 'ether')} BGT queued at {queue_time}, "
                    f"waiting {hours_queued:.2f} hours\n"
                )
            
            # Write to file
            with open("logs_delegate.txt", "a") as f:
                f.write(log_entry)
                
        except Exception as e:
            print(f"Error writing to log file: {str(e)}")
            print(f"Debug values:")
            print(f"total_claimed: {self.total_claimed}")
            print(f"total_delegated: {self.total_delegated}")
            print(f"total_activated: {self.total_activated}")
            print(f"queued_amount: {queued_amount}")
    
    def add_claim(self, amount):
        """Add claimed amount (in Wei)"""
        self.total_claimed += amount
        print(f"Total BGT claimed: {w3.from_wei(self.total_claimed, 'ether')}")
        self.log_status("BGT_CLAIMED")
    
    def add_delegation(self, amount):
        """Add delegated amount (in Wei)"""
        self.total_delegated += amount
        if self.first_delegation:
            self.first_delegation = False
        self.queued_boosts[int(time.time())] = amount
        print(f"Total BGT delegated: {w3.from_wei(self.total_delegated, 'ether')}")
        self.log_status("BGT_QUEUED_BOOST")
    
    def add_activation(self, amounts):
        """Record activated boosts (amounts in Wei)"""
        activated_amount = sum(amounts)
        self.total_activated += activated_amount
        print(f"Added {w3.from_wei(activated_amount, 'ether')} BGT to total activated amount")
        print(f"Total BGT activated: {w3.from_wei(self.total_activated, 'ether')}")
        self.log_status("BGT_ACTIVATED_BOOST")
    
    @property
    def pending_amount(self):
        """Get amount pending delegation (in Wei)"""
        return max(0, self.total_claimed - self.total_delegated)

    def get_activatable_boosts(self):
        """Returns list of amounts that can be activated (queued > 10 hours ago)"""
        current_time = int(time.time())
        activatable = []
        
        # Check each queued boost
        for queue_time, amount in list(self.queued_boosts.items()):
            hours_queued = (current_time - queue_time) / 3600
            if hours_queued >= 10:  # 10 hours waiting period
                activatable.append(amount)
                # Remove from queue since we're activating it
                del self.queued_boosts[queue_time]
                print(f"Found activatable boost: {w3.from_wei(amount, 'ether')} BGT, queued for {hours_queued:.2f} hours")
        
        return activatable

# Create global tracker
bgt_tracker = BGTTracker()

def get_bgt_balance():
    """Get BGT balance for the wallet"""
    try:
        bgt_contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        balance_wei = bgt_contract.functions.balanceOf(address).call()
        balance_bgt = w3.from_wei(balance_wei, 'ether')  # Convert from wei to BGT
        print(f"Current BGT balance: {balance_bgt} BGT")
        return balance_wei
    except Exception as e:
        print(f"Error checking BGT balance: {str(e)}")
        return 0

def delegate_bgt():
    try:
        # First check BGT balance
        bgt_balance_wei = get_bgt_balance()
        if bgt_balance_wei == 0:
            print("No BGT available to delegate")
            return False
            
        # Calculate the amount to delegate based on whether it's first time or not
        if bgt_tracker.first_delegation:
            # First time: delegate entire balance
            amount_to_delegate = bgt_balance_wei
            print("First delegation: delegating entire balance")
        else:
            # Subsequent times: only delegate new BGT since last delegation
            amount_to_delegate = bgt_tracker.pending_amount
            print(f"Subsequent delegation: delegating only new BGT ({w3.from_wei(amount_to_delegate, 'ether')} BGT)")
        
        if amount_to_delegate <= 0:
            print("No new BGT to delegate")
            return False
            
        bgt_contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        
        # Get current nonce
        nonce = w3.eth.get_transaction_count(address)
        
        # Build transaction
        transaction = bgt_contract.functions.queueBoost(
            VALIDATOR_ADDRESS,
            amount_to_delegate
        ).build_transaction({
            'from': address,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 80084
        })

        # Sign transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"Delegating {w3.from_wei(amount_to_delegate, 'ether')} BGT...")
        print(f"Transaction hash: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Delegation successful! Gas used: {receipt['gasUsed']}")
        
        # Update tracker
        bgt_tracker.add_delegation(amount_to_delegate)
        
        return True
        
    except Exception as e:
        print(f"Delegate error: {str(e)}")
        return False

def activate_boost():
    """Activate queued boosts that are older than 10 hours"""
    try:
        # Get list of boosts ready to activate
        activatable = bgt_tracker.get_activatable_boosts()
        if not activatable:
            print("No boosts ready to activate")
            return False
            
        print(f"Found {len(activatable)} boosts ready to activate")
        total_amount = sum(activatable)
        print(f"Total amount to activate: {w3.from_wei(total_amount, 'ether')} BGT")
        
        bgt_contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        
        # Get current nonce
        nonce = w3.eth.get_transaction_count(address)
        
        # Build transaction
        transaction = bgt_contract.functions.activateBoost(
            VALIDATOR_ADDRESS
        ).build_transaction({
            'from': address,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 80084
        })

        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"Activating boost for validator {VALIDATOR_ADDRESS}...")
        print(f"Transaction hash: {tx_hash.hex()}")
        
        # Wait for receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Boost activation successful! Gas used: {receipt['gasUsed']}")
        
        # Update tracker with activated amounts
        bgt_tracker.add_activation(activatable)
        
        return True
        
    except Exception as e:
        print(f"Activate boost error: {str(e)}")
        return False

# Test execution
if __name__ == "__main__":
    print("Testing BGT delegation functionality...")
    try:
        if w3.is_connected():
            print(f"Connected to Berachain")
            print(f"Current block number: {w3.eth.block_number}")
            print(f"Your wallet address: {address}")
            
            # Test delegate
            delegate_bgt()
        else:
            print("Failed to connect to Berachain")
    except Exception as e:
        print(f"Error: {str(e)}")
