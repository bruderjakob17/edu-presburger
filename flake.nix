# flake.nix – root of your repository
{
  description = "Next.js + FastAPI reproducible VM for bachelor thesis";

  ## ------------------------------------------------------------------
  ## 1. Pin inputs so that NO external state can change the build
  ## ------------------------------------------------------------------
  inputs = {
    # Stable channel pin – change to a specific commit if you need bit-for-bit
    nixpkgs.url          = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url      = "github:numtide/flake-utils";
    nixos-generators.url = "github:nix-community/nixos-generators";
  };

  ## ------------------------------------------------------------------
  ## 2. Define outputs (packages, NixOS configs, dev-shell)
  ## ------------------------------------------------------------------
  outputs = { self, nixpkgs, flake-utils, nixos-generators, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          # Turn this on only if you actually need proprietary stuff
          config.allowUnfree = false;
        };

        ## -------------------------------------------------------------
        ## 2.1  Python environment for FastAPI backend
        ## -------------------------------------------------------------
        presburgerConverter = pkgs.python3Packages.buildPythonPackage rec {
          pname = "presburger_converter";
          version = "0.1.0";   # bump if you tag the module
          src = ./presburger_converter;  # local editable module
          format = "setuptools";         # ≅ "python setup.py install"
          propagatedBuildInputs = [];
        };

        backendEnv = pkgs.python3.withPackages (ps: with ps; [
          fastapi uvicorn presburgerConverter
          # add any other libraries from backend/requirements.txt here
        ]);

        ## -------------------------------------------------------------
        ## 2.2  Build the Next.js frontend completely offline
        ##       Uses buildNpmPackage so npm / node_modules is vendored
        ## -------------------------------------------------------------
        frontendStatic = pkgs.buildNpmPackage {
          pname = "frontend-static";
          version = "0.1.0";
          src = ./frontend;      # your Next.js app root

          # ──► IMPORTANT ◄──
          #   Leave this fake hash for the first run. Nix will fail once,
          #   printing the real sha256.  Paste that here and rebuild.
          npmDepsHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";

          npmBuild = "npm ci && npm run build && npm run export";
          installPhase = ''
            mkdir -p $out
            cp -r out/* $out/
          '';
        };

        ## -------------------------------------------------------------
        ## 2.3  NixOS VM definition (VirtualBox OVA target)
        ## -------------------------------------------------------------
        vmConfig = { config, pkgs, ... }:
        {
          # Module that wires up VirtualBox guest additions + OVA export
          imports = [
            "${pkgs.path}/nixos/modules/virtualisation/virtualbox-image.nix"
          ];

          system.stateVersion = "24.05";  # don’t change once public!
          networking.hostName = "thesis-vm";
          networking.firewall.allowedTCPPorts = [ 80 8000 ];

          ## Users ─ minimal, change password for production
          users.users.thesis = {
            isNormalUser = true;
            extraGroups = [ "wheel" ];
            initialPassword = "thesis";
          };

          ## Packages baked into the image
          environment.systemPackages = [ backendEnv pkgs.git ];

          ## ------------ Web frontend served by nginx ------------
          services.nginx = {
            enable = true;
            virtualHosts."_" = {
              root = "${frontendStatic}";
              extraConfig = ''
                # Every request that isn’t a file → index.html (single-page)
                try_files $uri $uri/ /index.html;
              '';
            };
          };

          ## ------------ FastAPI backend -------------------------
          systemd.services.backend = {
            description = "FastAPI backend (uvicorn)";
            wantedBy    = [ "multi-user.target" ];
            after       = [ "network.target" ];
            serviceConfig = {
              WorkingDirectory = "${./backend}";
              ExecStart        = "${backendEnv}/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000";
              Restart          = "always";
            };
          };

          ## Enable VirtualBox guest additions so Clipboard, etc. work
          virtualisation.virtualbox.guest.enable = true;
        };

        ## Build a full NixOS system from the module above
        nixosSystem = pkgs.lib.nixosSystem {
          inherit system;
          modules = [ vmConfig ];
        };
      in {
        packages.${system}.ova = nixosSystem.config.system.build.virtualBoxOVA;

        ## Optional: a dev-shell matching the production env
        devShells.default = pkgs.mkShell {
          buildInputs = [ backendEnv pkgs.nodejs_20 ];
        };
      }
    );
}
