# Severe Slugging (Hydrodynamic Riser Slugging) - Event 3

## 1. Event Name & Definition
- **Event Identifier:** Event 3 - Severe Slugging
- **Category:** Multiphase Hydrodynamic Instability
- **Severity Level:** High Operational & Equipment Risk

## 2. Physical Description & Meaning
Severe slugging is a cyclic multiphase flow phenomenon typically occurring in pipeline-riser systems at low to moderate flow rates. Liquids (oil and water) accumulate at the lowest point (the riser base dip), forming a complete liquid seal that blocks gas passage. Upstream gas in the flowline compresses behind the liquid plug, building high pressure until the gas overcomes the hydrostatic weight of the liquid column in the riser. The liquid is then vigorously expelled as a massive slug into topside facilities, followed by high-velocity gas blowout, after which liquid falls back and repeats the cycle.

## 3. Typical Sensor Symptoms
- **Periodic Oscillations:** Large-amplitude, periodic cyclical swings in $P_{TPT}$, $P_{MON-CKP}$, $T_{TPT}$, and separator liquid levels.
- **P-MON-CKP Variance:** Standard deviation ($\sigma$) over 60s windows increases significantly ($\sigma_{P_{MON-CKP}} > 5-15$ bar).
- **P-PDG (Downhole Pressure):** Moderate cyclical fluctuations in phase with riser base pressure cycles.
- **Topside Flowrate / Separator Inflow:** Severe surges of liquid followed by high gas volume spikes, causing frequent separator high-high level (LAHH) and high pressure alarms.
- **Cycle Period:** Distinct periodic oscillation frequencies (typically 5 to 60 minutes per slug cycle).

## 4. Possible Root Causes
1. **Low Production Flow Rates:** Reservoir depletion or low flow velocities below the critical gas superficial velocity needed to carry liquid droplets.
2. **Terrain Geometry:** Downward-sloping seabed flowline ending at a steep vertical or catenary production riser.
3. **Ineffective Choke Control:** Choke operating at fully open setting without active anti-slug feedback control.
4. **Gas Lift Depletion:** Inadequate gas lift injection at the riser base or downhole to lighten the liquid column.

## 5. Diagnostic Verification Steps
1. Perform Fast Fourier Transform (FFT) or standard deviation monitoring on $P_{MON-CKP}$ and $P_{TPT}$ to detect dominant cyclical peak frequencies.
2. Cross-correlate riser base pressure with topside choke upstream pressure.
3. Check separator level trends for corresponding sawtooth liquid level oscillations.

## 6. Recommended Operator Actions
1. Implement active anti-slug choke control (choke throttling) to increase system damping and stabilize flow.
2. Increase gas lift injection rate ($Q_{GL}$) at the riser base or subsea wellhead to aerate the fluid and break liquid blockages.
3. If topside separator trips are imminent, strategically choke back the production valve until steady flow regimes are re-established.
4. Inject chemical drag reducers or foaming agents if available.

## 7. Critical Safety Considerations
- Massive liquid slugs can overflow separators, causing liquid carryover into the gas flare system and compressor suction scrubbers.
- Violent cyclic pressure pulsations induce mechanical fatigue, vibration, and pipe-hanger stress on topside piping and risers.
- In severe instances, repeated compressor trips can lead to full platform emergency shutdowns.

## 8. Relevant Sensor Relationships
- Strong periodicity and high variance in $P_{MON-CKP}$, $P_{TPT}$, and $T_{JUS-CKP}$.
- $\sigma(P_{MON-CKP}) \gg \sigma_{baseline}$ with distinct non-random cyclical oscillation.
