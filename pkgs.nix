{ lib, fetchFromGitHub, makeWrapper, python3, python3Packages, ... }:

let
  withPlugins = plugins:
    python3Packages.buildPythonApplication {
      name = "${package.name}-with-plugins";
      inherit (package) version meta;

      phases = [ "installPhase" "fixupPhase" ];
      buildInputs = [ makeWrapper ];
      propagatedBuildInputs = plugins ++ package.propagatedBuildInputs;

      installPhase = ''
        makeWrapper ${package}/bin/taxi $out/bin/taxi \
          --prefix PYTHONPATH : "${package}/${python3.sitePackages}:$PYTHONPATH"
      '';
      doCheck = false;

      passthru = package.passthru // {
        withPlugins = morePlugins: withPlugins (morePlugins ++ plugins);
      };
    };

  package = python3Packages.buildPythonApplication rec {
    pname = "taxi";
    version = "6.1.0";

    # Using GitHub instead of PyPI because tests are not distributed on the PyPI releases
    src = fetchFromGitHub {
      owner = "liip";
      repo = pname;
      rev = version;
      sha256 = "1ax95s0x30kr19szmfmmsffbck489raq15c04ldh19zsf6f0knkq";
    };

    propagatedBuildInputs = [
      python3Packages.click
      python3Packages.appdirs
      python3Packages.setuptools
    ];
    checkInputs = [ python3Packages.pytest python3Packages.freezegun ];
    checkPhase = "pytest";

    passthru = { inherit withPlugins; };

    meta = {
      homepage = "https://github.com/liip/taxi";
      description = "Timesheeting made easy";
      license = lib.licenses.wtfpl;
    };
  };

  taxiZebra = python3Packages.buildPythonPackage rec {
    pname = "taxi_zebra";
    version = "2.3.1";

    src = python3.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "177fzasgchgbixrr4xikfbis8i427qlyb8c93d404rjjny9g7nny";
    };

    buildInputs = [ package ];
    propagatedBuildInputs = [ python3Packages.requests python3Packages.click ];
    doCheck = false;

    meta = {
      homepage = "https://github.com/sephii/taxi-zebra";
      description = "Zebra backend for the Taxi timesheeting application";
      license = lib.licenses.wtfpl;
    };
  };

  taxiClockify = python3Packages.buildPythonPackage rec {
    pname = "taxi_clockify";
    version = "1.4.1";

    src = python3.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "18cfdih1pc097xw893sagmajfk52d3k63z6fq5hg4k71njaxrbdb";
    };

    buildInputs = [ package ];
    propagatedBuildInputs = [ python3Packages.requests python3Packages.arrow ];
    doCheck = false;

    meta = {
      homepage = "https://github.com/sephii/taxi-clockify";
      description = "Clockify backend for the Taxi timesheeting application";
      license = lib.licenses.wtfpl;
    };
  };

  taxiPetzi = python3Packages.buildPythonPackage rec {
    pname = "taxi_petzi";
    version = "1.0.0";

    src = python3.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "1zp6jpamrjgmaw2bpcdi8znxspn7v8f3hm3f8k9whjvc2q849ziq";
    };

    buildInputs = [ package ];
    propagatedBuildInputs = [
      python3Packages.google-auth-oauthlib
      python3Packages.google_api_python_client
    ];
    doCheck = false;

    meta = {
      homepage = "https://github.com/sephii/taxi-petzi";
      description = "Petzi backend for the Taxi timesheeting application";
      license = lib.licenses.wtfpl;
    };
  };
in {
  taxi = package.withPlugins [ taxiZebra ];
  taxi_zebra = taxiZebra;
  taxi_clockify = taxiClockify;
  taxi_petzi = taxiPetzi;
}
