from typing import Dict
from decimal import Decimal
from .base import BaseDapp
from web3 import Web3
from loguru import logger
import asyncio
import random
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import (
    CHAIN_ID, GAS_PRICE, APPROVAL_GAS, CURVANCE_DEPOSIT_GAS,
    WBTC, CURVANCE_WBTC, CURVANCE_USDC_TOKEN, CURVANCE_USDC,
    MIN_LENDING_AMOUNT_USDC, MAX_LENDING_AMOUNT_USDC,
    MIN_LENDING_AMOUNT_WBTC, MAX_LENDING_AMOUNT_WBTC,
    DEFAULT_REFERRAL_CODE, ERC20_ABI
)

class Curvance(BaseDapp):
    # Token selection rolls
    WBTC_ROLL = 1
    USDC_ROLL = 2

    # Curvance Lending ABI
    LENDING_ABI = [
        {
            "inputs": [
                {
                    "components": [
                        {"name": "target", "type": "address"},
                        {"name": "allowFailure", "type": "bool"},
                        {"name": "callData", "type": "bytes"}
                    ],
                    "name": "calls",
                    "type": "tuple[]"
                }
            ],
            "name": "multicall",
            "outputs": [{"name": "", "type": "bytes[]"}],
            "stateMutability": "nonpayable",
            "type": "function",
            "funcSelector": "0xe8bbf5d7"
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

    # Deposit function ABI (used to encode callData)
    DEPOSIT_ABI = [
        {
            "inputs": [
                {"name": "amount", "type": "uint256"},
                {"name": "onBehalfOf", "type": "address"}
            ],
            "name": "deposit",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "nonpayable",
            "type": "function",
            "funcSelector": "0x2f4a61d9"
        }
    ]

    async def get_contract_addresses(self) -> Dict[str, str]:
        """Get Curvance contract addresses"""
        return {
            'wbtc': WBTC,              # WBTC token
            'cwbtc': CURVANCE_WBTC,    # Curvance WBTC market
            'usdc': CURVANCE_USDC_TOKEN,  # USDC token for Curvance
            'cusdc': CURVANCE_USDC,    # Curvance USDC market
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
            logger.info(f"Approved token spending for Curvance")
            return receipt

    async def get_token_balance(self, token_type: str) -> int:
        """Get token balance (WBTC or USDC) of the current account"""
        addresses = await self.get_contract_addresses()
        token = self._get_contract(addresses[token_type], ERC20_ABI)
        
        balance = token.functions.balanceOf(self.account.address).call()
        return balance

    async def deposit(self, amount: int = None) -> Dict:
        """
        Deposit WBTC or USDC into Curvance lending
        
        Args:
            amount: Optional amount to deposit. If None, will be randomly generated based on token type
        """
        try:
            # Roll to decide which token to deposit (1: WBTC, 2: USDC)
            token_roll = random.randint(1, 2)
            
            # Set token type and market based on roll
            if token_roll == self.WBTC_ROLL:
                token_type = 'wbtc'
                market_type = 'cwbtc'
                decimals = 8
                if amount is None:
                    amount = random.randint(MIN_LENDING_AMOUNT_WBTC, MAX_LENDING_AMOUNT_WBTC)
            else:  # USDC
                token_type = 'usdc'
                market_type = 'cusdc'
                decimals = 6
                if amount is None:
                    amount = random.randint(MIN_LENDING_AMOUNT_USDC, MAX_LENDING_AMOUNT_USDC)

            addresses = await self.get_contract_addresses()
            lending = self._get_contract(addresses[market_type], self.LENDING_ABI)
            
            # Check token balance
            balance = await self.get_token_balance(token_type)
            logger.info(f"Current {token_type.upper()} balance: {balance/10**decimals:.{decimals}f}")
            
            if balance < amount:
                raise Exception(f"Insufficient {token_type.upper()} balance. Have: {balance/10**decimals:.{decimals}f}, Need: {amount/10**decimals:.{decimals}f}")

            # Ensure token is approved
            approval_receipt = await self._ensure_token_approval(addresses[token_type], addresses[market_type], amount)
            
            if approval_receipt:
                await asyncio.sleep(5)
            
            # Double check allowance
            token = self._get_contract(addresses[token_type], ERC20_ABI)
            allowance = token.functions.allowance(self.account.address, addresses[market_type]).call()
            logger.info(f"Current {token_type.upper()} allowance for Curvance: {allowance/10**decimals:.{decimals}f}")

            # Create deposit call data
            deposit_contract = self.web3.eth.contract(abi=self.DEPOSIT_ABI)
            deposit_data = deposit_contract.encodeABI(
                fn_name='deposit',
                args=[amount, self.account.address]
            )

            # Build multicall transaction
            multicall_tx = lending.functions.multicall(
                [(addresses[market_type], False, deposit_data)]
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'gas': CURVANCE_DEPOSIT_GAS,
                'gasPrice': GAS_PRICE,
                'value': 0,
                'chainId': CHAIN_ID
            })

            # Log transaction details
            logger.info(f"Sending deposit transaction: amount={amount/10**decimals:.{decimals}f} {token_type.upper()}, gas={multicall_tx['gas']}")
            
            receipt = await self._build_and_send_transaction(multicall_tx)
            
            if receipt['status'] == 0:
                raise Exception(f"Transaction failed. Gas used: {receipt['gasUsed']}")
                
            return receipt
            
        except Exception as e:
            logger.error(f"Deposit failed: {str(e)}")
            raise
