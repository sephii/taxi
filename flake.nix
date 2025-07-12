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
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ self.overlays.default ];
        };

        taxi = pkgs.callPackage ./pkgs.nix { };

        pythonVersions = [ "310" "311" "312" "313" ];

        makeCheckForPython = pythonVersion: let
          python3 = pkgs."python${pythonVersion}";
        in
          pkgs.callPackage ./tests.nix {
            inherit python3;
            taxi = pkgs.callPackage ./pkgs.nix { inherit python3; };
          };

        checksForPython = builtins.listToAttrs (
          map (pythonVersion: {
            name = "taxi-python${pythonVersion}";
            value = makeCheckForPython pythonVersion;
          }) pythonVersions
        );
      in
      {
        packages = {
          default = taxi;
          taxi = taxi;
          taxi-with-all-plugins = taxi.withPlugins (p: builtins.attrValues p);
        };

        devShells.default = pkgs.callPackage ./shell.nix {};

        checks = checksForPython;
      }
    )
    // {
      overlays.default = final: prev: {
        taxi-cli = final.callPackage ./pkgs.nix { };
      };
    };
}
