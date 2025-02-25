from web3 import Web3

# Chain settings
CHAIN_ID = 10143  # Monad Testnet

# Gas settings
GAS_PRICE = 65_000_000_000  # 65 gwei (0xf224d4a00)
APPROVAL_GAS = 70000  # Gas for token approvals (from successful tx)
WRAPPER_GAS = 100_000  # Gas for wrap/unwrap operations
SUMER_DEPOSIT_GAS = 350_000  # Gas for Sumer deposits
SUMER_WITHDRAW_GAS = 350_000  # Gas for Sumer withdrawals (from successful tx)
NOSTRA_DEPOSIT_GAS = 450_000  # Gas for Nostra deposits
NOSTRA_WITHDRAW_GAS = 450_000  # Gas for Nostra withdrawals
KINZA_DEPOSIT_GAS = 300_000  # Gas for Kinza deposits 
KINZA_WITHDRAW_GAS = 300_000  # Gas for Kinza withdrawals (from successful tx)
CURVANCE_DEPOSIT_GAS = 340_000  # Gas for Curvance deposits (from successful tx)
KINTSU_STAKE_GAS = 130_000  # Gas for Kintsu staking (from successful tx)
APRIORI_STAKE_GAS = 90_000  # Gas for Apriori staking (0x13cd6 from successful tx)
MAGMA_STAKE_GAS = 150_000    # Gas limit for Magma stake

# Contract addresses
USDC = Web3.to_checksum_address('0xf817257fed379853cDe0fa4F97AB987181B1E5Ea')  # USDC token for Sumer/Nostra/Kinza
WMON = Web3.to_checksum_address('0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701')
SUMER_LENDING = Web3.to_checksum_address('0x25b13e42763a97dd4041f595220642b593962356')
NOSTRA_LENDING = Web3.to_checksum_address('0x2904160c12098d248a5838920fbc2cd1849bc438')
KINZA_LENDING = Web3.to_checksum_address('0x590b03d84441c1277f32784d1fbc22fe18b1eee0')
WBTC = '0x6BB379A2056d1304E73012b99338F8F581eE2E18'  # WBTC token
CURVANCE_USDC_TOKEN = '0x5D876D73f4441D5f2438B1A3e2A51771B337F27A'  # USDC token for Curvance
CURVANCE_WBTC = '0xcDA16E9c25f429F4B01A87Ff302Ee7943F2D5015'  # Curvance WBTC market
CURVANCE_USDC = '0x9E7EbD0f8255F3A910Bc77FD006A410E9D54EE36'  # Curvance USDC market
KINTSU_STAKING = Web3.to_checksum_address('0x07aabd925866e8353407e67c1d157836f7ad923e')  # Kintsu staking contract
APRIORI_STAKING = Web3.to_checksum_address('0xb2f82d0f38dc453d596ad40a37799446cc89274a')  # Apriori staking contract
APRMON = Web3.to_checksum_address('0xb2f82d0f38dc453d596ad40a37799446cc89274a')  # aprMON token (same as staking contract)
SMON = Web3.to_checksum_address('0x07aabd925866e8353407e67c1d157836f7ad923e')  # sMON token (same as staking contract)
MAGMA_STAKING = Web3.to_checksum_address('0x2c9c959516e9aaedb2c748224a41249202ca8be7')  # Magma staking contract
GMON = Web3.to_checksum_address('0xaeef2f6b429cb59c9b2d7bb2141ada993e8571c3')          # gMON token

# Transaction settings
DEFAULT_REFERRAL_CODE = 0  # Default referral code for lending protocols

# Balance requirements
MIN_BALANCE_MON = Web3.to_wei(0.01, 'ether')  # Minimum 0.01 MON required
MIN_BALANCE_USDC = 200000  # Minimum 0.2 USDC required
MIN_BALANCE_WBTC = 1000  # Minimum 0.000001 WBTC required (1 satoshi = 100)

# Lending amounts
MIN_LENDING_AMOUNT_USDC = 2000  # Minimum deposit amount of 0.002 USDC
MAX_LENDING_AMOUNT_USDC = 2000  # Maximum deposit amount of 0.02 USDC
MIN_LENDING_AMOUNT_WBTC = 1000  # Minimum deposit amount of 0.000001 WBTC
MAX_LENDING_AMOUNT_WBTC = 1000  # Maximum deposit amount of 0.00001 WBTC

# Staking amounts
MIN_STAKE_AMOUNT_MON = Web3.to_wei(0.01, 'ether')  # Minimum stake amount of 0.01 MON
MAX_STAKE_AMOUNT_MON = Web3.to_wei(0.01, 'ether')  # Maximum stake amount of 0.01 MON

# Protocol-specific amounts will use random values between MIN and MAX:
SUMER_LENDING_AMOUNT = None  # Will be randomly generated between MIN and MAX
NOSTRA_LENDING_AMOUNT = None  # Will be randomly generated between MIN and MAX
KINZA_LENDING_AMOUNT = None  # Will be randomly generated between MIN and MAX
CURVANCE_LENDING_AMOUNT = None  # Will be randomly generated between MIN and MAX
KINTSU_STAKE_AMOUNT = None  # Will be randomly generated between MIN and MAX

# Common ABIs
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