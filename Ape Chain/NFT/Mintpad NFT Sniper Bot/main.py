from web3 import Web3
from eth_account import Account
import time
from dotenv import load_dotenv
import sys  
import os
import warnings
warnings.filterwarnings("ignore", category=Warning)

# Load environment variables
load_dotenv()

# Connect to ApeChain
w3 = Web3(Web3.HTTPProvider('https://rpc.apechain.com/http'))
print(f"Connected to ApeChain: {w3.is_connected()}")

# Global variables
CONTRACT_ADDRESS = None
MINT_AMOUNT = None
CHAIN_ID = 33139
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
if PRIVATE_KEY and PRIVATE_KEY.startswith('0x'):
    PRIVATE_KEY = PRIVATE_KEY[2:]  # Remove '0x' if present

# ABI for the mint function
ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "_receiver", "type": "address"},
            {"internalType": "uint256", "name": "_quantity", "type": "uint256"},
            {"internalType": "address", "name": "_currency", "type": "address"},
            {"internalType": "uint256", "name": "_pricePerToken", "type": "uint256"},
            {
                "components": [
                    {"internalType": "bytes32[]", "name": "proof", "type": "bytes32[]"},
                    {"internalType": "uint256", "name": "quantityLimitPerWallet", "type": "uint256"},
                    {"internalType": "uint256", "name": "pricePerToken", "type": "uint256"},
                    {"internalType": "address", "name": "currency", "type": "address"}
                ],
                "internalType": "struct IDrop.AllowlistProof",
                "name": "_allowlistProof",
                "type": "tuple"
            },
            {"internalType": "bytes", "name": "_data", "type": "bytes"}
        ],
        "name": "claim",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "transactionFee",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalMinted",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getActiveClaimConditionId",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_conditionId", "type": "uint256"}],
        "name": "getClaimConditionById",
        "outputs": [{
            "components": [
                {"internalType": "uint256", "name": "startTimestamp", "type": "uint256"},
                {"internalType": "uint256", "name": "maxClaimableSupply", "type": "uint256"},
                {"internalType": "uint256", "name": "supplyClaimed", "type": "uint256"},
                {"internalType": "uint256", "name": "quantityLimitPerWallet", "type": "uint256"},
                {"internalType": "bytes32", "name": "merkleRoot", "type": "bytes32"},
                {"internalType": "uint256", "name": "pricePerToken", "type": "uint256"},
                {"internalType": "address", "name": "currency", "type": "address"},
                {"internalType": "string", "name": "metadata", "type": "string"}
            ],
            "internalType": "struct IClaimCondition.ClaimCondition",
            "name": "condition",
            "type": "tuple"
        }],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "claimCondition",
        "outputs": [
            {"internalType": "uint256", "name": "currentStartId", "type": "uint256"},
            {"internalType": "uint256", "name": "count", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

def validate_setup():
    if not os.getenv('PRIVATE_KEY'):
        raise ValueError("PRIVATE_KEY not found in .env file")
    
    if not Web3.is_address(CONTRACT_ADDRESS):
        raise ValueError(f"Invalid contract address: {CONTRACT_ADDRESS}")
    
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to ApeChain")

def calculate_total_cost(mint_amount):
    try:
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
        
        # Get transaction fee from contract
        try:
            platform_fee = contract.functions.transactionFee().call()
        except Exception:
            try:
                platform_fee = contract.functions.getTransactionFee().call()
            except Exception:
                print("❌ Error: Could not read transaction fee from contract")
                return None, None, None
        
        # Use the NFT price that was set earlier (either from contract or manual input)
        nft_cost = NFT_PRICE * mint_amount
        total_cost = nft_cost + platform_fee
        
        return nft_cost, platform_fee, total_cost
    except Exception as e:
        print(f"Error calculating costs: {str(e)}")
        return None, None, None

def estimate_gas_cost(wallet_address, total_cost):
    try:
        # Get current gas price
        gas_price = w3.eth.gas_price
        estimated_gas = 300000  # Conservative gas estimate
        
        # Calculate estimated gas cost
        gas_cost = gas_price * estimated_gas
        
        print("\n⛽ Gas Estimate:")
        print(f"Gas Price: {Web3.from_wei(gas_price, 'gwei')} Gwei")
        print(f"Estimated Gas Units: {estimated_gas}")
        print(f"Estimated Gas Cost: {Web3.from_wei(gas_cost, 'ether')} APE")
        
        return gas_cost
    except Exception as e:
        print(f"Error estimating gas: {e}")
        return 0

def check_connection():
    try:
        account = Account.from_key(PRIVATE_KEY)
        wallet_address = account.address
        
        print(f"Using wallet address: {wallet_address}")
        
        balance = w3.eth.get_balance(wallet_address)
        print(f"Wallet Balance: {Web3.from_wei(balance, 'ether')} APE")
        
        # Calculate mint costs
        nft_cost, platform_fee, total_cost = calculate_total_cost(MINT_AMOUNT)
        
        # Estimate gas
        estimated_gas_cost = estimate_gas_cost(wallet_address, total_cost)
        
        print("\n Cost Breakdown:")
        print(f"NFT Cost ({MINT_AMOUNT} NFTs @ 1 APE): {Web3.from_wei(nft_cost, 'ether')} APE")
        print(f"Platform Fee (fixed): {Web3.from_wei(platform_fee, 'ether')} APE")
        print(f"Subtotal (excluding gas): {Web3.from_wei(total_cost, 'ether')} APE")
        print(f"Estimated Total (including gas): {Web3.from_wei(total_cost + estimated_gas_cost, 'ether')} APE")
        
        if balance < (total_cost + estimated_gas_cost):
            print("\n⚠️ WARNING: Insufficient balance for minting + gas!")
            return False
        else:
            print("\n✅ Balance sufficient for minting + gas")
            return True
            
    except Exception as e:
        print(f"Error checking connection: {str(e)}")
        return False

def simulate_mint():
    try:
        account = Account.from_key(PRIVATE_KEY)
        wallet_address = account.address
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
        
        nft_cost, tx_fee, total_cost = calculate_total_cost(MINT_AMOUNT)
        
        # Prepare allowlist proof with the correct price
        allowlist_proof = {
            "proof": [],
            "quantityLimitPerWallet": 0,
            "pricePerToken": nft_cost // MINT_AMOUNT,  # Calculate price per NFT
            "currency": "0x0000000000000000000000000000000000000000"
        }
        
        # Get current gas price
        gas_price = w3.eth.gas_price
        nonce = w3.eth.get_transaction_count(wallet_address)
        
        # Build transaction 
        transaction = contract.functions.claim(
            wallet_address,
            MINT_AMOUNT,
            "0x0000000000000000000000000000000000000000",
            nft_cost // MINT_AMOUNT,  # price per NFT
            allowlist_proof,
            "0x"
        ).build_transaction({
            'from': wallet_address,
            'value': total_cost,  # Total cost including fixed fee
            'gas': 300000,
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': CHAIN_ID
        })
        
        print("✅ Transaction built successfully!")
        print(f"Estimated total cost: {Web3.from_wei(total_cost, 'ether')} APE")
        return True
    except Exception as e:
        print(f"❌ Error building transaction: {e}")
        return False

def mint_nfts():
    try:
        account = Account.from_key(PRIVATE_KEY)
        wallet_address = account.address
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
        
        # Calculate costs
        nft_cost, platform_fee, total_cost = calculate_total_cost(MINT_AMOUNT)
        price_per_token = nft_cost // MINT_AMOUNT  # Calculate price per NFTs
        
        # Prepare allowlist proof structure with correct price
        allowlist_proof = {
            "proof": [Web3.to_bytes(hexstr="0x0000000000000000000000000000000000000000000000000000000000000000")],
            "quantityLimitPerWallet": 50,
            "pricePerToken": price_per_token, 
            "currency": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
        }
        
        print("Building transaction...")
        tx = contract.functions.claim(
            wallet_address,   
            MINT_AMOUNT,      
            "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",  
            price_per_token,  
            allowlist_proof,  
            "0x"            
        ).build_transaction({
            'from': wallet_address,
            'value': total_cost,
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(wallet_address),
            'chainId': CHAIN_ID
        })
        
        print("Signing transaction...")
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        
        print("Sending transaction...")
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"Transaction sent! Hash: {tx_hash.hex()}")
        
        print("Waiting for receipt...")
        receipt = wait_for_transaction(tx_hash)
        if receipt and receipt.status == 1:
            print(f"Successfully minted! Tx: {tx_hash.hex()}")
        else:
            print("Mint failed!")
            if receipt:
                print(f"Receipt status: {receipt.status}")
                
    except Exception as e:
        print(f"Error during minting: {str(e)}")
        print("Full error details:", e)

def test_setup():
    print("🔍 Testing Setup...")
    print("-" * 50)
    
    # Test 1: Connection
    print("\n1. Testing Connection")
    check_connection()
    
    print("\n2. Testing Transaction Building")
    simulate_mint()
    
    print("\n3. Checking Mint Status")
    check_mint_status()
    
    print("\n" + "-" * 50)

def check_mint_status():
    try:
        # Create contract instance
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
        
        try:
            is_active = contract.functions.isMintActive().call()
            print(f"Mint Status: {'Active' if is_active else 'Not Active'}")
        except:
            print("isMintActive() function not found in contract")
        
        try:
            price = contract.functions.pricePerToken().call()
            print(f"Mint Price: {Web3.from_wei(price, 'ether')} APE")
        except:
            print("pricePerToken() function not found in contract")
        
        return True
    except Exception as e:
        print(f"Error checking mint status: {e}")
        return False

def estimate_gas_price():
    try:
        gas_price = w3.eth.gas_price
        return int(gas_price * 1.1)  # Add 10% buffer
    except Exception as e:
        print(f"Error estimating gas price: {e}")
        return None

def wait_for_transaction(tx_hash):
    try:
        return w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    except Exception as e:
        print(f"Error waiting for transaction: {e}")
        return None

def get_user_inputs():
    print("\n=== Mint Configuration ===")
    
    # Get contract address (required)
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        try:
            contract_input = input("Enter contract address: ").strip()
            
            if contract_input:
                try:
                    contract_address = Web3.to_checksum_address(contract_input)
                    break
                except:
                    print("Invalid contract address. Please try again.")
                    attempt += 1
            else:
                print("Contract address cannot be empty.")
                attempt += 1
                
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled by user.")
            sys.exit(1)
    
    # Get mint amount
    attempt = 0
    while attempt < max_attempts:
        try:
            mint_amount = int(input("Enter number of NFTs to mint (1-50): "))
            if 1 <= mint_amount <= 50:
                break
            print("Please enter a number between 1 and 50.")
            attempt += 1
            
        except ValueError:
            print("Please enter a valid number.")
            attempt += 1
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled by user.")
            sys.exit(1)
    
    # Get gas settings (optional)
    attempt = 0
    while attempt < max_attempts:
        try:
            gas_input = input("Enter custom gas price in Gwei (or press Enter for automatic): ").strip()
            
            if not gas_input:
                gas_price = None
                break
            gas_price = Web3.to_wei(float(gas_input), 'gwei')
            break
            
        except ValueError:
            print("Please enter a valid number.")
            attempt += 1
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled by user.")
            sys.exit(1)
    
    return {
        'contract_address': contract_address,
        'mint_amount': mint_amount,
        'gas_price': gas_price
    }

def check_contract_details(contract_address):
    try:
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
        print("\n📄 NFTs Details:")
        
        # Try to get project name
        try:
            name = contract.functions.name().call()
            print(f"Project Name: {name}")
        except Exception:
            print("Could not read project name")
        
        # Try to get NFT price from contract
        nft_price = None
        try:
            # Method 1: Try active claim condition
            active_condition_id = contract.functions.getActiveClaimConditionId().call()
            claim_condition = contract.functions.getClaimConditionById(active_condition_id).call()
            nft_price = claim_condition[5]  
            print(f"NFT Price: {Web3.from_wei(nft_price, 'ether')} APE")
        except Exception:
            try:
                # Method 2: Try getting current claim condition
                claim_condition = contract.functions.claimCondition().call()
                current_start_id = claim_condition[0]  
                condition = contract.functions.getClaimConditionById(current_start_id).call()
                nft_price = condition[5]  
                print(f"NFT Price: {Web3.from_wei(nft_price, 'ether')} APE")
            except Exception:
                # If can't read from contract, ask user for input
                max_attempts = 3
                attempt = 0
                while attempt < max_attempts:
                    try:
                        price_input = input("Could not read NFT price from contract. Enter NFT price in APE (press Enter for free mint or enter 0 for free): ").strip()
                        
                        # Handle free mint cases
                        if price_input == "" or price_input == "0":
                            nft_price = 0
                            print("NFT Price: 0 APE (Free Mint)")
                            break
                        
                        # Handle paid mint cases
                        price_float = float(price_input)
                        if price_float >= 0:
                            nft_price = Web3.to_wei(price_float, 'ether')
                            print(f"NFT Price: {price_float} APE (manually set)")
                            break
                        print("Please enter a valid price (must be 0 or greater).")
                        attempt += 1
                    except ValueError:
                        print("Please enter a valid number or press Enter for free mint.")
                        attempt += 1
                    except (EOFError, KeyboardInterrupt):
                        print("\nOperation cancelled by user.")
                        sys.exit(1)
                
                if attempt >= max_attempts:
                    print("\nToo many failed attempts. Exiting...")
                    sys.exit(1)
        
        # Try to get transaction fee
        try:
            fee = contract.functions.transactionFee().call()
            print(f"Transaction Fee: {Web3.from_wei(fee, 'ether')} APE")
        except Exception:
            try:
                fee = contract.functions.getTransactionFee().call()
                print(f"Transaction Fee: {Web3.from_wei(fee, 'ether')} APE")
            except Exception:
                print("Could not read transaction fee")
        
        # Try to get total minted
        try:
            total_minted = contract.functions.totalMinted().call()
            print(f"Total Minted: {total_minted} NFTs")
        except Exception:
            print("Could not read total minted")
        
        # Try to get max supply
        try:
            max_supply = contract.functions.maxTotalSupply().call()
            print(f"Max Supply: {max_supply} NFTs")
            if 'total_minted' in locals():
                print(f"Remaining: {max_supply - total_minted} NFTs")
        except Exception:
            pass
        
        return nft_price
    except Exception as e:
        print(f"Error checking contract details: {str(e)}")
        return None

# Main execution
if __name__ == "__main__":
    try:
        choice = input("Enter 'test' to run tests or 'mint' to perform actual mint: ").lower()
        
        if choice == 'test':
            test_setup()
        elif choice == 'mint':
            config = get_user_inputs()
            
            # Update global variables
            CONTRACT_ADDRESS = config['contract_address']
            MINT_AMOUNT = config['mint_amount']
            
            # Get NFT price from contract
            NFT_PRICE = check_contract_details(CONTRACT_ADDRESS)
            if NFT_PRICE is None:
                print("Could not determine NFT price. Aborting.")
                sys.exit(1)
            
            # Format gas price string
            gas_price_str = 'Auto'
            if config['gas_price'] is not None:
                gas_price_str = f"{Web3.from_wei(config['gas_price'], 'gwei')} Gwei"
            
            # Confirm settings before proceeding
            print("\n=== Mint Settings ===")
            print(f"Contract: {CONTRACT_ADDRESS}")
            print(f"Amount to mint: {MINT_AMOUNT}")
            print(f"Gas Price: {gas_price_str}")
            
            if input("\nProceed with mint? (y/n): ").lower() == 'y':
                mint_nfts()
            else:
                print("Mint cancelled.")
        else:
            print("Invalid choice. Please enter either 'test' or 'mint'")
            
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled by user.")
        sys.exit(1)
