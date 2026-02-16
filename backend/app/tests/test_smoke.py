"""Very small smoke test for importability (placeholder).

This test simply imports `create_app()` from the scaffold and ensures
it returns an object. It does not perform network or DB operations.
"""


def test_import_create_app():
    from backend.app.main import create_app

    app = create_app()
    assert app is not None
