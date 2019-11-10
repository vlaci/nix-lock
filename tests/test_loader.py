from nix_lock import derivations


doc = """[srcs]
pkg1-source = { git = "https://github.com/owner2/repo2", rev = "develop" }
pkg2-source = { git = "https://github.com/owner2/repo2" }
pkg3-source.git = "https://github.com/owner2/repo2"
"""


def test_loading():
    result = derivations.loads(doc)
    assert result is not None
    assert "srcs" in result
    assert len(result["srcs"]) == 3
