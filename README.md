# ISS Predicted Tracker for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/baylanger/iss_predicted_tracker/actions)
[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)](https://github.com/baylanger/iss_predicted_tracker/releases)

The **ISS Predicted Tracker** is an advanced, high-precision custom integration for Home Assistant that tracks the International Space Station locally using real-time orbital mechanics. It uses local SGP4 orbit propagation via `skyfield` and your Home Assistant zone coordinates to calculate live subpoint positions and predict upcoming overhead passes.

This integration utilizes the `skyfield` library and live CelesTrak TLE (Two-Line Element) data to perform **local SGP4 propagation**, giving you institutional-grade positional accuracy entirely offline and free of cloud dependencies.

---

## Features

- **Local SGP4 Tracking**: Computes position locally without relying on external cloud tracking APIs.
- **Multi-Entity Architecture**: Registers native Home Assistant sensors for status, altitude, and peak pass elevation.
- **Automatic Home Overhead Pass Detection**: Automatically calculates your upcoming local overhead passes using your Home Assistant zone coordinates (`latitude`, `longitude`, `elevation`), exposing transition times and maximum elevation attributes.
- **Map Optimized**: Exposes standard latitude, longitude, and elevation attributes natively compatible with Home Assistant's Map Card.
- **Resilient Caching**: Automatically handles transient CelesTrak server errors (HTTP 500) by falling back to last known good TLE data in memory, preventing sensors from dropping to `unavailable`.
- **HACS Ready**: Easily install and manage updates via the Home Assistant Community Store.

---

## Installation

### Option 1: HACS (Recommended)

1. Ensure you have [HACS](https://hacs.xyz/) installed.
2. Open HACS in your Home Assistant dashboard and go to **Integrations**.
3. Click the three dots in the top right corner and select **Custom repositories**.
4. Paste your GitHub repository URL (`https://github.com/baylanger/iss_predicted_tracker`) and select **Integration** as the category.
5. Click **Add**.
6. Find **ISS Predicted Tracker** in the list, click **Download**, and restart Home Assistant.

### Option 2: Manual Installation

1. Download or clone this repository.
2. Copy the `custom_components/iss_predicted_tracker` folder into your Home Assistant configuration directory (`/config/custom_components/`).

---

### Configuration (Required for both methods)
Add the following entry to your `configuration.yaml` file:

```yaml
iss_predicted_tracker:
```
Restart Home Assistant to complete the setup.

---

## Entity States & Attributes

Multi-entity architecture and telemetry attributes:

### Provided Entities

The integration automatically discovers and registers three native Home Assistant sensors:

1. **`sensor.iss_status`**
   - **State**: High-level mission status (`In Orbit`, `Approaching (...)`, `Overhead Now!`).
   - **Attributes**: 
     - `latitude`, `longitude` : Live coordinates
     - `next_pass_time` : ISO8601 timestamp of the next upcoming orbital pass over your home coordinates
     - `next_pass_event` : The phase of the pass (Rise (Above 10°), Culmination (Highest Point), or Set
       - Rise (Above 10°): The ISS crosses above your 10° horizon threshold. It enters your visible sky.
       - Culmination (Highest Point): The ISS reaches its peak elevation angle in the sky directly above (or closest to) your home coordinates.
       - Set: The ISS dips back below the 10° threshold, ending the visible pass.
     - `source` : Tracking engine identifier (Local SGP4 Engine)

2. **`sensor.iss_orbital_altitude`**
   - **State**: Physical orbital altitude in kilometers (`km`).
   - **Unit of Measurement**: `km`
   - **Device Class**: `measurement`

3. **`sensor.iss_next_pass_max_elevation`**
   - **State**: Peak sky elevation angle in degrees (`°`) for the next overhead pass.
   - **Unit of Measurement**: `°`
   - **State Class**: `measurement`

---

## Recommended Map Card Setup

To keep the map cleanly zoomed out on a global view and display the historical trail of the ISS with timestamps, add a Manual card to your dashboard using the following YAML configuration:

```yaml
auto_fit: false
default_zoom: 2
entities:
  - entity: sensor.iss_predicted_position
    name: ISS
hours_to_show: 0.25
theme_mode: auto
type: map
```
Map Options Explained:
- `default_zoom: 2`: Keeps the map view zoomed out globally across the planet.
- `auto_fit: false`: Prevents the map from aggressively resetting or jumping focus every time coordinates update.
- `hours_to_show`: 0.25: Plots a trailing history line (approx. 15 minutes of movement) on the map so you can hover over previous points to see timestamps and direction of travel.
- `theme_mode: auto`: Automatically adjusts to match your dashboard's light or dark theme mode.

---

## License
This project is licensed under the MIT License. See the LICENSE file for details.
