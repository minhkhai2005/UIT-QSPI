#!/usr/bin/env python3
"""Render REVIEW_UIT_QSPI.md and vlsit_spec_2026-11-18.md from findings_data.json and the gate outputs."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
F = json.loads((HERE / "findings_data.json").read_text(encoding="utf-8"))
GATE = json.loads((HERE / "gate.json").read_text(encoding="utf-8"))
AUDIT = json.loads((HERE / "audit.json").read_text(encoding="utf-8"))
GROUPS = json.loads((HERE / "grouped.json").read_text(encoding="utf-8"))
SCORE_MD = (HERE / "scorecard.md").read_text(encoding="utf-8").strip()
DATE = "2026-11-18"
SPEC_PATH = "rtl/qspi/doc/UIT_QSPI_Specification.md"
SHA = "8cbfcfcf4ad0b5361935d3d4c3e3e46f601a4b77c3ae0d13d74b156c9e557cbb"
AUDIT_RESULT = {"F-009": ("tp", "Table 6-1 line 379 (200 MHz) vs §9.6 line 1400 and Table 11-4 line 1495 (100 MHz / 5 MHz) re-read; conflict confirmed."),
                "F-003": ("tp", "§11.2 lines 1463 and 1484 re-read: 40 % placeholder and unconstrained DDR falling edge confirmed."),
                "F-010": ("tp", "Table 1-1 lines 214-219 list REF-001/003/005/010 only; REF-002/006/008 cited at lines 166, 334, 1097; no DEC/ASM/DEP table found.")}

by_area = {}
for f in F:
    by_area.setdefault(f["area"], []).append(f)


def rows(areas):
    out = ["| ID | Severity | Locator | Statement (EN) | Phát hiện (VI) | Action |", "|---|---|---|---|---|---|"]
    for a in areas:
        for f in by_area.get(a, []):
            action = (f.get("fix") or ("Waive: " + f["why"])).replace("|", "/")
            out.append("| %s | %s | %s | %s: %s | %s | %s |" % (f["id"], f["severity"], f["locator"], f["label"],
                                                             f["title_en"], f["title_vi"], action))
    if len(out) == 2:
        out.append("| — | — | — | No finding in this area. | Không có phát hiện. | — |")
    return "\n".join(out)


CH = [
    ("3. Application fit / Phù hợp ứng dụng", ["application_fit"],
     "FACT §1.1: the IP is the UIT Tesla boot and code-storage path: XIP through AHB-Lite, program/erase and bulk reads in indirect mode by CPU or DMA, and status polling for program/erase completion, for one serial NOR flash or serial PSRAM. INFERENCE: the NOR-flash use is well served by the mode set; the PSRAM claim is not, and the XIP use depends on an AXI bridge that is not specified (F-007, chapter 18). Score 3.",
     "FACT §1.1: IP là đường boot và lưu code của UIT Tesla: XIP qua AHB-Lite, program/erase và đọc khối ở indirect mode bằng CPU hoặc DMA, và status polling để chờ program/erase, cho một serial NOR flash hoặc serial PSRAM. INFERENCE: use case NOR flash được phục vụ tốt; claim PSRAM thì không, và XIP phụ thuộc vào một AXI bridge chưa được đặc tả (F-007, chương 18). Điểm 3."),
    ("4. Features / Tính năng", ["features"],
     "FACT §2 lists 16 features and §3 lists 10 exclusions with decision IDs; the exclusion list is better than most student IPs. INFERENCE: two advertised features are not usable as specified, DDR (F-001, chapter 9) and PSRAM (F-008, chapter 3); no feature carries a FEAT/REQ ID (F-010). Score 3; the findings are recorded in their owning chapters.",
     "FACT §2 liệt kê 16 tính năng và §3 liệt kê 10 loại trừ kèm decision ID; danh sách loại trừ rõ ràng. INFERENCE: hai tính năng được quảng bá không dùng được như đặc tả, DDR (F-001, chương 9) và PSRAM (F-008, chương 3); không tính năng nào có FEAT/REQ ID (F-010). Điểm 3; các phát hiện được ghi ở chương sở hữu."),
    ("5. Functions and cycle behaviour / Chức năng và hành vi theo chu kỳ", ["functions"],
     "FACT §6.5-§6.8 give an FSM table, an output table and RTL-simulated waveforms for the Command Sequencer, Clock Manager, Shifter and Polling Status Control; frame triggers (Table 6-8), error conditions (Table 6-10) and abort are specified to the cycle. This is the strongest part of the document. INFERENCE: the PRESCALER legality rules were not updated with the V2.0 formula (F-004).",
     "FACT §6.5-§6.8 có bảng FSM, bảng output và waveform mô phỏng RTL cho Command Sequencer, Clock Manager, Shifter và Polling Status Control; trigger frame (Table 6-8), lỗi (Table 6-10) và abort được đặc tả tới từng chu kỳ. Đây là phần mạnh nhất. INFERENCE: quy tắc hợp lệ PRESCALER chưa cập nhật theo công thức V2.0 (F-004)."),
    ("6. Interfaces and protocol / Giao diện và giao thức", ["interfaces"],
     "FACT §7 gives every port with direction, width, domain and reset value. Compliance (standard, revision, topic; clause numbers not read are not cited, R-005):\n\n| Requirement | Standard | Specification statement | Verdict |\n|---|---|---|---|\n| APB3 signal set, no PSTRB/PPROT | Arm IHI 0024E, signal list | §1.2 | compliant (APB3 profile) |\n| Wait states through PREADY | Arm IHI 0024E, transfers with wait states | §7.2 | compliant |\n| PSLVERR on unmapped offset | Arm IHI 0024E, error response | §7.2, Table 6-10 | compliant |\n| HREADY input qualifies the address phase | Arm IHI 0033C, HREADY | §1.2 'no HREADY input' | deviation, F-006 |\n| IDLE/BUSY get zero-wait OKAY | Arm IHI 0033C, transfer types | §6.4.3 | compliant |\n| Two-cycle ERROR response | Arm IHI 0033C, response signaling | §7.3 | compliant |\n| HSIZE/HBURST/HPROT ignored | Arm IHI 0033C | §1.2 | deviation recorded; HBURST loss costs XIP (F-005) |\n| SPI mode 0/3, tCSS/tCSH/tCS | de facto SPI NOR (no standard) | §6.6 | compliant |\n| DDR input setup/hold at the flash | de facto SPI NOR DTR timing | §7.6 | deviation, F-001 |\n| SFDP discovery (JEDEC JESD216) | JESD216 | not stated | not stated (software owns it, §3) |\n\nThe skill catalog names APB IHI 0024 Issue D; the specification cites Issue E. Both are current Arm issues and the APB3 subset is unchanged by the newer issue for these signals (INFERENCE).",
     "FACT §7 có đủ port với hướng, độ rộng, domain và giá trị reset. Bảng compliance ở trên (tiêu chuẩn, revision, chủ đề; không trích số clause chưa đọc). INFERENCE: lệch quan trọng nhất là thiếu HREADY input ở AHB-Lite (F-006) và timing DDR ở pad (F-001); DMA req/clr là handshake tùy biến (F-022)."),
    ("7. Clock, reset and CDC / Clock, reset và CDC", ["clock_reset_cdc"],
     "FACT §6.1: four mutually asynchronous clocks; SCLK is a flop output, never a clock. FACT Table 6-2: eight crossings (CDC-001..007, CDC-010), each with a dedicated module: Gray async FIFOs, 2-flop level syncs, toggle pulse syncs with acknowledge. FACT §6.2: resets asserted asynchronously and released synchronously by the CRM (ASM-014), no internal reset synchronizer (DEC-022). INFERENCE: the structure is sound and well documented; the weak points are a quasi-static multi-bit crossing that relies on software (F-012) and the absence of an RDC table (F-013).",
     "FACT §6.1: bốn clock bất đồng bộ; SCLK là output của flop, không là clock. FACT Table 6-2: tám crossing, mỗi crossing có module riêng: Gray async FIFO, 2-flop sync, toggle pulse sync có acknowledge. FACT §6.2: reset do CRM assert bất đồng bộ và release đồng bộ (ASM-014). INFERENCE: cấu trúc tốt; điểm yếu là crossing đa bit quasi-static dựa vào phần mềm (F-012) và thiếu bảng RDC (F-013)."),
    ("8. Parameters and data / Tham số và biểu diễn dữ liệu", ["parameters", "data_representation"],
     "FACT Table 5-1: 14 parameters with value set, default and description; §5 lists the $error elaboration checks; Table 10-1 CFG-ILLEGAL tests them. FACT §6.3 defines bit order per lane mode, byte order of address/alternate bytes, DR byte order, partial-word zero padding and AHB little-endian packing, with truth tables 6-5/6-6/6-7. INFERENCE: data representation is complete (score 4, no finding); parameter naming is the only remark (F-023).",
     "FACT Table 5-1: 14 tham số có tập giá trị, default và mô tả; §5 nêu các kiểm tra $error khi elaboration. FACT §6.3 định nghĩa thứ tự bit, byte, zero padding và little-endian của AHB với truth table. INFERENCE: biểu diễn dữ liệu đầy đủ (điểm 4, không có phát hiện); chỉ có nhận xét về đặt tên tham số (F-023)."),
    ("9. ASIC feasibility / Khả thi ASIC", ["asic_feasibility"],
     "Synthesizability: FACT §11.1 standard cells only, no macros, no clock gating, no internal tri-states; flop FIFOs. Clock/reset: see chapter 7. CDC/RDC: see chapter 7. Timing path: FACT §7.6 all pad outputs come from flops; FACT §6.7.3 output and capture registers add one clk of latency each way. INFERENCE: the 200 MHz core logic (8-way 32-bit tag compare, 33-bit range adder, 33-bit byte counter) is ordinary for any node of 65 nm or newer, but the target technology is not stated, so a mapped timing claim cannot be made. The pad interface is the real risk: DDR output data changes at the sampling edges (F-001, Blocker) and read capture has only a half SCLK period (F-002).",
     "Synthesizability: FACT §11.1 chỉ dùng standard cell, không macro, không clock gating. Timing path: FACT §7.6 mọi output pad ra từ flop. INFERENCE: logic core 200 MHz là bình thường cho node 65 nm trở xuống, nhưng spec không nêu công nghệ nên không khẳng định được timing đã map. Rủi ro thật nằm ở pad: dữ liệu DDR đổi đúng tại cạnh lấy mẫu (F-001, Blocker) và capture khi đọc chỉ có nửa chu kỳ SCLK (F-002)."),
    ("10. SDC and timing / SDC và timing", ["sdc_timing"],
     "FACT Table 11-2 defines four 200 MHz clocks and SCLK as a divide-by-2 generated clock on the pad; Table 11-3 lists EXC-001..004 with rationale; reset paths are timed. FACT §11.2 states the file holds synthesis, not signoff, constraints. INFERENCE: the structure is honest, but the 40 % placeholders and the unconstrained DDR falling edge make the pad timing look closed when it is not (F-003); the CDC exceptions need tool and skew precision (F-014). The SDC file itself (sdc/m_uit_qspi_wrap.sdc) is not in the reviewed folder.",
     "FACT Table 11-2 định nghĩa bốn clock 200 MHz và SCLK là generated clock chia 2 tại pad; Table 11-3 có EXC-001..004 kèm lý do. INFERENCE: placeholder 40 % và cạnh xuống DDR không constrain làm timing pad có vẻ đạt dù thực tế không (F-003); exception CDC cần rõ tool và skew (F-014). File SDC không có trong thư mục được review."),
    ("11. Area and power / Diện tích và công suất", ["area_power"],
     "Proxy only (R-008), default parameters, no library, not mapped:\n\n| Block | Flops (proxy) | Assumption |\n|---|---:|---|\n| TX + RX FIFO | 2048 | 2 x 32 x 32 bit, flop storage (§6.10) |\n| AHB cache | 520 | 8 x (32 data + 32 tag + 1 valid) |\n| AHB control + data async FIFOs | 552 | 8 x 36 + 8 x 33 |\n| APB request + response async FIFOs | 328 | 4 x 49 + 4 x 33 |\n| Register file | 350 | 17 registers, reserved bits removed |\n| Frame latch (CCR, AR, ABR, DLR) | 130 | Command Sequencer |\n| Shifter | 200 | TX/RX shift, RX immediate, phase settings |\n| Counters | 210 | byte 33, polling timeout 32, interval 16, AHB timeout 21, CSN 3 x 8, others |\n| Synchronizers | 80 | pointer, level and toggle syncs |\n| **Total** | **about 4.4k** | about 30-40 kGE at 6 GE per flop plus muxes |\n\nPower: no figure, no activity assumption, no clock gating (F-019).",
     "Chỉ là proxy (R-008), tham số mặc định, chưa map thư viện. Tổng khoảng 4.4k flop, khoảng 30-40 kGE; TX/RX FIFO chiếm khoảng 46 %. Công suất: không có số liệu, không có clock gating (F-019)."),
    ("12. Performance and throughput / Hiệu năng và thông lượng", ["performance"],
     "| Metric | Value | Basis |\n|---|---|---|\n| Max SCLK, SDR | F/2 = 100 MHz | FACT Table 6-1, §6.6.2 |\n| Max SCLK, DDR | F/4 = 50 MHz | FACT §6.6.2 |\n| Legal SCLK at 200 MHz, SDR | 100, 50, 25, 16.7, 12.5 MHz ... | FACT Table 6-14 rule; F-004 |\n| Legal SCLK at 200 MHz, DDR | 50, 16.7, 10 MHz ... | FACT Table 6-14 rule; F-004 |\n| Peak flash bandwidth | 1 to 8 bits per SCLK; quad SDR at 50 MHz = 25 MB/s | FACT §6.3 |\n| Read SCLK closable without sample delay | about F/8 = 25 MHz | INFERENCE, F-002 |\n| XIP NONSEQ miss latency | about 130 clk = 650 ns per 4 bytes | INFERENCE, F-005 |\n| XIP hit latency | unquantified | flagged (R-009) |\n| APB access latency | unquantified (one PCLK cycle + two async FIFO crossings + register operation) | flagged, §7.2 |\n| AHB timeout | 2^20 HCLK = 5.24 ms at 200 MHz / 10.49 ms at 100 MHz | FACT Table 11-4; F-009 |\n\nUnquantified claims: §1.1 'reduces the read latency'; §6.9 cache benefit.",
     "Bảng trên nêu tốc độ SCLK, băng thông và latency. INFERENCE: nếu không có sample delay thì đọc chỉ chắc chắn ở khoảng 25 MHz (F-002); một miss NONSEQ ở XIP tốn khoảng 650 ns cho 4 byte và cache chỉ là stream buffer 32 byte (F-005). Latency hit và latency APB chưa được định lượng."),
    ("13. Software and application ease / Dễ lập trình và ứng dụng", ["software_ease"],
     "FACT §8: 17 registers with field tables and access types; §9 gives init, interrupt, DMA, indirect, polling, memory-mapped and abort flows; Table 6-10 maps every error to a flag and a recovery. INFERENCE: the programming model is workable and close to STM32 QUADSPI, which eases driver design but not driver reuse (F-024). Driver friction: silent locked writes (F-017) and the CPU DMA residue (F-018).",
     "FACT §8: 17 thanh ghi có bảng field và kiểu truy cập; §9 có các flow init, interrupt, DMA, indirect, polling, memory-mapped, abort; Table 6-10 ánh xạ lỗi sang flag và cách khôi phục. INFERENCE: mô hình lập trình dùng được, gần STM32 QUADSPI nhưng driver không tái sử dụng được (F-024). Điểm phiền: ghi bị khóa bị bỏ âm thầm (F-017) và phần dư DMA do CPU làm (F-018)."),
    ("14. DFT / DFT", ["dft"],
     "FACT DEC-021: no DFT ports; Table 11-4: all flops scan-eligible, scan inserted by the SoC flow; §11.1: no macros, so no MBIST. INFERENCE: acceptable for this IP class, provided the test-mode contract is written (F-020).",
     "FACT DEC-021: không có port DFT; mọi flop scan được, scan chèn ở flow SoC; không macro nên không cần MBIST. INFERENCE: chấp nhận được nếu viết rõ DFT contract (F-020)."),
    ("15. Security and RAS / An toàn và độ tin cậy", ["security_ras"],
     "FACT §3: no ECC/parity, no PPROT/HPROT filtering, no APB timeout (DEC-020); FACT §6.4.6: no error is fatal; AHB timeout prevents an XIP hang. INFERENCE: the stance is explicit; the two residual risks are accepted as waivers with owner and invalidation condition (F-015, F-016).",
     "FACT §3: không ECC/parity, không lọc PPROT/HPROT, không APB timeout (DEC-020); AHB timeout tránh treo XIP. INFERENCE: lập trường rõ ràng; hai rủi ro còn lại được waive có owner và điều kiện mất hiệu lực (F-015, F-016)."),
    ("16. Verification quality / Chất lượng kiểm chứng", ["verification_quality"],
     "FACT §10: environment (APB/AHB agents, DMA model, flash model, randomized clock ratios), 17 corner-case groups, about 20 key assertions and five configurations (Table 10-1). FACT inventory.json: 0 requirement IDs, 0 test IDs; sim/ and lint/ are empty. INFERENCE: a good plan seed with no traceability and no evidence (F-011).",
     "FACT §10: môi trường, 17 nhóm corner case, khoảng 20 assertion chính và năm cấu hình. FACT inventory.json: 0 requirement ID, 0 test ID; sim/ và lint/ trống. INFERENCE: nền tảng test plan tốt nhưng không có truy vết và không có bằng chứng (F-011)."),
    ("17. Documentation and traceability / Tài liệu và truy vết", ["documentation"],
     "FACT: 47 sections, 64 tables, 23 figures with a table of tables and figures; revision history records every change. INFERENCE: structure and writing are clear; the defects are contradictions and undefined identifiers (F-009, F-010). Smaller items: title 'Reversion' (Revision); legacy REF-002 figures that the notes say are outdated (Figure 6-4, Figure 6-23).",
     "FACT: 47 mục, 64 bảng, 23 hình có mục lục. INFERENCE: cấu trúc rõ; lỗi là mâu thuẫn và ID không được định nghĩa (F-009, F-010). Mục nhỏ: tiêu đề 'Reversion' (Revision); hình REF-002 cũ đã lỗi thời (Figure 6-4, Figure 6-23)."),
    ("18. Integration effort and bring-up / Công sức tích hợp và bring-up", ["integration_effort"],
     "FACT Table 11-4 lists ten integrator duties: HSEL gating, base addresses, AHB timeout, resets, clock stop, pads with IO2/IO3 pull-ups, interrupt, DMA, XIP bridge and DFT. INFERENCE: bring-up needs the AXI bridge (F-007), custom HSEL gating (F-006) and a real flash timing budget (F-003); with those, the effort is moderate.",
     "FACT Table 11-4 liệt kê mười nhiệm vụ của integrator. INFERENCE: bring-up cần AXI bridge (F-007), logic gate HSEL tùy biến (F-006) và budget timing flash thực (F-003); có những thứ đó thì công sức tích hợp ở mức vừa phải."),
    ("19. Market position / Vị thế thị trường", ["market_position"],
     "Source order (R-004): web search done on 2026-11-18; datasheets behind NDA (Cadence) not obtained.\n\n| Expectation | UIT QSPI (spec) | Commercial reference | Source, date | Verdict |\n|---|---|---|---|---|\n| Read sample shift / delay | none (§3) | STM32 QUADSPI SSHIFT shifts sampling by half a CLK cycle | ST STM32L4x6 RM, delayed data sampling (manualslib copy p.408), accessed 2026-11-18 | missing |\n| DDR output hold delay | none (§7.6) | STM32 DHQC delays DDR output by a quarter cycle; ST FAQ: enable DHQC in DTR | ST community FAQ for QUADSPI/OCTOSPI/HSPI/XSPI; STM32G4 HAL header, accessed 2026-11-18 | missing |\n| Programmable RX sample delay | none | DesignWare SSI RX_SAMPLE_DLY, one ssi_clk per step, optional by configuration | Intel Agilex5 HPS SPIM RX_SAMPLE_DLY register page; rp2040-pac XIP_SSI docs, accessed 2026-11-18 | missing |\n| Delay-line read calibration | none | xSPI soft PHY with RX DLL to shift sampling; Arasan xSPI PHY DLL in 625 ps steps | ADI EE-468; arasan.com xSPI PHY page, accessed 2026-11-18 | missing (not expected at this class) |\n| XIP | AHB-Lite, 8-word buffer | Cadence xSPI: XIP, PHY-less or combo PHY | cadence.com xSPI product page, accessed 2026-11-18 | matched (weaker cache, F-005) |\n| Register model | STM32-like offsets | STM32 QUADSPI CR/DCR/SR/FCR/DLR/CCR/AR/ABR/DR/PSMKR/PSMAR/PIR | INFERENCE (no external source): reviewer knowledge of the STM32 RM layout | matched in offsets, differs in bits (F-024) |\n| Flash tCLQV used for F-002 | — | 6 ns (Intel EPCQ-A), 7 ns (T25Q16BW, 2.7-3.6 V) | intel.com EPCQ-A read operation timing; jiepei T25Q16BW datasheet p.69, accessed 2026-11-18 | input to F-002 |",
     "Đã tìm web ngày 2026-11-18. INFERENCE: so với STM32 QUADSPI, DesignWare SSI và Cadence xSPI, IP thiếu đúng các tính năng timing ở pad (sample shift, DDR hold delay, sample delay) mà sản phẩm thương mại dùng để đạt tần số cao; cache XIP yếu hơn. Offset thanh ghi giống STM32 nhưng bit khác (F-024)."),
]

SOURCES = """Sources (accessed 2026-11-18):
- ST STM32L4x6 reference manual, QUADSPI delayed data sampling: https://www.manualslib.com/manual/1317428/St-Stm32l4x6.html?page=408
- ST community, Overall FAQs for QUADSPI/OCTOSPI/HSPI/XSPI: https://community.st.com/stm32-mcus-60/overall-faqs-for-quadspi-octospi-hspi-xspi-132640
- STM32G4 HAL QSPI header: https://codex.ac6.fr/Zephyr/xref/hal_stm32-3.5.0/stm32cube/stm32g4xx/drivers/include/stm32g4xx_hal_qspi.h
- Intel Agilex5 HPS SPIM RX_SAMPLE_DLY: https://www.intel.com/content/www/us/en/programmable/hps/agilex5/topics/register_SPIM_1_RX_SAMPLE_DLY.html
- rp2040-pac XIP_SSI: https://docs.rs/rp2040-pac/0.6.0/rp2040_pac/struct.XIP_SSI.html
- Cadence xSPI: https://www.cadence.com/en_US/home/tools/silicon-solutions/design-ip/memory-interface-and-storage-ip/storage-ip/xspi.html
- ADI EE-468 xSPI PHY: https://www.analog.com/media/en/technical-documentation/application-notes/ee-468.pdf
- Arasan xSPI PHY: https://www.arasan.com/?p=7830
- Intel EPCQ-A read operation timing: https://www.intel.com/content/www/us/en/docs/programmable/683818/current/read-operation-timing.html
- T25Q16BW datasheet: https://pdf.jiepei.com/t25q16bwept-34476627.html?page=69"""

SEV = {"Blocker": "Critical", "Major": "High", "Minor": "Medium", "Observation": "Low"}


def review_md():
    top = sorted(F, key=lambda f: ["Blocker", "Major", "Minor", "Observation"].index(f["severity"]))[:8]
    L = ["# Specification review — UIT QSPI / Đánh giá đặc tả — UIT QSPI", "",
         "| Field / Trường | Value / Giá trị |", "|---|---|",
         "| IP | m_uit_qspi_wrap (UIT QSPI controller) |",
         "| Specification reviewed | %s |" % SPEC_PATH,
         "| Revision and date | HDS V2.0, 11/11/2026 (title page still says V1.0) |",
         "| Reviewer | Claude (vlsit-ip-spec-review skill) |",
         "| Review date | %s |" % DATE,
         "| Verdict / Kết luận | Conditional (weighted 2.98 / 5; 1 Blocker) |", "",
         "## 1. Executive summary / Tóm tắt điều hành", "",
         "**EN.** FACT: the UIT QSPI controller is the UIT Tesla boot, XIP and flash-programming path, with APB3 control, a read-only AHB-Lite XIP port, DMA, status polling and SDR/DDR single/dual/quad framing (§1.1, §2). The functional specification is detailed and of good quality: every block has an FSM table, an output table and simulated waveforms, every crossing has an ID and a synchronizer, and the register map and software flows are complete. INFERENCE: the weak point is the flash pad timing. DDR output data changes on the sampling edges (F-001, Blocker), read capture has a fixed half-period window with no sample delay (F-002), and the SDC placeholders hide both (F-003). The XIP cache works as a single stream buffer (F-005), the AHB port lacks HREADY (F-006), and the UIT Tesla AXI bridge is not specified (F-007). Verdict: **Conditional**, weighted score 2.98. The three actions that matter most: fix the DDR launch and add a read sample delay; write the pad budget from a real flash datasheet; add requirement/test traceability and define the cited DEC/ASM/REF items.",
         "",
         "**VI.** FACT: UIT QSPI controller là đường boot, XIP và lập trình flash của UIT Tesla, có APB3, cổng XIP AHB-Lite chỉ đọc, DMA, status polling và frame SDR/DDR single/dual/quad (§1.1, §2). Phần đặc tả chức năng chi tiết và chất lượng tốt. INFERENCE: điểm yếu là timing pad flash: dữ liệu DDR đổi đúng tại cạnh lấy mẫu (F-001, Blocker), capture khi đọc chỉ có cửa sổ nửa chu kỳ, không có sample delay (F-002), và SDC placeholder che cả hai (F-003). Cache XIP chỉ là stream buffer (F-005), cổng AHB thiếu HREADY (F-006), AXI bridge của UIT Tesla chưa đặc tả (F-007). Kết luận: **Conditional**, điểm 2.98. Ba việc quan trọng nhất: sửa launch DDR và thêm sample delay; viết budget pad từ datasheet flash thật; thêm truy vết requirement/test và định nghĩa các mục DEC/ASM/REF.",
         "", "### 1.1 Top findings / Phát hiện quan trọng nhất", "",
         "| Rank | Severity | Area | Finding (EN) | Phát hiện (VI) | Locator |", "|---|---|---|---|---|---|"]
    for i, f in enumerate(top, 1):
        L.append("| %d (%s) | %s | %s | %s | %s | %s |" % (i, f["id"].replace("F-", "#"), f["severity"], f["area"], f["title_en"], f["title_vi"], f["locator"]))
    L += ["", "## 2. Scorecard / Bảng điểm", "", "**EN.** Scores 0-5 per area, weights and verdict computed by vlsit_scorecard.py from scorecard.json.", "", "**VI.** Điểm 0-5 theo từng area, trọng số và kết luận do vlsit_scorecard.py tính từ scorecard.json.", "", SCORE_MD, "",
          "The lowest score is ASIC feasibility (1) because of the DDR Blocker F-001. Performance and verification quality (2) follow: read capture and the XIP cache limit real throughput, and no requirement is traced to a test. / Điểm thấp nhất là ASIC feasibility (1) do Blocker F-001; tiếp theo là performance và verification quality (2).", ""]
    for title, areas, en, vi in CH:
        L += ["## " + title, "", "**EN.** " + en, "", "**VI.** " + vi, "", "**Findings**", "", rows(areas), ""]
    L += ["## 20. Actions / Hành động", "",
          "**EN.** Priorities follow severity and root cause (grouped.json).", "",
          "**VI.** Thứ tự ưu tiên theo severity và root cause.", "",
          "| Priority | Action | Owner | Evidence |", "|---|---|---|---|",
          "| P0 | DDR launch at half-period midpoint; read sample delay; PRESCALER rules | RTL | F-001, F-002, F-004 |",
          "| P0 | Pad budget from a named flash datasheet; DDR falling-edge constraints | SDC / spec | F-003 |",
          "| P1 | HREADY input; aligned block fills and multi-block XIP cache; AXI bridge section | RTL / SoC | F-005, F-006, F-007 |",
          "| P1 | Remove or complete PSRAM support | spec / RTL | F-008 |",
          "| P1 | One clock plan; REF/DEC/ASM/DEP tables; REQ/TEST IDs and coverage | spec / DV | F-009, F-010, F-011 |",
          "| P2 | Area/power table; CDC-005 handshake; RDC table; SDC portability; DFT table; locked-write flag; DMA residue | RTL / spec | F-012..F-014, F-017..F-020 |", "",
          "## 21. Evidence appendix / Phụ lục bằng chứng", "",
          "**EN.** Inputs, gate results, audit and limits of this review.", "",
          "**VI.** Đầu vào, kết quả gate, audit và giới hạn của review.", "",
          "Folder inventory (R-001), rtl/qspi:", "",
          "| Item | Content |", "|---|---|",
          "| doc/UIT_QSPI_Specification.md | 1541 lines, sha256 %s |" % SHA,
          "| doc/images/figure_01..26.png | 26 figures (23 referenced in the table of figures) |",
          "| lint/, logical/, sim/, syn/ | .gitkeep only: no RTL, lint, simulation or synthesis evidence |",
          "| sdc/m_uit_qspi_wrap.sdc, QSPI_Register_Description.pdf (REF-008), UIT-Tesla-QSPI-SPEC v0.2 | cited, not present |", "",
          "Extracted by vlsit_spec_inventory.py (inventory.json): 47 sections, 64 tables, 0 requirement IDs, 0 test IDs, 18 DEC, 14 open items (ASM-002/003/004/005/007/010/011/012/013/014/015, DEP-001/009/011). Age: not stated per item; earliest possible origin V1.0 (10/20/2026), so at most 29 days.", "",
          "Gate (vlsit_review_gate.py metrics): `RESULT: %s, %d finding(s)`; %s; waiver usage %s; sampling %.0f %%; closure %.0f %%." % (
              GATE["status"], GATE["findings"], "; ".join(GATE["reasons"]) or "no reason", GATE["waiver_usage"], GATE["sampling"] * 100, GATE["closure_rate"] * 100),
          "The gate fails by design on the open Blocker F-001: a specification review cannot fix RTL, and waiving it would hide the main result.", "",
          "Deep sample (R-022): 24 findings in %d root-cause groups; no group has more than 10 findings, so all 24 were traced and none aggregated." % GROUPS["count"], "",
          "Audit sample (R-021, vlsit_review_gate.py sample, 10 %%, self-audit because no second reviewer was available):", "",
          "| Finding | Severity | Result | Re-check |", "|---|---|---|---|"]
    for s in AUDIT["sample"]:
        r, note = AUDIT_RESULT[s["id"]]
        L.append("| audit of %s | %s | %s | %s |" % (s["id"], s["severity"], r, note))
    L += ["", "False-positive rate 0/3, false-negative rate 0/3 on the sample.", "",
          "Not assessed and why:", "",
          "- RTL, lint, CDC/RDC tool reports and synthesis: folders are empty; an implementation review (vlsit-ip-impl-review) is needed once RTL is present.",
          "- The SDC file and REF-008 register PDF: cited but absent.",
          "- Figures were not inspected image by image; their captions and notes were used.",
          "- Mapped area and power: no library (R-008).",
          "- Commercial datasheets behind NDA (Cadence, Synopsys databook) were not obtained.", "", SOURCES, ""]
    return "\n".join(L)


def dated_md():
    n = {k: sum(1 for f in F if SEV[f["severity"]] == k) for k in ("Critical", "High", "Medium", "Low")}
    waive = sum(1 for f in F if f["verdict"] == "waive")
    fix = sum(1 for f in F if f["verdict"] == "fix")
    L = ["# Specification review of m_uit_qspi_wrap - %s" % DATE, "",
         "## 1. Summary", "",
         "| Item | Value |", "|---|---|",
         "| Design | `m_uit_qspi_wrap` (%s) |" % SPEC_PATH,
         "| Review | Specification review |", "| Date | %s |" % DATE,
         "| Findings | %d |" % len(F), "| Critical | %d |" % n["Critical"], "| High | %d |" % n["High"],
         "| Medium | %d |" % n["Medium"], "| Low | %d |" % n["Low"],
         "| Waivable | %d |" % waive, "| Fixable | %d |" % fix,
         "| Verdict | Conditional, weighted 2.98 / 5 (scorecard.md) |",
         "| Gate | `RESULT: %s` (%s); waivers %s |" % (GATE["status"], "; ".join(GATE["reasons"]), GATE["waiver_usage"]),
         "| Audit | 3 of 24 sampled, FP 0/3, FN 0/3 (self-audit) |",
         "| Deep sample | 24 traced, 0 aggregated, 14 root-cause groups |", "",
         "Severity scale: Critical = Blocker, High = Major, Medium = Minor, Low = Observation. The full bilingual analysis is in REVIEW_UIT_QSPI.md.", "",
         "## 2. Findings", "",
         "Each finding has an assessment, a verdict and, when it can be fixed, the change and the reason it works.", ""]
    for f in F:
        L += ["### %s %s" % (f["id"], f["title_en"]), "",
              "- Severity: `%s` (%s), area `%s`, root cause %s" % (SEV[f["severity"]], f["severity"], f["area"], f["root_cause"]),
              "- Evidence: %s" % f["locator"],
              "- Assessment: %s" % f["assessment"],
              "- Verdict: `%s` (%s)" % (f["verdict"], f["gate_verdict"])]
        if f["verdict"] == "fix":
            L.append("- Fix: %s" % f["fix"])
        L.append("- Why: %s" % f["why"])
        if f["verdict"] == "waive":
            L += ["- Risk: %s" % f["risk"], "- Owner: %s" % f["owner"], "- Invalidation: %s" % f["invalidation"]]
        if f.get("snippet"):
            lang = "tcl" if f["gate_verdict"] == "fix SDC" else "systemverilog"
            L += ["", "```" + lang, f["snippet"], "```"]
        L.append("")
    L += ["## 3. Actions", "", "| Action | Owner | Blocks sign-off |", "|---|---|---|",
          "| DDR launch at the half-period midpoint, DDR PRESCALER rule (F-001, F-004) | RTL | yes |",
          "| Read sample delay field (F-002) | RTL | yes for reads above about 25 MHz |",
          "| Pad budget from a named flash and DDR falling-edge constraints (F-003) | SDC | yes |",
          "| HREADY input (F-006), aligned block XIP fills (F-005), AXI bridge spec (F-007) | RTL / SoC | yes for XIP |",
          "| PSRAM claim (F-008), clock plan (F-009), REF/DEC/ASM/DEP tables (F-010), traceability (F-011) | spec / DV | yes |",
          "| F-012 to F-014, F-017 to F-020, F-024 | RTL / spec | no |", "",
          "## 4. Limits", "",
          "- No RTL, lint, simulation, CDC/RDC or synthesis evidence exists in rtl/qspi (empty folders); every RTL fix and snippet is a proposal written from the specification, not checked against code.",
          "- The SDC file and REF-008 are cited but absent.",
          "- Area is a proxy (about 4.4k flops); no library.",
          "- The audit is a self-audit; no second reviewer was available.", ""]
    return "\n".join(L)


(HERE / "REVIEW_UIT_QSPI.md").write_text(review_md(), encoding="utf-8")
(HERE / ("vlsit_spec_%s.md" % DATE)).write_text(dated_md(), encoding="utf-8")
print("written")
