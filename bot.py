import discord
from discord.ext import commands
import os
import asyncio
from ai_cv import generate_all_files

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "PASTE_YOUR_DISCORD_TOKEN_HERE")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

active_sessions = {}


@bot.event
async def on_ready():
    print(f"✅ CV Bot online — {bot.user}")


@bot.command(name="apply")
async def apply(ctx):
    active_sessions[ctx.author.id] = {"step": "waiting_for_job"}
    await ctx.send(
        "📋 **CV Tailor Bot — Ready**\n\n"
        "Paste the **full job description** below and I'll send back:\n"
        "📄 `tailored_cv.docx` — CV in your exact original format\n"
        "📄 `cover_letter.docx` — Ready to paste into your email\n\n"
        "Just paste the job description now:"
    )


@bot.command(name="cancel")
async def cancel(ctx):
    if ctx.author.id in active_sessions:
        del active_sessions[ctx.author.id]
        await ctx.send("❌ Cancelled. Type `!apply` to start again.")
    else:
        await ctx.send("No active session. Type `!apply` to start.")


@bot.command(name="help")
async def help_cmd(ctx):
    await ctx.send(
        "**📋 CV Bot Commands:**\n\n"
        "`!apply` — Tailor your CV to a job description\n"
        "`!cancel` — Cancel current session"
    )


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)

    if message.author.id not in active_sessions:
        return
    if message.content.startswith("!"):
        return

    session = active_sessions[message.author.id]

    if session["step"] == "waiting_for_job":
        job_description = message.content.strip()

        if len(job_description) < 50:
            await message.channel.send("⚠️ That looks too short — paste the full job description.")
            return

        active_sessions[message.author.id]["step"] = "processing"
        msg = await message.channel.send("⏳ Tailoring your CV... ~20 seconds...")

        try:
            loop = asyncio.get_event_loop()
            files = await loop.run_in_executor(None, generate_all_files, job_description)

            discord_files = [
                discord.File(files["cv_docx"], filename="tailored_cv.docx"),
                discord.File(files["cl_docx"], filename="cover_letter.docx"),
            ]

            # Add PDFs if they were generated
            if files.get("cv_pdf"):
                discord_files.append(discord.File(files["cv_pdf"], filename="tailored_cv.pdf"))
            if files.get("cl_pdf"):
                discord_files.append(discord.File(files["cl_pdf"], filename="cover_letter.pdf"))

            await msg.delete()
            await message.channel.send(
                "✅ **Done! Your documents are ready:**\n"
                "• Attach `tailored_cv.docx` (or PDF) to your email\n"
                "• Copy cover letter text into the email body\n\n"
                "Type `!apply` to tailor for another job.",
                files=discord_files
            )

        except Exception as e:
            await msg.edit(content=f"❌ Error: {e}\n\nType `!apply` to try again.")

        finally:
            active_sessions.pop(message.author.id, None)


bot.run(DISCORD_TOKEN)
