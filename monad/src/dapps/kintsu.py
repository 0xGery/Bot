from typing import Dict
from decimal import Decimal
from .base import BaseDapp
from web3 import Web3
from loguru import logger
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import (
    CHAIN_ID, GAS_PRICE, KINTSU_STAKE_GAS,
    SMON, KINTSU_STAKING
)

class Kintsu(BaseDapp):
    # Kintsu Staking ABI
    STAKING_ABI = [
        {
            "inputs": [],
            "name": "stake",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "payable",
            "type": "function",
            "funcSelector": "0x3a4b66f1"
        },
        {
            "inputs": [{"name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    async def get_contract_addresses(self) -> Dict[str, str]:
        """Get Kintsu contract addresses"""
        return {
            'staking': KINTSU_STAKING,  # Kintsu staking contract
            'smon': SMON,              # sMON token
        }

    async def get_smon_balance(self) -> int:
        """Get sMON balance of the current account"""
        addresses = await self.get_contract_addresses()
        staking = self._get_contract(addresses['staking'], self.STAKING_ABI)
        
        balance = staking.functions.balanceOf(self.account.address).call()
        return balance

    async def stake(self, amount: int) -> Dict:
        """
        Stake MON to receive sMON
        
        Args:
            amount: Amount of MON to stake (in wei)
        """
        try:
            addresses = await self.get_contract_addresses()
            staking = self._get_contract(addresses['staking'], self.STAKING_ABI)
            
            # Check MON balance first
            balance = self.web3.eth.get_balance(self.account.address)
            logger.info(f"Current MON balance: {Web3.from_wei(balance, 'ether'):.6f}")
            
            if balance < amount:
                raise Exception(f"Insufficient MON balance. Have: {Web3.from_wei(balance, 'ether')}, Need: {Web3.from_wei(amount, 'ether')}")

            # Build stake transaction
            stake_tx = staking.functions.stake().build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'gas': KINTSU_STAKE_GAS,
                'gasPrice': GAS_PRICE,
                'value': amount,
                'chainId': CHAIN_ID
            })

            # Log transaction details for debugging
            logger.info(f"Sending stake transaction: amount={Web3.from_wei(amount, 'ether'):.6f} MON, gas={stake_tx['gas']}")
            
            receipt = await self._build_and_send_transaction(stake_tx)
            
            # Check transaction status
            if receipt['status'] == 0:
                raise Exception(f"Transaction failed. Gas used: {receipt['gasUsed']}")
                
            return receipt
            
        except Exception as e:
            logger.error(f"Stake failed: {str(e)}")
            # Re-raise to handle in the automation
            raise
