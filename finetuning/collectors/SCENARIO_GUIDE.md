# Aegis Data Collection — Scenario Guide

## Setup

```bash
pip install playwright pillow
playwright install chromium
python collect.py
```

**Keys during collection:**
| Key | Action |
|-----|--------|
| `S` | Capture current state |
| `B` | Capture as BEFORE action |
| `A` | Capture as AFTER action |
| `F` | Mark last capture as FAIL (prompts for expected vs actual) |
| `G` | Mark last capture as GOAL ACHIEVED (prompts for evidence) |
| `X` | Mark last capture as FLOW BLOCKED |
| `N` | New workflow (same scenario, fresh counter) |
| `Q` | Quit and save |

**Golden rule for step descriptions:**
Write the step description as if you are reading what the executor should do or verify — not what you just clicked. Be specific about text values, field names, row context.

---

## The Row-Context Problem

When a table has multiple identical buttons (Edit, Delete), the DOM alone cannot disambiguate. You MUST include the row-identifying text in your step description and the DOM extractor will capture `row_context`.

```
❌ "Click the delete button"
✅ "Click the delete button in the row containing 'Cierra Veness'"
✅ "Click edit for the row where First Name is 'Alden' and Last Name is 'Cantrell'"
```

The `row_context` field in the DOM JSON will contain the full row text, allowing the model to construct a scoped selector like:
```css
tr:has(td:contains('Cierra Veness')) button.delete-btn
```

---

## S01 — Single Click: Checkbox
**URL:** https://the-internet.herokuapp.com/checkboxes  
**Target:** 30 records

**What to do:**
1. Press `B` → *"Verify checkbox 1 is visible and currently unchecked"*
2. Click checkbox 1
3. Press `A` → *"Click checkbox 1 to check it"*
4. Press `B` → *"Verify checkbox 1 is now checked"*
5. Click checkbox 1 again
6. Press `A` → *"Click checkbox 1 to uncheck it"*
7. Press `B` → *"Verify checkbox 1 is unchecked again"*
8. Press `N`, repeat for checkbox 2, then both together
9. **FAIL case:** Describe *"Verify checkbox 1 is checked"* when it's unchecked → press `F`

---

## S02 — Single Click: Add/Remove Button
**URL:** https://the-internet.herokuapp.com/add_remove_elements  
**Target:** 30 records

**What to do:**
1. Press `B` → *"Verify Add Element button visible, no Delete buttons yet"*
2. Click Add Element
3. Press `A` → *"Click Add Element button"*
4. Press `B` → *"Verify one Delete button appeared"*
5. Click Add Element again
6. Press `B` → *"Verify two Delete buttons now visible"*
7. Click first Delete
8. Press `A` → *"Click first Delete button"*
9. Press `B` → *"Verify one Delete button remains"*
10. Press `N`, add 3 elements then delete them in reverse order

---

## S03 — Single Type: Number Input
**URL:** https://the-internet.herokuapp.com/inputs  
**Target:** 20 records

**What to do (per value):**
1. Press `B` → *"Verify number input field is empty"*
2. Click field, type value
3. Press `A` → *"Type [VALUE] into number input"*
4. Press `B` → *"Verify number field contains [VALUE]"*

**Use these values (one workflow per value):** 0, 1, 5, 42, 99, 100, 999, -1, 0.5, 10000

---

## S04 — Single Scroll
**URL:** https://the-internet.herokuapp.com/infinite_scroll  
**Target:** 20 records

**What to do:**
1. Press `B` → *"Verify first paragraph visible at top of page"*
2. Scroll down (mousewheel ×3)
3. Press `A` → *"Scroll down 300px to load more content"*
4. Press `B` → *"Verify new paragraph content appeared after scroll"*
5. Repeat 5 scrolls per workflow, press `N` and start fresh

---

## S05 — Single Hover
**URL:** https://the-internet.herokuapp.com/hovers  
**Target:** 20 records

**What to do:**
1. Press `B` → *"Verify profile image 1 visible, no caption shown"*
2. Hover over image 1
3. Press `A` → *"Hover over image 1 to reveal caption"*
4. Press `B` → *"Verify caption 'name: user1' and View Profile link visible under image 1"*
5. Move mouse away, repeat for images 2 and 3

---

## S06 — Dropdown Native
**URL:** https://the-internet.herokuapp.com/dropdown  
**Target:** 30 records

**What to do:**
1. Press `B` → *"Verify dropdown shows 'Please select an option'"*
2. Open dropdown, select Option 1
3. Press `A` → *"Select 'Option 1' from dropdown"*
4. Press `B` → *"Verify dropdown now shows 'Option 1' as selected value"*
5. Select Option 2
6. Press `A` → *"Select 'Option 2' from dropdown"*
7. Press `B` → *"Verify dropdown now shows 'Option 2'"*

**FAIL case:** Select Option 1, then describe *"Verify Option 2 is selected"* → `F`
**Each option change = 1 workflow (press N between)**

---

## S07 — Custom Dropdown (React)
**URL:** https://demoqa.com/select-menu  
**Target:** 30 records

**What to do:**
1. Press `B` → *"Verify 'Select Value' custom dropdown shows placeholder text"*
2. Click the dropdown
3. Press `A` → *"Click Select Value dropdown to open options list"*
4. Press `B` → *"Verify dropdown options list is open and visible"*
5. Click an option
6. Press `A` → *"Click 'A root option' from the dropdown list"*
7. Press `B` → *"Verify 'A root option' is now shown in the Select Value field"*

**Do all dropdowns on page:** Select Value, Select One, Old Style, Multiselect

---

## S08 — Sequential Form: 3 Fields
**URL:** https://demoqa.com/text-box  
**Target:** 50 records

**CRITICAL — capture every sub-step:**

For **each** of the 4 fields (Full Name, Email, Current Address, Permanent Address):
1. Press `B` → *"Verify [FIELD NAME] is empty and visible"*
2. Click field, type value  
3. Press `A` → *"Click [FIELD NAME] and type '[VALUE]'"*
4. Press `B` → *"Verify [FIELD NAME] contains '[VALUE]'"*

Then:
5. Press `B` → *"Verify all fields filled, Submit button visible"*
6. Click Submit
7. Press `A` → *"Click Submit button"*
8. Press `B` → *"Verify output box shows the submitted values"*
9. Press `G` → evidence: *"Output section shows Name: [name], Email: [email]"*

**Use DIFFERENT data each workflow — never repeat:**
- wf01: Alice Smith, alice@test.com, 123 Main St, 456 Oak Ave
- wf02: Bob Jones, bob@qa.io, 789 Pine Rd, 321 Elm St
- wf03: Carol White, carol@demo.org, 555 Maple Ln, 777 Cedar Dr
- wf04: David Park, david@sample.com, 100 First Ave, 200 Second Blvd

---

## S09 — Sequential Form: 5 Fields
**URL:** https://demoqa.com/automation-practice-form  
**Target:** 60 records

**Same B→A→B pattern for 5 text fields only:**
Fields: First Name, Last Name, Email, Mobile (10 digits), Current Address

Do NOT submit — stop after 5 fields verified.

**Data variety:**
- Mix names: John/Jane/Alex/Sam/Priya/Carlos + Smith/Lee/Park/Wong/Patel/Garcia
- Mix email domains: gmail.com, yahoo.com, outlook.com, hotmail.com, test.io
- Mobiles: 10 random digits each workflow

Press `N` after each complete 5-field workflow. Do 6+ workflows.

---

## S10 — Full Form All Types
**URL:** https://demoqa.com/automation-practice-form  
**Target:** 80 records

**Cover ALL field types in one workflow:**

| Field Type | Capture Pattern |
|-----------|-----------------|
| Text input | B → type → A → B(verify value) |
| Radio button | B → click radio → A → B(verify selected) |
| Checkbox | B → click → A → B(verify checked icon) |
| Date picker | B → click field → A(calendar open) → B → click date → A → B(verify date string) |
| Subjects (autocomplete) | B → type partial → A(suggestions appear) → B → click suggestion → A → B(verify tag added) |
| State dropdown | B → click → A(opens) → B → click State → A → B(verify) |
| City dropdown | B → click → A → B → click City → A → B |

**End each workflow:**
- Scroll to Submit button (B before, A after scroll)
- Click Submit (A)
- Press B → *"Verify success modal appeared"*
- Press `G` → evidence: *"Modal shows 'Thanks for submitting the form' with entered data"*

Do 4 complete workflows with fully different data.

---

## S11 — Form Validation Errors
**URL:** https://demoqa.com/automation-practice-form  
**Target:** 60 records

**Sequence 1 — Empty submit:**
1. Press `B` → *"Verify form is empty with no validation errors"*
2. Scroll to Submit, click it
3. Press `A` → *"Click Submit on completely empty form"*
4. Press `B` → *"Verify red borders appeared on all required fields"*
5. Take individual captures for each red field → `S` → *"Verify First Name field has red border indicating required"*

**Sequence 2 — Invalid email:**
1. Fill First Name only
2. Type "notanemail" in Email field
3. Click Submit
4. Press `A` → *"Submit form with invalid email format"*
5. Press `B` → *"Verify email field shows red border, error state"*

**Sequence 3 — Tab-triggered validation:**
1. Click Email field, type "bad"
2. Press Tab (triggers blur validation)
3. Press `B` → *"Verify email field turned red after tabbing away from invalid value"*

**Also use:** https://parabank.parasoft.com/parabank/transfer.htm
- Submit transfer with empty amount → capture error state

---

## S12 — Character Limit Enforcement
**URL:** https://demoqa.com/text-box  
**Target:** 50 records

**Prepare text strings in advance (run in Python):**
```python
print("A" * 50)
print("B" * 99)
print("C" * 100)
print("D" * 101)
print("E" * 200)
```

**Sequence per length:**
1. Press `B` → *"Verify Current Address textarea is empty"*
2. Paste/type N chars
3. Press `A` → *"Paste [N] characters into Current Address textarea"*
4. Press `B` → *"Verify textarea contains [N] characters"*

**FAIL case:**
After typing 99 chars: `B` → *"Verify textarea contains 100 characters"* → `F`
→ fail reason: *"Expected 100 characters but field only contains 99"*

Do: 50, 99, 100, 101, 200, 499, 500, 501 chars across workflows

---

## S13 — Exact Character Fill
**URL:** https://demoqa.com/text-box  
**Target:** 40 records

**Prepare:**
```python
print("X" * 100)   # copy to clipboard for 100-char test
print("Y" * 500)   # copy for 500-char test  
print("Z" * 3000)  # copy for 3000-char test
```

**Per size:**
1. Press `B` → *"Verify textarea empty, ready for exact [N] char fill"*
2. Click, Ctrl+A to select all, paste prepared string
3. Press `A` → *"Paste exactly [N] characters into textarea"*
4. Press `B` → *"Verify character count is exactly [N]"*
5. Press `G` → evidence: *"Field contains exactly [N] characters confirmed"*

Do 3 workflows per size (100, 500, 3000) = 9 workflows

---

## S14 — Modal Dialogs
**URL:** https://demoqa.com/modal-dialogs  
**Target:** 40 records

**Small modal (repeat 5×):**
1. `B` → *"Verify page has no open modal, Small Modal button visible"*
2. Click Small Modal  
3. `A` → *"Click Small Modal button"*
4. `B` → *"Verify small modal is open with title 'Small Modal' and content text"*
5. `B` → *"Verify modal Close button is visible and enabled"*
6. Click Close  
7. `A` → *"Click Close button in the small modal"*
8. `B` → *"Verify modal is closed and page content is accessible again"*

**Large modal:** Same pattern, 5× 

**FAIL case:** Open modal, describe *"Verify modal title is 'Large Modal'"* when Small Modal is open → `F`

**Cancel via X:** Open modal → click X top-right (not Close button) → `A` → `B`

---

## S15 — JavaScript Alerts
**URL:** https://the-internet.herokuapp.com/javascript_alerts  
**Target:** 40 records

**JS Alert (no choice):**
1. `B` → *"Verify JS Alert trigger button visible"*
2. Click JS Alert button  
3. `A` → *"Click button to trigger JavaScript alert"*
4. Accept alert (press OK in browser dialog)  
5. `A` → *"Accept the alert dialog"*
6. `B` → *"Verify result text shows 'You successfully clicked an alert'"*

**JS Confirm — OK:**
Same but click Confirm → result: "You clicked: Ok"

**JS Confirm — Cancel:**
Click Cancel → result: "You clicked: Cancel" 
→ This is a negative/cancel path — still `B` at end

**JS Prompt:**
Enter "Test input" → `B` → *"Verify result shows 'You entered: Test input'"*

---

## S16 — Table Row Edit (ROW CONTEXT CRITICAL)
**URL:** https://demoqa.com/webtables  
**Target:** 50 records

> **This is where you train the model to use row context. Always include the row-identifying text in your step description.**

**Sequence (editing Cierra Veness, Salary → 80000):**
1. `B` → *"Verify table shows 3 rows including 'Cierra Veness' in row 1"*
2. `S` → *"Identify edit button in the row containing 'Cierra Veness, Veness, cierra@hotmail.com'"*
3. Click the pencil icon on Cierra's row ONLY  
4. `A` → *"Click edit button for the row containing 'Cierra Veness'"*
5. `B` → *"Verify edit registration form appeared pre-filled with Cierra's data"*
6. Clear Salary, type 80000  
7. `A` → *"Clear Salary field and type 80000"*
8. `B` → *"Verify Salary field shows 80000"*
9. Click Save  
10. `A` → *"Click Save in the edit form"*
11. `B` → *"Verify Cierra Veness row now shows Salary as 80000"*
12. `G` → evidence: *"Table row for Cierra Veness shows updated salary 80000"*

**Also edit:** Alden Cantrell, Kierra Gentry — different fields each time
Press `N` between each

---

## S17 — Table Row Delete (ROW CONTEXT CRITICAL)
**URL:** https://demoqa.com/webtables  
**Target:** 50 records

**Sequence (deleting Alden Cantrell):**
1. `B` → *"Verify table has 3 rows, 'Alden Cantrell' visible in row 2"*
2. `S` → *"Identify delete button (red X) in the row containing 'Alden Cantrell'"*
3. Click delete icon on Alden's row ONLY  
4. `A` → *"Click delete button for row containing 'Alden Cantrell'"*
5. `B` → *"Verify 'Alden Cantrell' is no longer in the table"*
6. `G` → evidence: *"Table no longer contains row with text 'Alden Cantrell'"*

**FAIL case:** 
After deletion: `B` → *"Verify 'Alden Cantrell' is still visible in the table"* → `F`
→ fail reason: *"Expected to find Alden Cantrell in table but row was deleted"*

Add rows first (use S18 pattern), then delete specific ones.

---

## S18 — Table Row Add
**URL:** https://demoqa.com/webtables  
**Target:** 30 records

**Sequence:**
1. `B` → *"Verify Add button visible, table has N rows"*
2. Click Add  
3. `A` → *"Click Add button to open registration form"*
4. `B` → *"Verify registration form modal is visible with empty fields"*
5. Fill each field with B→A→B pattern (First Name, Last Name, Age, Email, Salary, Department)
6. Click Submit  
7. `A` → *"Click Submit to save new row"*
8. `B` → *"Verify new row with [First Name] [Last Name] appears in table"*
9. `G` → evidence: *"New row '[Name]' visible in table at bottom"*

**Data:** Use "Test User / QA", "Demo Person / Dev", "Sample Entry / HR"

---

## S19 — Auth Login Valid
**URL:** https://the-internet.herokuapp.com/login  
**Credentials:** tomsmith / SuperSecretPassword!  
**Target:** 40 records

**Full sequence (do 4 complete workflows):**
1. `B` → *"Verify login form visible with username and password fields"*
2. Click username → `A` → *"Click username field"*
3. Type tomsmith → `A` → *"Type 'tomsmith' into username field"*
4. `B` → *"Verify username field contains 'tomsmith'"*
5. Click password → `A` → *"Click password field"*
6. Type password → `A` → *"Type password (not verified — password field)"*
7. Click Login → `A` → *"Click Login button to submit credentials"*
8. `B` → *"Verify page redirected to /secure URL"*
9. `B` → *"Verify green success flash message visible: 'You logged into a secure area!'"*
10. `G` → evidence: *"Secure area page loaded. Flash banner visible in green. URL is /secure. Logout button visible."*

---

## S20 — Auth Login Invalid
**URL:** https://the-internet.herokuapp.com/login  
**Target:** 30 records

**Variants to capture (3 workflows each):**
- Wrong password: tomsmith + wrongpassword999
- Wrong username: wronguser + SuperSecretPassword!
- Both wrong: baduser + badpass
- Empty username: (blank) + SuperSecretPassword!
- Empty password: tomsmith + (blank)

**Sequence (wrong password example):**
1. `B` → *"Verify login form is visible"*
2. Fill username: tomsmith  
3. `A` → *"Type 'tomsmith' into username"*
4. `B` → *"Verify username shows tomsmith"*
5. Fill wrong password  
6. `A` → *"Type incorrect password"*
7. Click Login  
8. `A` → *"Click Login with invalid credentials"*
9. `B` → *"Verify error flash message: 'Your password is invalid!'"*
10. `B` → *"Verify URL still shows /login (no redirect occurred)"*
11. `F` on last → expected: */secure page loaded*, actual: *error message shown on /login*

---

## S21 — Auth Logout
**URL:** Start at https://the-internet.herokuapp.com/login  
**Target:** 20 records

Login first (full S19 sequence), then:
1. `B` → *"Verify user is on /secure page, logged in as tomsmith"*
2. Click Logout → `A` → *"Click Logout button"*
3. `B` → *"Verify redirected to /login page"*
4. `B` → *"Verify flash message 'You logged out of the secure area!' visible"*
5. `G` → evidence: *"Login page showing. Logout success flash message visible. URL is /login."*

---

## S22 — Wait For Element (Dynamic Loading 1)
**URL:** https://the-internet.herokuapp.com/dynamic_loading/1  
**Target:** 40 records

The element is HIDDEN then shown after loading.

1. `B` → *"Verify Start button visible, 'Hello World' text not visible"*
2. Click Start → `A` → *"Click Start to begin loading"*
3. `B` → *"Verify loading progress bar/indicator is visible"*
4. Wait 5 seconds (do nothing)  
5. `B` → *"Verify loading completed, 'Hello World' text is now visible"*
6. `G` → evidence: *"Hello World text appeared. Loading bar is gone."*

Capture the MID-LOAD state (loading bar visible) — this teaches `wait_for_element` pattern.
Do 6 workflows to get various load-state captures.

---

## S23 — Wait For Element (Dynamic Loading 2)
**URL:** https://the-internet.herokuapp.com/dynamic_loading/2  
**Target:** 30 records

Same as S22 but element is RENDERED (not just unhidden).

1. `B` → *"Verify Start button visible, no 'Hello World' element in DOM at all"*
2. Click Start → `A` → *"Click Start to trigger element render"*
3. `B` → *"Verify loading indicator is showing, element not yet rendered"*
4. Wait for completion  
5. `B` → *"Verify 'Hello World' element rendered and visible on page"*
6. `G` → evidence: *"Hello World element rendered and visible after loading completed"*

---

## S24 — Color Verification: Buttons
**URL:** https://demoqa.com/buttons then https://www.saucedemo.com  
**Target:** 40 records

> **Color verification records must have DOM = [] (empty). Leave DOM collection as-is — the DOM extractor returns empty for these.**

**DemoQA buttons:**
1. `B` → *"Verify Double Click Me button has default styling (grey/default color)"*
2. `S` → *"Verify button color is default before any interaction"*
3. Double-click the button  
4. `A` → *"Double-click the Double Click Me button"*
5. `B` → *"Verify success message appeared: 'You have done a double click'"*

**SauceDemo (after login standard_user/secret_sauce):**
1. `B` → *"Verify Add to Cart button visible in orange color on product card"*
2. `S` → *"Verify Add to Cart button background color (orange)"*
3. Click Add to Cart  
4. `A` → *"Click Add to Cart for Sauce Labs Backpack"*
5. `B` → *"Verify button changed to 'Remove' — color changed from orange to different shade"*

**FAIL cases:** Describe wrong color → `F`
*"Verify button is green"* when it's actually orange → fail reason: *"Expected green but button is orange"*

---

## S25 — Color Verification: Alert States
**URL:** https://demoqa.com/alerts  
**Target:** 30 records

1. `B` → *"Verify alert trigger buttons visible, no alerts open"*
2. Click a button to trigger an alert  
3. `A` → *"Click button to trigger alert"*
4. `B` → *"Verify browser alert dialog is showing"*
5. Accept/dismiss  
6. `A` → *"Accept the alert"*
7. `B` → *"Verify result/output updated on page"*

**Also capture:** https://getbootstrap.com/docs/5.0/components/alerts/
- Success alert (green)
- Warning alert (yellow)
- Danger alert (red)
- Info alert (blue)
- Each: `S` → *"Verify success alert has green background color"*

---

## S26 — Scroll To Element (Below Fold)
**URL:** https://demoqa.com/automation-practice-form  
**Target:** 40 records

The Submit button is below the fold on this long form.

1. `B` → *"Verify form top visible, Submit button NOT in viewport"*
2. Scroll slowly until Submit is visible  
3. `A` → *"Scroll down to bring Submit button into viewport"*
4. `B` → *"Verify Submit button is now visible in viewport"*

**FAIL case:** Describe *"Click Submit button"* before scrolling, when button is not in viewport  
→ `F` → fail reason: *"Submit button not in viewport, cannot click — must scroll first"*

Vary by scrolling in different amounts (100px, 300px, large jump)

---

## S27 — FAIL → raise_bug_ticket
**URL:** Various  
**Target:** 60 records

Capture 15 different failure scenarios across sites:

| # | Scenario | Site | Fail Reason |
|---|----------|------|-------------|
| 1 | Submit empty form | demoqa/practice-form | Expected success modal, got red errors |
| 2 | Wrong text in field | demoqa/text-box | Expected "Jane" in name, field shows "John" |
| 3 | Delete button missing | demoqa/webtables | Expected delete button for "Unknown Row", row not found |
| 4 | Wrong URL after nav | any | Expected /dashboard in URL, got /text-box |
| 5 | Login fails | herokuapp/login | Expected /secure, stayed on /login with error |
| 6 | Modal not closing | demoqa/modal-dialogs | Modal still visible after clicking Close |
| 7 | Wrong dropdown value | herokuapp/dropdown | Expected "Option 2", dropdown shows "Option 1" |
| 8 | Row still in table after delete | demoqa/webtables | Expected row removed, row still visible |
| 9 | Wrong checkbox state | herokuapp/checkboxes | Expected checked, checkbox is unchecked |
| 10 | Success toast absent | any | Expected success message, nothing appeared |
| 11 | Alert text wrong | herokuapp/alerts | Expected "correctly", got different message |
| 12 | Element disabled | saucedemo | Expected Checkout enabled, button is disabled (empty cart) |
| 13 | Color wrong | saucedemo/demoqa | Expected green button, button is orange |
| 14 | Count wrong | saucedemo products | Expected 6 products, page shows 4 |
| 15 | Form field not verified | demoqa/text-box | Expected 500 chars, field has 499 |

For each: `B` to capture the fail state → press `F` → describe expected vs actual

---

## S28 — FLOW BLOCKED
**URL:** Various  
**Target:** 40 records

Capture states where the ENTIRE FLOW cannot continue.

| # | Scenario | How to trigger |
|---|----------|---------------|
| 1 | Login failed 3 times | Enter wrong credentials 3× on herokuapp/login |
| 2 | Required element missing | Navigate to page missing expected form |
| 3 | Page error / 404 | Navigate to a non-existent URL |
| 4 | Empty cart → can't checkout | SauceDemo: go to cart with nothing in it, try Checkout |
| 5 | Modal blocking page | Open modal, then try to describe clicking something behind it |
| 6 | Form submission failed repeatedly | Submit invalid data twice in a row |
| 7 | Network error (offline) | DevTools → Network → Offline, try to submit |
| 8 | Session expired | Clear cookies mid-session, try protected action |

For each: `B` → capture the blocked state → press `X` → describe why flow can't continue

---

## S29 — GOAL ACHIEVED With Visual Proof
**URL:** End of any completed flow  
**Target:** 60 records

> **Press G ONLY when ALL success criteria are visually confirmed on screen.**

After each completed scenario above, press `G` with detailed evidence:

| Flow completed | What to describe in evidence |
|---------------|------------------------------|
| Login | "Secure area page. Flash 'You logged into a secure area!' visible. URL=/secure. Logout button present." |
| Form submit | "Success modal visible: 'Thanks for submitting the form'. Data values shown in modal." |
| Row added | "New row '[Name]' appears in table. Row shows all entered field values correctly." |
| Row deleted | "Table no longer contains row with '[Name]'. Row count decreased by 1." |
| Row edited | "Row for '[Name]' now shows updated value '[New Value]' in the '[Field]' column." |
| Modal dismissed | "Modal is closed. Page content is fully accessible. No overlay visible." |
| Alert handled | "Result text updated to '[expected message]' confirming alert was handled." |
| Dropdown selected | "Dropdown shows '[Selected Value]' as current selection." |
| Checkbox checked | "Checkbox appears checked (filled square/checkmark visible)." |
| Form validated | "No red borders visible. All fields show green/valid state." |

Collect **6 G captures per flow type** across your workflows.

---

## S30 — verify_* Tools Standalone
**URL:** https://www.saucedemo.com (login first)  
**Target:** 80 records

Login: standard_user / secret_sauce

Capture each verify tool type at least 8 times (PASS + FAIL states):

| Tool | Capture scenario |
|------|-----------------|
| `verify_text_present` | After login: `B` → *"Verify text 'Products' is present on the page"* |
| `verify_text_absent` | After login: `B` → *"Verify text 'Invalid credentials' is absent from page"* |
| `verify_element_visible` | Products page: `B` → *"Verify 'Add to Cart' button visible for first product"* |
| `verify_element_enabled` | Empty cart: `B` → *"Verify Checkout button is present"* |
| `verify_url_contains` | After login: `B` → *"Verify URL contains '/inventory'"* |
| `verify_input_value` | Checkout form, fill First Name: `B` → *"Verify First Name field contains 'John'"* |
| `get_text` | Product card: `B` → *"Read product name text from first product card"* |
| `verify_element_count` | Products page: `B` → *"Verify 6 product cards are visible on the page"* |

**FAIL versions:** Describe wrong expected → `F`
- "Verify 10 products visible" when 6 are shown → F
- "Verify text 'Welcome back' present" when text doesn't exist → F
- "Verify URL contains /cart" when on /inventory → F

---

## Progress Tracking

After each session, run:
```bash
python build_records.py --all
```

This prints how many records you have per scenario and which need human review (contain FILL_IN placeholders).

Records marked `needs_review: true` still need you to edit the assistant response in the output JSONL to replace placeholders with real descriptions. The action JSON is auto-inferred but always double-check it matches what you actually did.

---

## Tips

1. **Prepare test data before you open the browser** — have your name/email/address strings ready in a text file so you can copy-paste quickly.

2. **Always press B before and A after** for clean paired records. Standalone S captures are useful for verification steps but paired B+A records are higher quality.

3. **Be specific in step descriptions** — include exact text values, field names, and for tables always include the row-identifying text.

4. **Don't rush** — 5 good captures per session > 30 rushed ones. Quality > quantity for this dataset.

5. **Vary sites for same scenario** — e.g., do sequential form fills on demoqa/text-box, parabank, AND saucedemo checkout for variety. The model must generalize across sites.
