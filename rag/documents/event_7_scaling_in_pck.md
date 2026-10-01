# Scaling in PCK (Production Choke Mineral Deposition) - Event 7

## 1. Event Name & Definition
- **Event Identifier:** Event 7 (Transient: 107) - Scaling in PCK
- **Category:** Flow Assurance / Mineral Precipitation
- **Severity Level:** Moderate to High Progressive Restriction

## 2. Physical Description & Meaning
Scaling in the production choke is the progressive, continuous precipitation and crystalline deposition of inorganic mineral salts (such as Calcium Carbonate $CaCO_3$, Barium Sulfate $BaSO_4$, or Strontium Sulfate $SrSO_4$) onto the internal surfaces, ports, and trim of the production choke. Scaling occurs due to thermodynamic shifts—specifically, the sharp pressure drop ($\Delta P$) across the choke causes dissolved $CO_2$ to flash out of the aqueous phase, increasing pH and causing calcium carbonate to exceed its solubility limit and crystallize.

## 3. Typical Sensor Symptoms
- **Progressive Differential Pressure Drift:** Monotonic, gradual upward climb in upstream pressure ($P_{MON-CKP}$) relative to downstream pressure ($P_{JUS-CKP}$) over extended operational windows.
- **Choke Flow Coefficient ($C_v$) Degradation:** Apparent effective $C_v$ drops steadily for a fixed physical choke opening ($ABER-CKP$).
- **P-PDG / P-TPT:** Subtle long-term upward creeping trend in bottomhole and wellhead pressures as backpressure accumulates.
- **Production Rate:** Gradual decline in liquid flow delivery over multiple production days/weeks.

## 4. Possible Root Causes
1. **Incompatible Water Mixing:** Mixing of formation water rich in barium/calcium ions with injected seawater rich in sulfate ($SO_4^{2-}$) ions.
2. **$CO_2$ Flashing across Choke Orifice:** Sudden pressure drop across PCK strips dissolved acid gases, shifting carbonate equilibrium toward insoluble $CaCO_3$.
3. **Scale Inhibitor Depletion:** Failure, under-dosing, or blockage of the subsea continuous chemical scale inhibitor injection line.
4. **Thermal Gradient:** Cooling of produced brine as it approaches the cold seabed wellhead environment.

## 5. Diagnostic Verification Steps
1. Track the continuous trend of effective choke flow coefficient: $C_v = \frac{Q}{\sqrt{\frac{\Delta P}{SG}}}$. A smooth, non-oscillating downward drift in $C_v$ is the hallmark of mineral scaling.
2. Review scale prediction modeling software (e.g., ScaleChem / MultiScale) against current produced water ionic analysis.
3. Check subsea chemical injection rate telemetry for scale inhibitor pump status and dosing rate.

## 6. Recommended Operator Actions
1. Increase continuous subsea scale inhibitor chemical injection rate upstream of the Christmas Tree.
2. Perform chemical scale dissolver batch treatment (e.g., chelating agents like EDTA/DTPA for sulfate scale, or inhibited HCl for carbonate scale).
3. If scale layer is thick and mechanically resilient, execute subsea choke insert change-out via ROV (Remote Operated Vehicle).

## 7. Critical Safety Considerations
- Barium sulfate scale frequently co-precipitates with trace radium isotopes, creating Naturally Occurring Radioactive Material (NORM) hazards during maintenance and choke refurbishment.
- Excessive scale buildup can seize the choke actuator stem, preventing emergency choke closure.

## 8. Relevant Sensor Relationships
- Monotonic long-term growth in $\Delta P_{PCK} = P_{MON-CKP} - P_{JUS-CKP}$
- Gradual decay in $C_v(t)$ at constant $ABER-CKP$
