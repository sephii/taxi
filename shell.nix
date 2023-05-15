{ callPackage, python3, ... }:
(callPackage ./pkgs.nix { inherit python3; }).overrideAttrs (old: {
  src = ./.;
  propagatedBuildInputs = old.propagatedBuildInputs ++ [ python3.pkgs.pytest ];
})
