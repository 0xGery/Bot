import os
import json
from datetime import datetime

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
        if str(wallet_index) not in self.wallet_data:
            self.wallet_data[str(wallet_index)] = {
                'total_claimed': 0,
                'pending_amount': 0,
                'total_delegated': 0,
                'last_known_balance': 0,
                'first_delegation': True,
                'queued_boosts': {},
                'last_claim_time': None,
                'last_delegation_time': None,
                'last_activation_time': None,
                'claim_amounts': [],
                'unboosted_balance': 0,
                'boosted_amount': 0,
                'queued_boost': 0,
                'current_balance': 0,
                'total_balance': 0
            }
    
    def update_balance(self, wallet_index, balance):
        """Update last known balance for wallet"""
        self._init_wallet(str(wallet_index))
        self.wallet_data[str(wallet_index)]['last_known_balance'] = balance
        self._save_data()
    
    def add_claim(self, amount, wallet_index):
        """Record a BGT claim"""
        self._init_wallet(str(wallet_index))
        self.wallet_data[str(wallet_index)]['total_claimed'] += amount
        self.wallet_data[str(wallet_index)]['last_claim_time'] = datetime.now().isoformat()
        self._save_data()

# Create global instance
bgt_tracker = BGTTracker()
