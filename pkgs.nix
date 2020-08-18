{ lib, fetchFromGitHub, makeWrapper, python3, python3Packages, ... }:

let
  withPlugins = plugins: python3Packages.buildPythonApplication {
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
    version = "6.0";

    # Using GitHub instead of PyPI because tests are not distributed on the PyPI releases
    src = fetchFromGitHub {
      owner = "liip";
      repo = pname;
      rev = version;
      sha256 = "11c27g946rgl3px5i60532hh8cscm933bpkwxl6fb29xg0q30wsy";
    };

    propagatedBuildInputs = [ python3Packages.click python3Packages.appdirs python3Packages.setuptools ];
    checkInputs = [ python3Packages.pytest python3Packages.freezegun ];
    checkPhase = "pytest";

    passthru = {
      inherit withPlugins;
    };

    meta = {
      homepage = "https://github.com/liip/taxi";
      description = "Timesheeting made easy";
      license = lib.licenses.wtfpl;
    };
  };

  taxiZebra = python3Packages.buildPythonPackage rec {
    pname = "taxi_zebra";
    version = "2.2.0";

    src = python3.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "15gr6b0xlml583kfnwynkj4i85q6jvmrczk0w939v9ip2hr3mwrn";
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
in
{
  taxi = package.withPlugins [ taxiZebra ];
  taxi_zebra = taxiZebra;
}
