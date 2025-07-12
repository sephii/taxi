{ pkgs ? import <nixpkgs> {} }:
let
  taxi = pkgs.callPackage ./pkgs.nix { inherit (pkgs) python3; };
in
pkgs.mkShell {
  name = "taxi-dev-shell";

  buildInputs = [
    taxi
    pkgs.python3.pkgs.pytest
  ];
}
