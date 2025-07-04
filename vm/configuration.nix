{ config
, pkgs
, modulesPath
, frontendPath
, backendPath
, converterPath
, ...
}:

let

  presburgerConverter = pkgs.python3Packages.buildPythonPackage rec {
    pname   = "presburger_converter";
    version = "0.1.0";          # or leave = "unstable-2025-07-04"

    # Tell Nix it's a PEP-517 (pyproject) build, no setup.py
    format = "pyproject";
    src    = converterPath;

    # Converter’s pyproject lists lark, graphviz, libmata@Git …
    # libmata’s build needs CMake, SWIG, etc.  Add them here.
    nativeBuildInputs = [ pkgs.cmake pkgs.pkg-config pkgs.swig ];
    propagatedBuildInputs = [ pkgs.graphviz ];  # runtime needs `dot`

    # If the Git checkout in pyproject.toml fetches sub-dir bindings,
    # buildPythonPackage will handle it automatically.
  };

  # ──────────────────────────────────────────────────────────────────────
  # 2. One Python interpreter for the backend *including* the converter
  # ──────────────────────────────────────────────────────────────────────
  backendEnv = pkgs.python3.withPackages (ps: with ps; [
    fastapi uvicorn networkx matplotlib lxml numpy pydantic lark
    presburgerConverter     # ← pulls in lark, graphviz, libmata, …
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