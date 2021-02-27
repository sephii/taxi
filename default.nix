with import <nixpkgs> { };

let packages = pkgs.callPackage ./pkgs.nix { };
in { inherit (packages) taxi taxi_zebra taxi_clockify; }
