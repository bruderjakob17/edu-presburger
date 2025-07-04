{
  description = "Presburger VM (Next.js + FastAPI + converter)";

  inputs = {
    nixpkgs     .url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils .url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachSystem [ "x86_64-linux" ] (system:
      let
        pkgs = import nixpkgs { inherit system; };

        # ── 1  Build the static Next.js export inside Nix ───────────
        frontend = pkgs.buildNpmPackage {
          pname       = "frontend";
          version     = "0.1.0";
          src         = ../frontend;              # ← relative to vm/flake.nix
          npmDepsHash = "sha256-MURv5TIcfqa++/cTkRzPgrEPCdaG0DS7YVHBAG4zlVo=";
          installPhase = ''
            runHook preInstall
            next build
            next export -o $out               # produces static site
            runHook postInstall
          '';
          NODE_ENV = "production";
        };

        # ── 2  Copy back-end & converter sources into the store ─────
        backendSrc   = pkgs.symlinkJoin { name = "backend-src";  paths = [ ../backend ]; };
        converterSrc = pkgs.symlinkJoin { name = "converter";    paths = [ ../presburger_converter ]; };

        # ── 3  VM definition, injecting paths via _module.args ──────
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
        # Build targets you can call with `nix build`
        packages = {
          frontend  = frontend;
          backend   = backendSrc;
          converter = converterSrc;
          vm        = vmConfig.config.system.build.virtualBoxOVA;
        };

        # Optional: nixos-rebuild convenience
        nixosConfigurations.vm = vmConfig;
      });
}