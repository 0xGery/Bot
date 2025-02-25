import json
import time
from dotenv import load_dotenv
import os
from typing import List, Dict
from eth_account import Account
from web3 import Web3
from web3.exceptions import TransactionNotFound, TimeExhausted
from loguru import logger

class RPCManager:
    def __init__(self, rpc_urls: List[str], timeout: int = 10, max_tries: int = 3):
        self.rpc_urls = rpc_urls
        self.current_rpc_index = 0
        self.timeout = timeout
        self.max_tries = max_tries
        self._create_web3()

    def _create_web3(self):
        """Create Web3 instance with current RPC"""
        self.web3 = Web3(Web3.HTTPProvider(
            self.rpc_urls[self.current_rpc_index],
            request_kwargs={'timeout': self.timeout}
        ))

    def rotate_rpc(self):
        """Rotate to next RPC endpoint"""
        self.current_rpc_index = (self.current_rpc_index + 1) % len(self.rpc_urls)
        logger.warning(f"Rotating to RPC: {self.rpc_urls[self.current_rpc_index]}")
        self._create_web3()

    def get_web3(self) -> Web3:
        """Get current Web3 instance"""
        return self.web3

    async def make_request(self, method, *args, **kwargs):
        """Make RPC request with automatic rotation on failure"""
        tries = 0
        last_error = None

        while tries < self.max_tries * len(self.rpc_urls):
            try:
                return await method(*args, **kwargs)
            except (TimeExhausted, TransactionNotFound) as e:
                last_error = e
                logger.warning(f"RPC request failed: {str(e)}")
                self.rotate_rpc()
                tries += 1
                time.sleep(1)  # Small delay before retry

        raise Exception(f"All RPCs failed after {tries} tries. Last error: {str(last_error)}")

class Config:
    def __init__(self):
        load_dotenv()
        
        # Load RPC configuration with default values
        rpc_urls_str = os.getenv('MONAD_RPC_URLS', '["https://testnet-rpc.monad.xyz", "https://monad-testnet.drpc.org"]')
        try:
            # Try to parse as JSON first
            self.rpc_urls = json.loads(rpc_urls_str)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to parse as a comma-separated string
            if isinstance(rpc_urls_str, str):
                self.rpc_urls = [url.strip() for url in rpc_urls_str.strip('[]').split(',')]
            else:
                # Fallback to default URLs
                self.rpc_urls = ["https://testnet-rpc.monad.xyz", "https://monad-testnet.drpc.org"]
        
        logger.info(f"Initialized with RPC URLs: {self.rpc_urls}")
        
        self.chain_id = int(os.getenv('CHAIN_ID', '10143'))
        self.rpc_timeout = int(os.getenv('RPC_TIMEOUT_SECONDS', '10'))
        self.max_rpc_tries = int(os.getenv('MAX_RPC_TRIES', '3'))
        
        # Initialize RPC manager
        self.rpc_manager = RPCManager(
            self.rpc_urls,
            timeout=self.rpc_timeout,
            max_tries=self.max_rpc_tries
        )
        
        # Load other configuration
        self.min_delay = int(os.getenv('MIN_DELAY_SECONDS', '60'))
        self.max_delay = int(os.getenv('MAX_DELAY_SECONDS', '300'))
        self.wallets = self._load_wallets()

    def _load_wallets(self) -> List[Dict]:
        wallets = []
        wallet_index = 1
        
        while True:
            private_key = os.getenv(f'WALLET_{wallet_index}_PRIVATE_KEY')
            if not private_key:
                break
                
            account = Account.from_key(private_key)
            wallets.append({
                'address': account.address,
                'private_key': private_key,
                'account': account
            })
            wallet_index += 1
            
        if not wallets:
            logger.warning("No wallet private keys found in environment variables!")
        
        return wallets

    def get_web3(self) -> Web3:
        return self.rpc_manager.get_web3()

    def get_wallets(self) -> List[Dict]:
        return self.wallets 