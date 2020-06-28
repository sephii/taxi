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
    version = "5.0";

    # Using GitHub instead of PyPI because tests are not distributed on the PyPI releases
    src = fetchFromGitHub {
      owner = "liip";
      repo = pname;
      rev = "cfc33d044182ac978220ad6421c9802b493c9a43";
      sha256 = "09mla5wqkiwxx8higr7d3bl2gi569np68yxzddcsi7r93cwqbysb";
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
    version = "2.1.0";

    src = python3.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "1nzxpp49kfwzfq909ixqyynhnaqrqdn0r2zdix7p5cy14sxydhnh";
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
