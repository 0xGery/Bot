from typing import Dict
from decimal import Decimal
from .base import BaseDapp
from web3 import Web3
from loguru import logger
import asyncio
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import (
    CHAIN_ID, GAS_PRICE, APPROVAL_GAS, KINZA_DEPOSIT_GAS,
    USDC, KINZA_LENDING, DEFAULT_REFERRAL_CODE, ERC20_ABI
)

class Kinza(BaseDapp):
    # Kinza Lending ABI
    LENDING_ABI = [
        {
            "inputs": [
                {"name": "token", "type": "address"},
                {"name": "amount", "type": "uint256"},
                {"name": "onBehalfOf", "type": "address"},
                {"name": "referralCode", "type": "uint16"}
            ],
            "name": "deposit",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "funcSelector": "0x617ba037"
        }
    ]

    # ERC20 ABI for approvals
    ERC20_ABI = [
        {
            "inputs": [
                {"name": "spender", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"name": "owner", "type": "address"},
                {"name": "spender", "type": "address"}
            ],
            "name": "allowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {"name": "account", "type": "address"}
            ],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    async def get_contract_addresses(self) -> Dict[str, str]:
        """Get Kinza contract addresses"""
        return {
            'lending': KINZA_LENDING,  # Kinza lending contract
            'usdc': USDC,             # USDC token
        }

    async def _ensure_token_approval(self, token_address: str, spender: str, amount: int) -> None:
        """Ensure token approval for spender"""
        token_contract = self._get_contract(token_address, ERC20_ABI)
        
        # Check current allowance
        allowance = token_contract.functions.allowance(
            self.account.address,
            spender
        ).call()

        if allowance < amount:
            # Approve if needed
            approve_tx = token_contract.functions.approve(
                spender,
                amount
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'gas': APPROVAL_GAS,
                'gasPrice': GAS_PRICE,
                'chainId': CHAIN_ID
            })

            receipt = await self._build_and_send_transaction(approve_tx)
            logger.info(f"Approved USDC spending for Kinza lending")
            return receipt

    async def deposit(self, amount: int) -> Dict:
        """
        Deposit USDC into Kinza lending by minting kUSDC
        
        Args:
            amount: Amount of USDC to deposit (in wei)
        """
        try:
            addresses = await self.get_contract_addresses()
            lending = self._get_contract(addresses['lending'], self.LENDING_ABI)
            
            # Check USDC balance first
            usdc = self._get_contract(addresses['usdc'], ERC20_ABI)
            balance = usdc.functions.balanceOf(self.account.address).call()
            logger.info(f"Current USDC balance: {balance/1000000:.6f}")
            
            if balance < amount:
                raise Exception(f"Insufficient USDC balance. Have: {balance/1000000:.6f}, Need: {amount/1000000:.6f}")

            # First ensure USDC is approved
            approval_receipt = await self._ensure_token_approval(addresses['usdc'], addresses['lending'], amount)
            
            # If we got an approval receipt, we need to wait a bit before proceeding
            if approval_receipt:
                # Wait for a few seconds after approval
                await asyncio.sleep(5)
            
            # Double check allowance after approval
            allowance = usdc.functions.allowance(self.account.address, addresses['lending']).call()
            logger.info(f"Current USDC allowance for Kinza: {allowance/1000000:.6f}")

            # Build deposit transaction with exact parameters from successful tx
            deposit_tx = lending.functions.deposit(
                addresses['usdc'],  # token address
                amount,            # amount to deposit
                self.account.address,  # onBehalfOf
                DEFAULT_REFERRAL_CODE  # referralCode
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'gas': KINZA_DEPOSIT_GAS,
                'gasPrice': GAS_PRICE,
                'value': 0,
                'chainId': CHAIN_ID
            })

            # Log transaction details for debugging
            logger.info(f"Sending deposit transaction: amount={amount/1000000:.6f} USDC, gas={deposit_tx['gas']}")
            
            # Send transaction and wait for receipt
            signed_tx = self.account.sign_transaction(deposit_tx)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Check transaction status
            if receipt['status'] == 0:
                raise Exception(f"Transaction failed. Gas used: {receipt['gasUsed']}")
                
            return receipt
            
        except Exception as e:
            logger.error(f"Deposit failed: {str(e)}")
            # Re-raise to handle in the automation
            raise

