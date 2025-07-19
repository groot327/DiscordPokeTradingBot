import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve the bot token from environment variables
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("No DISCORD_BOT_TOKEN found in .env file. Please set it.")

class TradeDiscordBot:
    def __init__(self, prefix='/'):
        # Set up intents
        self.intents = discord.Intents.default()
        self.intents.message_content = True  # Enable message content intent for slash commands
        
        # Initialize the bot
        self.bot = commands.Bot(command_prefix=prefix, intents=self.intents)
        
        # Register event handlers
        self.bot.event(self.on_ready)
        
        # Register commands
        self.register_commands()
        
        # Read list of pokemon
        self.pokemon_list = []
        self.load_pokemon()

    async def on_ready(self):
        """Event handler for when the bot is ready."""
        print(f'Bot is ready! Logged in as {self.bot.user}')
        try:
            synced = await self.bot.tree.sync()  # Sync slash commands
            print(f'Synced {len(synced)} command(s)')
        except Exception as e:
            print(f'Error syncing commands: {e}')

    def register_commands(self):
        """Register all slash commands with restrictions."""
        # Command: /help
        @self.bot.tree.command(name="help", description="Displays the list of available commands")
        async def help_command(interaction: discord.Interaction):
            # Restrict to "trades" channel
            if interaction.channel.name.lower() != "trades":
                await interaction.response.send_message(
                    "This command can only be used in the 'trades' channel.", ephemeral=True
                )
                return
            embed = discord.Embed(title="Bot Commands", description="List of available commands:", color=discord.Color.blue())
            embed.add_field(name="/help", value="Shows this help message", inline=False)
            embed.add_field(name="/trade", value="Opens a new trade thread under the #trades channel: may only be run in the #trades channel", inline=False)
            embed.add_field(name="/close", value="Closes/ends an open trade request; may only be run in the trade thread by the trade requestor")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
        # Command: /trade
        @self.bot.tree.command(name="trade", description="Open/start a trade request")
        @discord.app_commands.describe(
            pokemon="Pokemon request",
            features="List of features, e.g.s, shiny, xxs, specific costume"
        )
        async def trade_command(interaction: discord.Interaction, pokemon: str, features: str):
            # Restrict to "trades" channel
            if interaction.channel.name.lower() != "trades":
                await interaction.response.send_message(
                    "This command can only be used in the 'trades' channel.", ephemeral=True
                )
                return
            thread_name = f'{pokemon}-{interaction.user.name}'
            try:
                # Create a new thread
                thread = await interaction.channel.create_thread(
                    name=thread_name,
                    auto_archive_duration=1440,
                    type=discord.ChannelType.public_thread
                )
#                response = f"Looking for: {pokemon}\nspecial features: {pokeopt or 'None'}\nDiscussion in: {thread.mention}"
#                embed = discord.Embed(
#                    title=f"Trade Request from {interaction.user.name}",
#                    description=response,
#                    color=discord.Color.purple()
#                )
#                embed.add_field(name="Thread", value=f"", inline=False)
                # Store the creator's ID in thread metadata or description for later verification
#                await interaction.response.send_message(embed=embed)

                # TODO: Code to check for valid Pokémon names
                
                thread_embed = discord.Embed(title="Trade Request Started", color=discord.Color.teal())
                #thread_embed.set_thumbnail(url="")
                thread_embed.add_field(name="Initiated By:",value=f"{interaction.user.mention}", inline=False)
                thread_embed.add_field(name="Request", value=pokemon, inline=True)
                thread_embed.add_field(name="Features", value=f'{features or "None"}', inline=True)
                thread_embed.set_footer(text=f'Ref: {interaction.user.id}')
                await thread.send(embed=thread_embed)
                
                # Message to requestor to post message in the thread
                embed = discord.Embed(
                    title="Please Post Message In Thread",
                    color=discord.Color.red()
                )
                embed.add_field(name="Is your request is visible?", value=f"Post a message in the {thread.mention} thread to be sure to be seen!")
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except discord.errors.Forbidden:
                await interaction.response.send_message(
                    "Error: Bot doesn't have permission to create threads",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"Error creating thread: {str(e)}",
                    ephemeral=True
                )
    
        # Command: /close
        @self.bot.tree.command(name="close", description="Close/End a Trade Request. Must be done by originator of the trade.")
        async def close_command(interaction: discord.Interaction):
            # Restrict to threads
            if not isinstance(interaction.channel, discord.Thread):
                await interaction.response.send_message("This command must be used in a trade thread", ephemeral=True)
                return
            # Check if the user is the thread creator
            # Note: interaction.channel.owner may not always be reliable, so we parse the initial thread message
#            try:
#                async for counter, message in enumerate(interaction.channel.history(oldest_first=True)):
#                    print(f'MESSAGE {counter}: {message}')
#            except Exception as e:
#                await interaction.response.send_message("there is likely no history")
#            try:
#                async for message in interaction.channel.history(limit=1, oldest_first=True):
#                    if str(interaction.user.id) not in message.content:
#                        await interaction.response.send_message(
#                            f"Only the original trade requestor can close this thread.\nuser.id = {interaction.user.id}\nmessage.content = {message.content}", ephemeral=True
#                        )
#                        return
            if interaction.user.name not in interaction.channel.name:
            	embed = discord.Embed(
                    title="Not Permitted",
                	description=f"{interaction.user.name} does not have permission to close this thread."
            	)
            	await interaction.response.send_message(embed=embed, ephemeral=True)
            	return
            try:
                response = f"{interaction.user.name} has requested closure of this trade request"
                embed = discord.Embed(
                    title="Close Trade Request",
                    description=response,
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                # Archive and delete the thread
                await interaction.channel.edit(archived=True)
                await interaction.channel.delete()
            except discord.errors.Forbidden:
                await interaction.response.send_message(
                    "Error: Bot doesn't have permission to delete threads",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"Error deleting thread: {str(e)}",
                    ephemeral=True
                )
                
        # Command: /reload_pokemon_list
        @self.bot.tree.command(name="reload_pokemon_list", description="Force a reload of Pokémon names.")
        async def reload_pokemon_list_command(interaction: discord.Interaction):
            # Restrict to Admin users
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    f'{interaction.user.name}, you do not have permission to run this command.',
                    ephemeral=True
                )
                return
            # Restrict to "change-log" channel
            if interaction.channel.name.lower() != "change-log":
                await interaction.response.send_message(
                    "This command can only be used in the 'change-log' channel.", ephemeral=True
                )
                return
            # Perform the load
            try:
                self.load_pokemon()
                await interaction.response.send_message(
                    f"Loaded {len(self.pokemon_list)} entries", 
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"Error loading Pokémon list: {str(e)}", 
                    ephemeral=True
                )

    def load_pokemon(self):
        """
        Perform the read and load of the pokemon list file
        """
        file_name = 'pokemon.list'
        try:
            with open(file_name, 'r', encoding='utf-8') as file:
                self.pokemon_list = [ line.strip() for line in file ]
                print(f"Loaded {len(self.pokemon_list)} from '{file_name}'.")
        except FileNotFoundError:
            print(f"Error: File '{file_name}'' not found.")
        except IOError:
            print(f"Error: Unable to read file '{file_name}'.")
              
    def add_new_command(self, name, description, callback):
        """
        Helper function to add new slash commands dynamically.
        Args:
            name (str): Command name
            description (str): Command description
            callback: The function to execute when the command is called
        """
        self.bot.tree.command(name=name, description=description)(callback)

    def run(self):
        """Start the bot."""
        self.bot.run(BOT_TOKEN)

# Example of how to add a new command dynamically
async def example_new_command(interaction: discord.Interaction):
    await interaction.response.send_message("This is a new command!")

if __name__ == "__main__":
    # Initialize and run the bot
    bot = TradeDiscordBot()
    # bot = TradeDiscordBot(prefix='/')
    
    # Optionally add a new command (uncomment to include it)
    # bot.add_new_command("newcommand", "An example new command", example_new_command)
    
    bot.run()
    
"""
    To get the list of pokemon for the pokemon.list file, use this site:
    https://pokemondb.net/tools/text-list
"""