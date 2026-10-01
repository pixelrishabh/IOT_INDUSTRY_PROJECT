# Normal Operation (Baseline State) - Offshore Production Well

## 1. Event Name & Definition
- **Event Identifier:** Event 0 - Normal Operation
- **Category:** Steady-State Production
- **Standard Operating Window:** Stable multiphase flow from subsea reservoir to topside production separator with all actuated valves in nominal command position.

## 2. Physical Description & Meaning
During normal operation, the well operates in a stable thermodynamic and hydraulic regime. Fluid flows continuously from the formation through the perforations, up the production tubing, past the Downhole Safety Valve (DHSV), across the subsea Christmas Tree, through the Production Choke (PCK), and along the production flowline to the platform.

## 3. Typical Sensor Symptoms & Nominal Ranges
- **P-PDG (Downhole Gauge Pressure):** Stable, within expected drawdown range (typically 200 - 350 bar depending on reservoir depth and depletion).
- **P-TPT (Transducer Pressure):** Stable upstream of the wellhead (typically 120 - 200 bar).
- **T-TPT (Transducer Temperature):** Stable operating temperature (typically 60 - 90 °C).
- **P-MON-CKP (Upstream Choke Pressure):** Stable, tracking tubing head pressure with negligible short-term variance.
- **T-JUS-CKP (Downstream Choke Temperature):** Stable, reflecting steady Joule-Thomson expansion across the choke orifice.
- **P-ANULAR (Annulus 'A' Pressure):** Low and stable, showing no tubing-to-annulus communication.
- **QGL (Gas Lift Flow Rate):** Constant rate matching the lift allocation setpoint (if gas-lifted).
- **ABER-CKP / ABER-CKGL:** Fixed at steady supervisory setpoint (e.g., 40% - 80%).

## 4. Normal Operating Variations
- Minor diurnal temperature fluctuations in seawater surrounding the riser/flowline.
- Controlled ramp-ups or choke adjustments initiated by operators during well testing.

## 5. Diagnostic Verification Steps
1. Verify that sensor variance (`std_dev`) over 60s windows remains within baseline noise threshold (< 1.5% mean).
2. Check differential pressure across PCK ($\Delta P = P_{MON} - P_{JUS}$) aligns with production curves.
3. Confirm Annulus 'A' pressure does not exhibit sustained linear build-up.

## 6. Recommended Operator Actions
- Maintain regular routine monitoring of downhole pressure and temperature trends.
- Log daily production rates (oil, water, gas) and compare against reservoir management targets.
- Ensure routine DHSV trip tests and choke calibration schedules are adhered to.

## 7. Safety Considerations
- Maintain continuous watchdog on high-pressure alarms and emergency shutdown (ESD) interlocks.
- Ensure subsea valve hydraulic accumulator pressures remain within certified API 14A/14B operating margins.

## 8. Sensor Correlation Rules
- $P_{PDG} > P_{TPT} > P_{MON-CKP} > P_{JUS-CKP}$ (Monotonic hydraulic gradient).
- Steady positive correlation between production choke opening ($ABER-CKP$) and wellhead pressure response.
