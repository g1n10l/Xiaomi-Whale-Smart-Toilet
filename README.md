# Xiaomi Mijia Whale Smart Toilet Cover

[![HACS validation](https://github.com/g1n10l/Xiaomi-Whale-Smart-Toilet/actions/workflows/hacs.yaml/badge.svg)](https://github.com/g1n10l/Xiaomi-Whale-Smart-Toilet/actions/workflows/hacs.yaml)
[![Hassfest](https://github.com/g1n10l/Xiaomi-Whale-Smart-Toilet/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/g1n10l/Xiaomi-Whale-Smart-Toilet/actions/workflows/hassfest.yaml)

A local Home Assistant integration for the **Xiaomi Mijia Whale Smart Toilet Cover**, model `xjx.toilet.pro`. It communicates directly with the device through Xiaomi miIO and does not require the Xiaomi cloud after setup.

This project modernizes [tykarol/home-assistant-xjx-toilet-pro](https://github.com/tykarol/home-assistant-xjx-toilet-pro) for Home Assistant 2026.9 and newer. It replaces the old YAML setup and no longer requires the separate `toiletlid` component.

## Features

- Setup and reconfiguration through the Home Assistant interface
- Local polling every 30 seconds
- Seat occupancy binary sensor
- Air filter status binary sensor
- Night LED switch
- Self-cleaning switch
- Experimental warm-air drying switch
- Experimental warm-air temperature selector with three levels
- `xjx_toilet_pro.send_command` action for advanced automations
- Stable device and entity identifiers based on the device MAC address

## Requirements

- Home Assistant 2026.9.0 or newer
- Xiaomi Mijia Whale Smart Toilet Cover with model identifier `xjx.toilet.pro`
- A fixed or DHCP-reserved IP address for the device
- The device's 32-character local miIO token

## Install with HACS

1. Open HACS and select **Custom repositories** from the menu.
2. Add `https://github.com/g1n10l/Xiaomi-Whale-Smart-Toilet` as an **Integration** repository.
3. Find **Xiaomi Mijia Whale Smart Toilet Cover** and select **Download**.
4. Restart Home Assistant.
5. Open **Settings > Devices & services > Add integration**.
6. Search for the integration and enter the device IP address and miIO token.

## Manual installation

Copy `custom_components/xjx_toilet_pro` to `/config/custom_components/xjx_toilet_pro`, restart Home Assistant, then add the integration from **Settings > Devices & services**.

## Migrating from the old integration

1. Remove or disable `custom_components/toiletlid` and the previous `custom_components/xjx_toilet_pro` version.
2. Remove the old YAML configuration, for example:

   ```yaml
   toiletlid:
     - platform: xjx_toilet_pro
       host: 192.168.1.50
       token: !secret xjx_toilet_pro_token
   ```

3. Install this version, restart Home Assistant, and configure the device through the interface.

## Warm-air drying

The **Warm-air drying** switch starts drying with `warm_dry_on` and stops it with
`func_off ["warm_dry"]`. The device does not reliably report the drying state,
so Home Assistant displays the last state requested during the current
integration session.

The **Warm-air temperature** selector sends `set_fan_temp` with these levels:

- Low: level 1, approximately 36°C
- Medium: level 2, approximately 43°C
- High: level 3, approximately 50°C

The device does not reliably report `fan_temp`, so Home Assistant displays the
last level selected during the current integration session.

## Raw command action

The `xjx_toilet_pro.send_command` action accepts these fields:

- `config_entry_id`: the integration entry to target
- `command`: the raw miIO command name
- `params`: an optional list or mapping of command parameters

Example:

```yaml
action: xjx_toilet_pro.send_command
data:
  config_entry_id: 01JEXAMPLE123456789
  command: func_off
  params:
    - night_led
```

Raw commands bypass the safeguards provided by entities. Use them only when you know how the device handles the selected command.

## Troubleshooting

- Reserve the device IP address in your router. A changed address will interrupt local communication.
- Check that the miIO token contains exactly 32 characters.
- Keep Home Assistant and the toilet cover on networks that can communicate over the local LAN.
- Enable debug logging if setup or polling fails:

  ```yaml
  logger:
    logs:
      custom_components.xjx_toilet_pro: debug
      miio: debug
  ```

The integration never writes the miIO token to its own logs. Review logs before sharing them and remove any private network details.

## Hardware testing

The modernization has passed static validation but has not yet been tested by the maintainer with a physical `xjx.toilet.pro` device. Please report hardware results and relevant sanitized logs through [GitHub Issues](https://github.com/g1n10l/Xiaomi-Whale-Smart-Toilet/issues).

## License and credits

Released under the MIT License. Thanks to [tykarol](https://github.com/tykarol) for the original integration and the device command research.
