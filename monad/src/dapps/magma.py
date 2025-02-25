from typing import Dict
from decimal import Decimal
from .base import BaseDapp
from web3 import Web3
from loguru import logger
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.settings import (
    CHAIN_ID, GAS_PRICE, MAGMA_STAKE_GAS,
    GMON, MAGMA_STAKING
)

class Magma(BaseDapp):
    # Magma Staking ABI
    STAKING_ABI = [
        {
            "inputs": [],
            "name": "stake",  # The name doesn't matter as we'll use the raw selector
            "outputs": [],
            "stateMutability": "payable",
            "type": "function",
            "selector": "0xd5575982"  # This is the exact selector from the successful tx
        }
    ]

    # ERC20 ABI for gMON token
    TOKEN_ABI = [
        {
            "inputs": [{"name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    async def get_contract_addresses(self) -> Dict[str, str]:
        """Get Magma contract addresses"""
        return {
            'staking': MAGMA_STAKING,  # Magma staking contract
            'gmon': GMON,             # gMON token
        }

    async def get_gmon_balance(self) -> int:
        """Get gMON balance of the current account"""
        addresses = await self.get_contract_addresses()
        gmon_token = self._get_contract(addresses['gmon'], self.TOKEN_ABI)  # Use gMON token contract
        
        balance = gmon_token.functions.balanceOf(self.account.address).call()
        return balance

    async def stake(self, amount: int) -> Dict:
        """
        Stake MON to receive gMON
        
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

            # Build transaction with raw data
            stake_tx = {
                'from': self.account.address,
                'to': addresses['staking'],
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'gas': MAGMA_STAKE_GAS,
                'gasPrice': GAS_PRICE,
                'value': amount,
                'chainId': CHAIN_ID,
                'data': '0xd5575982'  # Use the exact selector from successful tx
            }

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