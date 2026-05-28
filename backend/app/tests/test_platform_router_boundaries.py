from pathlib import Path


def test_platform_router_does_not_use_demo_store() -> None:
    router_source = Path("app/domains/platform/router.py").read_text()

    assert "app.core.store" not in router_source
    assert "store." not in router_source
