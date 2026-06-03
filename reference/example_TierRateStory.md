> **Provenance:** Extracted from `example_TierRateStory.pdf` (a 3-page GoFullPage screen
> capture of a Jira issue), preserving the original ticket's structure and context. Sections
> that exist only as images in the source (JSON snippets, contract documents, amortization
> tables, mobile & WebCSR screenshots) are kept by heading/caption and described faithfully,
> with any legibly readable detail transcribed.

---

`< Back`  ·  **DGL-9820**  ·  **DGL-10081**

# [BAU] Enhance Tire Rate Jai Pump

## Description

*As a* business unit

*I want* to เสนออัตราดอกเบี้ยแบบ tier rate สำหรับสินเชื่อ **"กรุงไทยใจป๋า"** ให้กับลูกค้าที่มีรายได้เกินกว่าที่ระบบ risk engine กำหนดไว้ (30,000 บาท)

*So that* อัตราดอกเบี้ยที่นำเสนอจะสอดคล้องอยู่กับฐานเงินเดือนที่มีในระบบ และสามารถแข่งขันได้ในตลาดสำหรับกลุ่มลูกค้าวงกว้างขึ้น

## Product

กรุงไทยใจป๋า new loan

## Background

1. เพิ่ม offer Tier rate ตามฐานเงินเดือนมากกว่า 30,000 บาท

## Business Logic

1. บริษัทใช้ว่า ให้รองรับ tier-rate ได้
   a. requirement รองรับ 2 tier
   b. ระบบรองรับแบบให้รองรับได้อย่างน้อย 5 tier
2. บริษัทมีความ "รายละเอียดผลิตภัณฑ์" หน้า Product Highlight ตามข้อมูลที่ได้จาก Data Inno (Lead)
   a. **ข้อความภาษาไทย:**
      - บุคคลทั่วไปมีรายได้ปกติ วงเงินอนุมัติสูงสุด 5 เท่าของรายได้ต่อเดือน และไม่เกิน 1 ล้านบาท ดอกเบี้ย 20% ต่อปี
      - ผู้ประกอบการรับค้าขายต่อ วงเงินอนุมัติสูงสุด 5 เท่าของรายได้ต่อเดือน และไม่เกิน 0.5 ล้านบาท ดอกเบี้ย 22% ต่อปี
      - โปรโมชั่นดอกเบี้ยพิเศษ 9.99% ต่อปี 3 งวดแรก สำหรับบุคคลทั่วไปที่มีรายได้ประจำ ที่ยื่นใบคำขอตั้งแต่วันที่ 1 ก.ย. – 31 ธ.ค. 2568 และได้รับอนุมัติภายใน 15 ม.ค. 2569
   b. **ข้อความภาษาอังกฤษ:**
      - Salaried person : Credit limit up to 5 times of the income, max 1,000,000 Baht. The interest rate is 20% per year.
      - Self Employed : Credit limit up to 5 times of the income, max 500,000 Baht. The interest rate is 22% per year.
      - Special Interest Rate! 9.99% p.a. for the first 3 instalments. For Salaried person with a minimum income of THB 30,000/month. Loan applications must be submitted between Sep 1 – Dec 31, 2025 and approved by Jan 15, 2026.
3. ระบบ label "อัตราดอกเบี้ย" เป็น "อัตราดอกเบี้ยสูงสุดตามสัญญา" ที่หน้าจอการกรอกอัตรา ตาม mock up reference#4
4. บริษัทรับ response จาก CMLOS ที่ DGL รองรับทั้ง single tier rate และ multi-tier rate
   a. `/internal-following-dgl/api/api/smact-money/updateStatus`
   b. Note: CMLOS ส่ง income ให้ risk engine → risk engine จัดเป็น income และ income source ตามจริงจากการตรวจสอบ

### Income → Interest-rate tiers

| Income Source | KTB Payroll | Monthly Income | อัตราดอกเบี้ยต่อปี |
|---|---|---|---|
| SA | Yes | < 30,000 บาท | 20% |
| | Yes | >= 30,000 บาท (multi-tier rate) | • 1–3 เดือนแรก : 7.99%<br>• เดือนที่ 4 เป็นต้นไป : 20% |
| | No | < 50,000 บาท | 20% |
| | No | >= 50,000 บาท (multi-tier rate) | • 1–3 เดือนแรก : 9.99%<br>• เดือนที่ 4 เป็นต้นไป : 20% |
| SE | N/A | N/A | 22% |

> ⚠️ **หมายเหตุ** : เพื่อความ flexible อัตราดอกเบี้ยตามขอบเขตเงื่อนไขด้านบนที่ risk engine กำหนดส่งมาให้ เมื่อเงื่อนไขอัตราดอกเบี้ยมาเปลี่ยนจาก risk engine ขึ้นอยู่กับเงื่อนไขใหม่นี้
>
> - วันที่มีผลตั้งแต่เริ่มสัญญาวันที่ 1 ก.ย. – 31 ธ.ค. 2568 และได้รับอนุมัติภายใน 15 ม.ค. 2569
> - Income
> - Income source
> - KTB payroll

5. บริษัท contract (สัญญา) สินเชื่อกรุงไทยใจป๋า ให้แสดงอัตราดอกเบี้ยตามเงื่อนไขที่มีให้ใหม่ตามที่อ่านหนังสือ tier ได้ (refer to mock up reference#2: Contract สัญญา สินเชื่อกรุงไทยใจป๋า)
   a. กรณีที่มี 1 tier และคอนเฟิกแพทเดียว โดยใช้ layout เดียวกับในสกรีน tier
6. บริษัท Amortization table ให้สามารถแสดงรายการชำระตามแบบ single tier และ multi-tier rate ตาม response จาก CMLOS
   a. ดูตัวอย่างการคำนวณ amortization table ที่ `@Payment_DGL_V3_1.xlsx`
   b. บริษัท Header Table และ Amortize Table ให้รองรับการแสดง multi-tier rate (refer to mock up reference#3: Amortize เอกสารแนบท้ายสัญญาแนบ 1)
      i. กรณีที่มี 1 tier และคอนเฟิกแพทเดียว โดยใช้ layout เดียวกับในสกรีน tier
   c. แสดงรายละเอียดเดียวกันเรียกว่า 1 rate โดย cut-off ที่ due date ที่ถูกค้าเลือก ตัวอย่างเช่น
      i. ครบวันเริ่ม = 20 Jun 2025 และ เลือก due date = 25 Jun 2025
      ii. งวดที่ 1 : 20–25 Jun → int rate 9.99% จะคงเหลือเงิน 5 งวด
          งวดที่ 2 : 26 Jun – 25 Jul → int rate 9.99%
          งวดที่ 3 : 26 Jul – 25 Aug → int rate 9.99% **เดือนสุดท้ายที่ cut-off**
          งวดที่ 4 : เป็นต้นไป → int rate 20%
7. บริษัทการเรียก API CBS เพื่อให้รองรับการตั้ง multi-tier rate
   a. (As-Is) call CreateConsumerLoan → ส่ง tier-rate ที่ 1
   b. (As-Is) call UpdateLoanPayment
   c. เพิ่มการ call AddEffectiveDateHistory → ส่ง effective date และ tier-rate ที่ 2 เป็นต้นไป
      i. effective date คำนวณจาก due date ที่ถูกค้าเลือก + จำนวนเดือน tierStart และ tier ที่ 2 เป็นต้นไป
8. ระบบรองรับการคำนวณ amortization table และ effective date ที่ CreateConsumerLoan ในการคิดหนี้นี้
   a. amortization ล้านปี
   b. leap year

## Acceptance Criteria

1. ระบบรองรับการ offer สินเชื่อแบบ single tier กรณี income < 30,000 บาท
2. รองรับการ offer สินเชื่อแบบ multi-tier rate มากกว่า 1 ครั้ง เก็บใน 5 Tier rate

## Out of Scope

1. ไม่รวมการปรับ label "อัตราดอกเบี้ย" เป็น "อัตราดอกเบี้ยสูงสุดตามสัญญา" ที่หน้าจอการกรอกของของ NEXT (เป็น scope งานของ NEXT)
2. อัตราดอกเบี้ยที่ mobile หน้า accept contract ยังไม่แสดงเป็น tier-rate
3. ตัวอย่างการคำนวณสินเชื่อที่ "เอกสารแนบท้ายสัญญาบุญาญหมายเลขที่ 2" คำนวณได้ผลลัพธ์ ไม่แก้ไขด้วยอย่างเป็น tier-rate
4. DGL ยังไม่เปลี่ยนปุ่มไปกับ risk engine ในสินเชื่อใหม่ใช้น้ำ

---

## Mock-up references

### 1. Loan Decision CMLOS

**Loan Decision – CMLOS to DGL** — *Before / After* (JSON payload comparison)

- **Before:** the consumer-loan decision JSON without tier-rate fields.
- **After:** the same JSON extended with a tier-rate structure — a `tierInfo` /
  `tierList` array carrying per-tier fields such as `tierStartTier`, `interestIndex`,
  `interestSpread` / `interestRate`, and `paymentNo` (the multi-tier additions are
  highlighted in the source image).
- **Spec API:** `POST /api/smart-money/updateStatus v2025.11.24`

### 2. Contract สัญญา สินเชื่อกรุงไทยใจป๋า

Loan contract document — *AS-IS / TO BE* (Krungthai contract form images).

- **AS-IS:** single interest-rate line on the contract.
- **TO BE:** the rate section is replaced by a per-period tier breakdown (highlighted),
  e.g. งวดที่ `1–3` อัตราดอกเบี้ย 9.99 ต่อปี and งวดที่ `4–12` อัตราดอกเบี้ย 20.00 ต่อปี.

### 3. Amortize Table เอกสารแนบท้ายสัญญาแนบ 1

Amortization schedule attachment — *AS IS / TO BE*
(ตารางแสดงการผ่อนชำระเงินกู้ / เอกสารแนบท้ายสัญญาแนบ 1).

- **AS IS:** a single flat rate across all instalments.
- **TO BE:** a header block stating the multi-tier rate (งวดที่ `1–3` อัตราดอกเบี้ย 9.99 ต่อปี;
  งวดที่ `4–12` อัตราดอกเบี้ย 20.00 ต่อปี — highlighted) above the per-instalment rows.

### 4. Accept Contract – Status

บริษัท label "อัตราดอกเบี้ย" เป็น "อัตราดอกเบี้ยสูงสุดตามสัญญา" ที่หน้าจอการกรอกอัตรา —
กรณีที่นำว่าเอเงิน → คลิ๊กปุ่ม ใหม่

**Accept Contract – Status, Confirm info and accept contract completed** — mobile app
screenshots of the contract-acceptance flow (status, confirm info, accept-completed
screens; the อัตราดอกเบี้ย / วงเงินอนุมัติ fields are highlighted).

### 5. หน้า WebCSR เพื่อความสบาย Interest

**Profile Direct** WebCSR screenshots:

- **Rate Determination** tab — Interest Rates section (Interest Rate, Internal Disclosure
  Rate, Semi-Annual Disclosure Rate, APR), Fixed Rate Plans, and Adjustable Rate Plans
  (Interest Index, Interest Spread highlighted).
- **Future Changes** tab — Balances list of effective-dated rate changes (Action,
  Effective, Posted, By User, Nature of Change = "Changes made to multiple attributes").

---

## Attachments (21)

| Name | Size | Date added |
|---|---|---|
| Screenshot 2568-08-29 at 09.33.32.png | 34 KB | Aug 29, 2025 |
| messageImage_1755228043515.jpg | 285 KB | Aug 15, 2025 |
| messageImage_1755228227591.jpg | 360 KB | Aug 15, 2025 |
| payment_date_Tier_Rate-RESULT (7b09337-5e26-4631-a85a-d80c24b76fd8).xlsm | 2.2 MB | Aug 15, 2025 |
| image-20250707-074309 (47bc1dc2-c8c1-4977-81e3-0165ec4fe41c).png | 455 KB | Aug 14, 2025 |
| image-20250707-073919 (5e9eec89-0069-4d98-9984-2ad6b5632840).png | 693 KB | Aug 14, 2025 |

*(Attachment list paginated 1 2 3 4 → ; 21 attachments total, first page shown above.)*

## Subtasks

*Add subtask* — (none listed)

## Linked work items

*Add linked work item* — (none listed)

## Confluence content

- `POST /api/smart-money/updateStatus v2025.11.24` — *Updated*

---

## Activity

Tabs: **All · Comments · History · Work log · Smart Checklist History · Issue History · Approvals**

### Comments summary  🔒 *Only visible to you*

This work item involved implementing tiered interest rates for the **"กรุงไทยใจป๋า"** loan
product to enhance competitiveness for customers with income over 30,000 บาท, with ongoing
adjustments and approvals.

- The system was updated to support multi-tier interest rates, initially deploying support
  for up to 5 tiers, with the first deployment scheduled around late August 2025.

*(Comment composer: Add a comment… · Suggest a reply… · Status update… · Thanks…)*
