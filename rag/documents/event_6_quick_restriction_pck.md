# Quick Restriction in PCK (Production Choke) - Event 6

## 1. Event Name & Definition
- **Event Identifier:** Event 6 (Transient: 106) - Quick Restriction in PCK
- **Category:** Subsea Wellhead Mechanical/Choke Obstruction
- **Severity Level:** High Immediate Flow Restriction

## 2. Physical Description & Meaning
A quick restriction in the Production Choke (PCK) occurs when the flow orifice through the choke trim is suddenly mechanically narrowed or obstructed over a brief timespan (seconds to minutes). Unlike slow mineral scaling (which takes weeks to months), quick restriction is typically caused by physical debris (drill debris, gravel, broken valve seat fragments), sudden stem/plug mechanical drift, or abrupt localized hydrate/slurry bridging in the choke throat.

## 3. Typical Sensor Symptoms
- **P-MON-CKP (Upstream Pressure):** Sudden steep pressure increase due to hydraulic backpressure piling up against the restriction.
- **P-JUS-CKP (Downstream Pressure):** Sudden drop in pressure downstream of the choke.
- **Differential Pressure ($\Delta P_{PCK} = P_{MON-CKP} - P_{JUS-CKP}$):** Sharp, pronounced step increase.
- **T-JUS-CKP (Downstream Temperature):** Sudden drop due to increased Joule-Thomson gas expansion cooling across the narrowed restriction orifice.
- **P-PDG & P-TPT:** Gradual increase in upstream pressures reflecting backpressure propagating back downhole.

## 4. Possible Root Causes
1. **Solid Debris Ingestion:** Formation rock fragments, drill cuttings, proppant, or disintegrated downhole packer debris lodging in the choke cage orifice.
2. **Choke Actuator / Stem Mechanical Drift:** Internal stem mechanical decoupling, lost motion, or hydraulic actuator trim misalignment causing the valve plug to move uncommanded.
3. **Localized Flash Hydrate / Wax Deposition:** Rapid local solid phase formation due to severe Joule-Thomson chilling in the high-velocity throat.
4. **Erosion Trim Failure / Fracture:** Tungsten carbide choke sleeve or cage fracture causing broken fragments to wedge in the flow port.

## 5. Diagnostic Verification Steps
1. Verify choke differential pressure: $\Delta P_{PCK} \uparrow$ sharply while commanded position indicator ($ABER-CKP$) remains unchanged.
2. Check $T_{JUS-CKP}$ for corresponding Joule-Thomson cooling dip.
3. Contrast with Event 7 (Scaling): Event 6 happens rapidly (minutes/hours), whereas Event 7 is gradual over weeks.

## 6. Recommended Operator Actions
1. Cycle the production choke trim gently (exercise choke open/close by +/- 5-10%) under controlled conditions to dislodge debris, if safe.
2. If Joule-Thomson cooling suggests ice/hydrate plugging, immediately initiate continuous thermodynamic inhibitor (MEG / Methanol) injection upstream of the choke.
3. If mechanical trim failure is suspected, switch production to the standby test choke or prepare for subsea choke insert replacement.

## 7. Critical Safety Considerations
- Severe differential pressure across a restricted choke can exceed the structural burst/collapse rating of downstream piping if downstream relief is restricted.
- High-velocity fluid jetting past debris causes accelerated localized impingement erosion on the choke body.

## 8. Relevant Sensor Relationships
- $P_{MON-CKP} \uparrow$ and $P_{JUS-CKP} \downarrow \implies \Delta P_{PCK} \gg \Delta P_{nominal}$
- $T_{JUS-CKP} \downarrow$ due to $\Delta T_{JT} = \mu_{JT} \cdot \Delta P$
- Negative correlation between upstream and downstream pressure across the choke.
