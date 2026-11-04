# venus (Orion stage/prod server) public keys — recorded 2026-11-04

Server: venus, 192.168.0.12, Ubuntu 26.04. Postgres 18 cluster in /home/postgres/18/main. orion-host.sh self-check 33/33 (Mike).

## Generated on venus by orion-host.sh (private halves stay in ~orion-<env>/shared/)
- orion-prod publish (deploy key, write, on masha256/orion-data):
  ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDEB6S/G7YNvA2jH3A8cSe3sKrRaTG9IvQ0nSxcUEYd9 orion-prod@venus publish
- orion-prod snapshot-sign (Ed25519 SPKI base64; site verifies manifest.json.sig):
  MCowBQYDK2VwAyEAFWvePLjGZVZOBaaSpNDefVJbbZOEzMJbOzVs4lywBbY=
- orion-stage publish (deploy key, write, on masha256/orion-data-staging):
  ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAYaNjoMAW3OLfke1jrOdxNLRC/hRhce7P6a9gHThq1L orion-stage@venus publish
- orion-stage snapshot-sign:
  MCowBQYDK2VwAyEABJnZmEHl2pvXsFrr8XEu7R32y4I7F2gmWG/shLUn8KQ=

## Deploy keys on this host (uranus, user hermes), forced-command only on venus
- ~/.ssh/orion-stage_ed25519: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAnGss/Syg3k15JUU7/pD0MP65wZ5hY4jPfwqpT9UM4O raymond@uranus deploy orion-stage
- ~/.ssh/orion-prod_ed25519:  ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIM2H4n9BVsIVD8LlFsELVKD6l+eoVhASJ2wguJzbp6lS raymond@uranus deploy orion-prod
