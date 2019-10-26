{ pkgs ? import <nixos-old> {}
, pythonPackages ? pkgs.python3Packages
, setup ? import (fetchTarball {
    url = "https://github.com/nix-community/setup.nix/archive/v3.2.0.tar.gz";
    sha256 = "0iqkrrsvp7sl9lif7rkdbam3wa8myw1b78miljrw6blk71dv47f7";
  })
}:

setup {
  inherit pkgs pythonPackages;
  src = ./.;
  overrides = self: super: {
    cryptography = super.cryptography.overridePythonAttrs(old: {
      patches = [];
    });
  };
  propagatedBuildInputs = [ pythonPackages.python-language-server ];
}
