# Autoterm Heater Integration

This custom integration allows Home Assistant to communicate with an **Autoterm Air 2D Heater** via usb-serial port.

## Features:

- Control heater power (on/off)
- Set target temperature
- Monitor current temperature
- Retrieve heater status

## Installation

1. **Install via HACS**:
   - Add this repository to HACS as a custom repository.
   - Search for `Autoterm Heater Integration` and install it.
2. **Manual Installation**:
   - Copy the `autoterm` folder into `custom_components/`.

## Configuration

1. Add the integration via the UI
2. Select the usb port

## About the temperature sensor:

The _Operating Mode_ is kind of tied to the _Temperature Sensor_ entity. When selecting _Stufenregelung_ the temp sensor is changed to _Manual_, when selecting _Thermostat_, the temp sensor is changed to _Bedienpanel_. (For completeness: the _Heizgerät_ Sensor is measuring the inlet temp of the heater).

When _Bedienpanel_ is selected, the actual temperature sensor is selected in the _External temperature sensor_ Entity. This should list all temperature sensors in HA.

## Additional Templates

### UI Card displaying the temperature range for _Thermostat_

```
type: markdown
content: >-
  {{states("number.autoterm_air_2d_target_temperature") | round(0) -
  2}}-{{states("number.autoterm_air_2d_target_temperature") | round(0) + 1}} °C
```

### Scheduler Card

from https://github.com/nielsfaber/scheduler-card

```yaml
type: custom:scheduler-card
include:
  - climate
exclude: []
```

### Burning off residue every 30 days

create an input datetime (Settings -> Devices & Services -> Helpers -> Add Helper -> Date and Time ):
`input_datetime.last_time_heater_burned`

and add these two automations:

```yaml
alias: Heizung hat gebrannt
description: ""
triggers:
  - trigger: numeric_state
    entity_id:
      - sensor.autoterm_air_2d_flame_temperature
    for:
      hours: 0
      minutes: 30
      seconds: 0
    above: 200
conditions: []
actions:
  - action: input_datetime.set_datetime
    metadata: {}
    target:
      entity_id: input_datetime.last_time_heater_burned
    data:
      date: "{{ now().strftime('%Y-%m-%d') }}"
mode: single
```

```yaml
alias: Heizung alle 30 Tage ausbrennen
description: ""
triggers:
  - trigger: time
    at: "14:00:00"
conditions:
  - condition: template
    value_template: >-
      {{ (now() - states('input_datetime.last_time_heater_burned') |
      as_datetime).days >= 30 }}
actions:
  - action: notify.persistent_notification
    metadata: {}
    data:
      title: Autoterm lange nicht benutzt
      message: >-
        Heizung muss ausgebrannt werden um viskose Filmsedimente auf beweglichen
        Teilen der Kraftstoffpumpe zu entfernen.
mode: single
```

## Support

For issues, please open a ticket on [GitHub Issues](https://github.com/hutterm/Autoterm-Air-2D-HACS/issues).

## Maintainer: Creating versioned HACS releases

This repository includes a release workflow at `.github/workflows/release.yaml`.

### Triggering a release

1. Open **GitHub → Actions → Create HACS release**.
2. Click **Run workflow**.
3. Choose the branch to release from (usually `master`).
4. Enter `version` as `x.y.z` or `vx.y.z` (example: `0.3.0`).
5. Optional: set `prerelease` to `true` for test/beta releases.

### How version numbers are set

- The workflow normalizes the input to `x.y.z` and creates tag `vx.y.z`.
- It updates `custom_components/autoterm/manifest.json` `version` to `x.y.z`.
- It commits that version bump to the selected branch (if needed), then tags that commit.
- A GitHub Release is created for the new tag.

### What commit is released

- The release is **not always the latest commit in the repository**.
- It is the exact commit that gets tagged during the workflow run (the selected branch tip, plus the manifest bump commit when version changes).
- Commits pushed later are not part of that release until a new version/tag is created.
