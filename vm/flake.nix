{
  description = "Presburger VM (frontend + FastAPI + converter)";

  inputs = {
    nixpkgs     .url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils .url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachSystem [ "x86_64-linux" ] (system:
      let
        pkgs = import nixpkgs { inherit system; };

        # ──────────────────────────────────────────────────────────────
        # 1️⃣  Build the static Next.js export inside Nix
        # ──────────────────────────────────────────────────────────────
        frontend = pkgs.buildNpmPackage {
          pname         = "frontend";
          version       = "0.1.0";
          src           = ./frontend;               # whole Next.js project
          npmDepsHash   = "sha256-REPLACE-ME";      # ← Run `nix build .#frontend`
                                                    #   once, copy the printed hash.
          installPhase  = ''
            runHook preInstall
            next build
            next export -o $out
            runHook postInstall
          '';
          # optional optimisation:
          npmBuildScript = "build";
          NODE_ENV       = "production";
        };

        # ──────────────────────────────────────────────────────────────
        # 2️⃣  Copy back-end & converter sources into the store closure
        # ──────────────────────────────────────────────────────────────
        backendSrc   = pkgs.symlinkJoin { name = "backend-src";  paths = [ ./backend ]; };
        converterSrc = pkgs.symlinkJoin { name = "converter";    paths = [ ./presburger_converter ]; };

        # ──────────────────────────────────────────────────────────────
        # 3️⃣  Define the VM, injecting the three paths via _module.args
        # ──────────────────────────────────────────────────────────────
        vmConfig = nixpkgs.lib.nixosSystem {
          inherit system;
          modules = [
            ./configuration.nix
            ({ ... }: {
              _module.args = {
                frontendPath  = frontend;
                backendPath   = backendSrc;
                converterPath = converterSrc;
              };
            })
          ];
        };
      in {
        # Expose artefacts for easy `nix build .#vm`
        packages = {
          frontend  = frontend;
          backend   = backendSrc;
          converter = converterSrc;
          vm        = vmConfig.config.system.build.virtualBoxOVA;
        };

        # Convenience: `nixos-rebuild` etc. if you ever want it
        nixosConfigurations.vm = vmConfig;
      });
}