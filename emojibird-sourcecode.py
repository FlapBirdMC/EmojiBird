import discord
from discord import app_commands
import aiohttp
import io

# 1. Set up the bot intents
intents = discord.Intents.default()
intents.message_content = True  
intents.guilds = True          

class EmojiCloneBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced globally!")

bot = EmojiCloneBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


# --- COMMAND 1: CREDITS ---
@bot.tree.command(name="credits", description="Shows who created and configured this bot.")
async def credits(interaction: discord.Interaction):
    # Creating a clean embed look for your networks
    embed = discord.Embed(
        title="🤖 Bot Credits", 
        description="Created By **FlapBirdMC**.", 
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Discord Servers", 
        value="[CreepCraft Network](https://discord.gg/JKBFwbGXTx)\n[Ocean Members](https://discord.gg/kHvtnRMGBy)", 
        inline=False
    )
    await interaction.response.send_message(embed=embed)


# --- COMMAND 2: AI EMOJI CREATOR ---
@bot.tree.command(name="create_ai_emoji", description="Generate a completely new custom emoji using AI artwork.")
@app_commands.describe(
    prompt="Describe the emoji you want to create (e.g., 'a cute pixel art cat crying')",
    emoji_name="What should the emoji be named in the server list?"
)
async def create_ai_emoji(interaction: discord.Interaction, prompt: str, emoji_name: str):
    # Permissions Guard
    if not interaction.user.guild_permissions.manage_expressions:
        await interaction.response.send_message("You don't have permission to manage emojis here!", ephemeral=True)
        return

    # Defer because AI images take 2-10 seconds to generate
    await interaction.response.defer(ephemeral=False)

    # API Configuration (Example using a Standard Stability/Together API structure)
    # You will need to sign up for an API key at a provider like together.ai or stability.ai
    API_KEY = "YOUR_AI_API_KEY_HERE"
    API_URL = "https://api.together.xyz/v1/images/generations" 

    # We append 'emoji style, isolated on white background' to ensure it fits an emoji format cleanly
    optimized_prompt = f"Emoji icon, 3D render style, vector graphics, {prompt}, isolated on plain background, highly detailed"
    
    payload = {
        "model": "stabilityai/stable-diffusion-xl-base-1.0",
        "prompt": optimized_prompt,
        "width": 512,
        "height": 512,
        "steps": 30,
        "n": 1
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            # 1. Tell the AI to generate the picture
            async with session.post(API_URL, json=payload, headers=headers) as response:
                if response.status != 200:
                    text_err = await response.text()
                    await interaction.followup.send(f"AI Generation failed. Make sure your API key is configured. Error: {response.status}")
                    print(text_err)
                    return
                
                result = await response.json()
                # Most APIs return a direct URL to the image inside a data list
                image_url = result['data'][0]['url']
            
            # 2. Download the resulting AI picture bytes
            async with session.get(image_url) as img_response:
                image_bytes = await img_response.read()

        # 3. Upload the generated picture directly to your Discord server as an emoji
        guild = interaction.guild
        new_emoji = await guild.create_custom_emoji(name=emoji_name, image=image_bytes)
        
        await interaction.followup.send(f"🎨 **AI Emoji Created!** Enjoy your new emoji: {new_emoji}")

    except Exception as e:
        await interaction.followup.send(f"An error occurred while creating your AI emoji: {str(e)}")


# --- COMMAND 3: ORIGINAL CLONE EMOJI ---
@bot.tree.command(name="clone_emoji", description="Steal/Copy an emoji from another server.")
@app_commands.describe(emoji_input="Paste the emoji or its raw ID format", new_name="Optional custom name")
async def clone_emoji(interaction: discord.Interaction, emoji_input: str, new_name: str = None):
    if not interaction.user.guild_permissions.manage_expressions:
        await interaction.response.send_message("You don't have permission to manage emojis here!", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=False)

    try:
        if emoji_input.startswith("<") and emoji_input.endswith(">"):
            parts = emoji_input.split(":")
            emoji_id = parts[-1].replace(">", "")
            emoji_name = new_name if new_name else parts[1]
            is_animated = parts[0] == "<a"
        else:
            emoji_id = emoji_input.strip()
            emoji_name = new_name if new_name else "cloned_emoji"
            is_animated = False

        extension = "gif" if is_animated else "png"
        emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{extension}?v=1"

        async with aiohttp.ClientSession() as session:
            async with session.get(emoji_url) as response:
                if response.status != 200 and extension == "gif":
                    emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.png?v=1"
                    async with session.get(emoji_url) as retry_response:
                        if retry_response.status != 200:
                            await interaction.followup.send("Failed to retrieve that emoji.")
                            return
                        image_bytes = await retry_response.read()
                else:
                    image_bytes = await response.read()

        guild = interaction.guild
        new_emoji = await guild.create_custom_emoji(name=emoji_name, image=image_bytes)
        await interaction.followup.send(f"Successfully cloned the emoji! {new_emoji}")

    except discord.HTTPException as e:
        if e.code == 30008:
            await interaction.followup.send("Error: This server has reached its maximum custom emoji slots limit!")
        else:
            await interaction.followup.send(f"An HTTP error occurred: {e.text}")
    except Exception as e:
        await interaction.followup.send(f"An unexpected error occurred: {str(e)}")


# Replace with your actual bot token from the developer portal
bot.run('PUT_YOUR_BOT_TOKEN')