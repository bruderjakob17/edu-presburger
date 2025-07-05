{
  description = "Presburger to Automata Converter VM";

  inputs = {
    nixpkgs     .url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils .url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachSystem [ "x86_64-linux" ] (system:
      let
        pkgs = import nixpkgs { inherit system; };

        # ── 1 Copy artefacts into the Nix store ──────────────────────────
        frontendOut = pkgs.symlinkJoin {
          name  = "frontend-out";
          paths = [ ../frontend/out ];          # <-- pre-built static site
        };

        backendSrc = pkgs.symlinkJoin {
          name  = "backend-src";
          paths = [ ../backend ];
        };

        converterSrc = pkgs.symlinkJoin {
          name  = "presburger_converter";
          paths = [ ../presburger_converter ];
        };

        # ── 2 Define the VM, injecting paths via _module.args ────────────
        vmConfig = nixpkgs.lib.nixosSystem {
          inherit system;
          modules = [
            ./configuration.nix
            ({ ... }: {
              _module.args = {
                frontendPath  = frontendOut;
                backendPath   = backendSrc;
                converterPath = converterSrc;
              };
            })
          ];
        };
      in {
        # `nix build .#vm` produces your .ova
        packages = {
          frontend  = frontendOut;          # optional convenience outputs
          backend   = backendSrc;
          converter = converterSrc;
          vm        = vmConfig.config.system.build.virtualBoxOVA;
        };

        # optional: nixos-rebuild convenience
        nixosConfigurations.vm = vmConfig;
      });
}