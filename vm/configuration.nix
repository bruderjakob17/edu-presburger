{ config
, pkgs
, modulesPath
, frontendPath      # ← injected by flake.nix
, backendPath
, converterPath
, ... }:

let
  # Where the app lives inside the VM
  appDir = "/etc/opt-app";
in
{
  # ── Build a VirtualBox image ───────────────────────────────────────
  imports = [ "${modulesPath}/virtualisation/virtualbox-image.nix" ];

  # Disable firewall for demo convenience
  networking.firewall.enable = false;

  # Simple user
  users.users.user = {
    isNormalUser = true;
    password     = "user";            # change if you like
    extraGroups  = [ "wheel" "networkmanager" ];
  };

  # ── Nginx: static site + proxy /api -> FastAPI ─────────────────────
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

  # ── FastAPI backend (runs under systemd) ───────────────────────────
  systemd.services.backend = {
    description  = "FastAPI backend";
    after        = [ "network.target" ];
    wantedBy     = [ "multi-user.target" ];
    serviceConfig = {
      WorkingDirectory = "${appDir}/backend";
      ExecStart        = "${pkgs.python3.withPackages (ps: with ps; [
                            fastapi uvicorn networkx matplotlib lxml numpy
                          ])}/bin/uvicorn main:app --host 0.0.0.0 --port 8000";
      Restart          = "always";
    };
  };

  # ── Copy project parts into the VM closure ─────────────────────────
  environment.etc."opt-app/frontend".source  = frontendPath;
  environment.etc."opt-app/backend".source   = backendPath;
  environment.etc."opt-app/converter".source = converterPath;

  # Optional: SSH into the VM
  services.openssh.enable = true;

  # VM resources / name
  virtualbox.memorySize = 4096;
  virtualbox.vmName     = "presburger-vm";
}