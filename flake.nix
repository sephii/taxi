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
    in recursiveMerge [
      (flake-utils.lib.eachDefaultSystem (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          taxi = pkgs.callPackage ./pkgs.nix { };
        in {
          packages = { inherit taxi; };
          defaultPackage = taxi;
          # You might need to use `PIP_DISABLE_PIP_VERSION_CHECK=1 nix develop`
          # until https://github.com/NixOS/nixpkgs/pull/198024 gets merged
          devShell = pkgs.callPackage ./shell.nix { };
          checks = let
            testWithPython = (pythonPackage:
              pkgs.callPackage ./tests.nix {
                python3 = pythonPackage;
                taxi = pkgs.callPackage ./pkgs.nix { python3 = pythonPackage; };
              });
          in {
            # TODO generate this dynamically
            taxiPython37 = testWithPython pkgs.python37;
            taxiPython38 = testWithPython pkgs.python38;
            taxiPython39 = testWithPython pkgs.python39;
            taxiPython310 = testWithPython pkgs.python310;
            taxiPython311 = testWithPython pkgs.python311;
          };
        }))
      {
        overlay = final: prev: rec {
          # Prevents collision with taxi from nixpkgs (sftp app)
          taxi-cli = self.packages.${prev.stdenv.hostPlatform.system}.taxi;
        };
      }
    ];
}
