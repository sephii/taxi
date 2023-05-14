{ python3, taxi, pkgs, ... }: taxi.overrideAttrs (old: {
  dontBuild = true;
  dontInstall = true;
  preConfigure = ''
    pythonOutputDistPhase() { touch $dist; }
  '';
})
