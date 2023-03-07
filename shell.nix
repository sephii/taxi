{ pkgs ? import <nixpkgs> { } }:

with pkgs.python37Packages;

buildPythonPackage rec {
  name = "taxi";
  src = ./.;
  propagatedBuildInputs = [ click requests ];
}
