from abc import ABC, abstractmethod
from typing import Dict, Any
from web3 import Web3
from eth_account.signers.local import LocalAccount
from loguru import logger

class BaseDapp(ABC):
    def __init__(self, web3: Web3, account: LocalAccount):
        self.web3 = web3
        self.account = account
        self.chain_id = 10143  # Monad Testnet

    @abstractmethod
    async def get_contract_addresses(self) -> Dict[str, str]:
        """Return a dictionary of contract addresses used by this dapp"""
        pass

    async def _build_and_send_transaction(self, transaction: Dict[str, Any]) -> Dict:
        """Build and send transaction with RPC rotation support"""
        tries = 0
        max_tries = 3
        last_error = None

        while tries < max_tries:
            try:
                if 'chainId' not in transaction:
                    transaction['chainId'] = self.chain_id

                signed_txn = self.web3.eth.account.sign_transaction(transaction, self.account.key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                return receipt
                
            except Exception as e:
                last_error = e
                logger.warning(f"Transaction failed: {str(e)}")
                tries += 1
                if tries < max_tries:
                    logger.info(f"Retrying transaction (attempt {tries + 1}/{max_tries})")
                    # Update nonce for retry
                    transaction['nonce'] = self.web3.eth.get_transaction_count(self.account.address)

        raise Exception(f"Transaction failed after {tries} attempts. Last error: {str(last_error)}")

    def _get_contract(self, address: str, abi: list) -> Any:
        """Helper to create contract instance"""
        return self.web3.eth.contract(address=address, abi=abi) 