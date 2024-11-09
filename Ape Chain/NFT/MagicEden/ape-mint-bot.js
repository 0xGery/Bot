const ethers = require('ethers');
require('dotenv').config();

const CHAIN_ID = 33139;
const CONTRACT_ADDRESS = 'input sc';
const APE_PRICE = ethers.parseUnits("input price", "ether");

// Only keep the working RPCs
const RPC_ENDPOINTS = [
    'https://rpc.apechain.com/http',
    'https://apechain.rpc.thirdweb.com'
];

const ABI = [
    "function mint(uint32 qty, bytes32[] proof, uint64 timestamp, bytes signature) payable",
    "function getStageInfo(uint256 index) view returns (tuple(uint80 price, uint80 mintFee, uint32 walletLimit, bytes32 merkleRoot, uint24 maxStageSupply, uint64 startTimeUnixSeconds, uint64 endTimeUnixSeconds), uint32, uint256)"
];

class WarMintBot {
    constructor(privateKey) {
        this.wallet = new ethers.Wallet(privateKey);
        this.activeProviders = [];
        this.mintAttempted = false;
        
        const now = new Date();
        this.targetTime = new Date(Date.UTC(
            now.getUTCFullYear(),
            now.getUTCMonth(),
            now.getUTCDate(),
            15, 0, 0, 1
        ));
    }

    async initializeProviders() {
        console.log("Initializing RPCs...");
        
        const providerPromises = RPC_ENDPOINTS.map(async (endpoint, index) => {
            try {
                const provider = new ethers.JsonRpcProvider(endpoint, {
                    chainId: CHAIN_ID,
                    name: 'ApeChain'
                });

                // Test the connection
                await provider.getBlockNumber();
                
                const connectedWallet = this.wallet.connect(provider);
                const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, connectedWallet);
                
                console.log(`✅ RPC ${index + 1}: Connected`);
                return {
                    provider,
                    wallet: connectedWallet,
                    contract
                };
            } catch (error) {
                console.log(`❌ RPC ${index + 1}: Failed`);
                return null;
            }
        });

        // Wait for all provider tests to complete
        const results = await Promise.all(providerPromises);
        this.activeProviders = results.filter(result => result !== null);

        if (this.activeProviders.length === 0) {
            throw new Error("No working RPCs found! Check your connection.");
        }

        console.log(`\n${this.activeProviders.length} RPCs ready for war mint`);
        
        // Pre-warm connections
        await Promise.all(this.activeProviders.map(async ({contract}) => {
            try {
                await contract.getStageInfo(1);
            } catch (error) {
                // Ignore errors during pre-warm
            }
        }));
    }

    async mint() {
        if (this.mintAttempted) return false;
        this.mintAttempted = true;

        // Number of retry attempts
        const MAX_RETRIES = 3;
        let retryCount = 0;

        while (retryCount < MAX_RETRIES) {
            const mintTimestamp = BigInt(Math.floor(Date.now() / 1000));  // Fresh timestamp each try

            const mintPromises = this.activeProviders.map(async ({contract, provider, wallet}, index) => {
                try {
                    const [nonce, feeData] = await Promise.all([
                        provider.getTransactionCount(wallet.address),
                        provider.getFeeData()
                    ]);

                    const tx = await contract.mint(
                        {input amount},              
                        [],            
                        mintTimestamp, 
                        "0x",         
                        {
                            value: APE_PRICE * 2n,
                            gasLimit: 160000,
                            maxFeePerGas: ethers.parseUnits("25.42069", "gwei"),
                            maxPriorityFeePerGas: ethers.parseUnits("25.42069", "gwei"),
                            type: 2,
                            nonce
                        }
                    );
                    
                    console.log(`🚀 WAR MINT TX SENT via RPC ${index + 1}! Hash: ${tx.hash}`);
                    return tx;
                } catch (error) {
                    if (error.message.includes("NotMintable")) {
                        console.log("❌ Minting not active yet");
                    } else if (error.message.includes("NoSupplyLeft")) {
                        console.log("❌ No supply left");
                        return null; // Don't retry if no supply
                    } else if (error.message.includes("WalletGlobalLimitExceeded")) {
                        console.log("❌ Wallet limit exceeded");
                        return null; // Don't retry if limit exceeded
                    } else if (error.message.includes("NotEnoughValue")) {
                        console.log("❌ Insufficient APE for mint");
                        return null; // Don't retry if insufficient funds
                    } else {
                        console.log(`RPC ${index + 1} mint failed:`, error.message);
                        return null;
                    }
                }
            });

            try {
                const result = await Promise.race([
                    Promise.any(mintPromises),
                    new Promise((_, reject) => setTimeout(() => reject(new Error("Timeout")), 1500))
                ]);

                if (result) return result; // Successful mint
            } catch (e) {
                console.log(`❌ Attempt ${retryCount + 1} failed. ${MAX_RETRIES - retryCount - 1} retries left`);
                retryCount++;
                
                if (retryCount < MAX_RETRIES) {
                    console.log("🔄 Retrying...");
                    await new Promise(r => setTimeout(r, 100)); // Small delay between retries
                }
            }
        }

        console.log("❌ All mint attempts exhausted");
        return null;
    }

    async execute() {
        console.log("\n=== 🔥 APE WAR MINT INITIALIZED 🔥 ===");
        console.log(`Target Time (UTC): ${this.targetTime.toUTCString()}`);
        console.log(`Target Time (WIB): ${this.targetTime.toLocaleString('en-US', { timeZone: 'Asia/Jakarta' })}`);
        console.log(`Wallet: ${this.wallet.address}`);
        console.log(`Price: 66 APE (2 NFTs)\n`);

        await this.initializeProviders();

        // Dynamic countdown with HH:MM:SS.ms format
        const updateInterval = setInterval(() => {
            const now = Date.now();
            const timeUntilMint = this.targetTime.getTime() - now;
            
            if (timeUntilMint > 0) {
                const hours = Math.floor(timeUntilMint / 3600000);
                const minutes = Math.floor((timeUntilMint % 3600000) / 60000);
                const seconds = Math.floor((timeUntilMint % 60000) / 1000);
                const milliseconds = timeUntilMint % 1000;

                process.stdout.write(
                    `\r⏳ T-minus ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${milliseconds.toString().padStart(3, '0')}     `
                );
            }
        }, 10); // Update every 10ms for smoother milliseconds display

        const timeUntilMint = this.targetTime.getTime() - Date.now();
        if (timeUntilMint > 50) {
            await new Promise(r => setTimeout(r, timeUntilMint - 50));
        }

        // Clear the interval before final countdown
        clearInterval(updateInterval);
        console.log("\n"); // New line after countdown

        // Ultra-precise final countdown
        while (Date.now() < this.targetTime.getTime()) {
            const remaining = this.targetTime.getTime() - Date.now();
            if (remaining > 10) {
                await new Promise(r => setTimeout(r, 2));
            } else {
                await new Promise(r => setTimeout(r, 1));
            }
        }

        console.log("⚔️ EXECUTING WAR MINT!");
        return await this.mint();
    }
}

async function main() {
    if (!process.env.PRIVATE_KEY) {
        console.error("❌ Set PRIVATE_KEY in .env file");
        return;
    }

    const bot = new WarMintBot(process.env.PRIVATE_KEY);
    await bot.execute();
}

main().catch(console.error);
