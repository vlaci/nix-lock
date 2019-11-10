{ pkgs ? import <nixpkgs> {}
, pythonPackages ? pkgs.python3Packages
, setup ? import (fetchTarball {
    url = "https://github.com/nix-community/setup.nix/archive/v3.3.0.tar.gz";
    sha256 = "1v1rgv1rl7za7ha3ngs6zap0b61z967aavh4p2ydngp44w5m2j5a";
  })
}:

setup {
  inherit pkgs pythonPackages;
  src = ./.;
  overrides = self: super: {
    cryptography = super.cryptography.overridePythonAttrs(old: {
      patches = [];
    });
    pytest = super.pytest.overridePythonAttrs(old: {
      doCheck = false;
    });
    pylint = super.pylint.overridePythonAttrs(old: {
      doCheck = false;
    });
  };
}
