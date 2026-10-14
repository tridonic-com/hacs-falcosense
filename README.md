# Tridonic FalcoSENSE — HACS test distribution

Pre-release distribution of the **Tridonic FalcoSENSE** Home Assistant
integration for early testers, before it is available in Home Assistant core. It
integrates the [Tridonic FalcoSENSE](https://www.tridonic.com/de/int/product/32878)
people-counting / occupancy sensor over its local REST and MQTT APIs.

> This is a temporary channel. Once the integration ships in Home Assistant core,
> install it from there and remove this custom repository.

## Requirements

- A running Home Assistant instance (OS, Container, or Supervised recommended;
  these ship `git`, which is needed to install the `falcosense` dependency).
- [HACS](https://hacs.xyz) installed and linked to a GitHub account that has been
  **granted read access to this private repository**.
- Network access on the Home Assistant host (first setup installs the
  `falcosense` library from GitHub via pip).
- A commissioned FalcoSENSE sensor on your network with the MQTT endpoint enabled
  and an API token generated in its dashboard.

## Install

1. Ask the maintainer to grant your GitHub account read access to this repo, and
   make sure HACS on your instance is logged in as that account
   (HACS → three-dot menu → *Reload* after access is granted).
2. In Home Assistant: **HACS → Integrations → three-dot menu → Custom
   repositories**.
3. Add this repository's URL with category **Integration**.
4. Find **Tridonic FalcoSENSE** in HACS, install it, then **restart Home
   Assistant**.
5. Go to **Settings → Devices & Services → Add integration**, search for
   **FalcoSENSE** (under the Tridonic brand), and enter the sensor's host and
   API token.

## How this repo is maintained

The integration here is a copy of the core integration, kept in sync with
[`scripts/sync.py`](scripts/sync.py), which copies
`homeassistant/components/falcosense/` from a local Home Assistant core checkout
and applies the two changes a HACS custom integration needs: a `version` field
and a git-URL requirement for the `falcosense` library. Re-run it after any
change in core and cut a matching release tag.
