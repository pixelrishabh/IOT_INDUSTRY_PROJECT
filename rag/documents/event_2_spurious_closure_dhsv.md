# Spurious Closure of DHSV (Downhole Safety Valve) - Event 2

## 1. Event Name & Definition
- **Event Identifier:** Event 2 (Transient: 102) - Spurious Closure of DHSV
- **Category:** Safety Critical Subsea Valve Mechanical/Hydraulic Malfunction
- **Severity Level:** Critical / Immediate Production Interruption

## 2. Physical Description & Meaning
The Downhole Safety Valve (DHSV / SSSV) is a failsafe-closed flapper valve positioned typically 100-300 meters below the seabed inside the production tubing. It is held open by continuous hydraulic pressure supplied via a small hydraulic control line from the topside surface hydraulic power unit (HPU). A spurious closure occurs when the valve snaps or drifts shut uncommanded due to loss of hydraulic pressure, line leakage, or mechanical spring/flapper failure, instantly blocking the well's entire production conduit.

## 3. Typical Sensor Symptoms
- **P-PDG (Downhole Pressure):** Sudden steep pressure buildup (rapid transition towards static reservoir shut-in pressure, $P_{res}$) as flow stops abruptly.
- **P-TPT & P-MON-CKP:** Instantaneous catastrophic drop towards downstream flowline backpressure or vacuum.
- **T-TPT & T-JUS-CKP:** Gradual thermal decay towards ambient seabed temperature (~4 °C in deepwater) due to cessation of warm reservoir fluids.
- **Flowrate / Mass Flow:** Drops to zero instantaneously.
- **DHSV Control Line Pressure ($P_{hyd}$):** Often drops below the minimum valve hold-open threshold (e.g., < 3,000 psi).

## 4. Possible Root Causes
1. **Hydraulic Control Line Rupture / Leakage:** Loss of hydraulic fluid in the subsea umbilical control conduit holding the flapper actuator.
2. **Topside Hydraulic Power Unit (HPU) Solenoid Glitch:** Inadvertent de-energizing of safety ESD solenoids or hydraulic manifold pressure drops.
3. **Mechanical Flapper / Spring Latch Failure:** Particulate jamming, scale accumulation, or spring fatigue inside the safety valve assembly.
4. **Hydraulic Seal Elastomer Degradation:** O-ring/seal blow-by within the DHSV piston chamber under downhole temperature and pressure.

## 5. Diagnostic Verification Steps
1. Observe the signature: $P_{PDG} \uparrow$ simultaneously with $P_{TPT} \downarrow$ and $P_{MON-CKP} \downarrow$. This opposite divergence confirms downhole blockage below TPT.
2. Check topside HPU hydraulic pressure gauges on the well's dedicated DHSV line.
3. Verify hydraulic fluid replenishment rate and check for rapid HPU header pressure bleed.
4. Confirm with subsea control module (SCM) telemetry whether any ESD command was registered.

## 6. Recommended Operator Actions
1. Immediately throttle/close the topside production choke ($ABER-CKP$) to prevent extreme pressure differential surges across downstream valves.
2. Check HPU hydraulic supply pressure and attempt controlled hydraulic re-opening according to operator safety procedures.
3. Equalize pressure across the DHSV flapper if an equalization prong/pump-in procedure is available before applying opening hydraulic pressure.
4. If hydraulic pressure cannot be maintained, notify subsea intervention team for wireline valve replacement or storm choke setting.

## 7. Critical Safety Considerations
- **Water Hammer / Hydraulic Shock:** Sudden closure generates an acoustic pressure shockwave downhole.
- **Depressurization Hazards:** Rapid evacuation of topside flowlines can destabilize gas/liquid interfaces in separators.
- **DO NOT attempt to force open** against excessive differential pressure ($\Delta P > 50$ bar) to prevent shearing the valve flapper mechanism.

## 8. Relevant Sensor Relationships
- $P_{PDG} \rightarrow P_{static}$ (sharp positive slope $\frac{dP_{PDG}}{dt} \gg 0$)
- $P_{TPT} \rightarrow 0$ or $P_{separator}$ (sharp negative slope $\frac{dP_{TPT}}{dt} \ll 0$)
- Inverted pressure differential across tubing.
