# Hydrate in Service Line (Gas Lift / Service Line Plugging) - Event 9

## 1. Event Name & Definition
- **Event Identifier:** Event 9 (Transient: 109) - Hydrate in Service Line
- **Category:** Flow Assurance / Auxiliary Line Plugging
- **Severity Level:** High Flow Assurance & Well Support Impact

## 2. Physical Description & Meaning
Subsea service lines provide vital auxiliary fluid connectivity to offshore production wells, including continuous gas-lift injection lines, chemical injection lines, hydraulic service lines, and well-kill/scale-squeeze lines. Hydrate formation inside service lines occurs when high-pressure gas (e.g. lift gas with residual moisture) or water-bearing service fluids cool in the cold seabed environment (~4 °C). Solid hydrate crystal formation in the service line blocks gas-lift delivery or chemical treatment, disrupting artificial lift and precipitating well stall.

## 3. Typical Sensor Symptoms
- **P-JUS-CKGL & P-MON-CKGL:** Sharp pressure buildup upstream of the service line blockage, or abnormal gas lift manifold supply pressure.
- **QGL (Gas Lift Flow Rate):** Steep decay down to zero flowrate despite fully open gas lift choke ($ABER-CKGL = 100\%$).
- **P-ANULAR (Annular Pressure):** Rapid drop in casing annulus pressure as lift gas fails to replenish the annular volume while downhole valves continue drawing gas.
- **P-PDG & P-TPT:** Secondary loss of well drawdown and decaying production rate as artificial gas lift assistance ceases.

## 4. Possible Root Causes
1. **Wet / Inadequately Dehydrated Lift Gas:** Dewpoint breakthrough in the topside molecular sieve / TEG gas dehydration contactor unit, introducing free water into the high-pressure gas lift stream.
2. **Cold Subsea Gas Line Exposure:** Uninsulated service line resting on the ocean floor operating at high pressure (150-250 bar) and low seawater temperature (4 °C).
3. **Absence of Continuous Methanol / MEG Dosing:** Failure of methanol injection pump on the topside gas lift header prior to subsea injection.
4. **Line Shut-in under Operating Pressure:** Leaving service lines pressurized with wet gas during facility shutdowns without solvent purging.

## 5. Diagnostic Verification Steps
1. Correlate $Q_{GL}$ vs gas-lift injection header pressure ($P_{GL\_header}$). Rising header pressure with plummeting flowrate confirms downstream service line blockage.
2. Check topside gas dehydration unit hygrometer telemetry for elevated moisture content ($H_2O > 7$ lbs/MMSCF).
3. Cross-reference gas-lift operating pressure and seabed temperature against hydrate dissociation curves for the specific lift-gas composition.

## 6. Recommended Operator Actions
1. Immediately align continuous Methanol/MEG injection pump into the upstream service line header at high dosing rate.
2. Perform controlled depressurization of the service line from the platform topside to decompose the hydrate crystals.
3. Switch gas-lift source to dried, heated export gas or clean fuel gas if available.
4. Inspect topside TEG dehydration contactor reboiler temperature and glycol circulation rate.

## 7. Critical Safety Considerations
- **Pressure Entrapment & Line Rupture:** Depressurizing service lines must be executed carefully to prevent extreme differential pressures that can blow seals on subsea check valves.
- **Gas Blowback Hazard:** If the service line is disconnected or purged, ensure check valves prevent backflow of hydrocarbons from the reservoir into the utility system.

## 8. Relevant Sensor Relationships
- $Q_{GL} \rightarrow 0$ while Gas Lift Supply Pressure $\uparrow$
- $P_{ANULAR} \downarrow$ due to gas starvation in casing
- $P_{TPT} \downarrow$ and $P_{PDG} \uparrow$ as gas-lift artificial energy is lost.
