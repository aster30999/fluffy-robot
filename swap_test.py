#!/usr/bin/env python3
"""
Solana Devnet Swap Test Script
Performs SOL to USDC swap using Jupiter API V6 (stable)

Uses predefined test wallet from wallet-1-keypair.json

Requirements:
    pip install -r requirements.txt

Usage:
    python swap_test.py

Features:
    - Uses predefined test wallet
    - Requests Devnet SOL via airdrop
    - Performs SOL -> USDC swap using Jupiter API V6
    - Displays balances before/after swap
    - Shows transaction details
"""

import asyncio
import os
import base58
import json
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.signature import Signature
import httpx

# Configuration
DEVNET_RPC_URL = "https://api.devnet.solana.com"
JUPITER_API_URL = "https://quote-api.jup.ag/v6"
SOL_MINT = "So11111111111111111111111111111111111111112"  # SOL
USDC_MINT = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"  # USDC Devnet

# Predefined test wallet from ~/wallet-1-keypair.json
TEST_WALLET_SECRET_KEY = [
    21,173,82,149,254,53,244,45,76,83,122,87,69,48,52,14,
    171,255,204,65,114,110,37,38,147,24,98,206,124,142,250,251,
    83,35,13,89,102,161,10,217,163,39,32,27,102,48,255,182,
    210,50,248,207,42,238,97,67,121,234,181,132,191,7,209,120
]


def get_test_wallet() -> Keypair:
    """Get the predefined test wallet from secret key"""
    secret_key_bytes = bytes(TEST_WALLET_SECRET_KEY)
    return Keypair.from_bytes(secret_key_bytes)


async def get_sol_balance(client: AsyncClient, wallet: Keypair) -> float:
    """Get SOL balance for a wallet"""
    balance = await client.get_balance(wallet.pubkey(), commitment=Processed)
    return balance.value / 10**9


async def get_token_balance(client: AsyncClient, wallet: Keypair, mint: Pubkey) -> float:
    """Get SPL token balance for a wallet"""
    try:
        # Use dict instead of TokenAccountOpts for better compatibility
        token_accounts = await client.get_token_accounts_by_owner(
            wallet.pubkey(),
            opts={"mint": mint}  # Using dict instead of TokenAccountOpts
        )
        
        if token_accounts.value:
            account_info = token_accounts.value[0]
            account_data = base58.b58decode(account_info.account.data[0])
            amount_bytes = account_data[64:72]
            amount = int.from_bytes(amount_bytes, byteorder='little')
            return amount / 10**6  # USDC has 6 decimals
        return 0.0
    except Exception as e:
        print(f"Error getting token balance: {e}")
        return 0.0


async def request_airdrop(client: AsyncClient, wallet: Keypair, amount: float = 1.0) -> Optional[str]:
    """Request SOL airdrop on Devnet with retry logic"""
    print(f"Requesting {amount} SOL airdrop...")
    
    lamports = int(amount * 10**9)
    
    for attempt in range(3):  # Max 3 attempts
        try:
            response = await client.request_airdrop(
                wallet.pubkey(), lamports, commitment=Processed
            )
            signature = response.value
            await client.confirm_transaction(signature, commitment=Processed)
            print(f"✅ Airdrop successful!")
            print(f"   Transaction: https://explorer.solana.com/tx/{signature}?cluster=devnet")
            return signature
        except Exception as e:
            if attempt < 2:
                print(f"   Attempt {attempt + 1} failed, retrying... ({e})")
                await asyncio.sleep(5)
            else:
                print(f"❌ Airdrop failed after 3 attempts: {e}")
                return None
    return None


async def get_jupiter_quote(input_mint: str, output_mint: str, amount: int, slippage: float = 1.0) -> dict:
    """Get swap quote from Jupiter API V6"""
    async with httpx.AsyncClient() as http_client:
        quote_url = f"{JUPITER_API_URL}/quote?inputMint={input_mint}&outputMint={output_mint}&amount={amount}&slippageBps={int(slippage * 100)}"
        
        response = await http_client.get(quote_url)
        response.raise_for_status()
        
        return response.json()


async def perform_swap(client: AsyncClient, wallet: Keypair, amount: float = 0.1) -> Optional[str]:
    """Perform SOL to USDC swap using Jupiter API V6"""
    print(f"Swapping {amount} SOL to USDC...")
    
    try:
        # Convert SOL amount to lamports (Jupiter expects lamports for SOL)
        sol_amount_lamports = int(amount * 10**9)
        
        # Step 1: Get quote
        print("   Getting quote from Jupiter API...")
        quote = await get_jupiter_quote(SOL_MINT, USDC_MINT, sol_amount_lamports, slippage=1.0)
        
        if not quote.get("setupTransaction"):
            print("   No setup transaction needed")
        
        # Step 2: Get swap transaction
        print("   Getting swap transaction...")
        swap_url = f"{JUPITER_API_URL}/swap"
        swap_payload = {
            "quoteResponse": quote,
            "userPublicKey": str(wallet.pubkey()),
            "wrapAndUnwrapSol": True
        }
        
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(swap_url, json=swap_payload)
            response.raise_for_status()
            swap_data = response.json()
        
        # Step 3: Sign and send transaction
        print("   Signing and sending transaction...")
        
        # Deserialize transaction
        swap_transaction = VersionedTransaction.deserialize(bytes.fromhex(swap_data["swapTransaction"]))
        
        # Sign transaction
        swap_transaction.sign([wallet])
        
        # Send transaction
        signature = await client.send_transaction(swap_transaction, max_retries=3)
        
        print(f"✅ Swap successful!")
        print(f"   Transaction: https://explorer.solana.com/tx/{signature.value}?cluster=devnet")
        return signature.value
        
    except Exception as e:
        print(f"❌ Swap failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main function to execute the swap test"""
    print("=== Solana Devnet Swap Test ===\n")
    
    # Load environment variables
    load_dotenv()
    
    # Use the predefined test wallet
    wallet = get_test_wallet()
    print(f"Using test wallet: {wallet.pubkey()}")
    print(f"Wallet address: {wallet.pubkey()}")
    
    # Initialize Solana client
    rpc_url = os.getenv("SOLANA_RPC_URL", DEVNET_RPC_URL)
    client = AsyncClient(rpc_url, commitment=Processed)
    
    try:
        # Check initial balances
        print("\nChecking initial balances...")
        sol_balance_before = await get_sol_balance(client, wallet)
        usdc_balance_before = await get_token_balance(client, wallet, Pubkey.from_string(USDC_MINT))
        
        print(f"SOL balance before swap: {sol_balance_before:.6f} SOL")
        print(f"USDC balance before swap: {usdc_balance_before:.6f} USDC")
        
        # Request airdrop if needed
        if sol_balance_before < 0.5:
            print("\nSOL balance too low, requesting airdrop...")
            await request_airdrop(client, wallet, 1.0)
            await asyncio.sleep(5)
            sol_balance_before = await get_sol_balance(client, wallet)
            print(f"SOL balance after airdrop: {sol_balance_before:.6f} SOL")
        
        print()
        
        # Perform swap
        swap_amount = 0.1
        if sol_balance_before >= swap_amount:
            signature = await perform_swap(client, wallet, swap_amount)
            
            if signature:
                await asyncio.sleep(10)
            
            # Check balances after swap
            print("\nChecking balances after swap...")
            sol_balance_after = await get_sol_balance(client, wallet)
            usdc_balance_after = await get_token_balance(client, wallet, Pubkey.from_string(USDC_MINT))
            
            print(f"SOL balance after swap: {sol_balance_after:.6f} SOL")
            print(f"USDC balance after swap: {usdc_balance_after:.6f} USDC")
            
            # Calculate changes
            sol_change = sol_balance_before - sol_balance_after
            usdc_change = usdc_balance_after - usdc_balance_before
            
            print(f"\n=== Summary ===")
            print(f"SOL spent: {sol_change:.6f} SOL")
            print(f"USDC received: {usdc_change:.6f} USDC")
            if signature:
                print(f"Transaction: https://explorer.solana.com/tx/{signature}?cluster=devnet")
        else:
            print(f"Insufficient SOL balance. Need at least {swap_amount} SOL, have {sol_balance_before:.6f} SOL")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()
        print("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(main())