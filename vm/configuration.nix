{ config, pkgs, modulesPath, ... }:

let
  # Where the app will live inside the VM
  appDir = "/etc/opt-app";

  # Bundle the three local folders into the flake closure
  frontendPath  = builtins.path { path = ../frontend/out;          name = "frontend-out"; };
  backendPath   = builtins.path { path = ../backend;               name = "backend-src";  };
  converterPath = builtins.path { path = ../presburger_converter;  name = "converter";    };

  # Build static Next.js export during the image build
  nextStatic = pkgs.buildNpmPackage {
    pname = "frontend";
    version = "0.1.0";
    src = ../frontend;                 # whole Next.js project
    npmDepsHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="; # fill in once

    installPhase = ''
      runHook preInstall
      next build
      next export -o $out
      runHook postInstall
    '';
  };

in
{
  # --- Import the VirtualBox image module (no pkgs recursion) ---------
  imports = [
    "${modulesPath}/virtualisation/virtualbox-image.nix"
  ];

  networking.firewall.enable = false;

  users.users.user = {
    isNormalUser = true;
    password     = "user";            # change or leave empty
    extraGroups  = [ "wheel" "networkmanager" ];
  };

  # --- Nginx: static site + proxy /api -> FastAPI ---------------------
  services.nginx.enable = true;
  services.nginx.virtualHosts."_" = {
    root = "${appDir}/frontend";
    locations."/" = {};
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

  # --- FastAPI backend ------------------------------------------------
  systemd.services.backend = {
    description = "FastAPI backend";
    after       = [ "network.target" ];
    wantedBy    = [ "multi-user.target" ];
    serviceConfig = {
      WorkingDirectory = "${appDir}/backend";
      ExecStart = "${pkgs.python3.withPackages (ps: with ps; [
        fastapi uvicorn networkx matplotlib lxml numpy
      ])}/bin/uvicorn main:app --host 0.0.0.0 --port 8000";
      Restart = "always";
    };
  };

  # --- Copy project parts into the image ------------------------------
  environment.etc."opt-app/frontend".source  = frontendPath;
  environment.etc."opt-app/backend".source   = backendPath;
  environment.etc."opt-app/converter".source = converterPath;

  services.openssh.enable = true;

  # VM resources / name
  virtualbox.memorySize = 4096;
  virtualbox.vmName     = "presburger-vm";

}