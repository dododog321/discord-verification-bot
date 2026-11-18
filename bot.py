
import discord
from discord.ext import commands
from discord import app_commands
import json
import os

TOKEN = os.getenv("BOT_TOKEN")
CONFIG_FILE = "config.json"

intents = discord.Intents.default()


def save_config(message_id, role_id):
    with open(CONFIG_FILE, "w") as f:
        json.dump({
            "message_id": message_id,
            "role_id": role_id
        }, f)


class VerifyView(discord.ui.View):
    def __init__(self, role_id):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(
        label="I've read and agree to the rules",
        style=discord.ButtonStyle.success,
        custom_id="verify_member"
    )
    async def verify(self, interaction: discord.Interaction,
                     button: discord.ui.Button):

        role = interaction.guild.get_role(self.role_id)
        member = interaction.user

        if role is None:
            await interaction.response.send_message(
                "The Member role could not be found.",
                ephemeral=True
            )
            return

        if role in member.roles:
            await interaction.response.send_message(
                "You're already verified!",
                ephemeral=True
            )
            return

        try:
            await member.add_roles(role, reason="Accepted server rules")
            await interaction.response.send_message(
                "You're verified! Welcome to the server!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to assign that role.",
                ephemeral=True
            )


class VerificationBot(commands.Bot):
    async def setup_hook(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)

            self.add_view(
                VerifyView(config["role_id"]),
                message_id=config["message_id"]
            )

        await self.tree.sync()


bot = VerificationBot(
    command_prefix="!",
    intents=intents
)


@bot.tree.command(
    name="setup",
    description="Create the server verification message"
)
@app_commands.default_permissions(manage_guild=True)
async def setup(interaction: discord.Interaction, role: discord.Role):

    if role.is_default() or role.managed:
        await interaction.response.send_message(
            "Please select a normal, assignable server role.",
            ephemeral=True
        )
        return

    bot_member = interaction.guild.me

    if role >= bot_member.top_role:
        await interaction.response.send_message(
            "My bot role must be higher than the Member role!",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="Welcome to the server!",
        description=(
            "Please read the rules above before continuing.\n\n"
            "When you've finished reading, click the button below "
            "to gain access to the rest of the server."
        ),
        color=discord.Color.green()
    )

    view = VerifyView(role.id)

    await interaction.response.send_message(
        "Creating verification message...",
        ephemeral=True
    )

    message = await interaction.channel.send(
        embed=embed,
        view=view
    )

    save_config(message.id, role.id)


if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing")

bot.run(TOKEN)
