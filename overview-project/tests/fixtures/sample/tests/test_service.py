from src.service import register


def test_register():
    assert register(' ADA ') == 'ada'
