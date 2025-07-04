{
  description = "Presburger Arithmetic to Automaton OVA VM";

  inputs = {
    nixpkgs.url      = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url  = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    let
      mkSystem = system:
        let
          pkgs = import nixpkgs { inherit system; };
        in {
          packages.vm =
            self.nixosConfigurations.vm.config.system.build.virtualBoxOVA;
        };

    in flake-utils.lib.eachDefaultSystem mkSystem // {
      nixosConfigurations.vm = nixpkgs.lib.nixosSystem {
          system = "x86_64-linux";
          modules = [ ./configuration.nix ];
      };
    };
}