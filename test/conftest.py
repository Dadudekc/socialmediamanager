from unittest.mock import MagicMock
import sys
import types

def ensure_module(name, **attrs):
    if name in sys.modules:
        return sys.modules[name]
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod

try:
    import mysql.connector
except ModuleNotFoundError:
    connector = ensure_module("mysql.connector")
    mysql = ensure_module("mysql", connector=connector)
    import mysql.connector

# Stub external packages if missing
ensure_module("dotenv", load_dotenv=lambda *a, **k: None, find_dotenv=lambda: "")
class DummyAioSession:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass
    def get(self, *a, **k):
        return object()
ensure_module("aiohttp", ClientSession=DummyAioSession)

# Use the real pandas package if available; fall back to a lightweight stub
# only when pandas is not installed. This allows tests that rely on pandas
# functionality (e.g., DataFrame operations) to run correctly when the
# dependency is present while still keeping the suite runnable without it.
try:  # pragma: no cover - import check
    import pandas  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    ensure_module("pandas", read_csv=lambda *a, **k: [])
selenium = ensure_module("selenium")
ensure_module("selenium.webdriver", Chrome=object())
ensure_module("selenium.webdriver.common")
ensure_module("selenium.webdriver.common.by", By=object())
ensure_module("selenium.webdriver.common.keys", Keys=object())
ensure_module("selenium.webdriver.chrome.service", Service=object())
ensure_module("selenium.webdriver.chrome.options", Options=object())
ensure_module("selenium.common.exceptions", WebDriverException=type("WebDriverException", (), {}))
class DummyTextBlob:
    def __init__(self, text):
        self.text = text
    @property
    def sentiment(self):
        return type("S", (), {"polarity": 0})()
ensure_module("textblob", TextBlob=DummyTextBlob)
ensure_module("vaderSentiment.vaderSentiment", SentimentIntensityAnalyzer=type("SentimentIntensityAnalyzer", (), {"polarity_scores": lambda self, text: {"compound": 0}}))
class DummyCDM:
    def install(self):
        return "chromedriver"
ensure_module("webdriver_manager.chrome", ChromeDriverManager=DummyCDM)

class DummyColor:
    @staticmethod
    def red():
        return 0

    @staticmethod
    def green():
        return 0

    @staticmethod
    def light_gray():
        return 0

class DummyEmbed:
    def __init__(self, *args, **kwargs):
        pass
    def add_field(self, name=None, value=None, inline=None):
        pass
    def set_footer(self, text=None):
        pass

ensure_module(
    "discord",
    Embed=DummyEmbed,
    Color=DummyColor,
    Intents=types.SimpleNamespace(default=lambda: None),
)

# Patch mysql.connector.connect to return a dummy connection object.
mysql.connector.connect = MagicMock(return_value=MagicMock(
    cursor=lambda: MagicMock(),
    commit=lambda: None,
    rollback=lambda: None,
    close=lambda: None
))

# Enable running of async test functions without requiring external plugins.
import asyncio
import inspect
import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):  # pragma: no cover - pytest hook
    if inspect.iscoroutinefunction(pyfuncitem.obj):
        asyncio.run(pyfuncitem.obj())
        return True


def pytest_collection_modifyitems(config, items):  # pragma: no cover
    for item in items:
        if inspect.iscoroutinefunction(item.obj):
            coro = item.obj

            def _wrapper(*args, __coro=coro, **kwargs):
                return asyncio.run(__coro(*args, **kwargs))

            item.obj = _wrapper
