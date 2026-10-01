# Flow Instability (Multiphase Heading & Oscillations) - Event 4

## 1. Event Name & Definition
- **Event Identifier:** Event 4 - Flow Instability
- **Category:** Wellbore & Flowline Hydrodynamic Instability / Heading
- **Severity Level:** Moderate to High Operational Disturbance

## 2. Physical Description & Meaning
Flow instability encompasses irregular, chaotic, or fluctuating flow dynamics inside the wellbore and near-wellbore piping (such as casing heading, density heading, or tubing flow instability). Unlike severe slugging (which is characterized by regular, well-defined riser-induced periodic cycles), flow instability manifests as chaotic, multi-frequency fluctuations in pressure, temperature, and volumetric flowrates. It typically arises from dynamic interactions between gas-lift injection points, casing-tubing gas storage volume, and liquid holdup fluctuations.

## 3. Typical Sensor Symptoms
- **P-PDG & P-TPT:** Erratic, non-harmonic oscillations without a single clear fixed period.
- **P-ANULAR & QGL (Gas Lift):** Unstable annular pressure indicating casing heading (gas alternately storing in the casing and rushing through gas lift valves into the tubing).
- **T-TPT / T-JUS-CKP:** High high-frequency jitter and irregular temperature excursions.
- **P-MON-CKP:** Continuous wandering and turbulence with elevated standard deviation ($\sigma$).

## 4. Possible Root Causes
1. **Casing Heading:** Compressible gas volume in the casing annulus charges and discharges intermittently through gas lift valves due to multiphase density changes in the tubing.
2. **Tubing Heading:** Cyclic fluid accumulation and expulsion inside the production tubing at low reservoir drive.
3. **Multi-Point Gas Lift Injection:** Inadvertent simultaneous gas injection through multiple downhole gas lift valves due to mismatched valve opening/closing pressures.
4. **Sub-Critical Choke Flow:** Choke operating in the sub-critical flow regime where downstream flowline pressure disturbances propagate upstream into the wellbore.

## 5. Diagnostic Verification Steps
1. Compare casing annulus pressure ($P_{ANULAR}$) with gas lift flowrate ($Q_{GL}$) and $P_{TPT}$. Out-of-phase oscillation confirms casing heading.
2. Calculate pressure ratio across the production choke ($P_{JUS-CKP} / P_{MON-CKP}$). If ratio > 0.55, the choke is non-critical and transmitting topside surges into the well.
3. Review gas lift mandrel valve diagnostics and gradient surveys.

## 6. Recommended Operator Actions
1. Adjust gas lift injection rate ($Q_{GL}$) to ensure stable critical flow through the operating gas lift orifice.
2. Slightly close the production choke ($ABER-CKP$) to transition into the critical acoustic flow regime, decoupling topside pressure fluctuations from the wellbore.
3. Perform acoustic fluid level measurement in the annulus to ensure no liquid loading above the operating gas lift valve.

## 7. Critical Safety Considerations
- Chronic cyclic stress on downhole gas lift check valves leading to seal degradation and backflow into the annulus.
- Disturbance to topside separation trains and gas compression turbines due to irregular surge delivery.

## 8. Relevant Sensor Relationships
- Elevated standard deviation $\sigma(P_{PDG})$, $\sigma(P_{TPT})$, $\sigma(P_{ANULAR})$ across sliding time windows.
- Strong negative phase correlation between $P_{ANULAR}$ and instantaneous $Q_{GL}$.
