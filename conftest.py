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
