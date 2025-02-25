from abc import ABC, abstractmethod
from typing import Dict
from web3 import Web3
from web3.exceptions import TimeoutError, TransactionError
from eth_account.signers.local import LocalAccount
from loguru import logger

class BaseTransaction(ABC):
    def __init__(self, web3: Web3, account: LocalAccount):
        self.web3 = web3
        self.account = account

    @abstractmethod
    async def execute(self) -> Dict:
        pass

    async def _build_and_send_transaction(self, transaction):
        """Build and send transaction with RPC rotation support"""
        tries = 0
        max_tries = 3  # Maximum number of tries per RPC
        last_error = None

        while tries < max_tries:
            try:
                # Add chainId if not present
                if 'chainId' not in transaction:
                    transaction['chainId'] = 10143  # Monad Testnet chainId

                signed_txn = self.web3.eth.account.sign_transaction(transaction, self.account.key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                return self.web3.eth.wait_for_transaction_receipt(tx_hash)
                
            except (TimeoutError, TransactionError) as e:
                last_error = e
                logger.warning(f"Transaction failed: {str(e)}")
                # Get a fresh Web3 instance (this will trigger RPC rotation if needed)
                self.web3 = self.web3  # This will get a fresh Web3 instance from the provider
                tries += 1
                if tries < max_tries:
                    logger.info(f"Retrying transaction (attempt {tries + 1}/{max_tries})")
                    # Update nonce for retry
                    transaction['nonce'] = self.web3.eth.get_transaction_count(self.account.address)

        raise Exception(f"Transaction failed after {tries} attempts. Last error: {str(last_error)}")

class NativeTransfer(BaseTransaction):
    async def execute(self, to_address: str, amount: int) -> Dict:
        transaction = {
            'nonce': self.web3.eth.get_transaction_count(self.account.address),
            'to': to_address,
            'value': amount,
            'gas': 21000,
            'gasPrice': self.web3.eth.gas_price,
            'chainId': 10143  # Monad Testnet chainId
        }
        return await self._build_and_send_transaction(transaction)

class TokenTransfer(BaseTransaction):
    async def execute(self, token_address: str, to_address: str, amount: int) -> Dict:
        contract = self.web3.eth.contract(
            address=token_address,
            abi=[{
                "constant": False,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }]
        )
        
        transaction = contract.functions.transfer(
            to_address,
            amount
        ).build_transaction({
            'nonce': self.web3.eth.get_transaction_count(self.account.address),
            'gas': 100000,
            'gasPrice': self.web3.eth.gas_price,
            'chainId': 10143  # Monad Testnet chainId
        })
        
        return await self._build_and_send_transaction(transaction) 