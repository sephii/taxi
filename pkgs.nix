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
    version = "6.0.1";

    # Using GitHub instead of PyPI because tests are not distributed on the PyPI releases
    src = fetchFromGitHub {
      owner = "liip";
      repo = pname;
      rev = version;
      sha256 = "13nj3w76dk7h64y6phapkwa6iwdwpsnwlf5l6mmfcalbplpyvcxc";
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
    version = "2.3.0";

    src = python3.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "1gwqhpxi12lpsd73q8rhak0lkmjncnd741d65hgfvfzvvyaayddy";
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
    version = "1.3";

    src = python3.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "1gb47sn19s441w5wnd52j28ncqmw22cjmg5j6kiw3khdi37y24va";
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
in {
  taxi = package.withPlugins [ taxiZebra ];
  taxi_zebra = taxiZebra;
  taxi_clockify = taxiClockify;
}
