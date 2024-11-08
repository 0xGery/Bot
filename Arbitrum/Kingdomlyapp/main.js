const ethers = require('ethers');
const readline = require('readline');
require('dotenv').config();

// Constants
const GAS_LIMIT = 284000;

// RPC endpoints list   
const RPC_ENDPOINTS = [
    'https://arbitrum.drpc.org',           // 73ms
    'https://arbitrum.blockpi.network/v1/rpc/public', // 78ms
    'https://rpc.ankr.com/arbitrum',       // 144ms
    'https://arb1.arbitrum.io/rpc',        // 347ms
    'https://arbitrum.llamarpc.com',       // 523ms
    'https://1rpc.io/arb'                  // 619ms
];

// ABI
const ABI = [
    "function batchMint(uint256 amount, uint256 mintId) payable returns (uint256)",
    "function mintLive() view returns (bool)",
    "function threeDollarsEth() view returns (uint256)",
    "function activeMintGroups(uint256) view returns (uint256)",
    "function contractPresaleActive(uint256) view returns (bool)"
];

// Function to get user input
async function getUserInput() {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    const question = (query) => new Promise((resolve) => rl.question(query, resolve));

    console.log("\n=== Precision Mint Bot Configuration ===");
    const contractAddress = await question("Enter contract address: ");
    
    console.log("\nMint Stage Options:");
    console.log("0. Stage 0");
    console.log("1. Stage 1");
    console.log("2. Stage 2");
    const mintStage = await question("Choose mint stage (0, 1, or 2): ");
    
    console.log("\nMint Time Setup Options:");
    console.log("1. UTC Time");
    console.log("2. Block Number");
    const timeOption = await question("Choose option (1 or 2): ");

    let targetTime;
    let targetBlock;

    if (timeOption === "1") {
        const utcTime = await question("Enter UTC time (format: YYYY-MM-DD HH:mm:ss): ");
        targetTime = new Date(utcTime);
    } else {
        targetBlock = await question("Enter target block number: ");
    }

    rl.close();
    return { contractAddress, mintStage, timeOption, targetTime, targetBlock };
}

class PrecisionMintBot {
    constructor(privateKey, walletId, contractAddress, mintStage) {
        this.currentProviderIndex = 0;
        this.providers = RPC_ENDPOINTS.map(endpoint => new ethers.JsonRpcProvider(endpoint));
        this.wallet = new ethers.Wallet(privateKey);
        this.walletId = walletId;
        this.contractAddress = contractAddress;
        this.mintStage = mintStage;
        this.mintAttempted = false;
    }

    async getFastestProvider() {
        const latencies = await Promise.all(
            this.providers.map(async (provider, index) => {
                const start = Date.now();
                try {
                    await provider.getBlockNumber();
                    return { index, latency: Date.now() - start };
                } catch (e) {
                    return { index, latency: Infinity };
                }
            })
        );
        
        const fastest = latencies.sort((a, b) => a.latency - b.latency)[0];
        return this.providers[fastest.index];
    }

    async getMintCost() {
        if (this.mintCost === null) {
            try {
                // Get the threeDollarsEth value directly from the contract
                this.mintCost = await this.contracts[0].threeDollarsEth();
                console.log(`Wallet ${this.walletId} - Mint cost (threeDollarsEth): ${ethers.formatEther(this.mintCost)} ETH`);
            } catch (error) {
                console.error(`Wallet ${this.walletId} - Error getting mint cost:`, error.message);
                throw error;
            }
        }
        return this.mintCost;
    }

    async checkMintStatus() {
        try {
            const provider = this.getNextProvider();
            const contract = new ethers.Contract(this.contractAddress, ABI, this.wallet.connect(provider));
            
            // Check specific mint stage
            const isMintActive = await contract.contractPresaleActive(this.mintStage);
            
            if (!isMintActive) {
                console.log(`Wallet ${this.walletId} - Stage ${this.mintStage} mint not live yet`);
            }
            
            return isMintActive;
        } catch (error) {
            console.error(`Wallet ${this.walletId} - Error checking mint status:`, error.message);
            return false;
        }
    }

    async mint() {
        if (this.mintAttempted) return false;
        this.mintAttempted = true;

        try {
            const provider = this.getNextProvider();
            const contract = new ethers.Contract(this.contractAddress, ABI, this.wallet.connect(provider));
            
            const nonce = await provider.getTransactionCount(this.wallet.address);
            const latestMintCost = await contract.threeDollarsEth();

            const tx = await contract.batchMint(
                1, // amount
                Number(this.mintStage), // mintId based on user input
                {
                    value: latestMintCost,
                    gasLimit: GAS_LIMIT,
                    nonce,
                    maxFeePerGas: ethers.parseUnits("0.0135", "gwei"),
                    maxPriorityFeePerGas: ethers.parseUnits("0", "gwei"),
                    type: 2
                }
            );

            console.log(`Wallet ${this.walletId} - Mint TX sent! Hash: ${tx.hash}`);
            const receipt = await tx.wait();
            console.log(`Wallet ${this.walletId} - Mint successful! Block: ${receipt.blockNumber}`);
            return true;
        } catch (error) {
            console.error(`Wallet ${this.walletId} - Mint error:`, error.message);
            return false;
        }
    }

    async waitForMintTime(targetTime, targetBlock) {
        console.log(`\nWallet ${this.walletId} - Waiting for mint time...`);
        
        if (targetTime) {
            const now = new Date();
            const timeUntilMint = targetTime - now;
            
            if (timeUntilMint > 5000) { // If more than 5 seconds until mint
                console.log(`Wallet ${this.walletId} - Sleeping until 5 seconds before mint time`);
                await new Promise(r => setTimeout(r, timeUntilMint - 5000));
            }
            
            // Precision waiting for last 5 seconds
            while (new Date() < targetTime) {
                await new Promise(r => setTimeout(r, 1)); // 1ms precision
            }
        } else {
            const provider = this.getNextProvider();
            while (true) {
                const currentBlock = await provider.getBlockNumber();
                if (currentBlock >= targetBlock - 1) {
                    break;
                }
                await new Promise(r => setTimeout(r, 500)); // Check every 500ms
            }
            
            // Precision monitoring for target block
            while (true) {
                const currentBlock = await provider.getBlockNumber();
                if (currentBlock >= targetBlock) {
                    break;
                }
                await new Promise(r => setTimeout(r, 1)); // 1ms precision
            }
        }
    }

    async monitorWithPrecision(targetTime, targetBlock) {
        console.log(`Wallet ${this.walletId} - Starting monitoring with address: ${this.wallet.address}`);
        
        // Wait for mint time
        await this.waitForMintTime(targetTime, targetBlock);
        
        // Execute mint immediately when time is reached
        console.log(`Wallet ${this.walletId} - MINT TIME REACHED! Executing...`);
        await this.mint();
    }
}

async function main() {
    const { contractAddress, mintStage, timeOption, targetTime, targetBlock } = await getUserInput();

    // Create bot instances with mint stage
    const bots = [
        new PrecisionMintBot(process.env.PRIVATE_KEY_1, "1", contractAddress, mintStage),
        new PrecisionMintBot(process.env.PRIVATE_KEY_2, "2", contractAddress, mintStage),
        new PrecisionMintBot(process.env.PRIVATE_KEY_3, "3", contractAddress, mintStage),
        new PrecisionMintBot(process.env.PRIVATE_KEY_4, "4", contractAddress, mintStage),
        new PrecisionMintBot(process.env.PRIVATE_KEY_5, "5", contractAddress, mintStage)
    ];

    // Display configuration
    console.log("\n=== Mint Configuration ===");
    console.log(`Contract Address: ${contractAddress}`);
    console.log(`Mint Stage: ${mintStage}`);
    if (targetTime) {
        console.log(`Target UTC Time: ${targetTime.toUTCString()}`);
        const timeUntilMint = targetTime - new Date();
        console.log(`Time until mint: ${(timeUntilMint / 1000).toFixed(2)} seconds`);
    } else {
        console.log(`Target Block: ${targetBlock}`);
    }
    console.log("\nStarting precision mint monitoring...");

    // Start bots with minimal delays
    await Promise.all(
        bots.map((bot, index) => 
            new Promise(r => setTimeout(r, index * 20))
                .then(() => bot.monitorWithPrecision(targetTime, targetBlock))
        )
    );
}

main().catch(console.error);
