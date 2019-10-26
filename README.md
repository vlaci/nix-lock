# nix-lock

Use `package.json` style dependencies from Nix expressions

## Usage

1. Create a `derivations.json` file spwcifying your dependencies (_currently
   only GitHub repos are supported_):

``` json
{
    "nix-straight.el": {
        "owner": "vlaci",
        "repo": "nix-straight.el",
        "rev": "v1.0"
    },
    "emacs-overlay": {
        "owner": "nix-community",
        "repo": "emacs-overlay"
    }
}
```

2. run `bin/lock update` to generate or update `derivations.lock`

<details><summary>Example</summary>

``` json
{
    "nix-straight.el": {
        "fetcher": "fetchFromGitHub",
        "args": {
            "owner": "vlaci",
            "repo": "nix-straight.el",
            "rev": "6182914aefea06ef514cd3f3f7f9f67db45940db",
            "sha256": "038dss49bfvpj15psh5pr9jyavivninl0rzga9cn8qyc4g2cj5i0"
        },
        "meta": {
            "updated": "2019-10-25T22:28:25+00:00",
            "rev": "6182914aefea06ef514cd3f3f7f9f67db45940db"
        }
    },
    "emacs-overlay": {
        "fetcher": "fetchFromGitHub",
        "args": {
            "owner": "nix-community",
            "repo": "emacs-overlay",
            "rev": "daf9002714e9adfa415a385d939539524482142d",
            "sha256": "1w3zyk4847h1avd50cs1r7apw37bsyslv17vjkdk4h0r4gqz9cvs"
        },
        "meta": {
            "updated": "2019-10-25T22:28:28+00:00",
            "rev": "daf9002714e9adfa415a385d939539524482142d"
        }
    }
}
```

</details>

3. Add the following stub to your nix-expression a `let ... in` scope:

``` nix
let
  lock = pkgs.callPackage "${
    builtins.fetchTarball https://github.com/vlaci/nix-lock/archive/master.tar.gz
      }/lock.nix" {
    path = ./derivations.lock;
  };
in {
# ...
}
```

4. Look-up dependencies where needed in your expression:

``` nix
{
  nixpkgs.overlays = [
    (import lock.get "emacs-overlay")
  ];
}
```
