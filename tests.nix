{ python3, taxi, pkgs, ... }:
let devShell = pkgs.callPackage ./shell.nix { inherit python3; };
in devShell.overrideAttrs (old: {
  dontBuild = true;
  dontInstall = true;
})
