{ pkgs, ... }:

let
  lib = pkgs.lib;
  withPlugins = pluginsFunc:
    let plugins = pluginsFunc availablePlugins;
    in pkgs.python3Packages.buildPythonApplication {
      name = "${taxi.name}-with-plugins";
      inherit (taxi) version meta;

      phases = [ "installPhase" "fixupPhase" ];
      buildInputs = [ pkgs.makeWrapper ];
      propagatedBuildInputs = plugins ++ taxi.propagatedBuildInputs;

      installPhase = ''
        makeWrapper ${taxi}/bin/taxi $out/bin/taxi \
          --prefix PYTHONPATH : "${taxi}/${pkgs.python3.sitePackages}:$PYTHONPATH"
      '';
      doCheck = false;

      passthru = taxi.passthru // {
        withPlugins = morePlugins: withPlugins (morePlugins ++ plugins);
      };
    };

  taxi = pkgs.python3Packages.buildPythonApplication rec {
    pname = "taxi";
    version = "6.1.1";

    # Using GitHub instead of PyPI because tests are not distributed on the PyPI releases
    src = pkgs.fetchFromGitHub {
      owner = "sephii";
      repo = pname;
      rev = version;
      sha256 = "1chwi2dililglx1kj9mq8hl1ih4v6ngic06d3gahrpfps2hvg348";
    };

    propagatedBuildInputs = [
      pkgs.python3Packages.click
      pkgs.python3Packages.appdirs
      pkgs.python3Packages.setuptools
    ];
    checkInputs =
      [ pkgs.python3Packages.pytest pkgs.python3Packages.freezegun ];
    checkPhase = "pytest";

    passthru = { inherit withPlugins; };

    meta = {
      homepage = "https://github.com/sephii/taxi";
      description = "Timesheeting made easy";
      license = lib.licenses.wtfpl;
    };
  };

  taxiZebra = pkgs.python3Packages.buildPythonPackage rec {
    pname = "taxi_zebra";
    version = "3.0.1";

    src = pkgs.fetchFromGitHub {
      owner = "liip";
      repo = "taxi-zebra";
      rev = version;
      sha256 = "sha256-5Sy/goElwLGt2Sg05Z8G04vsEZsTKCZKsI1/wQNifTI=";
    };

    buildInputs = [ taxi ];
    propagatedBuildInputs =
      [ pkgs.python3Packages.requests pkgs.python3Packages.click ];

    meta = {
      homepage = "https://github.com/liip/taxi-zebra";
      description = "Zebra backend for the Taxi timesheeting application";
      license = lib.licenses.wtfpl;
    };
  };

  taxiClockify = pkgs.python3Packages.buildPythonPackage rec {
    pname = "taxi_clockify";
    version = "1.4.1";

    src = pkgs.python3.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "18cfdih1pc097xw893sagmajfk52d3k63z6fq5hg4k71njaxrbdb";
    };

    buildInputs = [ taxi ];
    propagatedBuildInputs =
      [ pkgs.python3Packages.requests pkgs.python3Packages.arrow ];
    doCheck = false;

    meta = {
      homepage = "https://github.com/sephii/taxi-clockify";
      description = "Clockify backend for the Taxi timesheeting application";
      license = lib.licenses.wtfpl;
    };
  };

  taxiPetzi = pkgs.python3Packages.buildPythonPackage rec {
    pname = "taxi_petzi";
    version = "1.0.1";

    src = pkgs.python3.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "94KuiV9S4vblbLHOM6YGJij36dbuN6ThcfkAkoA2Ggo=";
    };

    buildInputs = [ taxi ];
    propagatedBuildInputs = [
      pkgs.python3Packages.google-auth-oauthlib
      pkgs.python3Packages.google_api_python_client
    ];
    doCheck = false;

    meta = {
      homepage = "https://github.com/sephii/taxi-petzi";
      description = "Petzi backend for the Taxi timesheeting application";
      license = lib.licenses.wtfpl;
    };
  };

  availablePlugins = {
    zebra = taxiZebra;
    petzi = taxiPetzi;
    clockify = taxiClockify;
  };
in taxi
