import discord
from discord.ext import commands
from discord import app_commands  
import os
from flask import Flask
from threading import Thread
from keep_alive import keep_alive
import psutil

# Create a bot object with the necessary intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# Sync slash commands when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    if not hasattr(bot, 'synced'):
        try:
            synced = await bot.tree.sync()  # Syncs the slash commands
            bot.synced = True  # Prevents multiple syncs
            print(f'Synced {len(synced)} command(s)')
        except Exception as e:
            print(f"Error syncing commands: {e}")


@bot.command(name="sync_commands")
@commands.has_permissions(administrator=True)  # Only allow admins to sync
async def sync_commands(ctx):
    try:
        synced = await bot.tree.sync()
        await ctx.send(f'Synced {len(synced)} command(s).')
    except Exception as e:
        await ctx.send(f"Error syncing commands: {e}")

# Checking the  current memoy of the bot
bot = commands.Bot(command_prefix="!", intents=intents)  # Adjust the prefix as needed  

@bot.command()
async def memory(ctx):
    process = psutil.Process()
    memory_in_mb = process.memory_info().rss / (1024 ** 2)
    await ctx.send(f"Memory used by the bot: {memory_in_mb:.2f} MB")





# Validate wallet address formats for BTC, ord, ETH, SOL and SUI
def is_valid_btc(wallet_address):
    # BTC addresses should start with '1' or '3' and must not start with 'bc1'
    return (wallet_address.startswith('1') or wallet_address.startswith('3')) and 26 <= len(wallet_address) <= 35

def is_valid_ord(wallet_address):
    # Ordinals addresses must ONLY start with 'bc1' and must be between 26 and 35 characters long
    return wallet_address.startswith('bc1') and 35 <= len(wallet_address) <= 66

def is_valid_eth(wallet_address):
    return wallet_address.startswith('0x') and len(wallet_address) == 42

def is_valid_sol(wallet_address):
    return len(wallet_address) in [43, 44]

def is_valid_sui(wallet_address):
    # SUI wallet address must be exactly 66 characters long
    return len(wallet_address) == 66



# Function to check if a user already has a stored wallet for the chain
def has_user_stored_wallet(user_id, wallet_file_name):
    if not os.path.exists(wallet_file_name):
        return False
    with open(wallet_file_name, "r") as wallet_file:
        for line in wallet_file:
            if user_id in line:  # Check if the user has an entry in the file
                return True
    return False


# Function to check if a wallet address already exists (duplicate check)
def is_duplicate_wallet(wallet_address, wallet_file_name):
    if not os.path.exists(wallet_file_name):
        return False
    with open(wallet_file_name, "r") as wallet_file:
        for line in wallet_file:
            if wallet_address in line:  # Check if the wallet address already exists
                return True
    return False


# Define a slash command to store wallet addresses with duplicate checking
@bot.tree.command(name="store", description="Store a wallet address for BTC, ord, ETH, SOL or SUI.")
@app_commands.describe(wallet_address="Your wallet address", chain="Type of wallet: btc, ord, eth, sol, sui")
async def store(interaction: discord.Interaction, wallet_address: str, chain: str):
    # Defer the interaction to avoid timeout
    await interaction.response.defer(ephemeral=True)

    # Determine the file to store the wallet address based on chain
    wallet_file_name = {
        "btc": "btc_wallets.txt",
        "ord": "ord_wallets.txt",
        "eth": "eth_wallets.txt",
        "sol": "solana_wallets.txt",
        "sui": "sui_wallets.txt"
    }.get(chain.lower())

    if wallet_file_name is None:
        await interaction.followup.send("Invalid chain. Please specify 'btc', 'ord', 'eth', or 'sol'.", ephemeral=True)
        return

    # Validate the wallet address based on type
    if chain == "btc" and not is_valid_btc(wallet_address):
        await interaction.followup.send("Invalid Bitcoin wallet address. Please check and try again.", ephemeral=True)
        return
    elif chain == "ord" and not is_valid_ord(wallet_address):
        await interaction.followup.send("Invalid ord wallet address. Please check and try again.", ephemeral=True)
        return
    elif chain == "eth" and not is_valid_eth(wallet_address):
        await interaction.followup.send("Invalid Ethereum wallet address. Please check and try again.", ephemeral=True)
        return
    elif chain == "sol" and not is_valid_sol(wallet_address):
        await interaction.followup.send("Invalid Solana wallet address. Please check and try again.", ephemeral=True)
        return
    elif chain == "sui" and not is_valid_sui(wallet_address):
        await interaction.followup.send("Invalid SUI wallet address. Please check and try again.", ephemeral=True)
        return


    # Check if the user already has a wallet stored for this chain
    user_id = f'{interaction.user.name}#{interaction.user.discriminator}'
    if has_user_stored_wallet(user_id, wallet_file_name):
        await interaction.followup.send(f"You have already stored a {chain.upper()} wallet address. You can only store one wallet per chain.", ephemeral=True)
        return

    # Check for duplicates before storing
    if is_duplicate_wallet(wallet_address, wallet_file_name):
        await interaction.followup.send(f"This {chain.upper()} wallet address is already stored.", ephemeral=True)
        return

    # Store the wallet address in the respective file
    with open(wallet_file_name, "a") as wallet_file:
        wallet_file.write(f'{user_id}: {wallet_address}\n')

    # Follow-up message after processing
    await interaction.followup.send(f'{chain.upper()} wallet address saved for {interaction.user.name}.', ephemeral=True)


# Function to edit wallet addresses with duplicate checking
@bot.tree.command(name="edit", description="Edit your wallet address for BTC, ord, ETH, SOL or SUI.")
@app_commands.describe(current_wallet="Your current wallet address", new_wallet="Your new wallet address", chain="Type of wallet: btc, ord, eth, sol, sui")
async def edit(interaction: discord.Interaction, current_wallet: str, new_wallet: str, chain: str):
    await interaction.response.defer(ephemeral=True)  # Defer the response to prevent timeout

    # Validate the new wallet address based on type
    if chain == "btc" and not is_valid_btc(new_wallet):
        await interaction.followup.send("Invalid new Bitcoin wallet address. Please check and try again.", ephemeral=True)
        return
    elif chain == "ord" and not is_valid_ord(new_wallet):
        await interaction.followup.send("Invalid new Ordinal wallet address. Please check and try again.", ephemeral=True)
        return
    elif chain == "eth" and not is_valid_eth(new_wallet):
        await interaction.followup.send("Invalid new Ethereum wallet address. Please check and try again.", ephemeral=True)
        return
    elif chain == "sol" and not is_valid_sol(new_wallet):
        await interaction.followup.send("Invalid new Solana wallet address. Please check and try again.", ephemeral=True)
        return
    elif chain == "sui" and not is_valid_sui(new_wallet):
        await interaction.followup.send("Invalid SUI wallet address. Please check and try again.", ephemeral=True)
        return

    # Determine the file to edit the wallet address based on chain
    wallet_file_name = {
        "btc": "btc_wallets.txt",
        "ord": "ord_wallets.txt",
        "eth": "eth_wallets.txt",
        "sol": "solana_wallets.txt",
        "sui": "sui_wallets.txt"
    }.get(chain.lower())

    if wallet_file_name is None:
        await interaction.followup.send("Invalid chain. Please specify 'btc', 'ord', 'eth', 'sol' or 'sui'.", ephemeral=True)
        return

    # Check for duplicates before updating to a new wallet address
    if is_duplicate_wallet(new_wallet, wallet_file_name):
        await interaction.followup.send(f"This {chain.upper()} wallet address is already stored by someone else.", ephemeral=True)
        return

    # Check if the file exists
    if not os.path.exists(wallet_file_name):
        await interaction.followup.send(f"No {chain.upper()} wallet addresses have been stored yet.", ephemeral=True)
        return

    # Read the file and update the wallet address
    with open(wallet_file_name, "r") as wallet_file:
        lines = wallet_file.readlines()

    user_id = f'{interaction.user.name}#{interaction.user.discriminator}'
    found = False

    # Write the updated file back
    with open(wallet_file_name, "w") as wallet_file:
        for line in lines:
            if line.startswith(user_id) and current_wallet in line:
                # Replace the old wallet with the new one
                wallet_file.write(f'{user_id}: {new_wallet}\n')
                found = True
            else:
                wallet_file.write(line)

    if found:
        await interaction.followup.send(f"Your {chain.upper()} wallet address has been updated from {current_wallet} to {new_wallet}.", ephemeral=True)
    else:
        await interaction.followup.send(f"Could not find the wallet address {current_wallet}. Please make sure it is correct.", ephemeral=True)


# Prefix command to send the file with stored wallet addresses
@bot.command(name="get")
async def get(ctx, chain: str):
    wallet_file_name = {
        "btc": "btc_wallets.txt",
        "ord": "ord_wallets.txt",
        "eth": "eth_wallets.txt",
        "sol": "solana_wallets.txt",
        "sui": "sui_wallets.txt"
    }.get(chain.lower())

    if wallet_file_name is None:
        await ctx.send("Invalid chain. Please specify 'btc', 'ord', 'eth', 'sol' or 'sui'.")
        return

    # Check if the file exists
    if os.path.exists(wallet_file_name):
        await ctx.send(f"Here are the stored {chain.upper()} wallet addresses:", file=discord.File(wallet_file_name))
    else:
        await ctx.send(f"No {chain.upper()} wallet addresses have been stored yet.")


# Prefix command to clear the wallet list (delete or empty the file)
@bot.command(name="clear")
@commands.has_permissions(administrator=True)  # Allow only admins to clear wallets
async def clear(ctx, chain: str):
    wallet_file_name = {
        "btc": "btc_wallets.txt",
        "ord": "ord_wallets.txt",
        "eth": "eth_wallets.txt",
        "sol": "solana_wallets.txt",
        "sui": "sui_wallets.txt"
    }.get(chain.lower())

    if wallet_file_name is None:
        await ctx.send("Invalid chain. Please specify 'btc', 'ord', 'eth', 'sol' or 'sui'.")
        return

    # Check if the file exists
    if os.path.exists(wallet_file_name):
        # Empty the contents of the file
        with open(wallet_file_name, "w") as wallet_file:
            wallet_file.write("")  # Writing an empty string clears the file
        await ctx.send(f"The {chain.upper()} wallet list has been cleared.")
    else:
        await ctx.send(f"No {chain.upper()} wallet list found to clear.")


# This will start the Flask server
keep_alive()

# Get the Discord bot token from the environment variable
token = os.getenv("DISCORD_BOT_TOKEN")

# Check if the token is available
if token is None:
    print("DISCORD_BOT_TOKEN environment variable not found. Please set it.")
    exit(1)

# Start the bot with your token
bot.run(token)
