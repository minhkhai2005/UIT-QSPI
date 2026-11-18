# Specification review — UIT QSPI / Đánh giá đặc tả — UIT QSPI

| Field / Trường | Value / Giá trị |
|---|---|
| IP | m_uit_qspi_wrap (UIT QSPI controller) |
| Specification reviewed | rtl/qspi/doc/UIT_QSPI_Specification.md |
| Revision and date | HDS V2.0, 11/11/2026 (title page still says V1.0) |
| Reviewer | Claude (vlsit-ip-spec-review skill) |
| Review date | 2026-11-18 |
| Verdict / Kết luận | Conditional (weighted 2.98 / 5; 1 Blocker) |

## 1. Executive summary / Tóm tắt điều hành

**EN.** FACT: the UIT QSPI controller is the UIT Tesla boot, XIP and flash-programming path, with APB3 control, a read-only AHB-Lite XIP port, DMA, status polling and SDR/DDR single/dual/quad framing (§1.1, §2). The functional specification is detailed and of good quality: every block has an FSM table, an output table and simulated waveforms, every crossing has an ID and a synchronizer, and the register map and software flows are complete. INFERENCE: the weak point is the flash pad timing. DDR output data changes on the sampling edges (F-001, Blocker), read capture has a fixed half-period window with no sample delay (F-002), and the SDC placeholders hide both (F-003). The XIP cache works as a single stream buffer (F-005), the AHB port lacks HREADY (F-006), and the UIT Tesla AXI bridge is not specified (F-007). Verdict: **Conditional**, weighted score 2.98. The three actions that matter most: fix the DDR launch and add a read sample delay; write the pad budget from a real flash datasheet; add requirement/test traceability and define the cited DEC/ASM/REF items.

**VI.** FACT: UIT QSPI controller là đường boot, XIP và lập trình flash của UIT Tesla, có APB3, cổng XIP AHB-Lite chỉ đọc, DMA, status polling và frame SDR/DDR single/dual/quad (§1.1, §2). Phần đặc tả chức năng chi tiết và chất lượng tốt. INFERENCE: điểm yếu là timing pad flash: dữ liệu DDR đổi đúng tại cạnh lấy mẫu (F-001, Blocker), capture khi đọc chỉ có cửa sổ nửa chu kỳ, không có sample delay (F-002), và SDC placeholder che cả hai (F-003). Cache XIP chỉ là stream buffer (F-005), cổng AHB thiếu HREADY (F-006), AXI bridge của UIT Tesla chưa đặc tả (F-007). Kết luận: **Conditional**, điểm 2.98. Ba việc quan trọng nhất: sửa launch DDR và thêm sample delay; viết budget pad từ datasheet flash thật; thêm truy vết requirement/test và định nghĩa các mục DEC/ASM/REF.

### 1.1 Top findings / Phát hiện quan trọng nhất

| Rank | Severity | Area | Finding (EN) | Phát hiện (VI) | Locator |
|---|---|---|---|---|---|
| 1 (#001) | Blocker | asic_feasibility | DDR output data changes on the same clk edge as every SCLK edge, so the flash sees zero hold time on address, alternate and data bits | Dữ liệu ra ở DDR đổi trạng thái cùng clk edge với mọi SCLK edge, flash nhận hold time bằng 0 cho address, alternate và data | §7.6, Table 6-15, §11.2 |
| 2 (#002) | Major | performance | Read data is always captured half an SCLK period after the flash launch, with no sample shift or delay, so F/2 and probably F/4 reads cannot close | Dữ liệu đọc luôn được capture sau nửa chu kỳ SCLK, không có sample shift hay delay, nên đọc ở F/2 và có thể F/4 không đạt timing | §3, Table 6-15, §11.2 |
| 3 (#003) | Major | sdc_timing | Pad IO delays are 40 % placeholders of the fastest SCLK period and the DDR falling edge is unconstrained, so synthesis cannot reveal F-001 or F-002 | IO delay của pad là placeholder 40 % chu kỳ SCLK nhanh nhất và cạnh xuống DDR không được constrain, nên synthesis không phát hiện được F-001, F-002 | §11.2, Table 11-2 |
| 4 (#004) | Major | functions | PRESCALER legality rules look stale after the V2.0 formula change: odd values are rejected in SDR and DDR allows only 2, 6, 10, ... | Quy tắc hợp lệ của PRESCALER có vẻ còn từ công thức cũ trước V2.0: giá trị lẻ bị từ chối ở SDR, DDR chỉ cho 2, 6, 10, ... | §6.6.2, Table 6-14, Table 6-10, Table 8-3 |
| 5 (#005) | Major | performance | The XIP cache is a single 32-byte stream buffer: every miss invalidates all lines, a NONSEQ miss fetches one word, HBURST is ignored and miss latency is not quantified | Cache XIP thực chất là một stream buffer 32 byte: mỗi miss invalidate toàn bộ line, miss NONSEQ chỉ fetch 1 word, bỏ qua HBURST, và latency miss không được định lượng | §6.4.3, §6.9, DEC-016, DEC-030 |
| 6 (#006) | Major | interfaces | The AHB-Lite subordinate has no HREADY input and relies on the interconnect gating HSEL, a deviation from AMBA AHB (IHI 0033C) | AHB-Lite subordinate không có input HREADY và dựa vào interconnect để gate HSEL, lệch khỏi AMBA AHB (IHI 0033C) | §1.2, Table 7-3, Table 11-4 (ASM-003) |
| 7 (#007) | Major | integration_effort | UIT Tesla provides an AXI XIP connection but the IP has an AHB-Lite port; the required bridge is not specified | UIT Tesla cung cấp kết nối XIP AXI nhưng IP chỉ có cổng AHB-Lite; bridge cần thiết chưa được đặc tả | Table 11-4 (XIP bus row) |
| 8 (#008) | Major | application_fit | Serial PSRAM is claimed as supported, but there are no memory-mapped writes and CSN can stay low without limit, violating PSRAM tCEM | PSRAM được công bố là hỗ trợ, nhưng không có ghi memory-mapped và CSN có thể giữ mức thấp vô hạn, vi phạm tCEM của PSRAM | §1.1, §2, §3 (ASM-015), §6.4.1 |

## 2. Scorecard / Bảng điểm

**EN.** Scores 0-5 per area, weights and verdict computed by vlsit_scorecard.py from scorecard.json.

**VI.** Điểm 0-5 theo từng area, trọng số và kết luận do vlsit_scorecard.py tính từ scorecard.json.

| Area | Weight | Score | Justification |
|---|---:|---:|---|
| application_fit | 1.0 | 3 | Boot/XIP/program-erase use is clear (§1.1), but PSRAM is claimed without memory-mapped writes or tCEM control (F-008). |
| features | 1.0 | 3 | Feature list is explicit with an exclusion list (§2, §3); two advertised features (DDR, PSRAM) are not usable as specified (F-001, F-008). |
| functions | 1.5 | 3 | Cycle-level FSM tables and simulated waveforms for every block (§6.5-§6.8); PRESCALER legality rules are stale after the V2.0 formula change (F-004). |
| interfaces | 1.5 | 3 | Complete port tables with domain and reset (§7); the AHB-Lite subordinate has no HREADY input (F-006). |
| clock_reset_cdc | 1.5 | 4 | Every crossing has an ID and a structure (Table 6-2); quasi-static and reset assumptions rest on software rules (F-012, F-013). |
| parameters | 1.0 | 4 | Every parameter has a range, a default and an elaboration check (Table 5-1, §5); naming and base-address subtraction are observations (F-023). |
| data_representation | 0.5 | 4 | Bit, byte and word order, partial words and endianness are stated with a worked frame (§6.3, Table 6-5/6-6); no finding. |
| asic_feasibility | 1.5 | 1 | Flop-based, no macro, no clock gating, pads from flops (§11.1, §7.6); DDR write data changes on the SCLK sampling edges (Blocker F-001). |
| sdc_timing | 1.5 | 3 | Clocks and exceptions are listed (Table 11-2/11-3); pad budgets are 40 % placeholders that hide the read round trip (F-003, F-014). |
| area_power | 1.0 | 3 | No area or power figure; reviewer proxy is about 4.4k flops with TX/RX FIFOs at about 46 % (F-019). |
| performance | 1.5 | 2 | Peak rates follow from the formula, but read capture limits SCLK (F-002) and the XIP cache is a single 32-byte stream buffer with unquantified miss latency (F-005). |
| software_ease | 1.0 | 4 | Register map, flows and error table are complete (§8, §9); silent BUSY-locked writes and CPU DMA residue add driver work (F-017, F-018). |
| dft | 1.0 | 4 | No DFT ports by decision DEC-021, all flops scan-eligible, no macros (§11.1); the test-mode contract for resets and clocks is not written (F-020). |
| security_ras | 1.0 | 4 | No access control, no ECC and no APB timeout, all stated as decisions (§3, DEC-020); accepted as waivers (F-015, F-016). |
| verification_quality | 1.5 | 2 | Good corner-case and assertion list (§10), but no requirement or test IDs, no coverage plan and no result; sim/ and lint/ are empty (F-011). |
| documentation | 0.5 | 2 | Consistent structure and figures, but conflicting clock frequencies (F-009) and 32 cited DEC/ASM/DEP IDs plus REF-002/006/008 not defined (F-010). |
| integration_effort | 1.0 | 3 | Table 11-4 lists the integrator duties; the AXI-to-AHB-Lite XIP bridge required by UIT Tesla is not specified (F-007). |
| market_position | 1.0 | 3 | Register model follows STM32 QUADSPI but without its sample shift and DDR hold delay; no read calibration as in DesignWare SSI or Cadence xSPI (F-024, F-002). |
| **Weighted** | **20.5** | **2.98** | **Verdict: Conditional** |

The lowest score is ASIC feasibility (1) because of the DDR Blocker F-001. Performance and verification quality (2) follow: read capture and the XIP cache limit real throughput, and no requirement is traced to a test. / Điểm thấp nhất là ASIC feasibility (1) do Blocker F-001; tiếp theo là performance và verification quality (2).

## 3. Application fit / Phù hợp ứng dụng

**EN.** FACT §1.1: the IP is the UIT Tesla boot and code-storage path: XIP through AHB-Lite, program/erase and bulk reads in indirect mode by CPU or DMA, and status polling for program/erase completion, for one serial NOR flash or serial PSRAM. INFERENCE: the NOR-flash use is well served by the mode set; the PSRAM claim is not, and the XIP use depends on an AXI bridge that is not specified (F-007, chapter 18). Score 3.

**VI.** FACT §1.1: IP là đường boot và lưu code của UIT Tesla: XIP qua AHB-Lite, program/erase và đọc khối ở indirect mode bằng CPU hoặc DMA, và status polling để chờ program/erase, cho một serial NOR flash hoặc serial PSRAM. INFERENCE: use case NOR flash được phục vụ tốt; claim PSRAM thì không, và XIP phụ thuộc vào một AXI bridge chưa được đặc tả (F-007, chương 18). Điểm 3.

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-008 | Major | §1.1, §2, §3 (ASM-015), §6.4.1 | FACT: Serial PSRAM is claimed as supported, but there are no memory-mapped writes and CSN can stay low without limit, violating PSRAM tCEM | PSRAM được công bố là hỗ trợ, nhưng không có ghi memory-mapped và CSN có thể giữ mức thấp vô hạn, vi phạm tCEM của PSRAM | Either remove PSRAM from §1.1 and §2, or add memory-mapped write support plus a DLY-like maximum CSN-low counter that ends the frame at a byte boundary and restarts it. |

## 4. Features / Tính năng

**EN.** FACT §2 lists 16 features and §3 lists 10 exclusions with decision IDs; the exclusion list is better than most student IPs. INFERENCE: two advertised features are not usable as specified, DDR (F-001, chapter 9) and PSRAM (F-008, chapter 3); no feature carries a FEAT/REQ ID (F-010). Score 3; the findings are recorded in their owning chapters.

**VI.** FACT §2 liệt kê 16 tính năng và §3 liệt kê 10 loại trừ kèm decision ID; danh sách loại trừ rõ ràng. INFERENCE: hai tính năng được quảng bá không dùng được như đặc tả, DDR (F-001, chương 9) và PSRAM (F-008, chương 3); không tính năng nào có FEAT/REQ ID (F-010). Điểm 3; các phát hiện được ghi ở chương sở hữu.

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| — | — | — | No finding in this area. | Không có phát hiện. | — |

## 5. Functions and cycle behaviour / Chức năng và hành vi theo chu kỳ

**EN.** FACT §6.5-§6.8 give an FSM table, an output table and RTL-simulated waveforms for the Command Sequencer, Clock Manager, Shifter and Polling Status Control; frame triggers (Table 6-8), error conditions (Table 6-10) and abort are specified to the cycle. This is the strongest part of the document. INFERENCE: the PRESCALER legality rules were not updated with the V2.0 formula (F-004).

**VI.** FACT §6.5-§6.8 có bảng FSM, bảng output và waveform mô phỏng RTL cho Command Sequencer, Clock Manager, Shifter và Polling Status Control; trigger frame (Table 6-8), lỗi (Table 6-10) và abort được đặc tả tới từng chu kỳ. Đây là phần mạnh nhất. INFERENCE: quy tắc hợp lệ PRESCALER chưa cập nhật theo công thức V2.0 (F-004).

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-004 | Major | §6.6.2, Table 6-14, Table 6-10, Table 8-3 | INFERENCE: PRESCALER legality rules look stale after the V2.0 formula change: odd values are rejected in SDR and DDR allows only 2, 6, 10, ... | Quy tắc hợp lệ của PRESCALER có vẻ còn từ công thức cũ trước V2.0: giá trị lẻ bị từ chối ở SDR, DDR chỉ cho 2, 6, 10, ... | Accept every PRESCALER in SDR (1..255, 0 kept as F/2) and every even PRESCALER >= 2 in DDR (with the F-001 midpoint launch); update the TEF check in m_qspi_reg_cfg, Table 6-10, Table 6-14 and Table 8-3. |
| F-021 | Observation | §6.4.6, §6.6.3, Table 8-19 | FACT: Abort raises CSN mid-byte without the CSN hold time and reports the same TCF as a normal completion | Abort kéo CSN lên giữa byte không có CSN hold time và báo cùng TCF như hoàn tất bình thường | Waive: Same behaviour as STM32 QUADSPI; software knows it issued the abort. |

## 6. Interfaces and protocol / Giao diện và giao thức

**EN.** FACT §7 gives every port with direction, width, domain and reset value. Compliance (standard, revision, topic; clause numbers not read are not cited, R-005):

| Requirement | Standard | Specification statement | Verdict |
|---|---|---|---|
| APB3 signal set, no PSTRB/PPROT | Arm IHI 0024E, signal list | §1.2 | compliant (APB3 profile) |
| Wait states through PREADY | Arm IHI 0024E, transfers with wait states | §7.2 | compliant |
| PSLVERR on unmapped offset | Arm IHI 0024E, error response | §7.2, Table 6-10 | compliant |
| HREADY input qualifies the address phase | Arm IHI 0033C, HREADY | §1.2 'no HREADY input' | deviation, F-006 |
| IDLE/BUSY get zero-wait OKAY | Arm IHI 0033C, transfer types | §6.4.3 | compliant |
| Two-cycle ERROR response | Arm IHI 0033C, response signaling | §7.3 | compliant |
| HSIZE/HBURST/HPROT ignored | Arm IHI 0033C | §1.2 | deviation recorded; HBURST loss costs XIP (F-005) |
| SPI mode 0/3, tCSS/tCSH/tCS | de facto SPI NOR (no standard) | §6.6 | compliant |
| DDR input setup/hold at the flash | de facto SPI NOR DTR timing | §7.6 | deviation, F-001 |
| SFDP discovery (JEDEC JESD216) | JESD216 | not stated | not stated (software owns it, §3) |

The skill catalog names APB IHI 0024 Issue D; the specification cites Issue E. Both are current Arm issues and the APB3 subset is unchanged by the newer issue for these signals (INFERENCE).

**VI.** FACT §7 có đủ port với hướng, độ rộng, domain và giá trị reset. Bảng compliance ở trên (tiêu chuẩn, revision, chủ đề; không trích số clause chưa đọc). INFERENCE: lệch quan trọng nhất là thiếu HREADY input ở AHB-Lite (F-006) và timing DDR ở pad (F-001); DMA req/clr là handshake tùy biến (F-022).

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-006 | Major | §1.2, Table 7-3, Table 11-4 (ASM-003) | FACT: The AHB-Lite subordinate has no HREADY input and relies on the interconnect gating HSEL, a deviation from AMBA AHB (IHI 0033C) | AHB-Lite subordinate không có input HREADY và dựa vào interconnect để gate HSEL, lệch khỏi AMBA AHB (IHI 0033C) | Add input i_qspi_ahb_hready and accept an address phase only when HSEL & HREADY & HTRANS[1]; drop ASM-003 from Table 11-4. |
| F-022 | Observation | §7.4, Table 7-4 (ASM-005) | FACT: The DMA req/clr handshake is custom and the target DMA controller is not named | Handshake DMA req/clr là tùy biến và DMA controller đích không được nêu | Waive: The handshake is fully specified and the integrator duty is in Table 11-4. |

## 7. Clock, reset and CDC / Clock, reset và CDC

**EN.** FACT §6.1: four mutually asynchronous clocks; SCLK is a flop output, never a clock. FACT Table 6-2: eight crossings (CDC-001..007, CDC-010), each with a dedicated module: Gray async FIFOs, 2-flop level syncs, toggle pulse syncs with acknowledge. FACT §6.2: resets asserted asynchronously and released synchronously by the CRM (ASM-014), no internal reset synchronizer (DEC-022). INFERENCE: the structure is sound and well documented; the weak points are a quasi-static multi-bit crossing that relies on software (F-012) and the absence of an RDC table (F-013).

**VI.** FACT §6.1: bốn clock bất đồng bộ; SCLK là output của flop, không là clock. FACT Table 6-2: tám crossing, mỗi crossing có module riêng: Gray async FIFO, 2-flop sync, toggle pulse sync có acknowledge. FACT §6.2: reset do CRM assert bất đồng bộ và release đồng bộ (ASM-014). INFERENCE: cấu trúc tốt; điểm yếu là crossing đa bit quasi-static dựa vào phần mềm (F-012) và thiếu bảng RDC (F-013).

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-012 | Minor | Table 6-2 CDC-005 (ASM-007) | INFERENCE: DCR.FSIZE and the memory-mapped enable cross to HCLK through per-bit 2-flop synchronizers, safe only under a software rule | DCR.FSIZE và memory-mapped enable sang HCLK qua 2-flop synchronizer từng bit, chỉ an toàn nhờ quy tắc phần mềm | Carry FSIZE with the enable through a request/acknowledge handshake (data held in the clk domain, captured in HCLK on the synchronized toggle), or hold memory-mapped mode off in HCLK until the new FSIZE is stable. |
| F-013 | Minor | §6.2, Table 6-3 (ASM-002, ASM-012, ASM-014) | INFERENCE: Reset assumptions conflict and no RDC analysis is given for the four reset domains | Các giả định reset mâu thuẫn và không có phân tích RDC cho bốn reset domain | Add an RDC table: each crossing, its two resets, the state at release in each order, and why no spurious word or pulse is produced; reconcile ASM-002 with the core-in-reset sentences. |

## 8. Parameters and data / Tham số và biểu diễn dữ liệu

**EN.** FACT Table 5-1: 14 parameters with value set, default and description; §5 lists the $error elaboration checks; Table 10-1 CFG-ILLEGAL tests them. FACT §6.3 defines bit order per lane mode, byte order of address/alternate bytes, DR byte order, partial-word zero padding and AHB little-endian packing, with truth tables 6-5/6-6/6-7. INFERENCE: data representation is complete (score 4, no finding); parameter naming is the only remark (F-023).

**VI.** FACT Table 5-1: 14 tham số có tập giá trị, default và mô tả; §5 nêu các kiểm tra $error khi elaboration. FACT §6.3 định nghĩa thứ tự bit, byte, zero padding và little-endian của AHB với truth table. INFERENCE: biểu diễn dữ liệu đầy đủ (điểm 4, không có phát hiện); chỉ có nhận xét về đặt tên tham số (F-023).

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-023 | Observation | Table 5-1 rows 6, 13, 14; §7.3 | FACT: PARA_AHB_SYNC_FIFO_DEPTH sizes async FIFOs, and the IP subtracts base addresses that an interconnect normally removes | PARA_AHB_SYNC_FIFO_DEPTH thực chất là độ sâu async FIFO, và IP tự trừ base address vốn thường do interconnect xử lý | Waive: Defaults of 0 remove the subtractor's effect and the wrap case is documented. |

## 9. ASIC feasibility / Khả thi ASIC

**EN.** Synthesizability: FACT §11.1 standard cells only, no macros, no clock gating, no internal tri-states; flop FIFOs. Clock/reset: see chapter 7. CDC/RDC: see chapter 7. Timing path: FACT §7.6 all pad outputs come from flops; FACT §6.7.3 output and capture registers add one clk of latency each way. INFERENCE: the 200 MHz core logic (8-way 32-bit tag compare, 33-bit range adder, 33-bit byte counter) is ordinary for any node of 65 nm or newer, but the target technology is not stated, so a mapped timing claim cannot be made. The pad interface is the real risk: DDR output data changes at the sampling edges (F-001, Blocker) and read capture has only a half SCLK period (F-002).

**VI.** Synthesizability: FACT §11.1 chỉ dùng standard cell, không macro, không clock gating. Timing path: FACT §7.6 mọi output pad ra từ flop. INFERENCE: logic core 200 MHz là bình thường cho node 65 nm trở xuống, nhưng spec không nêu công nghệ nên không khẳng định được timing đã map. Rủi ro thật nằm ở pad: dữ liệu DDR đổi đúng tại cạnh lấy mẫu (F-001, Blocker) và capture khi đọc chỉ có nửa chu kỳ SCLK (F-002).

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-001 | Blocker | §7.6, Table 6-15, §11.2 | INFERENCE: DDR output data changes on the same clk edge as every SCLK edge, so the flash sees zero hold time on address, alternate and data bits | Dữ liệu ra ở DDR đổi trạng thái cùng clk edge với mọi SCLK edge, flash nhận hold time bằng 0 cho address, alternate và data | In m_qspi_edge_sel add a DDR launch strobe at the middle of each SCLK half period (a quarter SCLK period after the edge) and use it to load the output register in DDR write phases; restrict DDR to an even PRESCALER >= 2 so the midpoint is an integer clk count; constrain the DDR falling edge in the SDC. |

## 10. SDC and timing / SDC và timing

**EN.** FACT Table 11-2 defines four 200 MHz clocks and SCLK as a divide-by-2 generated clock on the pad; Table 11-3 lists EXC-001..004 with rationale; reset paths are timed. FACT §11.2 states the file holds synthesis, not signoff, constraints. INFERENCE: the structure is honest, but the 40 % placeholders and the unconstrained DDR falling edge make the pad timing look closed when it is not (F-003); the CDC exceptions need tool and skew precision (F-014). The SDC file itself (sdc/m_uit_qspi_wrap.sdc) is not in the reviewed folder.

**VI.** FACT Table 11-2 định nghĩa bốn clock 200 MHz và SCLK là generated clock chia 2 tại pad; Table 11-3 có EXC-001..004 kèm lý do. INFERENCE: placeholder 40 % và cạnh xuống DDR không constrain làm timing pad có vẻ đạt dù thực tế không (F-003); exception CDC cần rõ tool và skew (F-014). File SDC không có trong thư mục được review.

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-003 | Major | §11.2, Table 11-2 | FACT: Pad IO delays are 40 % placeholders of the fastest SCLK period and the DDR falling edge is unconstrained, so synthesis cannot reveal F-001 or F-002 | IO delay của pad là placeholder 40 % chu kỳ SCLK nhanh nhất và cạnh xuống DDR không được constrain, nên synthesis không phát hiện được F-001, F-002 | Write the pad budget from a named flash (tCLQV, tDS/tDH, tCSS/tCSH) plus pad and board delays; add set_output_delay -clock_fall for DDR; state the SCLK limit the budget closes for SDR read, SDR write and DDR. |
| F-014 | Minor | Table 11-3 EXC-001, EXC-002 | INFERENCE: set_clock_groups -allow_paths is tool-specific and the Gray-pointer crossings have no skew constraint | set_clock_groups -allow_paths phụ thuộc tool và các crossing Gray pointer không có ràng buộc skew | State the STA tool; use set_max_delay -ignore_clock_latency (or -datapath_only) and add a skew constraint (set_data_check or set_bus_skew) on each Gray pointer bus. |

## 11. Area and power / Diện tích và công suất

**EN.** Proxy only (R-008), default parameters, no library, not mapped:

| Block | Flops (proxy) | Assumption |
|---|---:|---|
| TX + RX FIFO | 2048 | 2 x 32 x 32 bit, flop storage (§6.10) |
| AHB cache | 520 | 8 x (32 data + 32 tag + 1 valid) |
| AHB control + data async FIFOs | 552 | 8 x 36 + 8 x 33 |
| APB request + response async FIFOs | 328 | 4 x 49 + 4 x 33 |
| Register file | 350 | 17 registers, reserved bits removed |
| Frame latch (CCR, AR, ABR, DLR) | 130 | Command Sequencer |
| Shifter | 200 | TX/RX shift, RX immediate, phase settings |
| Counters | 210 | byte 33, polling timeout 32, interval 16, AHB timeout 21, CSN 3 x 8, others |
| Synchronizers | 80 | pointer, level and toggle syncs |
| **Total** | **about 4.4k** | about 30-40 kGE at 6 GE per flop plus muxes |

Power: no figure, no activity assumption, no clock gating (F-019).

**VI.** Chỉ là proxy (R-008), tham số mặc định, chưa map thư viện. Tổng khoảng 4.4k flop, khoảng 30-40 kGE; TX/RX FIFO chiếm khoảng 46 %. Công suất: không có số liệu, không có clock gating (F-019).

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-019 | Major | §11.1, §6.10, Table 5-1 | INFERENCE: No area or power figure; the reviewer proxy is about 4.4k flops, with the TX/RX FIFOs about 46 % while the XIP cache is 8 words | Không có số liệu diện tích hay công suất; proxy của reviewer khoảng 4.4k flop, TX/RX FIFO chiếm khoảng 46 % trong khi cache XIP chỉ 8 word | Add an area/power table (proxy now, mapped with the UIT Tesla library later), allow synthesis clock-gating insertion, and reconsider 32-word FIFOs against a larger XIP cache for UIT Tesla. |

## 12. Performance and throughput / Hiệu năng và thông lượng

**EN.** | Metric | Value | Basis |
|---|---|---|
| Max SCLK, SDR | F/2 = 100 MHz | FACT Table 6-1, §6.6.2 |
| Max SCLK, DDR | F/4 = 50 MHz | FACT §6.6.2 |
| Legal SCLK at 200 MHz, SDR | 100, 50, 25, 16.7, 12.5 MHz ... | FACT Table 6-14 rule; F-004 |
| Legal SCLK at 200 MHz, DDR | 50, 16.7, 10 MHz ... | FACT Table 6-14 rule; F-004 |
| Peak flash bandwidth | 1 to 8 bits per SCLK; quad SDR at 50 MHz = 25 MB/s | FACT §6.3 |
| Read SCLK closable without sample delay | about F/8 = 25 MHz | INFERENCE, F-002 |
| XIP NONSEQ miss latency | about 130 clk = 650 ns per 4 bytes | INFERENCE, F-005 |
| XIP hit latency | unquantified | flagged (R-009) |
| APB access latency | unquantified (one PCLK cycle + two async FIFO crossings + register operation) | flagged, §7.2 |
| AHB timeout | 2^20 HCLK = 5.24 ms at 200 MHz / 10.49 ms at 100 MHz | FACT Table 11-4; F-009 |

Unquantified claims: §1.1 'reduces the read latency'; §6.9 cache benefit.

**VI.** Bảng trên nêu tốc độ SCLK, băng thông và latency. INFERENCE: nếu không có sample delay thì đọc chỉ chắc chắn ở khoảng 25 MHz (F-002); một miss NONSEQ ở XIP tốn khoảng 650 ns cho 4 byte và cache chỉ là stream buffer 32 byte (F-005). Latency hit và latency APB chưa được định lượng.

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-002 | Major | §3, Table 6-15, §11.2 | INFERENCE: Read data is always captured half an SCLK period after the flash launch, with no sample shift or delay, so F/2 and probably F/4 reads cannot close | Dữ liệu đọc luôn được capture sau nửa chu kỳ SCLK, không có sample shift hay delay, nên đọc ở F/2 và có thể F/4 không đạt timing | Add a CR.SSHIFT-like field (or a 3-bit DCR sample-delay in clk cycles) that delays the sample strobe of read phases by 1..N clk cycles, and state the maximum read SCLK per delay setting in §6.6.2. |
| F-005 | Major | §6.4.3, §6.9, DEC-016, DEC-030 | INFERENCE: The XIP cache is a single 32-byte stream buffer: every miss invalidates all lines, a NONSEQ miss fetches one word, HBURST is ignored and miss latency is not quantified | Cache XIP thực chất là một stream buffer 32 byte: mỗi miss invalidate toàn bộ line, miss NONSEQ chỉ fetch 1 word, bỏ qua HBURST, và latency miss không được định lượng | Fetch an aligned block (PARA_PREFETCH_LENGTH words) on every miss, NONSEQ included, using HBURST to size it; replace invalidate-all with a FIFO or LRU replacement of aligned blocks; add a latency table (hit, NONSEQ miss, SEQ miss) to §6.4.3. |

## 13. Software and application ease / Dễ lập trình và ứng dụng

**EN.** FACT §8: 17 registers with field tables and access types; §9 gives init, interrupt, DMA, indirect, polling, memory-mapped and abort flows; Table 6-10 maps every error to a flag and a recovery. INFERENCE: the programming model is workable and close to STM32 QUADSPI, which eases driver design but not driver reuse (F-024). Driver friction: silent locked writes (F-017) and the CPU DMA residue (F-018).

**VI.** FACT §8: 17 thanh ghi có bảng field và kiểu truy cập; §9 có các flow init, interrupt, DMA, indirect, polling, memory-mapped, abort; Table 6-10 ánh xạ lỗi sang flag và cách khôi phục. INFERENCE: mô hình lập trình dùng được, gần STM32 QUADSPI nhưng driver không tái sử dụng được (F-024). Điểm phiền: ghi bị khóa bị bỏ âm thầm (F-017) và phần dư DMA do CPU làm (F-018).

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-017 | Minor | §8.1, §7.2, §9.7 | FACT: Writes to BUSY-locked fields are silently dropped with no flag | Ghi vào field bị khóa khi BUSY bị bỏ qua âm thầm, không có flag | Add a sticky SR.WLKF (write-locked) flag, cleared through FCR, set when a write hits a BUSY-locked field. |
| F-018 | Minor | §6.4.4, §9.3 (DEC-029, ASM-013) | FACT: DMA moves whole bursts only; the CPU must move the residue and a DMA channel programmed for it waits forever | DMA chỉ chuyển trọn burst; CPU phải chuyển phần dư và kênh DMA lập trình cho phần dư sẽ chờ mãi | Raise the request for the last partial burst when the remaining words are fewer than the threshold (TX: remaining bytes to write; RX: frame complete and RX FIFO not empty), with the DMA programmed by word count. |

## 14. DFT / DFT

**EN.** FACT DEC-021: no DFT ports; Table 11-4: all flops scan-eligible, scan inserted by the SoC flow; §11.1: no macros, so no MBIST. INFERENCE: acceptable for this IP class, provided the test-mode contract is written (F-020).

**VI.** FACT DEC-021: không có port DFT; mọi flop scan được, scan chèn ở flow SoC; không macro nên không cần MBIST. INFERENCE: chấp nhận được nếu viết rõ DFT contract (F-020).

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-020 | Minor | §3, Table 11-4 (DEC-021) | INFERENCE: The DFT contract for the four clocks, four async resets and the pad capture flop is not written | Chưa viết DFT contract cho bốn clock, bốn async reset và flop capture của pad | Add a DFT table: reset controllability, clock sources in scan mode, synchronizer handling, pad IO in scan mode, expected coverage exclusions. |

## 15. Security and RAS / An toàn và độ tin cậy

**EN.** FACT §3: no ECC/parity, no PPROT/HPROT filtering, no APB timeout (DEC-020); FACT §6.4.6: no error is fatal; AHB timeout prevents an XIP hang. INFERENCE: the stance is explicit; the two residual risks are accepted as waivers with owner and invalidation condition (F-015, F-016).

**VI.** FACT §3: không ECC/parity, không lọc PPROT/HPROT, không APB timeout (DEC-020); AHB timeout tránh treo XIP. INFERENCE: lập trường rõ ràng; hai rủi ro còn lại được waive có owner và điều kiện mất hiệu lực (F-015, F-016).

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-015 | Minor | §3, §7.2, Table 11-4 (DEC-020) | FACT: No APB timeout: an APB access while i_qspi_clk is stopped or in reset hangs the CPU bus | Không có APB timeout: truy cập APB khi i_qspi_clk dừng hoặc đang reset sẽ treo bus CPU | Waive: DEC-020 is a closed decision and the CRM rule in Table 11-4 removes the trigger. |
| F-016 | Minor | §3, §1.1 | FACT: No access control, register lock or integrity check on the boot/XIP path | Không có access control, khóa thanh ghi hay kiểm tra toàn vẹn trên đường boot/XIP | Waive: The exclusion is stated, and UIT Tesla states no secure-boot or untrusted-manager requirement. |

## 16. Verification quality / Chất lượng kiểm chứng

**EN.** FACT §10: environment (APB/AHB agents, DMA model, flash model, randomized clock ratios), 17 corner-case groups, about 20 key assertions and five configurations (Table 10-1). FACT inventory.json: 0 requirement IDs, 0 test IDs; sim/ and lint/ are empty. INFERENCE: a good plan seed with no traceability and no evidence (F-011).

**VI.** FACT §10: môi trường, 17 nhóm corner case, khoảng 20 assertion chính và năm cấu hình. FACT inventory.json: 0 requirement ID, 0 test ID; sim/ và lint/ trống. INFERENCE: nền tảng test plan tốt nhưng không có truy vết và không có bằng chứng (F-011).

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-011 | Major | §10, Table 10-1 | FACT: No requirement-to-test traceability, no coverage plan, no flash model named and no verification result; sim/ and lint/ are empty | Không có truy vết requirement-test, không có coverage plan, không nêu flash model và không có kết quả kiểm chứng; sim/ và lint/ trống | Give each §10 bullet a TEST-nnn ID mapped to REQ-nnn, name the flash model and require it to check tDS/tDH and tCLQV, list functional coverage bins, and add the regression status per configuration of Table 10-1. |

## 17. Documentation and traceability / Tài liệu và truy vết

**EN.** FACT: 47 sections, 64 tables, 23 figures with a table of tables and figures; revision history records every change. INFERENCE: structure and writing are clear; the defects are contradictions and undefined identifiers (F-009, F-010). Smaller items: title 'Reversion' (Revision); legacy REF-002 figures that the notes say are outdated (Figure 6-4, Figure 6-23).

**VI.** FACT: 47 mục, 64 bảng, 23 hình có mục lục. INFERENCE: cấu trúc rõ; lỗi là mâu thuẫn và ID không được định nghĩa (F-009, F-010). Mục nhỏ: tiêu đề 'Reversion' (Revision); hình REF-002 cũ đã lỗi thời (Figure 6-4, Figure 6-23).

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-009 | Major | Table 6-1, Table 11-2, §9.6, Table 11-4 | FACT: Clock frequencies conflict: all clocks are 200 MHz in Table 6-1/11-2, but §9.6 and Table 11-4 use HCLK = 100 MHz and i_qspi_clk = 5 MHz; PRESCALER <= 54 gives 108, not 110, clk cycles | Tần số clock mâu thuẫn: Table 6-1/11-2 ghi 200 MHz, nhưng §9.6 và Table 11-4 dùng HCLK = 100 MHz và i_qspi_clk = 5 MHz; PRESCALER <= 54 cho 108 chứ không phải 110 chu kỳ clk | State one UIT Tesla delivery clock plan, recompute the AHB timeout and the memory-mapped PRESCALER limit from it with the frame length used, and correct the 110/108 arithmetic. |
| F-010 | Major | Table 1-1, §4, §5, §8, Appendix B | FACT: REF-002/006/008, the source design specification and 32 cited DEC/ASM/DEP items are not defined in the document; no requirement IDs; the review table is empty | REF-002/006/008, tài liệu design specification nguồn và 32 mục DEC/ASM/DEP được trích dẫn nhưng không định nghĩa trong tài liệu; không có requirement ID; bảng review trống | Add REF-002/006/008 and UIT-Tesla-QSPI-SPEC v0.2 to Table 1-1, append DEC/ASM/DEP tables with status and owner, add REQ-nnn IDs to normative statements, and set the title to V2.0. |

## 18. Integration effort and bring-up / Công sức tích hợp và bring-up

**EN.** FACT Table 11-4 lists ten integrator duties: HSEL gating, base addresses, AHB timeout, resets, clock stop, pads with IO2/IO3 pull-ups, interrupt, DMA, XIP bridge and DFT. INFERENCE: bring-up needs the AXI bridge (F-007), custom HSEL gating (F-006) and a real flash timing budget (F-003); with those, the effort is moderate.

**VI.** FACT Table 11-4 liệt kê mười nhiệm vụ của integrator. INFERENCE: bring-up cần AXI bridge (F-007), logic gate HSEL tùy biến (F-006) và budget timing flash thực (F-003); có những thứ đó thì công sức tích hợp ở mức vừa phải.

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-007 | Major | Table 11-4 (XIP bus row) | FACT: UIT Tesla provides an AXI XIP connection but the IP has an AHB-Lite port; the required bridge is not specified | UIT Tesla cung cấp kết nối XIP AXI nhưng IP chỉ có cổng AHB-Lite; bridge cần thiết chưa được đặc tả | Add a section that names the AXI-to-AHB-Lite bridge (or an AXI4 subordinate option), its owner, burst/WRAP conversion, response mapping, outstanding count and added latency. |

## 19. Market position / Vị thế thị trường

**EN.** Source order (R-004): web search done on 2026-11-18; datasheets behind NDA (Cadence) not obtained.

| Expectation | UIT QSPI (spec) | Commercial reference | Source, date | Verdict |
|---|---|---|---|---|
| Read sample shift / delay | none (§3) | STM32 QUADSPI SSHIFT shifts sampling by half a CLK cycle | ST STM32L4x6 RM, delayed data sampling (manualslib copy p.408), accessed 2026-11-18 | missing |
| DDR output hold delay | none (§7.6) | STM32 DHQC delays DDR output by a quarter cycle; ST FAQ: enable DHQC in DTR | ST community FAQ for QUADSPI/OCTOSPI/HSPI/XSPI; STM32G4 HAL header, accessed 2026-11-18 | missing |
| Programmable RX sample delay | none | DesignWare SSI RX_SAMPLE_DLY, one ssi_clk per step, optional by configuration | Intel Agilex5 HPS SPIM RX_SAMPLE_DLY register page; rp2040-pac XIP_SSI docs, accessed 2026-11-18 | missing |
| Delay-line read calibration | none | xSPI soft PHY with RX DLL to shift sampling; Arasan xSPI PHY DLL in 625 ps steps | ADI EE-468; arasan.com xSPI PHY page, accessed 2026-11-18 | missing (not expected at this class) |
| XIP | AHB-Lite, 8-word buffer | Cadence xSPI: XIP, PHY-less or combo PHY | cadence.com xSPI product page, accessed 2026-11-18 | matched (weaker cache, F-005) |
| Register model | STM32-like offsets | STM32 QUADSPI CR/DCR/SR/FCR/DLR/CCR/AR/ABR/DR/PSMKR/PSMAR/PIR | INFERENCE (no external source): reviewer knowledge of the STM32 RM layout | matched in offsets, differs in bits (F-024) |
| Flash tCLQV used for F-002 | — | 6 ns (Intel EPCQ-A), 7 ns (T25Q16BW, 2.7-3.6 V) | intel.com EPCQ-A read operation timing; jiepei T25Q16BW datasheet p.69, accessed 2026-11-18 | input to F-002 |

**VI.** Đã tìm web ngày 2026-11-18. INFERENCE: so với STM32 QUADSPI, DesignWare SSI và Cadence xSPI, IP thiếu đúng các tính năng timing ở pad (sample shift, DDR hold delay, sample delay) mà sản phẩm thương mại dùng để đạt tần số cao; cache XIP yếu hơn. Offset thanh ghi giống STM32 nhưng bit khác (F-024).

**Findings**

| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |
|---|---|---|---|---|---|
| F-024 | Observation | §8.2 Table 8-2, Table 8-3, Table 8-15 | INFERENCE: Register offsets mirror STM32 QUADSPI but bit positions and PTR meaning differ, and its SSHIFT/DHQC timing features are absent | Offset thanh ghi giống STM32 QUADSPI nhưng vị trí bit và ý nghĩa PTR khác, và thiếu các tính năng timing SSHIFT/DHQC | State in §8 that the map is STM32-inspired but not compatible, list the differences, and adopt the sample-shift and DDR-hold fields of F-001/F-002. |

## 20. Actions / Hành động

**EN.** Priorities follow severity and root cause (grouped.json).

**VI.** Thứ tự ưu tiên theo severity và root cause.

| Priority | Action | Owner | Evidence |
|---|---|---|---|
| P0 | DDR launch at half-period midpoint; read sample delay; PRESCALER rules | RTL | F-001, F-002, F-004 |
| P0 | Pad budget from a named flash datasheet; DDR falling-edge constraints | SDC / spec | F-003 |
| P1 | HREADY input; aligned block fills and multi-block XIP cache; AXI bridge section | RTL / SoC | F-005, F-006, F-007 |
| P1 | Remove or complete PSRAM support | spec / RTL | F-008 |
| P1 | One clock plan; REF/DEC/ASM/DEP tables; REQ/TEST IDs and coverage | spec / DV | F-009, F-010, F-011 |
| P2 | Area/power table; CDC-005 handshake; RDC table; SDC portability; DFT table; locked-write flag; DMA residue | RTL / spec | F-012..F-014, F-017..F-020 |

## 21. Evidence appendix / Phụ lục bằng chứng

**EN.** Inputs, gate results, audit and limits of this review.

**VI.** Đầu vào, kết quả gate, audit và giới hạn của review.

Folder inventory (R-001), rtl/qspi:

| Item | Content |
|---|---|
| doc/UIT_QSPI_Specification.md | 1541 lines, sha256 8cbfcfcf4ad0b5361935d3d4c3e3e46f601a4b77c3ae0d13d74b156c9e557cbb |
| doc/images/figure_01..26.png | 26 figures (23 referenced in the table of figures) |
| lint/, logical/, sim/, syn/ | .gitkeep only: no RTL, lint, simulation or synthesis evidence |
| sdc/m_uit_qspi_wrap.sdc, QSPI_Register_Description.pdf (REF-008), UIT-Tesla-QSPI-SPEC v0.2 | cited, not present |

Extracted by vlsit_spec_inventory.py (inventory.json): 47 sections, 64 tables, 0 requirement IDs, 0 test IDs, 18 DEC, 14 open items (ASM-002/003/004/005/007/010/011/012/013/014/015, DEP-001/009/011). Age: not stated per item; earliest possible origin V1.0 (10/20/2026), so at most 29 days.

Gate (vlsit_review_gate.py metrics): `RESULT: FAIL, 24 finding(s)`; 1 unwaived Critical finding(s): F-001; waiver usage 5/10; sampling 100 %; closure 79 %.
The gate fails by design on the open Blocker F-001: a specification review cannot fix RTL, and waiving it would hide the main result.

Deep sample (R-022): 24 findings in 14 root-cause groups; no group has more than 10 findings, so all 24 were traced and none aggregated.

Audit sample (R-021, vlsit_review_gate.py sample, 10 %%, self-audit because no second reviewer was available):

| Finding | Severity | Result | Re-check |
|---|---|---|---|
| audit of F-009 | High | tp | Table 6-1 line 379 (200 MHz) vs §9.6 line 1400 and Table 11-4 line 1495 (100 MHz / 5 MHz) re-read; conflict confirmed. |
| audit of F-003 | High | tp | §11.2 lines 1463 and 1484 re-read: 40 % placeholder and unconstrained DDR falling edge confirmed. |
| audit of F-010 | High | tp | Table 1-1 lines 214-219 list REF-001/003/005/010 only; REF-002/006/008 cited at lines 166, 334, 1097; no DEC/ASM/DEP table found. |

False-positive rate 0/3, false-negative rate 0/3 on the sample.

Not assessed and why:

- RTL, lint, CDC/RDC tool reports and synthesis: folders are empty; an implementation review (vlsit-ip-impl-review) is needed once RTL is present.
- The SDC file and REF-008 register PDF: cited but absent.
- Figures were not inspected image by image; their captions and notes were used.
- Mapped area and power: no library (R-008).
- Commercial datasheets behind NDA (Cadence, Synopsys databook) were not obtained.

Sources (accessed 2026-11-18):
- ST STM32L4x6 reference manual, QUADSPI delayed data sampling: https://www.manualslib.com/manual/1317428/St-Stm32l4x6.html?page=408
- ST community, Overall FAQs for QUADSPI/OCTOSPI/HSPI/XSPI: https://community.st.com/stm32-mcus-60/overall-faqs-for-quadspi-octospi-hspi-xspi-132640
- STM32G4 HAL QSPI header: https://codex.ac6.fr/Zephyr/xref/hal_stm32-3.5.0/stm32cube/stm32g4xx/drivers/include/stm32g4xx_hal_qspi.h
- Intel Agilex5 HPS SPIM RX_SAMPLE_DLY: https://www.intel.com/content/www/us/en/programmable/hps/agilex5/topics/register_SPIM_1_RX_SAMPLE_DLY.html
- rp2040-pac XIP_SSI: https://docs.rs/rp2040-pac/0.6.0/rp2040_pac/struct.XIP_SSI.html
- Cadence xSPI: https://www.cadence.com/en_US/home/tools/silicon-solutions/design-ip/memory-interface-and-storage-ip/storage-ip/xspi.html
- ADI EE-468 xSPI PHY: https://www.analog.com/media/en/technical-documentation/application-notes/ee-468.pdf
- Arasan xSPI PHY: https://www.arasan.com/?p=7830
- Intel EPCQ-A read operation timing: https://www.intel.com/content/www/us/en/docs/programmable/683818/current/read-operation-timing.html
- T25Q16BW datasheet: https://pdf.jiepei.com/t25q16bwept-34476627.html?page=69
