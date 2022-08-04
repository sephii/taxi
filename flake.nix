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
    let
      # Recursively merge a list of attribute sets. Following elements take
      # precedence over previous elements if they have conflicting keys.
      recursiveMerge = with nixpkgs.lib; foldl recursiveUpdate { };
    in
    recursiveMerge [
      (flake-utils.lib.eachDefaultSystem
        (system:
          let
            pkgs = nixpkgs.legacyPackages.${system};
            taxi = (import ./pkgs.nix { inherit pkgs; });
          in
          {
            packages = { inherit taxi; };
            defaultPackage = taxi;
            devShell = import ./shell.nix { inherit pkgs; };
          })
      )
      {
        overlay = final: prev: rec {
          # Prevents collision with taxi from nixpkgs (sftp app)
          taxi-cli = self.packages.${prev.stdenv.hostPlatform.system}.taxi;
        };
      }
    ];
}
