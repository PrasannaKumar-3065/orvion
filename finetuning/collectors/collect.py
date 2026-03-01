#!/usr/bin/env python3
"""
Aegis Executor Dataset Collector
=================================
Keyboard shortcuts (type in terminal while browser is open):

  S  — Capture current state (screenshot + DOM). You will be prompted for step description.
  B  — Capture as BEFORE_ACTION  (state before you do something)
  A  — Capture as AFTER_ACTION   (state right after you did something)
  F  — Mark LAST capture as FAIL state (prompts for expected vs actual)
  G  — Mark LAST capture as GOAL_ACHIEVED (prompts for visual evidence)
  X  — Mark LAST capture as FLOW_BLOCKED
  N  — Start NEW workflow (same scenario, fresh step counter)
  Q  — Quit and save summary

Saves to ./aegis_captures/<scenario_id>/
  step_0001_before.png
  step_0001_before.json
  step_0001_after.png
  step_0001_after.json
  ...
  workflow_wfXXX_summary.json

Usage:
  python collect.py
  → Choose scenario number
  → Browser opens at target URL
  → Perform actions, press keys to capture
"""

import asyncio
import json
import os
import sys
import time
import re
from pathlib import Path
from datetime import datetime

try:
    from playwright.async_api import async_playwright
    import playwright
except ImportError:
    print("playwright not found. Installing...")
    os.system(f"{sys.executable} -m pip install playwright --break-system-packages")
    os.system(f"{sys.executable} -m playwright install chromium")
    from playwright.async_api import async_playwright

# ── CONFIG ────────────────────────────────────────────────────────────────────
BASE_DIR        = Path("./aegis_captures")
VIEWPORT_W      = 1280
VIEWPORT_H      = 720
TRAIN_W         = 1120
TRAIN_H         = 630

# ── SCENARIOS ─────────────────────────────────────────────────────────────────
SCENARIOS = {
    # ── SINGLE STEP ───────────────────────────────────────────────────────────
    "S01": {
        "name": "Single click — checkbox",
        "url":  "https://the-internet.herokuapp.com/checkboxes",
        "target_records": 30,
        "family": "single_step",
        "instructions": """
WHAT TO CAPTURE:
  Each capture = 1 step (B before click, A after click)
  
SEQUENCE (repeat 15 times for variety):
  1. Press B  → describe: "Verify checkbox 1 is visible and unchecked"
  2. Click checkbox 1 in browser
  3. Press A  → describe: "Click checkbox 1 to check it"
  4. Press B  → describe: "Verify checkbox 1 is now checked"
  5. Click it again
  6. Press A  → describe: "Verify checkbox 1 is unchecked"
  7. Press N to start new workflow, repeat for checkbox 2

ALSO CAPTURE:
  - Both checkboxes state at once (S) → describe: "Verify both checkboxes visible"
  - A FAIL case: describe step as verify_checked but checkbox is actually unchecked → press F
"""
    },
    "S02": {
        "name": "Single click — add/remove button",
        "url":  "https://the-internet.herokuapp.com/add_remove_elements",
        "target_records": 30,
        "family": "single_step",
        "instructions": """
SEQUENCE (repeat 10 times):
  1. Press B  → "Verify Add Element button is visible"
  2. Click Add Element
  3. Press A  → "Click Add Element button"
  4. Press B  → "Verify a Delete button appeared"
  5. Click Delete
  6. Press A  → "Click Delete button, verify it disappears"
  
ALSO:
  - Add 3 elements, then capture S → "Verify 3 delete buttons are visible"
  - Try to click a Delete that doesn't exist → press F → fail reason: "Delete button not found"
"""
    },
    "S03": {
        "name": "Single type — number input",
        "url":  "https://the-internet.herokuapp.com/inputs",
        "target_records": 20,
        "family": "single_step",
        "instructions": """
SEQUENCE (repeat 10 times with different values):
  1. Press B  → "Verify number input field is visible and empty"
  2. Click field, type a number (e.g. 42)
  3. Press A  → "Type 42 into the number input field"
  4. Press B  → "Verify number field contains 42"
  5. Clear and type different value
  6. Press A  → "Type 99 into the number input field"

VALUES TO USE: 0, 1, 42, 100, 999, -1, 0.5, 9999
"""
    },
    "S04": {
        "name": "Single scroll down",
        "url":  "https://the-internet.herokuapp.com/infinite_scroll",
        "target_records": 20,
        "family": "single_step",
        "instructions": """
SEQUENCE:
  1. Press B  → "Verify initial paragraph content visible at page top"
  2. Scroll down 300px using mousewheel
  3. Press A  → "Scroll down 300px to load more content"
  4. Repeat 5 times per workflow
  5. Press N, scroll differently (fast scroll, slow scroll)
  
ALSO CAPTURE:
  - Scroll_to_top state → B before, A after pressing Home key
"""
    },
    "S05": {
        "name": "Single hover — reveal hidden content",
        "url":  "https://the-internet.herokuapp.com/hovers",
        "target_records": 20,
        "family": "single_step",
        "instructions": """
SEQUENCE (3 images, repeat each 3x):
  1. Press B  → "Verify profile image 1 shows no caption initially"
  2. Hover over image 1
  3. Press A  → "Hover over image 1 to reveal name and view profile link"
  4. Press B  → "Verify caption 'name: user1' is now visible under image 1"
  5. Move mouse away, hover image 2, repeat
"""
    },

    # ── DROPDOWNS ─────────────────────────────────────────────────────────────
    "S06": {
        "name": "Dropdown native select",
        "url":  "https://the-internet.herokuapp.com/dropdown",
        "target_records": 30,
        "family": "dropdown",
        "instructions": """
SEQUENCE (repeat 10 times with all options):
  1. Press B  → "Verify dropdown shows 'Please select an option'"
  2. Open dropdown, select Option 1
  3. Press A  → "Select 'Option 1' from dropdown"
  4. Press B  → "Verify dropdown now shows 'Option 1'"
  5. Select Option 2
  6. Press A  → "Select 'Option 2' from dropdown"
  7. Press B  → "Verify dropdown now shows 'Option 2'"

FAIL CASE:
  Select option 1, then Press B → "Verify Option 2 is selected" → press F
  → fail reason: "Expected Option 2 but Option 1 is selected"
"""
    },
    "S07": {
        "name": "Custom dropdown — DemoQA select menu",
        "url":  "https://demoqa.com/select-menu",
        "target_records": 30,
        "family": "dropdown",
        "instructions": """
PAGE HAS: Select Value, Select One, Old Style Select Menu, Multiselect, etc.

SEQUENCE for custom React dropdowns (repeat 8x):
  1. Press B  → "Verify Select Value dropdown shows placeholder"
  2. Click the Select Value dropdown
  3. Press A  → "Click Select Value dropdown to open options list"
  4. Press B  → "Verify dropdown options are visible: Group 1, Group 2"
  5. Click an option (e.g. "A root option")
  6. Press A  → "Select 'A root option' from Select Value dropdown"
  7. Press B  → "Verify 'A root option' is now shown in dropdown"

DO ALSO: Old Style Select (native), Multiselect dropdown, React Select
"""
    },

    # ── SEQUENTIAL FORM ───────────────────────────────────────────────────────
    "S08": {
        "name": "Sequential form — DemoQA text box (3 fields)",
        "url":  "https://demoqa.com/text-box",
        "target_records": 50,
        "family": "sequential_form",
        "instructions": """
FIELDS: Full Name, Email, Current Address, Permanent Address

CRITICAL PATTERN (capture every sub-step):
  For EACH field:
    1. Press B  → "Verify [field] is empty and visible"
    2. Click field, type value
    3. Press A  → "Click [field] and type '[value]'"
    4. Press B  → "Verify [field] contains '[value]'"

  Then:
    5. Press B  → "Verify all fields filled, Submit button visible"
    6. Click Submit
    7. Press A  → "Click Submit button"
    8. Press B  → "Verify output box shows submitted values"
    9. Press G  → evidence: "Output section shows Name: [name], Email: [email]"

USE VARIED DATA each workflow:
  Workflow 1: "Alice Smith", "alice@test.com", "123 Main St"
  Workflow 2: "Bob Jones", "bob@example.org", "456 Oak Ave"
  Workflow 3: "Carol White", "carol.w@qa.io", "789 Pine Rd"
  ... etc — NEVER repeat same data twice
  Press N between each workflow
"""
    },
    "S09": {
        "name": "Sequential form — DemoQA practice form (5 fields)",
        "url":  "https://demoqa.com/automation-practice-form",
        "target_records": 60,
        "family": "sequential_form",
        "instructions": """
FIELDS: First Name, Last Name, Email, Mobile, Address (5 text fields only first)

SAME PATTERN as S08 but 5 fields:
  B → A → B pattern for each field
  
DATA VARIETY (use different data each workflow):
  Names: mix of John/Jane/Alex/Sam + Smith/Lee/Park/Wong/Patel
  Emails: different domains — gmail.com, yahoo.com, outlook.com, test.io
  Mobiles: 10-digit numbers
  
CAPTURE THESE STATES:
  - Empty form (B at start)
  - After each field filled (A)
  - Verified field value (B after each fill)
  - All 5 filled (B before submit)
  
Do NOT submit in this scenario — stop after 5 fields verified
"""
    },

    # ── FULL FORM ─────────────────────────────────────────────────────────────
    "S10": {
        "name": "Full form all field types — DemoQA practice form",
        "url":  "https://demoqa.com/automation-practice-form",
        "target_records": 80,
        "family": "full_form",
        "instructions": """
FIELDS (all types):
  Text:    First Name, Last Name, Email, Mobile, Address
  Radio:   Gender (Male/Female/Other)
  Date:    Date of Birth (date picker)
  Tags:    Subjects (autocomplete multi-select)  
  Check:   Hobbies (Sports/Reading/Music)
  Upload:  Picture (SKIP — mark as HUMAN_STEP)
  Text:    Current Address
  Dropdown: State, City (dependent dropdowns)

PATTERN for each type:
  TEXT FIELD:  B → click+type → A → B(verify)
  RADIO:       B → click radio → A → B(verify selected)
  CHECKBOX:    B → click → A → B(verify checked)
  DATE PICKER: B → click field → A(calendar opens) → B → click date → A → B(verify date)
  DROPDOWN:    B → click → A(opens) → B → click option → A → B(verify)

CAPTURE the SUBMIT + SUCCESS MODAL:
  After all fields: B → click Submit → A → B(modal visible) → G

IMPORTANT: Each full form fill = 1 workflow (press N between attempts)
Do 4-5 complete workflows with different data
"""
    },

    # ── FORM VALIDATION ───────────────────────────────────────────────────────
    "S11": {
        "name": "Form validation errors — red borders and messages",
        "url":  "https://demoqa.com/automation-practice-form",
        "target_records": 60,
        "family": "form_validation",
        "instructions": """
GOAL: Capture error states — red borders, error messages

SEQUENCE 1: Submit completely empty form
  1. Press B  → "Verify form is empty, no errors visible"
  2. Scroll to Submit, click it
  3. Press A  → "Click Submit button with all fields empty"
  4. Press B  → "Verify red borders appear on all required fields"
  5. Capture each red field individually (S for each)

SEQUENCE 2: Submit with invalid email
  1. Fill First Name, Last Name, leave email empty
  2. Fill Mobile with only 3 digits (invalid — needs 10)
  3. Click Submit
  4. Press A  → "Submit form with invalid mobile number"
  5. Press B  → "Verify error state on Mobile field (red border)"

SEQUENCE 3: One field at a time errors
  1. Click Email field, type invalid format "notanemail"
  2. Press Tab (triggers validation)
  3. Press B  → "Verify email field shows red border after invalid input"

ALSO CAPTURE:
  - Parabank.parasoft.com/transfer.htm
  - Submit transfer with 0 amount → error
  - Submit with letters in amount field → error
"""
    },

    # ── CHARACTER LIMIT ───────────────────────────────────────────────────────
    "S12": {
        "name": "Character limit enforcement — boundary tests",
        "url":  "https://demoqa.com/text-box",
        "target_records": 50,
        "family": "char_limit",
        "instructions": """
USE: The Current Address textarea (no explicit limit shown — test browser default)
ALSO USE: https://www.htmlquick.com/reference/tags/textarea/maxlength.html for maxlength demos

SEQUENCE 1: Fill to perceived limit
  1. Press B  → "Verify textarea is empty"
  2. Type 100 characters
  3. Press A  → "Type 100 characters into textarea"
  4. Press B  → "Verify textarea contains 100 characters"
  5. Keep typing until you notice truncation or counter changes
  6. Press A at each notable state

SEQUENCE 2: Boundary test (use demoqa/text-box textarea)
  Type exactly these amounts and capture: 50, 99, 100, 101, 200, 499, 500, 501

SEQUENCE 3: FAIL case  
  Step says "verify field contains 500 chars" but it's actually 499
  Press F → expected: 500 chars, actual: 499 chars

NOTE: For real char-limit DOM evidence, use a page that shows maxlength attribute
"""
    },
    "S13": {
        "name": "Exact character fill (100, 500, 3000 chars)",
        "url":  "https://demoqa.com/text-box",
        "target_records": 40,
        "family": "char_exact",
        "instructions": """
SEQUENCE for each target size (100, 500, 3000):
  1. Press B  → "Verify textarea is empty, ready for exact fill"
  2. Paste exactly N chars (prepare strings in advance)
     python: print("A" * 100)  etc.
  3. Press A  → "Paste exactly [N] characters into Current Address field"
  4. Press B  → "Verify character count is exactly [N]"
  
  Prepare these strings in advance and have them in clipboard:
    100 chars:  print("X" * 100)   
    500 chars:  print("Y" * 500)
    3000 chars: print("Z" * 3000)

DO 3 WORKFLOWS PER SIZE = 9 workflows total
"""
    },

    # ── COLOR VERIFICATION ────────────────────────────────────────────────────
    "S24": {
        "name": "Color verification — DemoQA buttons",
        "url":  "https://demoqa.com/buttons",
        "target_records": 40,
        "family": "color",
        "instructions": """
PAGE HAS: Double Click Me, Right Click Me, Click Me buttons

SEQUENCE:
  1. Press B  → "Verify Click Me button is visible with default styling"
  2. Capture color state: S → "Verify Click Me button background color"
  3. Click the button (triggers success message)
  4. Press A  → "Click the Click Me button"
  5. Press B  → "Verify success message appears after click"

ALSO CAPTURE ON: https://www.saucedemo.com
  Login first (standard_user / secret_sauce)
  1. Press B  → "Verify Add to Cart button is visible in orange/green"
  2. Click Add to Cart on one product
  3. Press A  → "Click Add to Cart on Sauce Labs Backpack"
  4. Press B  → "Verify button changed to Remove (color changed)"
  
THESE ARE YOUR COLOR VERIFICATION RECORDS:
  - Default button color (capture DOM empty for color tasks)
  - Hover state color (different shade)
  - Success/active state color
  - Disabled state grey

FOR FAIL CASES:
  Describe step as "verify button is green" but button is actually orange → press F
"""
    },
    "S25": {
        "name": "Color verification — alert states",
        "url":  "https://demoqa.com/alerts",
        "target_records": 30,
        "family": "color",
        "instructions": """
PAGE HAS: Various alert trigger buttons

SEQUENCE:
  1. Press B  → "Verify page loaded, trigger buttons visible"
  2. Click 'Click me' to trigger simple alert
  3. Press A  → "Click button to trigger browser alert"
  4. Press B  → "Verify browser alert dialog is showing"
  5. Accept the alert
  6. Press A  → "Accept the alert dialog"

ALSO USE: https://demoqa.com/alerts page success/warning/info boxes
  These show Bootstrap alert colors:
  - Success: green background
  - Warning: yellow/orange  
  - Danger: red
  - Info: blue
  
CAPTURE EACH:
  Press B before visible → S to capture → note color in step description
  These ARE your color training records (DOM will be empty for color tasks)
"""
    },

    # ── MODALS ────────────────────────────────────────────────────────────────
    "S14": {
        "name": "Modal dialogs — DemoQA",
        "url":  "https://demoqa.com/modal-dialogs",
        "target_records": 40,
        "family": "modal",
        "instructions": """
PAGE HAS: Small Modal button, Large Modal button

SEQUENCE for Small Modal (repeat 5x):
  1. Press B  → "Verify Small Modal button is visible, no modal open"
  2. Click Small Modal button
  3. Press A  → "Click Small Modal button to open modal"
  4. Press B  → "Verify modal is now visible with title 'Small Modal'"
  5. Press B  → "Verify modal contains text content and Close button"
  6. Click Close
  7. Press A  → "Click Close button in modal"
  8. Press B  → "Verify modal is closed, page returned to normal"

SEQUENCE for Large Modal (repeat 5x): Same pattern

CANCEL case:
  Open modal → do NOT close immediately → S → "Verify modal blocks background content"
  Click X (top right) instead of Close → A → "Click X to dismiss modal"

FAIL case:
  Open modal, describe step as "verify modal title is 'Large Modal'" but it's Small
  → press F
"""
    },
    "S15": {
        "name": "JavaScript alerts — confirm and prompt",
        "url":  "https://the-internet.herokuapp.com/javascript_alerts",
        "target_records": 40,
        "family": "modal",
        "instructions": """
PAGE HAS: JS Alert, JS Confirm, JS Prompt buttons

SEQUENCE for JS Alert:
  1. Press B  → "Verify JS Alert button visible"
  2. Click JS Alert button
  3. Press A  → "Click JS Alert button (alert will appear)"
  4. Press B  → "Verify alert dialog is showing with message"
  5. Accept (click OK)
  6. Press A  → "Accept the alert"
  7. Press B  → "Verify result text shows 'You successfully clicked an alert'"

SEQUENCE for JS Confirm — OK:
  Same flow but choose OK → result: "You clicked: Ok"

SEQUENCE for JS Confirm — Cancel:
  Choose Cancel → result: "You clicked: Cancel"
  This is important — Cancel is a negative test path

SEQUENCE for JS Prompt:
  Click → type "Test input" in prompt → OK
  B → A → B at each step
"""
    },

    # ── TABLE ROW ACTIONS (THE DUPLICATE SELECTOR PROBLEM) ───────────────────
    "S16": {
        "name": "Table row edit — DemoQA web tables",
        "url":  "https://demoqa.com/webtables",
        "target_records": 50,
        "family": "table_crud",
        "instructions": """
PAGE HAS: Table with columns First Name, Last Name, Age, Email, Salary, Department + Actions

THIS IS THE KEY SCENARIO FOR TEACHING ROW-SCOPED SELECTORS.

THE DOM PROBLEM:
  Every row has an Edit button with the same selector.
  Model MUST use screenshot to identify WHICH row to edit.

SEQUENCE for editing "Cierra" (row 1):
  1. Press B  → "Verify table shows 3 employee records"
  2. Look at screenshot — row 1 has "Cierra Veness", row 2 has "Alden", etc.
  3. Press S  → "Identify row containing 'Cierra Veness' — edit button is in that row"
     (When writing step description: be EXPLICIT about row identification)
  4. Click the edit (pencil) icon on Cierra's row ONLY
  5. Press A  → "Click edit button for row containing 'Cierra Veness'"
  6. Press B  → "Verify edit form appeared pre-filled with Cierra's data"
  7. Change the Salary field to 80000
  8. Press A  → "Clear salary field and type 80000"
  9. Press B  → "Verify salary field shows 80000"
  10. Click Save
  11. Press A  → "Click Save button in edit form"
  12. Press B  → "Verify table row for Cierra now shows salary 80000"
  13. Press G  → evidence: "Table row shows updated salary 80000 for Cierra Veness"

CRITICAL: In your step descriptions, ALWAYS mention the row-identifying text:
  ❌ "Click the edit button"
  ✅ "Click the edit button in the row containing 'Cierra Veness'"
"""
    },
    "S17": {
        "name": "Table row delete — DemoQA web tables",
        "url":  "https://demoqa.com/webtables",
        "target_records": 50,
        "family": "table_crud",
        "instructions": """
SAME SITE as S16 — same duplicate selector problem for delete buttons.

SEQUENCE:
  1. Press B  → "Verify table has 3 records including 'Alden Cantrell'"
  2. Locate 'Alden Cantrell' row visually in screenshot
  3. Press S  → "Identify delete button for row with text 'Alden Cantrell'"
  4. Click the delete (red X) icon on ALDEN'S row specifically
  5. Press A  → "Click delete button for row containing 'Alden Cantrell'"
  6. Press B  → "Verify 'Alden Cantrell' row is no longer in the table"
  7. Press G  → evidence: "Table no longer contains 'Alden Cantrell'"

ALSO CAPTURE:
  - After delete: table shows only 2 rows
  - Add a row first (Add button), then delete the new one

FAIL case:
  Delete a row → B → describe: "Verify 'Alden Cantrell' still visible in table"
  → press F  (it was deleted, so verify_text_present would fail)
"""
    },
    "S18": {
        "name": "Table row add — DemoQA web tables",
        "url":  "https://demoqa.com/webtables",
        "target_records": 30,
        "family": "table_crud",
        "instructions": """
SEQUENCE (repeat 5x with different data):
  1. Press B  → "Verify Add button visible, table has N rows"
  2. Click Add button
  3. Press A  → "Click Add button to open registration form"
  4. Press B  → "Verify registration form is visible"
  5-14. Fill each field: First Name, Last Name, Email, Age, Salary, Department
        B → type → A → B(verify) for each field
  15. Click Submit
  16. Press A  → "Click Submit to add new row"
  17. Press B  → "Verify new row appears in table with entered data"
  18. Press G  → evidence: "New row with [name] visible in table"

DATA TO USE:
  Row 1: "Test User", "QA Team", "qa@test.com", 25, 60000, "Quality"
  Row 2: "Demo Person", "Dev", "dev@test.org", 30, 90000, "Engineering"
  Row 3: "Sample Entry", "HR", "hr@sample.io", 28, 55000, "Human Resources"
"""
    },

    # ── AUTH ─────────────────────────────────────────────────────────────────
    "S19": {
        "name": "Auth login valid — Herokuapp",
        "url":  "https://the-internet.herokuapp.com/login",
        "target_records": 40,
        "family": "auth",
        "instructions": """
CREDENTIALS: tomsmith / SuperSecretPassword!

FULL SEQUENCE:
  1. Press B  → "Verify login form visible with username and password fields"
  2. Click username field
  3. Press A  → "Click username field to focus it"
  4. Type tomsmith
  5. Press A  → "Type 'tomsmith' into username field"
  6. Press B  → "Verify username field contains 'tomsmith'"
  7. Click password field
  8. Press A  → "Click password field"
  9. Type password (won't verify value — password field)
  10. Press A  → "Type password into password field"
  11. Click Login button
  12. Press A  → "Click Login button to submit credentials"
  13. Press B  → "Verify page redirected to secure area"
  14. Press B  → "Verify success message 'You logged into a secure area!' visible"
  15. Press G  → evidence: "Secure area page loaded, success flash message visible"

Do 4 complete login workflows (press N between each)
"""
    },
    "S20": {
        "name": "Auth login invalid — wrong password",
        "url":  "https://the-internet.herokuapp.com/login",
        "target_records": 30,
        "family": "auth",
        "instructions": """
SAME SITE, use WRONG password

SEQUENCE:
  1. Press B  → "Verify login form is visible"
  2. Fill username: tomsmith
  3. Press A  → "Type 'tomsmith' into username"
  4. Press B  → "Verify username shows tomsmith"
  5. Fill password: wrongpassword999
  6. Press A  → "Type wrong password"
  7. Click Login
  8. Press A  → "Click Login with invalid credentials"
  9. Press B  → "Verify error message appears on page"
  10. Press B  → "Verify error text says 'Your password is invalid!'"
  11. Press B  → "Verify URL still contains /login (no redirect)"
  12. Press F on last capture → expected: dashboard, actual: error message shown

VARIANTS:
  - Wrong username + correct password
  - Both wrong
  - Empty username
  - Empty password
"""
    },
    "S21": {
        "name": "Auth logout",
        "url":  "https://the-internet.herokuapp.com/login",
        "target_records": 20,
        "family": "auth",
        "instructions": """
LOGIN FIRST then logout:
  1. Login as tomsmith (full sequence as S19)
  2. On secure page: Press B → "Verify user is logged in on secure page"
  3. Click Logout button
  4. Press A  → "Click Logout button"
  5. Press B  → "Verify redirected to login page"
  6. Press B  → "Verify 'You logged out of the secure area!' message shown"
  7. Press G  → evidence: "Login page showing with logout confirmation message"
"""
    },

    # ── WAIT / SLOW LOAD ──────────────────────────────────────────────────────
    "S22": {
        "name": "wait_for_element — dynamic loading (hidden element)",
        "url":  "https://the-internet.herokuapp.com/dynamic_loading/1",
        "target_records": 40,
        "family": "wait",
        "instructions": """
PAGE: Has a Start button, hidden element loads after 5 seconds

SEQUENCE:
  1. Press B  → "Verify Start button visible, Hello World text not visible"
  2. Click Start
  3. Press A  → "Click Start button to begin loading"
  4. Press B  → "Verify loading bar/spinner is visible"
  5. WAIT (do not press anything for 5 seconds while loading)
  6. Press B  → "Verify loading completed, Hello World text is now visible"
  7. Press G  → evidence: "Hello World text appeared after loading completed"

ALSO CAPTURE mid-load state:
  Click Start → immediately press B (capture spinner visible) → press B again after load

Do 6 workflows to get variety of load-state captures
"""
    },
    "S23": {
        "name": "wait_for_element — element rendered after delay",
        "url":  "https://the-internet.herokuapp.com/dynamic_loading/2",
        "target_records": 30,
        "family": "wait",
        "instructions": """
Similar to S22 but element is rendered (not just hidden)

SEQUENCE:
  1. Press B  → "Verify Start button visible, no Hello World element in DOM"
  2. Click Start
  3. Press A  → "Click Start to trigger dynamic element render"
  4. Press B  → "Verify loading indicator is showing"
  5. Wait for completion
  6. Press B  → "Verify Hello World element has been rendered and is visible"
  7. Press G  → evidence: "Hello World text rendered and visible after load"
"""
    },

    # ── SCROLL TO ELEMENT ─────────────────────────────────────────────────────
    "S26": {
        "name": "Scroll to element — button below fold",
        "url":  "https://demoqa.com/automation-practice-form",
        "target_records": 40,
        "family": "scroll",
        "instructions": """
GOAL: Submit button is BELOW the fold on this long form

SEQUENCE:
  1. Press B  → "Verify form top is visible, Submit button NOT visible in viewport"
  2. Press S  → "Identify that Submit button is below the fold, need to scroll"
  3. Scroll down slowly until Submit visible
  4. Press A  → "Scroll down to bring Submit button into viewport"
  5. Press B  → "Verify Submit button is now visible in viewport"

ALSO CAPTURE:
  - State where an element is IN viewport (in_viewport: true in DOM)
  - State where element is OUT of viewport (in_viewport: false)
  This directly demonstrates the DOM in_viewport flag your extractor captures

FAIL CASE:
  Describe step as "Click Submit button" but button not in viewport yet → F
"""
    },

    # ── FAIL → RAISE BUG ─────────────────────────────────────────────────────
    "S27": {
        "name": "FAIL → raise_bug_ticket flow",
        "url":  "https://demoqa.com/automation-practice-form",
        "target_records": 60,
        "family": "fail",
        "instructions": """
GOAL: Capture steps where EXPECTED != ACTUAL

SEQUENCE 1 — Submit triggers error instead of success:
  1. Fill only First Name, leave all others empty
  2. Click Submit
  3. Press A  → "Click Submit with incomplete form"
  4. Press F  → expected: success modal, actual: red validation errors shown

SEQUENCE 2 — Wrong text in field:
  1. Type "John" in First Name
  2. Verify field: Press B → "Verify First Name contains 'Jane'"
  3. Press F  → expected: Jane, actual: John

SEQUENCE 3 — Element missing:
  1. Describe step: "Click Delete button for row 'Missing Record'"
  2. Press B  → capture table with no matching row
  3. Press F  → expected: delete button for Missing Record, actual: row not found

SEQUENCE 4 — Wrong URL:
  1. Navigate somewhere
  2. Press B → "Verify URL contains /dashboard"
  3. Press F → expected: /dashboard in URL, actual: /text-box in URL

CAPTURE 15 DIFFERENT FAIL SCENARIOS
"""
    },

    # ── FLOW BLOCKED ─────────────────────────────────────────────────────────
    "S28": {
        "name": "FLOW_BLOCKED detection",
        "url":  "https://the-internet.herokuapp.com/login",
        "target_records": 40,
        "family": "flow_blocked",
        "instructions": """
GOAL: Capture states where the ENTIRE FLOW cannot continue

SEQUENCE 1 — Login required but fails:
  1. Go to /login, enter wrong credentials 3 times in a row
  2. After 3rd failure: Press B → "Attempt 3 of 3 login failed with wrong credentials"
  3. Press X → reason: "Cannot proceed — login required for all subsequent steps, 3 attempts failed"

SEQUENCE 2 — Required modal won't close:
  1. Trigger a modal (demoqa/modal-dialogs)
  2. Press B → "Verify modal is blocking all page content"
  3. Simulate modal not having a close button (just for training)
  4. Press X → reason: "Modal blocking page, no dismiss button available"

SEQUENCE 3 — Network error state:
  1. Navigate to a page, then disable network (devtools)
  2. Try to submit a form
  3. Press B → "Verify network error prevents form submission"
  4. Press X → reason: "Network unavailable — cannot complete form submission"

DO 8 different FLOW_BLOCKED scenarios
"""
    },

    # ── GOAL ACHIEVED ─────────────────────────────────────────────────────────
    "S29": {
        "name": "GOAL ACHIEVED with visual proof",
        "url":  "https://the-internet.herokuapp.com/login",
        "target_records": 60,
        "family": "goal_achieved",
        "instructions": """
GOAL: Capture the FINAL STATE of any completed flow where G is pressed.
      These are your most important records — fixes premature [GOAL ACHIEVED]

RULE: Press G ONLY when ALL these are visible in screenshot:
  1. The expected outcome is visually on screen
  2. No error messages visible
  3. URL/page matches expected destination

GOAL ACHIEVED SCENARIOS:
  1. After successful login → secure page + flash message visible → G
  2. After successful form submit → success modal visible → G
  3. After adding table row → new row visible in table → G
  4. After deleting row → row gone from table → G
  5. After editing row → updated value in table → G
  6. After modal dismiss → modal gone, page back to normal → G
  7. After alert handled → result text updated on page → G
  8. After checkbox check → checkbox shows checked → G
  9. After dropdown select → selected value shown → G
  10. After scroll → target element in viewport → G

COLLECT 6 G presses PER SCENARIO ABOVE = 60 total
For each: write detailed visual evidence in the prompt
  Example: "Secure area page loaded. Flash message 'You logged into a secure area!' 
            visible in green at top. URL is /secure. Logout button visible."
"""
    },

    # ── VERIFY STANDALONE ─────────────────────────────────────────────────────
    "S30": {
        "name": "verify_* tools standalone — SauceDemo",
        "url":  "https://www.saucedemo.com",
        "target_records": 80,
        "family": "verify_standalone",
        "instructions": """
LOGIN FIRST: standard_user / secret_sauce

VERIFY TOOLS TO COVER:
  verify_text_present:
    After login → B → "Verify text 'Products' is present on the page"
    
  verify_text_absent:
    After login → B → "Verify text 'Invalid credentials' is absent from page"
    
  verify_element_visible:
    Product cards → B → "Verify Add to Cart button is visible for first product"
    
  verify_element_enabled:
    Checkout button → B → "Verify Checkout button is enabled (not disabled)"
    
  verify_url_contains:
    After login → B → "Verify URL contains '/inventory'"
    After adding to cart → navigate to cart → B → "Verify URL contains '/cart'"
    
  verify_input_value:
    Checkout form → fill First Name → B → "Verify First Name field contains 'John'"
    
  get_text:
    Product name → B → "Read product title text from first product card"
    
  verify_element_count:
    Products page → B → "Verify 6 product cards are visible on page"

DO EACH TOOL AT LEAST 8 TIMES = 8 × 10 tools = 80 records
Mix PASS and FAIL states (describe wrong expected → press F)
"""
    },
}


# ── DOM EXTRACTOR — WITH ROW CONTEXT ─────────────────────────────────────────
DOM_SCRIPT = """
() => {
    function inViewport(el) {
        const r = el.getBoundingClientRect();
        const vw = window.innerWidth, vh = window.innerHeight;
        return r.top < vh && r.bottom > 0 && r.left < vw && r.right > 0 && r.width > 0;
    }

    function getSelector(el) {
        if (el.id && !el.id.match(/^[0-9]/)) return '#' + CSS.escape(el.id);
        const tag = el.tagName.toLowerCase();
        if (el.name) return `${tag}[name="${el.name}"]`;
        if (tag === 'input' || tag === 'textarea') {
            if (el.placeholder) return `${tag}[placeholder="${el.placeholder.slice(0,40)}"]`;
            if (el.type && el.type !== 'text') return `${tag}[type="${el.type}"]`;
        }
        const classes = Array.from(el.classList)
            .filter(c => c.length > 1 && !c.match(/^(active|focus|hover|open|show|visible|hide|d-)/))
            .slice(0, 3).join('.');
        return classes ? `${tag}.${classes}` : tag;
    }

    function getRowContext(el) {
        let node = el.parentElement;
        for (let i = 0; i < 6; i++) {
            if (!node) break;
            const tag = node.tagName;
            if (tag === 'TR' || tag === 'LI' || 
                (node.className && node.className.toString().match(/row|item|entry|record/i))) {
                const cells = node.querySelectorAll('td, th, .cell, [class*="cell"]');
                if (cells.length > 0) {
                    return Array.from(cells).map(c => c.textContent.trim()).filter(t=>t).join(' | ').slice(0, 120);
                }
                const txt = node.textContent.trim().replace(/\\s+/g, ' ');
                return txt.slice(0, 120);
            }
            node = node.parentElement;
        }
        return null;
    }

    function getLabelText(el) {
        // Try aria-label
        if (el.getAttribute('aria-label')) return el.getAttribute('aria-label').slice(0, 60);
        // Try associated <label>
        if (el.id) {
            const label = document.querySelector(`label[for="${el.id}"]`);
            if (label) return label.textContent.trim().slice(0, 60);
        }
        // Try parent label
        let p = el.parentElement;
        for (let i = 0; i < 3; i++) {
            if (!p) break;
            if (p.tagName === 'LABEL') return p.textContent.trim().replace(el.value || '', '').trim().slice(0, 60);
            p = p.parentElement;
        }
        return null;
    }

    const results = [];
    const seen = new Set();
    const INTERACTIVE = [
        'a', 'button', 'input', 'select', 'textarea',
        '[role="button"]', '[role="link"]', '[role="checkbox"]',
        '[role="menuitem"]', '[role="option"]', '[role="tab"]',
        '[onclick]', '[tabindex]'
    ].join(',');

    document.querySelectorAll(INTERACTIVE).forEach(el => {
        const inVP = inViewport(el);
        // Skip completely off-screen elements unless they're forms
        if (!inVP && !['input','textarea','select'].includes(el.tagName.toLowerCase())) return;
        if (el.type === 'hidden') return;

        const sel = getSelector(el);
        const text = (el.textContent || el.value || el.placeholder || el.getAttribute('aria-label') || '').trim().slice(0, 80);
        const key = sel + '|' + text.slice(0,20);
        if (seen.has(key)) {
            // DUPLICATE SELECTOR — add row context to differentiate
        }
        seen.add(key);

        const item = {
            tag: el.tagName.toLowerCase(),
            selector: sel,
            text: text,
            type: el.type || el.getAttribute('role') || '',
            value: el.value || '',
            in_viewport: inVP,
            is_focused: document.activeElement === el,
        };
        if (el.maxLength > 0 && el.maxLength < 100000) item.maxlength = el.maxLength;
        if (el.disabled) item.disabled = true;
        if (el.checked !== undefined) item.checked = el.checked;

        // Row context for table action buttons
        const rowCtx = getRowContext(el);
        if (rowCtx) item.row_context = rowCtx;

        // Label
        const lbl = getLabelText(el);
        if (lbl) item.label = lbl;

        results.push(item);
    });

    // Add current URL and page title as metadata
    results.unshift({
        _meta: true,
        url: window.location.href,
        title: document.title,
        scroll_y: window.scrollY,
        viewport: { w: window.innerWidth, h: window.innerHeight }
    });

    return results;
}
"""


# ── COLLECTOR ─────────────────────────────────────────────────────────────────
class Collector:
    def __init__(self, scenario_id):
        scen = SCENARIOS[scenario_id]
        self.scenario_id   = scenario_id
        self.scenario_name = scen["name"]
        self.start_url     = scen["url"]
        self.family        = scen["family"]
        self.instructions  = scen["instructions"]

        self.out_dir = BASE_DIR / scenario_id
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.workflow_num  = 1
        self.step_num      = 0
        self.captures      = []
        self.last_id       = None

    def _next_step_id(self):
        self.step_num += 1
        wf = f"wf{self.workflow_num:02d}"
        return f"{self.scenario_id}_{wf}_step{self.step_num:03d}"

    async def capture(self, page, state="normal"):
        sid = self._next_step_id()

        # Screenshot full viewport
        png_path = self.out_dir / f"{sid}.png"
        await page.screenshot(
            path=str(png_path),
            clip={"x": 0, "y": 0, "width": VIEWPORT_W, "height": VIEWPORT_H}
        )

        # Resize to training resolution
        try:
            from PIL import Image
            img = Image.open(png_path).resize((TRAIN_W, TRAIN_H), Image.LANCZOS)
            img.save(png_path)
        except ImportError:
            pass  # PIL not installed — keep original

        # Extract DOM
        try:
            dom = await page.evaluate(DOM_SCRIPT)
        except Exception as e:
            dom = [{"_meta": True, "error": str(e), "url": page.url}]

        # Get step description from user
        print(f"\n  Captured: {sid}  [{state.upper()}]")
        dom_count = len([d for d in dom if not d.get('_meta')])
        print(f"  DOM elements: {dom_count}  |  URL: {page.url[:60]}")
        desc = input(f"  Step description: ").strip()

        meta = {
            "id":            sid,
            "scenario_id":   self.scenario_id,
            "scenario_name": self.scenario_name,
            "family":        self.family,
            "workflow":      f"wf{self.workflow_num:02d}",
            "step_num":      self.step_num,
            "capture_state": state,
            "step_desc":     desc,
            "url":           page.url,
            "timestamp":     datetime.now().isoformat(),
            "screenshot":    f"{sid}.png",
            "dom":           dom,
        }

        json_path = self.out_dir / f"{sid}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        self.last_id = sid
        self.captures.append(sid)
        print(f"  ✅ Saved {sid}.png + {sid}.json")
        return sid

    def mark_last(self, page, mark_type, extra_key, extra_prompt):
        if not self.last_id:
            print("  Nothing to mark yet.")
            return
        path = self.out_dir / f"{self.last_id}.json"
        with open(path) as f:
            data = json.load(f)
        data["capture_state"] = mark_type
        val = input(f"  {extra_prompt}: ").strip()
        data[extra_key] = val
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Marked {self.last_id} as {mark_type.upper()}: {val}")

    def new_workflow(self):
        self.workflow_num += 1
        self.step_num = 0
        print(f"\n  ─── Started workflow wf{self.workflow_num:02d} ───")

    def save_summary(self):
        summary = {
            "scenario_id":    self.scenario_id,
            "scenario_name":  self.scenario_name,
            "family":         self.family,
            "target_records": SCENARIOS[self.scenario_id]["target_records"],
            "total_captures": len(self.captures),
            "workflows":      self.workflow_num,
            "captures":       self.captures,
            "completed_at":   datetime.now().isoformat(),
        }
        path = self.out_dir / f"{self.scenario_id}_summary.json"
        with open(path, "w") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\n  Summary saved → {path}")


async def run(scenario_id):
    col = Collector(scenario_id)

    print(f"\n{'='*60}")
    print(f"  SCENARIO {scenario_id}: {col.scenario_name}")
    print(f"  TARGET: {SCENARIOS[scenario_id]['target_records']} records")
    print(f"  FAMILY: {col.family}")
    print(f"{'='*60}")
    print(col.instructions)
    print(f"\n{'─'*60}")
    print("  KEYS:  S=capture  B=before  A=after  F=fail  G=goal")
    print("         X=blocked  N=new_workflow  Q=quit")
    print(f"{'─'*60}\n")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, slow_mo=50)
        ctx     = await browser.new_context(viewport={"width": VIEWPORT_W, "height": VIEWPORT_H})
        page    = await ctx.new_page()
        await page.goto(col.start_url)
        print(f"  Browser opened → {col.start_url}\n")

        loop = asyncio.get_event_loop()

        while True:
            try:
                cmd = await loop.run_in_executor(
                    None, lambda: input("  cmd> ").strip().upper()
                )
            except (EOFError, KeyboardInterrupt):
                break

            if   cmd == "S": await col.capture(page, "normal")
            elif cmd == "B": await col.capture(page, "before_action")
            elif cmd == "A": await col.capture(page, "after_action")
            elif cmd == "F": col.mark_last(page, "fail",          "fail_reason",    "Fail reason (expected vs actual)")
            elif cmd == "G": col.mark_last(page, "goal_achieved", "goal_evidence",  "Visual evidence of success")
            elif cmd == "X": col.mark_last(page, "flow_blocked",  "blocked_reason", "Blocked reason")
            elif cmd == "N": col.new_workflow()
            elif cmd == "Q": break
            elif cmd == "?":
                print("  S=capture  B=before  A=after  F=fail  G=goal  X=blocked  N=new_workflow  Q=quit")
            else:
                print("  Unknown command. Type ? for help.")

        col.save_summary()
        print(f"\n  Total captures: {len(col.captures)}")
        await browser.close()


def main():
    print("\n  AEGIS DATA COLLECTOR")
    print("  " + "─"*40)
    print("  Available scenarios:\n")
    for sid, scen in SCENARIOS.items():
        target = scen["target_records"]
        done   = len(list((BASE_DIR / sid).glob("*.json"))) - 1 if (BASE_DIR / sid).exists() else 0
        status = f"({done}/{target})" if done > 0 else f"(target: {target})"
        print(f"  [{sid}] {scen['name']:<42} {status}")

    print()
    sid = input("  Enter scenario ID (e.g. S01): ").strip().upper()
    if sid not in SCENARIOS:
        print(f"  Unknown scenario: {sid}")
        return

    asyncio.run(run(sid))


if __name__ == "__main__":
    BASE_DIR.mkdir(exist_ok=True)
    main()
