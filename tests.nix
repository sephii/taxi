{ python3, taxi, pkgs, ... }: taxi.overrideAttrs (old: {
  dontInstall = true;
})
