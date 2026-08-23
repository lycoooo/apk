import threading
import uuid
import urllib.request
import urllib.error
import json
import ssl

import kivy
kivy.require('2.3.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp

# ── Colours ──────────────────────────────────────────────────────────────────
BG_DARK    = get_color_from_hex('#0a0a0f')
BG_CARD    = get_color_from_hex('#14141cdd')
NF_RED     = get_color_from_hex('#E50914')
NF_RED2    = get_color_from_hex('#B20710')
TEXT_WHITE = get_color_from_hex('#FFFFFF')
TEXT_GREY  = get_color_from_hex('#999999')
GREEN      = get_color_from_hex('#46d369')
YELLOW     = get_color_from_hex('#f5c518')
RED_ERR    = get_color_from_hex('#ff4444')
CYAN       = get_color_from_hex('#00d4ff')

Window.clearcolor = BG_DARK

# ── Netflix constants (same as net.py) ───────────────────────────────────────
GRAPHQL_URL     = "https://web.prod.cloud.netflix.com/graphql"
LANDING_URL     = "https://www.netflix.com/ph-en/"
RECAPTCHA_KEY   = "6LdqW_EqAAAAAO87Fb_kcZfNzs0IqJRcKiJDYpUv"
INIT_QUERY_ID   = "5d76d6a0-ccfe-4c31-b587-b4e1954732ca"
UPDATE_QUERY_ID = "0fd81de7-07af-4c7d-802f-0f4ea4181aa3"
DEFAULT_NFVDID  = (
    "BQFmAAEBEHd71oHfkM7FU_oofLECV31AjKJNl9T0lBwR96xzXmWutUqrRdHCkAN1hcHjRlxLI8Eay"
    "T3bVFbyZDu8hLHeBXCz1dcwGebHrzm-7Ty5ckJTvQ%3D%3D"
)

UA = ("Mozilla/5.0 (Linux; Android 10; K) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/137.0.0.0 Mobile Safari/537.36")

SSL_CTX = ssl.create_default_context()


def _uuid():
    return str(uuid.uuid4())


# ── TrialSender (mirrors net.py) ─────────────────────────────────────────────
class TrialSender:
    def __init__(self, email: str, nfvdid: str = DEFAULT_NFVDID):
        self.email   = email
        self.nfvdid  = nfvdid
        self.locale  = "en-IN"
        self.flwssn  = _uuid()
        self.req_id  = _uuid()
        self.top_uuid = _uuid()

    def _base_headers(self) -> dict:
        return {
            "User-Agent":                        UA,
            "Content-Type":                      "application/json",
            "Origin":                            "https://www.netflix.com",
            "Referer":                           "https://www.netflix.com/",
            "Accept-Language":                   "en-US,en;q=0.9",
            "x-netflix.request.id":              self.req_id,
            "x-netflix.request.toplevel.uuid":   self.top_uuid,
            "x-netflix.request.clcs.bucket":     "high",
            "x-netflix.context.form-factor":     "phone",
            "x-netflix.context.app-version":     "v38c5b0da",
            "x-netflix.context.locales":         "en-in",
            "Cookie": f"nfvdid={self.nfvdid}; flwssn={self.flwssn}",
        }

    def _payload_init(self) -> bytes:
        data = {
            "operationName": "CLCSWebInitSignup",
            "variables": {
                "inputNode": "WELCOME",
                "locale": self.locale,
                "inputFields": [
                    {"name": "flwssn",                "value": {"stringValue": self.flwssn}},
                    {"name": "email",                 "value": {"stringValue": self.email}},
                    {"name": "recaptchaError",        "value": {"stringValue": "LOAD_TIMED_OUT"}},
                    {"name": "recaptchaResponseTime", "value": {}},
                    {"name": "recaptchaSiteKey",      "value": {"stringValue": RECAPTCHA_KEY}},
                    {"name": "recaptchaToken",        "value": {}},
                ],
            },
            "extensions": {"persistedQuery": {"id": INIT_QUERY_ID, "version": 102}},
        }
        return json.dumps(data).encode()

    def _payload_update(self) -> bytes:
        data = {
            "operationName": "CLCSScreenUpdate",
            "variables": {
                "format": "HTML",
                "imageFormat": "PNG",
                "locale": self.locale,
                "serverState": "Bgjru+vcAxLTAf/qOOEwXPLVxW+7Jod9WpjYuKN8j1qfhQpzCK4mmQts5eMSeaP+l7s6NKcNBO4rmYabFFCVnMpCH3ib4AicvXAKm30Z+s5W3Cst0D0BK5x/pwn3QmByi/OgGwU/fzaiR5oxSlZe4fKVexWHISkE4GMzJqLaaXQR0M73ynZB9idNBfqsz3RA5WJN+DGAbVUOZlWl8eZqffvQpp/5MGubeQFpdwKqkAx1nHh7/xI1i9tDU0KLgrvkZrbe6nQ1MX2nc9TBxqnVVxtc3ptHdqydP1wlIu0YBiIOCgydgLg1SvK6tSPOff8=",
                "serverScreenUpdate": "Bgjru+vcAxKSAjDnHOxlaIbFSbwaWzZo/REHFnNG7OtpcXdKTDlcL4/o+huGi/fNW+jrqNDqDSsv1iytiG/ZtvO9ierUE9M1Kc/yEj9JsSiG3XpPciFDzPd6psSaG68XLbos+Qie0wniXCtJyWDLDuLd9ayCMB8qGCxwbov6B41kCQY/zArwlecm0GNoJdd5jvZfBJVtytD6mMCYnPA/9zhX4okj+6IGet9xOCYt76IDiuyESxgKbaOLcd6DQIDSBf4m/lYi2Tasj7olPkCaDIXxjU+0UY+b7eDyhvi2if2vt6510ARrGsSZq8DaazQmrpAbfiCW47s1/1mR59vUMYeT8VCqqAvbNwipqyP1DQMHtoTnCoWns0+x6IgYBiIOCgx9EW4i3i9SUswnHEg=",
                "inputFields": [
                    {"name": "email",       "value": {"stringValue": self.email}},
                    {"name": "pipcConsent", "value": {"booleanValue": False}},
                ],
            },
            "extensions": {"persistedQuery": {"id": UPDATE_QUERY_ID, "version": 102}},
        }
        return json.dumps(data).encode()

    def check_banner(self) -> str | None:
        req = urllib.request.Request(LANDING_URL, headers=self._base_headers())
        with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as r:
            html = r.read().decode("utf-8", errors="replace")

        if 'data-uia="free-trial-banner"' in html or "Try 30 days" in html:
            marker = 'data-uia="free-trial-banner-text"'
            i = html.find(marker)
            if i != -1:
                j = html.find("</p>", i)
                if j != -1:
                    banner = html[i:j].split(">")[-1]
                    return banner or "30-day trial"
            return "30-day trial"
        return None

    def send_signup(self) -> bool:
        headers = self._base_headers()

        req1 = urllib.request.Request(
            GRAPHQL_URL, data=self._payload_init(), headers=headers, method="POST"
        )
        with urllib.request.urlopen(req1, timeout=30, context=SSL_CTX) as r:
            text1 = r.read().decode()
        if '"errors"' in text1.lower():
            raise RuntimeError(f"Init rejected")

        req2 = urllib.request.Request(
            GRAPHQL_URL, data=self._payload_update(), headers=headers, method="POST"
        )
        with urllib.request.urlopen(req2, timeout=30, context=SSL_CTX) as r:
            text2 = r.read().decode()
            code2 = r.status
        if code2 != 200 or '"errors"' in text2.lower():
            raise RuntimeError(f"Signup failed (HTTP {code2})")
        return True


# ── Kivy Widgets ──────────────────────────────────────────────────────────────

class RoundedBox(BoxLayout):
    """BoxLayout with a rounded dark card background."""
    def __init__(self, radius=16, bg_color=None, **kwargs):
        super().__init__(**kwargs)
        self._radius = radius
        self._bg = bg_color or [0.08, 0.08, 0.12, 0.92]
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg)
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[dp(self._radius)])


class RedButton(Button):
    def __init__(self, **kwargs):
        kwargs.setdefault('background_color', [0, 0, 0, 0])
        kwargs.setdefault('color', TEXT_WHITE)
        kwargs.setdefault('bold', True)
        kwargs.setdefault('font_size', dp(15))
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', dp(52))
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*NF_RED)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])


class StyledInput(TextInput):
    def __init__(self, **kwargs):
        kwargs.setdefault('multiline', False)
        kwargs.setdefault('background_color', [0.1, 0.1, 0.15, 1])
        kwargs.setdefault('foreground_color', TEXT_WHITE)
        kwargs.setdefault('cursor_color', NF_RED)
        kwargs.setdefault('hint_text_color', [0.4, 0.4, 0.4, 1])
        kwargs.setdefault('padding', [dp(14), dp(14), dp(14), dp(14)])
        kwargs.setdefault('font_size', dp(15))
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', dp(52))
        super().__init__(**kwargs)


class LogLine(Label):
    ICONS = {'ok': '[color=46d369]✓[/color]',
             'warn': '[color=f5c518]⚠[/color]',
             'err': '[color=ff4444]✗[/color]',
             'info': '[color=00d4ff]•[/color]'}

    def __init__(self, msg: str, kind: str = 'info', **kwargs):
        icon = self.ICONS.get(kind, '•')
        super().__init__(
            text=f"{icon}  {msg}",
            markup=True,
            halign='left',
            valign='middle',
            color=TEXT_WHITE,
            font_size=dp(13),
            size_hint_y=None,
            **kwargs
        )
        self.bind(width=lambda *_: self.setter('text_size')(self, (self.width, None)))
        self.bind(texture_size=lambda *_: self.setter('height')(self, self.texture_size[1] + dp(6)))


# ── Main Layout ───────────────────────────────────────────────────────────────

class TrialDetectLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=dp(16), spacing=dp(12), **kwargs)
        self._sender = None
        self._busy   = False
        self._build()

    def _build(self):
        # ── Banner ──────────────────────────────────────────────────────────
        header = BoxLayout(orientation='vertical',
                           size_hint_y=None, height=dp(90),
                           spacing=dp(4))
        title = Label(
            text='[b][color=E50914]Trial[/color] Detect[/b]',
            markup=True, font_size=dp(26), color=TEXT_WHITE,
            size_hint_y=None, height=dp(40), halign='center'
        )
        subtitle = Label(
            text='30 Days Trial Checker  •  by [color=E50914]Lyco[/color]',
            markup=True, font_size=dp(12), color=TEXT_GREY,
            size_hint_y=None, height=dp(22), halign='center'
        )
        header.add_widget(title)
        header.add_widget(subtitle)
        self.add_widget(header)

        # ── Email card ──────────────────────────────────────────────────────
        email_card = RoundedBox(orientation='vertical',
                                padding=dp(16), spacing=dp(10),
                                size_hint_y=None, height=dp(140))
        email_lbl = Label(text='Email Address', color=TEXT_GREY,
                          font_size=dp(12), halign='left',
                          size_hint_y=None, height=dp(20))
        email_lbl.bind(size=email_lbl.setter('text_size'))

        self.email_input = StyledInput(
            hint_text='yourname@example.com',
            input_type='mail_address',
        )

        self.check_btn = RedButton(text='Check Trial  →')
        self.check_btn.bind(on_press=self._on_check)

        email_card.add_widget(email_lbl)
        email_card.add_widget(self.email_input)
        email_card.add_widget(self.check_btn)
        self.add_widget(email_card)

        # ── nfvdid override (hidden until needed) ───────────────────────────
        self.nfvdid_card = RoundedBox(
            orientation='vertical', padding=dp(16), spacing=dp(10),
            size_hint_y=None, height=dp(160)
        )
        nf_lbl = Label(
            text='[color=f5c518]⚠[/color]  Trial not found — try a different nfvdid:',
            markup=True, color=TEXT_WHITE, font_size=dp(12),
            halign='left', size_hint_y=None, height=dp(28)
        )
        nf_lbl.bind(size=nf_lbl.setter('text_size'))
        self.nfvdid_input = StyledInput(hint_text='Paste new nfvdid here…')
        self.retry_btn = RedButton(text='Retry with new nfvdid')
        self.retry_btn.bind(on_press=self._on_retry)
        self.nfvdid_card.add_widget(nf_lbl)
        self.nfvdid_card.add_widget(self.nfvdid_input)
        self.nfvdid_card.add_widget(self.retry_btn)
        self.nfvdid_card.opacity = 0
        self.nfvdid_card.height  = 0
        self.add_widget(self.nfvdid_card)

        # ── Log card ─────────────────────────────────────────────────────────
        log_card = RoundedBox(orientation='vertical',
                              padding=dp(14), spacing=dp(4))
        log_title = Label(
            text='PROGRESS LOG', color=NF_RED,
            font_size=dp(10), bold=True, halign='left',
            size_hint_y=None, height=dp(22), letter_spacing=2
        )
        log_title.bind(size=log_title.setter('text_size'))
        log_card.add_widget(log_title)

        self.log_scroll = ScrollView(do_scroll_x=False)
        self.log_box    = BoxLayout(orientation='vertical',
                                    spacing=dp(4), size_hint_y=None)
        self.log_box.bind(minimum_height=self.log_box.setter('height'))
        self.log_scroll.add_widget(self.log_box)
        log_card.add_widget(self.log_scroll)
        self.add_widget(log_card)

        # Initial message
        self._log("Ready. Enter your email and tap Check Trial.", 'info')

    # ── Logging ──────────────────────────────────────────────────────────────
    def _log(self, msg: str, kind: str = 'info'):
        def _do(_dt=None):
            line = LogLine(msg, kind)
            self.log_box.add_widget(line)
            Clock.schedule_once(lambda dt: setattr(
                self.log_scroll, 'scroll_y', 0), 0.1)
        Clock.schedule_once(_do)

    # ── Actions ──────────────────────────────────────────────────────────────
    def _on_check(self, *_):
        if self._busy:
            return
        email = self.email_input.text.strip()
        if not email or '@' not in email:
            self._log("Invalid email address.", 'err')
            return
        nfvdid = self.nfvdid_input.text.strip() or DEFAULT_NFVDID
        self._start_check(email, nfvdid)

    def _on_retry(self, *_):
        if self._busy:
            return
        self._hide_nfvdid()
        self._on_check()

    def _start_check(self, email: str, nfvdid: str):
        self._busy = True
        self.check_btn.disabled = True
        self._sender = TrialSender(email, nfvdid)
        self._log(f"Email: {email}", 'info')
        self._log("Checking Netflix PH for 30-day trial banner…", 'info')
        threading.Thread(target=self._do_check, daemon=True).start()

    def _do_check(self):
        try:
            banner = self._sender.check_banner()
        except Exception as e:
            self._log(f"Banner check error: {e}", 'err')
            self._finish()
            return

        if not banner or '30' not in banner.lower():
            self._log("30-day trial NOT detected.", 'warn')
            Clock.schedule_once(lambda dt: self._show_nfvdid())
            self._finish()
            return

        self._log(f"30-day trial DETECTED ✓  ({banner})", 'ok')
        self._log("Sending CLCSWebInitSignup…", 'info')
        threading.Thread(target=self._do_signup, daemon=True).start()

    def _do_signup(self):
        try:
            self._sender.send_signup()
            self._log("CLCSWebInitSignup → OK", 'ok')
            self._log("CLCSScreenUpdate  → OK", 'ok')
            self._log(f"🎉 Trial activated for {self._sender.email}!", 'ok')
        except Exception as e:
            self._log(f"Signup failed: {e}", 'err')
        finally:
            self._finish()

    def _finish(self):
        def _do(_dt=None):
            self._busy = False
            self.check_btn.disabled = False
        Clock.schedule_once(_do)

    def _show_nfvdid(self):
        self.nfvdid_card.opacity = 1
        self.nfvdid_card.height  = dp(160)

    def _hide_nfvdid(self):
        self.nfvdid_card.opacity = 0
        self.nfvdid_card.height  = 0


# ── App ───────────────────────────────────────────────────────────────────────

class TrialDetectApp(App):
    title = 'Trial Detect'

    def build(self):
        Window.clearcolor = BG_DARK
        return TrialDetectLayout()


if __name__ == '__main__':
    TrialDetectApp().run()
