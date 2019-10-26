{ lib
, pkgs
, overrides ? {}
, path }:


let
  versions = lib.importJSON path;
in rec {
  get = name:
    let
      node = versions."${name}";
    in
      if overrides ? "${name}" then
        overrides."${name}"
      else if node.fetcher == "fetchTarball" then
        builtins.fetchTarball node.args
      else if pkgs ? "${node.fetcher}" then
        pkgs."${node.fetcher}" node.args
      else
        abort "Unknown fetcher '${node.fetcher}'";

  getAll  = map get (lib.attrNames versions);
}
