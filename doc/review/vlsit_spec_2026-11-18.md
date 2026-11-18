# Specification review of m_uit_qspi_wrap - 2026-11-18

## 1. Summary

| Item | Value |
|---|---|
| Design | `m_uit_qspi_wrap` (rtl/qspi/doc/UIT_QSPI_Specification.md) |
| Review | Specification review |
| Date | 2026-11-18 |
| Findings | 24 |
| Critical | 1 |
| High | 11 |
| Medium | 8 |
| Low | 4 |
| Waivable | 5 |
| Fixable | 19 |
| Verdict | Conditional, weighted 2.98 / 5 (scorecard.md) |
| Gate | `RESULT: FAIL` (1 unwaived Critical finding(s): F-001); waivers 5/10 |
| Audit | 3 of 24 sampled, FP 0/3, FN 0/3 (self-audit) |
| Deep sample | 24 traced, 0 aggregated, 14 root-cause groups |

Severity scale: Critical = Blocker, High = Major, Medium = Minor, Low = Observation. The full bilingual analysis is in REVIEW_UIT_QSPI.md.

## 2. Findings

Each finding has an assessment, a verdict and, when it can be fixed, the change and the reason it works.

### F-001 DDR output data changes on the same clk edge as every SCLK edge, so the flash sees zero hold time on address, alternate and data bits

- Severity: `Critical` (Blocker), area `asic_feasibility`, root cause RC-1 pad launch/capture timing not derived from flash AC timing
- Evidence: §7.6, Table 6-15, §11.2
- Assessment: FACT §7.6: 'In a DDR write phase it changes on the clk edge of every SCLK edge'; FACT Table 6-15: DDR launch strobe precedes every SCLK edge; FACT §11.2: 'The SCLK falling edge is not constrained for DDR write data'. INFERENCE: a DTR flash samples on both edges, so each bit is launched exactly at the edge that samples the previous bit; hold margin is only the pad/board skew between SCLK and IO, while DTR flash inputs require a positive hold time. Every DDR frame (CCR.DDRM=1) sends its address in DDR, so the DDR feature cannot work reliably.
- Verdict: `fix` (fix RTL)
- Fix: In m_qspi_edge_sel add a DDR launch strobe at the middle of each SCLK half period (a quarter SCLK period after the edge) and use it to load the output register in DDR write phases; restrict DDR to an even PRESCALER >= 2 so the midpoint is an integer clk count; constrain the DDR falling edge in the SDC.
- Why: Launching at the half-period midpoint gives the flash a quarter SCLK period of setup and of hold on each edge, which is how STM32 QUADSPI DHQC (delay hold quarter cycle) solves the same problem.

```systemverilog
// m_qspi_edge_sel: DDR launch at the half-period midpoint
assign o_launch = r_ddr ? (r_half_cnt == (i_prescaler >> 1)) & r_sclk_req
                        : w_trailing_tick & r_sclk_req;
```

### F-002 Read data is always captured half an SCLK period after the flash launch, with no sample shift or delay, so F/2 and probably F/4 reads cannot close

- Severity: `High` (Major), area `performance`, root cause RC-1 pad launch/capture timing not derived from flash AC timing
- Evidence: §3, Table 6-15, §11.2
- Assessment: FACT §3 excludes 'programmable sample delay or delay-line calibration'; FACT Table 6-15: mode 0 SDR samples before the rising edge, half a period after the falling-edge launch. INFERENCE: the available time is one SCLK half period = PRESCALER clk cycles (1 clk = 5 ns at PRESCALER=0, 200 MHz) for SCLK pad out + board + flash tCLQV + board + pad in + setup. Typical serial-flash tCLQV is 6-7 ns (Intel EPCQ-A 6 ns, T25Q16BW 7 ns, sources in §19), so PRESCALER=0 fails and PRESCALER=2 (10 ns) is marginal; reads fall back to F/8 = 25 MHz.
- Verdict: `fix` (fix RTL)
- Fix: Add a CR.SSHIFT-like field (or a 3-bit DCR sample-delay in clk cycles) that delays the sample strobe of read phases by 1..N clk cycles, and state the maximum read SCLK per delay setting in §6.6.2.
- Why: Moving the capture later by whole clk cycles recovers the round-trip delay that the half-period window cannot absorb, as STM32 SSHIFT and DesignWare RX_SAMPLE_DLY do.

```systemverilog
// m_qspi_edge_sel: delayed sample strobe for read phases
always_ff @(posedge i_clk_qspi or negedge i_rst_n_qspi)
  if (!i_rst_n_qspi) r_smp_dly <= '0;
  else               r_smp_dly <= {r_smp_dly[6:0], w_sample_raw};
assign o_sample = (i_sample_dly == 3'd0) ? w_sample_raw : r_smp_dly[i_sample_dly-1];
```

### F-003 Pad IO delays are 40 % placeholders of the fastest SCLK period and the DDR falling edge is unconstrained, so synthesis cannot reveal F-001 or F-002

- Severity: `High` (Major), area `sdc_timing`, root cause RC-1 pad launch/capture timing not derived from flash AC timing
- Evidence: §11.2, Table 11-2
- Assessment: FACT §11.2: 'Every IO delay is a placeholder of 40 % of the clock period' (DEP-009, DEP-011) and 'The SCLK falling edge is not constrained for DDR write data'. INFERENCE: a placeholder input delay relative to SCLK does not model tCLQV plus the round trip, so the input path looks closed at F/2 while the silicon fails.
- Verdict: `fix` (fix SDC)
- Fix: Write the pad budget from a named flash (tCLQV, tDS/tDH, tCSS/tCSH) plus pad and board delays; add set_output_delay -clock_fall for DDR; state the SCLK limit the budget closes for SDR read, SDR write and DDR.
- Why: Constraints derived from the device datasheet make STA report the real read-capture and DDR hold paths instead of a placeholder that always passes.

```tcl
set_output_delay -clock sclk_gen -max  $tDS_flash [get_ports o_qspi_pad_io*]
set_output_delay -clock sclk_gen -min -$tDH_flash [get_ports o_qspi_pad_io*]
set_output_delay -clock sclk_gen -clock_fall -add_delay -max $tDS_flash [get_ports o_qspi_pad_io*]
```

### F-004 PRESCALER legality rules look stale after the V2.0 formula change: odd values are rejected in SDR and DDR allows only 2, 6, 10, ...

- Severity: `High` (Major), area `functions`, root cause RC-2 V2.0 revision not propagated consistently
- Evidence: §6.6.2, Table 6-14, Table 6-10, Table 8-3
- Assessment: FACT §6.6.2: half period = PRESCALER clk cycles, 50 % duty for every value, yet PRESCALER must be even (SDR) and PRESCALER+2 a multiple of 4 (DDR); FACT Table 6-10 still words the rule as 'PRESCALER + 2 odd'; FACT revision history V2.0 'Corrected the SCLK frequency formula to the RTL'. INFERENCE: both rules match the old period PRESCALER+2 (even period for 50 % duty, period multiple of 4 for a quarter point), not the new 2xPRESCALER. Result at 200 MHz: SDR 100, 50, 25, 16.7 MHz (no 33 or 40 MHz); DDR 50, 16.7, 10 MHz; PRESCALER=1 would equal PRESCALER=0 but is rejected.
- Verdict: `fix` (fix RTL)
- Fix: Accept every PRESCALER in SDR (1..255, 0 kept as F/2) and every even PRESCALER >= 2 in DDR (with the F-001 midpoint launch); update the TEF check in m_qspi_reg_cfg, Table 6-10, Table 6-14 and Table 8-3.
- Why: With a half period of PRESCALER clk cycles the duty cycle is 50 % for any value, so the odd restriction only removes usable frequencies; the DDR midpoint needs an even half period only.

```systemverilog
assign w_presc_illegal = r_ccr_ddrm ? (r_cr_presc[0] | (r_cr_presc == 8'd0)) : 1'b0;
```

### F-005 The XIP cache is a single 32-byte stream buffer: every miss invalidates all lines, a NONSEQ miss fetches one word, HBURST is ignored and miss latency is not quantified

- Severity: `High` (Major), area `performance`, root cause RC-3 XIP path sized as a minimal stream buffer
- Evidence: §6.4.3, §6.9, DEC-016, DEC-030
- Assessment: FACT §6.4.3: 'Every miss first invalidates all cache lines' (DEC-016), 'A NONSEQ miss fetches 1 word', a miss during a fetch waits for the whole prefetch; FACT §1.2: HBURST not connected. INFERENCE: a branch costs a full frame per word; a WRAP8 line refill starting mid-line costs three frames; loops larger than 32 bytes never hit. Estimated NONSEQ miss with EBh quad SDR, 24-bit address, PRESCALER=2: 8+6+2+4+8 = 28 SCLK = 112 clk plus CSS/CSH, two async FIFO crossings and the pad flops, about 130 clk = 650 ns per 4 bytes. The spec gives no number (§1.1 'reduces the read latency').
- Verdict: `fix` (fix RTL)
- Fix: Fetch an aligned block (PARA_PREFETCH_LENGTH words) on every miss, NONSEQ included, using HBURST to size it; replace invalidate-all with a FIFO or LRU replacement of aligned blocks; add a latency table (hit, NONSEQ miss, SEQ miss) to §6.4.3.
- Why: Aligned block fills turn a branch into one frame per block and keep previous blocks for loops, which is where XIP spends its time.

```systemverilog
assign w_fetch_addr = {w_offset[31:LPARA_BLK_W+2], {(LPARA_BLK_W+2){1'b0}}}; // aligned block
assign w_fetch_len  = PARA_PREFETCH_LENGTH;                                  // NONSEQ and SEQ
```

### F-006 The AHB-Lite subordinate has no HREADY input and relies on the interconnect gating HSEL, a deviation from AMBA AHB (IHI 0033C)

- Severity: `High` (Major), area `interfaces`, root cause RC-4 XIP bus contract does not match the UIT Tesla fabric
- Evidence: §1.2, Table 7-3, Table 11-4 (ASM-003)
- Assessment: FACT §1.2: 'There is no HREADY input (the interconnect gates HSEL)'; FACT Table 11-4 makes it an integrator requirement (ASM-003). INFERENCE: a standard AHB decoder drives HSEL from HADDR regardless of HREADY, so while another subordinate inserts wait states this IP samples the stalled address phase again and starts a duplicate or wrong fetch. AHB subordinates normally take HREADY as an input to qualify the address phase (IHI 0033C, HREADY signal description; clause number not verified by this review).
- Verdict: `fix` (fix RTL)
- Fix: Add input i_qspi_ahb_hready and accept an address phase only when HSEL & HREADY & HTRANS[1]; drop ASM-003 from Table 11-4.
- Why: Qualifying with HREADY is the standard subordinate contract, so any AHB-Lite interconnect or AXI-to-AHB bridge connects without custom gating.

```systemverilog
assign w_addr_phase = i_qspi_ahb_hsel & i_qspi_ahb_hready & i_qspi_ahb_htrans[1];
```

### F-007 UIT Tesla provides an AXI XIP connection but the IP has an AHB-Lite port; the required bridge is not specified

- Severity: `High` (Major), area `integration_effort`, root cause RC-4 XIP bus contract does not match the UIT Tesla fabric
- Evidence: Table 11-4 (XIP bus row)
- Assessment: FACT Table 11-4: 'The UIT Tesla top provides an AXI XIP connection ... A bridge is needed before XIP can be used.' INFERENCE: the boot/XIP path (§1.1) depends on a block whose owner, burst mapping (WRAP refills, see F-005), error mapping (AHB ERROR to SLVERR), outstanding policy and latency are unknown, so XIP performance and boot cannot be signed off.
- Verdict: `fix` (fix HAS)
- Fix: Add a section that names the AXI-to-AHB-Lite bridge (or an AXI4 subordinate option), its owner, burst/WRAP conversion, response mapping, outstanding count and added latency.
- Why: The boot path crosses the bridge, so its behaviour is part of this IP's integration contract.

### F-008 Serial PSRAM is claimed as supported, but there are no memory-mapped writes and CSN can stay low without limit, violating PSRAM tCEM

- Severity: `High` (Major), area `application_fit`, root cause RC-5 feature claims exceed the specified behaviour
- Evidence: §1.1, §2, §3 (ASM-015), §6.4.1
- Assessment: FACT §2 lists serial PSRAM; FACT §3 excludes memory-mapped writes and tCEM enforcement (ASM-015); FACT §6.4.1: SCLK stops with CSN held low while a FIFO is empty or full. INFERENCE: a PSRAM is used as RAM, so without memory-mapped writes it is not usable as memory, and a stalled indirect frame keeps CSN low past tCEM, which blocks the PSRAM self-refresh and corrupts data.
- Verdict: `fix` (fix HAS)
- Fix: Either remove PSRAM from §1.1 and §2, or add memory-mapped write support plus a DLY-like maximum CSN-low counter that ends the frame at a byte boundary and restarts it.
- Why: The feature list must only promise what the controller can do without corrupting the device.

### F-009 Clock frequencies conflict: all clocks are 200 MHz in Table 6-1/11-2, but §9.6 and Table 11-4 use HCLK = 100 MHz and i_qspi_clk = 5 MHz; PRESCALER <= 54 gives 108, not 110, clk cycles

- Severity: `High` (Major), area `documentation`, root cause RC-2 V2.0 revision not propagated consistently
- Evidence: Table 6-1, Table 11-2, §9.6, Table 11-4
- Assessment: FACT Table 6-1 and Table 11-2: i_qspi_clk, PCLK, HCLK, DMA_CLK at 200 MHz; FACT §9.6: 'AHB timeout 2^20 HCLK cycles at 100 MHz, i_qspi_clk at 5 MHz'; FACT Table 11-4: '10.49 ms at 100 MHz'. INFERENCE: the AHB timeout limit and the PRESCALER <= 54 rule are derived from a configuration that the frequency table does not describe; at 200 MHz HCLK the timeout is 5.24 ms and the limit changes. 2 x 54 = 108 clk cycles (Table 8-19 formula).
- Verdict: `fix` (fix HAS)
- Fix: State one UIT Tesla delivery clock plan, recompute the AHB timeout and the memory-mapped PRESCALER limit from it with the frame length used, and correct the 110/108 arithmetic.
- Why: Integration and software limits are derived from these numbers; a single clock plan removes the contradiction.

### F-010 REF-002/006/008, the source design specification and 32 cited DEC/ASM/DEP items are not defined in the document; no requirement IDs; the review table is empty

- Severity: `High` (Major), area `documentation`, root cause RC-6 traceability absent
- Evidence: Table 1-1, §4, §5, §8, Appendix B
- Assessment: FACT Table 1-1 lists REF-001/003/005/010 only, while figures cite REF-002, Table 5-1 REF-006 and §8 REF-008 (the register authority); FACT 18 DEC, 11 ASM and 3 DEP identifiers are cited (inventory.json) and §1.1 says DEC decisions override the sources, but none is listed; FACT Appendix B has no reviewer for V1.0 to V2.0; the title says V1.0 while the history reaches V2.0.
- Verdict: `fix` (fix HAS)
- Fix: Add REF-002/006/008 and UIT-Tesla-QSPI-SPEC v0.2 to Table 1-1, append DEC/ASM/DEP tables with status and owner, add REQ-nnn IDs to normative statements, and set the title to V2.0.
- Why: A reader cannot check a decision or an assumption that the document only names.

### F-011 No requirement-to-test traceability, no coverage plan, no flash model named and no verification result; sim/ and lint/ are empty

- Severity: `High` (Major), area `verification_quality`, root cause RC-6 traceability absent
- Evidence: §10, Table 10-1
- Assessment: FACT §10 lists corner cases, key assertions and five configurations, but inventory.json finds 0 requirements and 0 test IDs; FACT the rtl/qspi folders sim/, lint/, logical/, syn/ contain only .gitkeep. INFERENCE: the list is a good test-plan seed, but no closure can be measured, and the DDR/read-timing issues (F-001, F-002) are invisible to an RTL-only flash model unless it checks setup/hold.
- Verdict: `fix` (fix HAS)
- Fix: Give each §10 bullet a TEST-nnn ID mapped to REQ-nnn, name the flash model and require it to check tDS/tDH and tCLQV, list functional coverage bins, and add the regression status per configuration of Table 10-1.
- Why: Traceability turns the corner-case list into a closure metric.

### F-012 DCR.FSIZE and the memory-mapped enable cross to HCLK through per-bit 2-flop synchronizers, safe only under a software rule

- Severity: `Medium` (Minor), area `clock_reset_cdc`, root cause RC-7 safety rests on unchecked assumptions
- Evidence: Table 6-2 CDC-005 (ASM-007)
- Assessment: FACT CDC-005 is valid 'because the source changes only while no AHB access is in progress (ASM-007)'. INFERENCE: nothing in hardware enforces it; another AHB manager, or a CPU still fetching XIP code, can see a mixed FSIZE value for one HCLK cycle and pass or fail the range check wrongly.
- Verdict: `fix` (fix RTL)
- Fix: Carry FSIZE with the enable through a request/acknowledge handshake (data held in the clk domain, captured in HCLK on the synchronized toggle), or hold memory-mapped mode off in HCLK until the new FSIZE is stable.
- Why: A handshake makes the multi-bit value coherent by construction instead of by software discipline.

### F-013 Reset assumptions conflict and no RDC analysis is given for the four reset domains

- Severity: `Medium` (Minor), area `clock_reset_cdc`, root cause RC-7 safety rests on unchecked assumptions
- Evidence: §6.2, Table 6-3 (ASM-002, ASM-012, ASM-014)
- Assessment: FACT §6.2: partial reset 'is not supported (ASM-002)', yet the same section specifies AHB and APB behaviour 'while the core domain is in reset' and allows release in any order. INFERENCE: the async FIFOs and pulse synchronizers span two reset domains; with release in any order a source-side pointer or toggle can change while the destination is still in reset. The behaviour is probably safe, but it is not shown.
- Verdict: `fix` (fix HAS)
- Fix: Add an RDC table: each crossing, its two resets, the state at release in each order, and why no spurious word or pulse is produced; reconcile ASM-002 with the core-in-reset sentences.
- Why: An explicit RDC table is the evidence a reset-domain review needs.

### F-014 set_clock_groups -allow_paths is tool-specific and the Gray-pointer crossings have no skew constraint

- Severity: `Medium` (Minor), area `sdc_timing`, root cause RC-8 CDC constraint portability
- Evidence: Table 11-3 EXC-001, EXC-002
- Assessment: FACT EXC-001 uses set_clock_groups -asynchronous -allow_paths, EXC-002 a set_max_delay of one destination period. INFERENCE: -allow_paths is not portable to every STA tool; a max delay that includes clock latency is not a bus-skew limit on Gray-coded pointers.
- Verdict: `fix` (fix SDC)
- Fix: State the STA tool; use set_max_delay -ignore_clock_latency (or -datapath_only) and add a skew constraint (set_data_check or set_bus_skew) on each Gray pointer bus.
- Why: Gray code is safe only when all bits arrive within one source period of each other; that must be constrained, not assumed.

```tcl
set_bus_skew -from [get_cells u_qspi_apb_if/*wptr_gray*] [expr 0.8*$T_PCLK]
```

### F-015 No APB timeout: an APB access while i_qspi_clk is stopped or in reset hangs the CPU bus

- Severity: `Medium` (Minor), area `security_ras`, root cause RC-7 safety rests on unchecked assumptions
- Evidence: §3, §7.2, Table 11-4 (DEC-020)
- Assessment: FACT §7.2: 'There is no timeout'; FACT Table 11-4 forbids register access while i_qspi_clk is stopped. INFERENCE: one firmware error becomes a system hang recoverable only by a watchdog. Accepted as a recorded decision.
- Verdict: `waive` (waive)
- Why: DEC-020 is a closed decision and the CRM rule in Table 11-4 removes the trigger.
- Risk: CPU hang on a register access during clock stop or core reset
- Owner: UIT Tesla SoC integrator
- Invalidation: The CRM can stop or reset i_qspi_clk while the CPU runs, or a watchdog is not present

### F-016 No access control, register lock or integrity check on the boot/XIP path

- Severity: `Medium` (Minor), area `security_ras`, root cause RC-9 security stance
- Evidence: §3, §1.1
- Assessment: FACT §3 excludes ECC/parity and PPROT/HPROT filtering; FACT §1.1 makes the IP the boot and code-storage path. INFERENCE: any APB manager can issue erase commands and XIP code is executed without integrity; acceptable when UIT Tesla has no secure-boot requirement.
- Verdict: `waive` (waive)
- Why: The exclusion is stated, and UIT Tesla states no secure-boot or untrusted-manager requirement.
- Risk: Flash content can be erased or executed unchecked by any bus manager
- Owner: UIT Tesla architecture lead
- Invalidation: UIT Tesla adds secure boot, an untrusted bus manager or a safety target

### F-017 Writes to BUSY-locked fields are silently dropped with no flag

- Severity: `Medium` (Minor), area `software_ease`, root cause RC-10 programming-model friction
- Evidence: §8.1, §7.2, §9.7
- Assessment: FACT §8.1: 'A write while BUSY = 1 is ignored for those fields'; FACT §9.7 asks software to read back after every write. INFERENCE: every driver write to CR/DCR/CCR/DLR/DLY needs a read-back, doubling the APB cost of configuration and hiding race bugs.
- Verdict: `fix` (fix RTL)
- Fix: Add a sticky SR.WLKF (write-locked) flag, cleared through FCR, set when a write hits a BUSY-locked field.
- Why: A flag reports the dropped write once, so the driver checks one bit instead of reading back every register.

```systemverilog
if (w_apb_wr & w_locked_hit & r_busy) r_sr_wlkf <= 1'b1;
else if (w_fcr_wr & i_wdata[6])      r_sr_wlkf <= 1'b0;
```

### F-018 DMA moves whole bursts only; the CPU must move the residue and a DMA channel programmed for it waits forever

- Severity: `Medium` (Minor), area `software_ease`, root cause RC-7 safety rests on unchecked assumptions
- Evidence: §6.4.4, §9.3 (DEC-029, ASM-013)
- Assessment: FACT §6.4.4 'Only whole bursts are requested (DEC-029)'; FACT §9.3 'A DMA channel programmed for such a residue would wait forever (ASM-013)'. INFERENCE: every DMA transfer needs a CPU tail, so DMA does not offload short or odd-length transfers.
- Verdict: `fix` (fix RTL)
- Fix: Raise the request for the last partial burst when the remaining words are fewer than the threshold (TX: remaining bytes to write; RX: frame complete and RX FIFO not empty), with the DMA programmed by word count.
- Why: A final short request lets one DMA descriptor move the whole transfer.

### F-019 No area or power figure; the reviewer proxy is about 4.4k flops, with the TX/RX FIFOs about 46 % while the XIP cache is 8 words

- Severity: `High` (Major), area `area_power`, root cause RC-11 area and power not stated
- Evidence: §11.1, §6.10, Table 5-1
- Assessment: FACT §11.1: standard cells only, no memory macros, no clock-gating cells; FACT §6.10: FIFOs are flops. INFERENCE (proxy, defaults): TX+RX FIFO 2048, cache 520, AHB async FIFOs 552, APB async FIFOs 328, registers about 350, frame latch about 130, shifter about 200, counters about 210, synchronizers about 80: about 4.4k flops, roughly 30-40 kGE assuming 6 GE per flop plus read multiplexers; no library, not mapped. Without clock gating all flops toggle at 200 MHz.
- Verdict: `fix` (fix HAS)
- Fix: Add an area/power table (proxy now, mapped with the UIT Tesla library later), allow synthesis clock-gating insertion, and reconsider 32-word FIFOs against a larger XIP cache for UIT Tesla.
- Why: Area and power must be stated with a basis to support the floorplan and to rebalance storage towards the boot/XIP use.

### F-020 The DFT contract for the four clocks, four async resets and the pad capture flop is not written

- Severity: `Medium` (Minor), area `dft`, root cause RC-12 DFT contract
- Evidence: §3, Table 11-4 (DEC-021)
- Assessment: FACT DEC-021: no DFT ports, all flops scan-eligible. INFERENCE: scan needs top-level control of every async reset, one scan clock per domain or a test-clock mux at the CRM, and the synchronizer flops in the scan chains; the SoC DFT team needs these listed.
- Verdict: `fix` (fix HAS)
- Fix: Add a DFT table: reset controllability, clock sources in scan mode, synchronizer handling, pad IO in scan mode, expected coverage exclusions.
- Why: An explicit contract lets the SoC flow insert scan without reverse-engineering the IP.

### F-021 Abort raises CSN mid-byte without the CSN hold time and reports the same TCF as a normal completion

- Severity: `Low` (Observation), area `functions`, root cause RC-13 abort semantics
- Evidence: §6.4.6, §6.6.3, Table 8-19
- Assessment: FACT §6.4.6: CSN goes high without DLY.CSH; TCF = 1 on abort. INFERENCE: flash devices discard a partial command, so this is acceptable, but software cannot tell abort from completion from SR alone.
- Verdict: `waive` (waive)
- Why: Same behaviour as STM32 QUADSPI; software knows it issued the abort.
- Risk: Driver misreads an aborted transfer as complete
- Owner: QSPI driver owner
- Invalidation: An abort can be raised by hardware without software knowledge

### F-022 The DMA req/clr handshake is custom and the target DMA controller is not named

- Severity: `Low` (Observation), area `interfaces`, root cause RC-4 XIP bus contract does not match the UIT Tesla fabric
- Evidence: §7.4, Table 7-4 (ASM-005)
- Assessment: FACT §7.4: level req, clr pulse after all APB accesses of the burst (ASM-005). INFERENCE: interoperability depends on the UIT Tesla DMA controller implementing exactly this handshake.
- Verdict: `waive` (waive)
- Why: The handshake is fully specified and the integrator duty is in Table 11-4.
- Risk: DMA controller handshake mismatch
- Owner: UIT Tesla SoC integrator
- Invalidation: The UIT Tesla DMA controller uses another request protocol (for example single/burst requests)

### F-023 PARA_AHB_SYNC_FIFO_DEPTH sizes async FIFOs, and the IP subtracts base addresses that an interconnect normally removes

- Severity: `Low` (Observation), area `parameters`, root cause RC-14 parameter naming
- Evidence: Table 5-1 rows 6, 13, 14; §7.3
- Assessment: FACT Table 5-1 row 6 describes 'AHB control and data async FIFOs'; FACT §7.3: below-base addresses wrap and pass the range check when FSIZE = 31. INFERENCE: naming misleads, and a 32-bit subtractor sits in the AHB address path.
- Verdict: `waive` (waive)
- Why: Defaults of 0 remove the subtractor's effect and the wrap case is documented.
- Risk: Wrong FIFO sizing by name; address alias at FSIZE = 31
- Owner: QSPI RTL owner
- Invalidation: A non-zero PARA_AHB_BASE_ADDRESS is used with FSIZE = 31

### F-024 Register offsets mirror STM32 QUADSPI but bit positions and PTR meaning differ, and its SSHIFT/DHQC timing features are absent

- Severity: `Low` (Observation), area `market_position`, root cause RC-1 pad launch/capture timing not derived from flash AC timing
- Evidence: §8.2 Table 8-2, Table 8-3, Table 8-15
- Assessment: FACT Table 8-2: CR..PIR at 0x00..0x2C in the STM32 QUADSPI order, but CR bit fields differ (Table 8-3) and PTR is a polling timeout (Table 8-15). INFERENCE (STM32 layout from public reference manuals, §19): a developer may reuse an STM32 driver and get wrong behaviour; the two STM32 features that solve F-001/F-002 are missing.
- Verdict: `fix` (fix HAS)
- Fix: State in §8 that the map is STM32-inspired but not compatible, list the differences, and adopt the sample-shift and DDR-hold fields of F-001/F-002.
- Why: An explicit non-compatibility note prevents silent driver reuse errors.

## 3. Actions

| Action | Owner | Blocks sign-off |
|---|---|---|
| DDR launch at the half-period midpoint, DDR PRESCALER rule (F-001, F-004) | RTL | yes |
| Read sample delay field (F-002) | RTL | yes for reads above about 25 MHz |
| Pad budget from a named flash and DDR falling-edge constraints (F-003) | SDC | yes |
| HREADY input (F-006), aligned block XIP fills (F-005), AXI bridge spec (F-007) | RTL / SoC | yes for XIP |
| PSRAM claim (F-008), clock plan (F-009), REF/DEC/ASM/DEP tables (F-010), traceability (F-011) | spec / DV | yes |
| F-012 to F-014, F-017 to F-020, F-024 | RTL / spec | no |

## 4. Limits

- No RTL, lint, simulation, CDC/RDC or synthesis evidence exists in rtl/qspi (empty folders); every RTL fix and snippet is a proposal written from the specification, not checked against code.
- The SDC file and REF-008 are cited but absent.
- Area is a proxy (about 4.4k flops); no library.
- The audit is a self-audit; no second reviewer was available.
