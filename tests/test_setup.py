from tools.validate_setup import validate


def test_upstream_materials_and_team_links_remain_consistent() -> None:
    assert validate() == []
