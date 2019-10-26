{ lib
, pkgs
, path }:


let
  versions = lib.importJSON path;
  download = node:
    if node.fetcher == "fetchTarball" then
      builtins.fetchTarball node.args
    else if pkgs ? "${node.fetcher}" then
      pkgs."${node.fetcher}" node.args
    else
      abort "Unknown fetcher '${node.fetcher}'";
in
{
  get = name:
    let
      node = versions."${name}";
    in download node;

  getAll  = map download versions;
}
