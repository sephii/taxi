{ pkgs ? import <nixpkgs> { } }:

with pkgs.python310Packages;

buildPythonPackage rec {
  name = "taxi";
  src = ./.;
  propagatedBuildInputs = [ click requests ];
}
