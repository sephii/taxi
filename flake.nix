{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    flake-compat = {
      url = "github:edolstra/flake-compat";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        taxi = (import ./pkgs.nix {
          inherit pkgs;
          lib = nixpkgs.lib;
        });
      in {
        packages = { inherit taxi; };
        defaultPackage = taxi;
        devShell = import ./shell.nix { inherit pkgs; };
      });
}
