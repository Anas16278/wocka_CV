import discord
from discord.ext import commands
import os
import asyncio
import subprocess
from ai_cv import tailor_cv, generate_docx

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "PASTE_YOUR_DISCORD_TOKEN_HERE")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

active_sessions = {}


def docx_to_pdf(docx_path: str, output_name: str) -> str:
    """Convert docx to PDF, return PDF path"""
    output_dir = "/tmp"
    result = subprocess.run(
        ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", output_dir, docx_path],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise Exception(f"PDF conversion failed: {result.stderr}")

    base = os.path.splitext(os.path.basename(docx_path))[0]
    pdf_path = os.path.join(output_dir, base + ".pdf")

    # Rename to clean output name
    final_path = os.path.join(output_dir, output_name)
    os.rename(pdf_path, final_path)
    return final_path


def generate_all_files(job_description: str) -> dict:
    """Full pipeline: AI tailor → docx → pdf. Returns all file paths."""
    cv_data = tailor_cv(job_description)
    cv_docx, cl_docx = generate_docx(cv_data)

    cv_pdf = docx_to_pdf(cv_docx, "tailored_cv.pdf")
    cl_pdf = docx_to_pdf(cl_docx, "cover_letter.pdf")

    return {
        "cv_docx": cv_docx,
        "cv_pdf": cv_pdf,
        "cl_docx": cl_docx,
        "cl_pdf": cl_pdf,
    }


@bot.event
async def on_ready():
    print(f"✅ CV Bot online — {bot.user}")


@bot.command(name="apply")
async def apply(ctx):
    active_sessions[ctx.author.id] = {"step": "waiting_for_job"}
    await ctx.send(
        "📋 **CV Tailor Bot — Ready**\n\n"
        "Paste the **full job description** below.\n\n"
        "I'll send back:\n"
        "📄 `tailored_cv.pdf` — ready to attach to your email\n"
        "📄 `cover_letter.pdf` — paste into your email body\n"
        "📝 `tailored_cv.docx` — editable Word version\n"
        "📝 `cover_letter.docx` — editable Word version\n\n"
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
        "`!apply` — Tailor your CV to a specific job\n"
        "`!cancel` — Cancel current session\n\n"
        "Outputs PDF + Word versions of both your CV and cover letter."
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
        msg = await message.channel.send(
            "⏳ Working on it...\n"
            "`[1/3]` 🤖 AI tailoring your CV to this job...\n"
            "`[2/3]` 📄 Generating Word documents...\n"
            "`[3/3]` 🖨️ Converting to PDF..."
        )

        try:
            loop = asyncio.get_event_loop()
            files = await loop.run_in_executor(None, generate_all_files, job_description)

            await msg.delete()
            await message.channel.send(
                "✅ **All 4 files ready — Anas Ali**\n"
                "───────────────────────────────────\n"
                "📎 **Send to employer:**\n"
                "• Attach `tailored_cv.pdf` to your email\n"
                "• Copy cover letter text into the email body\n\n"
                "✏️ **Want to edit first?**\n"
                "• Open the `.docx` versions in Word\n"
                "───────────────────────────────────",
                files=[
                    discord.File(files["cv_pdf"],   filename="tailored_cv.pdf"),
                    discord.File(files["cl_pdf"],   filename="cover_letter.pdf"),
                    discord.File(files["cv_docx"],  filename="tailored_cv.docx"),
                    discord.File(files["cl_docx"],  filename="cover_letter.docx"),
                ]
            )

        except Exception as e:
            await msg.edit(content=f"❌ Error: {e}\n\nType `!apply` to try again.")

        finally:
            active_sessions.pop(message.author.id, None)


bot.run(DISCORD_TOKEN)
