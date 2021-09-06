{ lib, pkgs, ... }:

let
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
    version = "6.1.0";

    # Using GitHub instead of PyPI because tests are not distributed on the PyPI releases
    src = pkgs.fetchFromGitHub {
      owner = "liip";
      repo = pname;
      rev = version;
      sha256 = "1ax95s0x30kr19szmfmmsffbck489raq15c04ldh19zsf6f0knkq";
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
      homepage = "https://github.com/liip/taxi";
      description = "Timesheeting made easy";
      license = lib.licenses.wtfpl;
    };
  };

  taxiZebra = pkgs.python3Packages.buildPythonPackage rec {
    pname = "taxi_zebra";
    version = "2.3.1";

    src = pkgs.python3.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "177fzasgchgbixrr4xikfbis8i427qlyb8c93d404rjjny9g7nny";
    };

    buildInputs = [ taxi ];
    propagatedBuildInputs =
      [ pkgs.python3Packages.requests pkgs.python3Packages.click ];
    doCheck = false;

    meta = {
      homepage = "https://github.com/sephii/taxi-zebra";
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
    version = "1.0.0";

    src = pkgs.python3.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "1zp6jpamrjgmaw2bpcdi8znxspn7v8f3hm3f8k9whjvc2q849ziq";
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
    taxi = taxiZebra;
    petzi = taxiPetzi;
    clockify = taxiClockify;
  };
in taxi
