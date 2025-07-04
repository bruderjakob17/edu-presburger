{ config
, pkgs
, modulesPath
, frontendPath
, backendPath
, converterPath
, ...
}:

let

    libmataPy = pkgs.python3Packages.buildPythonPackage rec {
    pname   = "libmata";
    version = "2025-04-15";          # any tag; it's “unstable” anyway
    format  = "pyproject";

    # The exact commit you already pinned in pyproject.toml
    src = pkgs.fetchFromGitHub {
      owner = "verifit";
      repo  = "mata";
      rev   = "56a4259c64d619906acd2ac2aed2b3cd26cad345";
      # Run `nix hash --type sha256 --base32 .` once to fill this:
      hash  = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";
    };

    subPackages = [ "bindings/python" ];

    nativeBuildInputs = [
      pkgs.cmake pkgs.pkg-config pkgs.swig
    ];
    propagatedBuildInputs = [
      pkgs.graphviz          # Mata calls `dot` at run-time
    ];
  };

  presburgerConverter = pkgs.python3Packages.buildPythonPackage rec {
    pname   = "presburger_converter";
    version = "0.1.0";
    format  = "pyproject";
    src     = converterPath;

    dontUseCmakeConfigure = true;
    dontUseCmakeBuild     = true;

    propagatedBuildInputs = [
      pkgs.python3Packages.lark-parser
      pkgs.python3Packages.graphviz
      libmataPy                            # ← use the wheel we just built
    ];
  };

  backendEnv = pkgs.python3.withPackages (ps: with ps; [
    fastapi uvicorn networkx matplotlib lxml numpy pydantic lark
    presburgerConverter
  ]);


  appDir = "/etc/opt-app";
in
{
  imports = [ "${modulesPath}/virtualisation/virtualbox-image.nix" ];

  networking.firewall.enable = false;

  users.users.user = {
    isNormalUser = true;
    password     = "user";
    extraGroups  = [ "wheel" "networkmanager" ];
  };

  # ─────────── Nginx: static site + /api proxy ─────────────────────────
  services.nginx.enable = true;
  services.nginx.virtualHosts."_" = {
    root = "${appDir}/frontend";
    locations."/" = { };
    locations."/api/" = {
      extraConfig = ''
        rewrite ^/api(/.*)$ $1 break;
        proxy_pass         http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
      '';
    };
  };

  # ─────────── FastAPI backend service ─────────────────────────────────
  systemd.services.backend = {
    description = "FastAPI backend";
    after       = [ "network.target" ];
    wantedBy    = [ "multi-user.target" ];

    serviceConfig = {
      WorkingDirectory = "${appDir}/backend";
      ExecStart =
        "${backendEnv}/bin/uvicorn main:app --host 0.0.0.0 --port 8000";
      Restart = "always";
    };
  };

  # ─────────── Copy artefacts into the VM image ────────────────────────
  environment.etc."opt-app/frontend".source  = frontendPath;
  environment.etc."opt-app/backend".source   = backendPath;
  environment.etc."opt-app/converter".source = converterPath;

  # Converter calls the `dot` binary → make it available system-wide
  environment.systemPackages = [ pkgs.graphviz ];

  services.openssh.enable = true;

  virtualbox.memorySize = 4096;
  virtualbox.vmName     = "presburger-to-automata-vm";
}