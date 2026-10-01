# Abrupt Increase of BSW (Basic Sediment and Water) - Event 1

## 1. Event Name & Definition
- **Event Identifier:** Event 1 (Transient: 101) - Abrupt Increase of BSW
- **Category:** Fluid Influx / Reservoir Breakthrough
- **Severity Level:** Moderate to High Operational Impact

## 2. Physical Description & Meaning
An abrupt increase in Basic Sediment and Water (BSW) represents a sudden surge in the volumetric water cut / produced water fraction. Water has a significantly higher density (~1000 kg/m³) and heat capacity than crude oil and associated gas (~800 kg/m³). The introduction of a dense water column increases the hydrostatic pressure gradient in the production tubing, loading the well column and potentially killing the well's natural flow if lift pressure is insufficient.

## 3. Typical Sensor Symptoms
- **P-PDG (Downhole Pressure):** Sharp increase in bottomhole flowing pressure due to higher hydrostatic head of the heavier fluid column.
- **P-TPT / P-MON-CKP:** Steady or rapid decrease in wellhead pressure as hydrostatic loading suffocates flow velocity.
- **T-TPT / T-JUS-CKP:** Noticeable thermal transient (often a gradual drop in topside temperature as liquid heat capacity changes thermal profile).
- **QGL (Gas Lift):** If gas lifted, injected gas might struggle to maintain aeration against high water density, causing fluctuating gas lift backpressure.
- **ABER-CKP:** May remain open while throughput rapidly drops.

## 4. Possible Root Causes
1. **Water Coning / Fingering:** Rapid advancement of bottom-water or edge-water through high-permeability thief zones in the reservoir.
2. **Casing / Tubing Breach:** Mechanical failure or corrosion leak in production casing allowing water from an adjacent aquifer zone into the tubing.
3. **Zone Isolation Packer Failure:** Breakdown of downhole isolation elastomeric seals, exposing the wellbore to a high-pressure water-bearing formation.
4. **Water Injection Breakthrough:** Direct communication with nearby water injection wells deployed for secondary recovery.

## 5. Diagnostic Verification Steps
1. Compare $P_{PDG}$ vs $P_{TPT}$ differential: a sharp increase in $\Delta P_{hydrostatic} = P_{PDG} - P_{TPT}$ confirms an increase in average fluid density inside the tubing.
2. Check topside test separator water cut measurements and centrifuge grab samples.
3. Review neighboring water injection rates and tracer monitoring data.
4. Perform downhole production logging tool (PLT) or pulsed neutron logging to identify water entry depth.

## 6. Recommended Operator Actions
1. Immediately adjust gas lift injection rate ($Q_{GL}$) upwards to reduce mixture density and assist fluid lift.
2. Throttle production choke ($ABER-CKP$) if necessary to prevent severe topside separator level tripping.
3. Route wellstream to test separator for continuous water-cut and emulsion monitoring.
4. Initiate demulsifier and corrosion inhibitor chemical dosing adjustments topside.

## 7. Critical Safety Considerations
- Elevated water production drastically accelerates internal carbonic acid ($H_2CO_3$) and sweet/sour corrosion in subsea flowlines.
- Water loading can lead to sudden well shut-in (well killing itself), requiring high-pressure nitrogen lift or intervention to restart.
- Topside produced water treatment facility may experience severe oil-in-water carryover and environmental discharge compliance risk.

## 8. Relevant Sensor Relationships & Rules
- $\Delta P_{tubing} = P_{PDG} - P_{TPT} \uparrow$ while Wellhead Flowrate $\downarrow$
- $P_{MON-CKP} \downarrow$ despite constant $ABER-CKP$
