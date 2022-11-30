{ lib, makeWrapper, python3, fetchFromGitHub, ... }:

let
  withPlugins = pluginsFunc:
    let plugins = pluginsFunc availablePlugins;
    in python3.pkgs.buildPythonPackage {
      name = "${taxi.name}-with-plugins";
      inherit (taxi) version meta;
      format = "other";

      nativeBuildInputs = [ makeWrapper ];
      propagatedBuildInputs = plugins ++ taxi.propagatedBuildInputs;

      installPhase = ''
        makeWrapper ${taxi}/bin/taxi $out/bin/taxi \
          --prefix PYTHONPATH : "${taxi}/${python3.sitePackages}:$PYTHONPATH"
      '';

      doCheck = false;
      dontUnpack = true;
      dontBuild = true;

      passthru = taxi.passthru // {
        withPlugins = morePlugins: withPlugins (morePlugins ++ plugins);
      };
    };

  taxi = python3.pkgs.buildPythonPackage rec {
    pname = "taxi";
    version = "6.1.1";

    # Using GitHub instead of PyPI because tests are not distributed on the PyPI releases
    src = fetchFromGitHub {
      owner = "sephii";
      repo = pname;
      rev = version;
      sha256 = "1chwi2dililglx1kj9mq8hl1ih4v6ngic06d3gahrpfps2hvg348";
    };

    propagatedBuildInputs =
      [ python3.pkgs.click python3.pkgs.appdirs python3.pkgs.setuptools ];
    checkInputs = [ python3.pkgs.pytest python3.pkgs.freezegun ];
    checkPhase = "pytest";

    passthru = { inherit withPlugins; };

    meta = {
      homepage = "https://github.com/sephii/taxi";
      description = "Timesheeting made easy";
      license = lib.licenses.wtfpl;
    };
  };

  taxiZebra = python3.pkgs.buildPythonPackage rec {
    pname = "taxi_zebra";
    version = "3.0.1";

    src = fetchFromGitHub {
      owner = "liip";
      repo = "taxi-zebra";
      rev = version;
      sha256 = "sha256-5Sy/goElwLGt2Sg05Z8G04vsEZsTKCZKsI1/wQNifTI=";
    };

    buildInputs = [ taxi ];
    propagatedBuildInputs = [ python3.pkgs.requests python3.pkgs.click ];

    meta = {
      homepage = "https://github.com/liip/taxi-zebra";
      description = "Zebra backend for the Taxi timesheeting application";
      license = lib.licenses.wtfpl;
    };
  };

  taxiClockify = python3.pkgs.buildPythonPackage rec {
    pname = "taxi_clockify";
    version = "1.4.1";

    src = python3.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "18cfdih1pc097xw893sagmajfk52d3k63z6fq5hg4k71njaxrbdb";
    };

    buildInputs = [ taxi ];
    propagatedBuildInputs = [ python3.pkgs.requests python3.pkgs.arrow ];

    meta = {
      homepage = "https://github.com/sephii/taxi-clockify";
      description = "Clockify backend for the Taxi timesheeting application";
      license = lib.licenses.wtfpl;
    };
  };

  taxiPetzi = python3.pkgs.buildPythonPackage rec {
    pname = "taxi_petzi";
    version = "1.0.1";

    src = python3.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "94KuiV9S4vblbLHOM6YGJij36dbuN6ThcfkAkoA2Ggo=";
    };

    buildInputs = [ taxi ];
    propagatedBuildInputs = [
      python3.pkgs.google-auth-oauthlib
      python3.pkgs.google_api_python_client
    ];

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
