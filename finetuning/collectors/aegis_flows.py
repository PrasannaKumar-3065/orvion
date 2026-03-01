"""
AEGIS FLOWS — Complete Dataset Coverage
========================================
Target: 550 records across all 13 scenario types.

DOM STRATEGY (answers the dynamic DOM question):
-------------------------------------------------
The generator uses a 5-tier selector resolution chain:
  Tier 1 — data-testid / data-cy / data-qa   (most stable, never changes)
  Tier 2 — #id                               (stable if dev uses IDs)
  Tier 3 — aria-label / placeholder          (semantic, readable)
  Tier 4 — label[for] association            (form standard)
  Tier 5 — tag + visible text                (last resort, fragile)

For DYNAMIC DOMs (OrangeHRM oxd- classes, React tables, SPAs):
  - We pass the TARGET selector hint to extract_relevant_dom()
  - The extractor does a BM25-style proximity filter: elements within
    200px of the target get priority over nav chrome
  - We also run a pre-step DOM probe to find the actual live selector
    BEFORE writing the training record (probe_selector() function)

For TRAINING DATA: the selector in the record reflects what the
extractor found at runtime — so the model learns real selectors,
not hardcoded guesses.
"""

# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO TYPE 1: Form Filling — Single Field (80 records target)
# Sites: demoqa.com/text-box, demoqa.com/automation-practice-form
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_FORM_SINGLE = [

    # 1a. Basic text fields
    {
        "name": "form_single_fullname",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to the Text Box form page."},
            {"action": "clear_and_type", "selector": "#userName", "value": "Alice Johnson",
             "task": "Enter Alice Johnson in the Full Name field."},
            {"action": "verify_input_value", "selector": "#userName", "value": "Alice Johnson",
             "task": "Verify the Full Name field contains Alice Johnson.", "is_verify": True},
        ]
    },
    {
        "name": "form_single_email",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to the Text Box form page."},
            {"action": "clear_and_type", "selector": "#userEmail", "value": "alice@company.io",
             "task": "Enter alice@company.io in the Email field."},
            {"action": "verify_input_value", "selector": "#userEmail", "value": "alice@company.io",
             "task": "Verify the Email field contains alice@company.io.", "is_verify": True},
        ]
    },
    {
        "name": "form_single_textarea",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to the Text Box form page."},
            {"action": "clear_and_type", "selector": "#currentAddress",
             "value": "42 Elm Street, Austin, TX 78701",
             "task": "Enter 42 Elm Street, Austin, TX 78701 in the Current Address field."},
            {"action": "verify_input_value", "selector": "#currentAddress",
             "value": "42 Elm Street, Austin, TX 78701",
             "task": "Verify the Current Address field contains 42 Elm Street, Austin, TX 78701.",
             "is_verify": True},
        ]
    },
    {
        "name": "form_single_permanent_address",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to the Text Box form page."},
            {"action": "scroll_down",
             "task": "Scroll down to bring the Permanent Address field into view."},
            {"action": "clear_and_type", "selector": "#permanentAddress",
             "value": "99 Oak Lane, Denver, CO 80202",
             "task": "Enter 99 Oak Lane, Denver, CO 80202 in the Permanent Address field."},
            {"action": "verify_input_value", "selector": "#permanentAddress",
             "value": "99 Oak Lane, Denver, CO 80202",
             "task": "Verify the Permanent Address field contains 99 Oak Lane, Denver, CO 80202.",
             "is_verify": True},
        ]
    },

    # 1b. Practice form — first name, last name, phone (separate single-field steps)
    {
        "name": "form_single_firstname",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/automation-practice-form",
             "task": "Navigate to the Automation Practice Form page."},
            {"action": "clear_and_type", "selector": "#firstName", "value": "Robert",
             "task": "Enter Robert in the First Name field."},
            {"action": "verify_input_value", "selector": "#firstName", "value": "Robert",
             "task": "Verify First Name field contains Robert.", "is_verify": True},
        ]
    },
    {
        "name": "form_single_lastname",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/automation-practice-form",
             "task": "Navigate to the Automation Practice Form page."},
            {"action": "clear_and_type", "selector": "#lastName", "value": "Martinez",
             "task": "Enter Martinez in the Last Name field."},
            {"action": "verify_input_value", "selector": "#lastName", "value": "Martinez",
             "task": "Verify Last Name field contains Martinez.", "is_verify": True},
        ]
    },
    {
        "name": "form_single_phone",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/automation-practice-form",
             "task": "Navigate to the Automation Practice Form page."},
            {"action": "clear_and_type", "selector": "#userNumber", "value": "9876543210",
             "task": "Enter 9876543210 in the Mobile Number field."},
            {"action": "verify_input_value", "selector": "#userNumber", "value": "9876543210",
             "task": "Verify Mobile Number contains 9876543210.", "is_verify": True},
        ]
    },
    {
        "name": "form_single_email_practice",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/automation-practice-form",
             "task": "Navigate to the Automation Practice Form page."},
            {"action": "clear_and_type", "selector": "#userEmail", "value": "robert.m@test.com",
             "task": "Enter robert.m@test.com in the Email field."},
            {"action": "verify_input_value", "selector": "#userEmail", "value": "robert.m@test.com",
             "task": "Verify Email field contains robert.m@test.com.", "is_verify": True},
        ]
    },

    # 1c. SauceDemo login fields individually
    {
        "name": "form_single_username_sauce",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to the SauceDemo login page."},
            {"action": "clear_and_type", "selector": "#user-name", "value": "performance_glitch_user",
             "task": "Enter performance_glitch_user in the Username field."},
            {"action": "verify_input_value", "selector": "#user-name", "value": "performance_glitch_user",
             "task": "Verify Username field contains performance_glitch_user.", "is_verify": True},
        ]
    },
    {
        "name": "form_single_password_sauce",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to the SauceDemo login page."},
            {"action": "clear_and_type", "selector": "#password", "value": "secret_sauce",
             "task": "Enter secret_sauce in the Password field."},
            {"action": "verify_input_value", "selector": "#password", "value": "secret_sauce",
             "task": "Verify Password field is filled.", "is_verify": True},
        ]
    },
]

# Repeat with different data variants to hit 80 records
# Each flow above = 3 records avg → 10 flows = 30. Add variants:
FLOWS_FORM_SINGLE_VARIANTS = [
    {
        "name": "form_single_fullname_v2",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to the Text Box form page."},
            {"action": "clear_and_type", "selector": "#userName", "value": "Priya Nair",
             "task": "Enter Priya Nair in the Full Name field."},
            {"action": "verify_input_value", "selector": "#userName", "value": "Priya Nair",
             "task": "Verify Full Name field contains Priya Nair.", "is_verify": True},
        ]
    },
    {
        "name": "form_single_fullname_v3",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to the Text Box form page."},
            {"action": "clear_and_type", "selector": "#userName", "value": "محمد علي",
             "task": "Enter محمد علي (Arabic name) in the Full Name field — unicode test."},
            {"action": "verify_input_value", "selector": "#userName", "value": "محمد علي",
             "task": "Verify Full Name field contains the unicode Arabic name محمد علي.", "is_verify": True},
        ]
    },
    {
        "name": "form_single_email_invalid",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to the Text Box form page."},
            {"action": "clear_and_type", "selector": "#userEmail", "value": "not-an-email",
             "task": "Enter not-an-email (invalid format) in the Email field — boundary test."},
            {"action": "verify_input_value", "selector": "#userEmail", "value": "not-an-email",
             "task": "Verify Email field contains not-an-email.", "is_verify": True},
        ]
    },
    {
        "name": "form_single_overwrite",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to the Text Box form page."},
            {"action": "clear_and_type", "selector": "#userName", "value": "First Entry",
             "task": "Enter First Entry in the Full Name field."},
            {"action": "clear_and_type", "selector": "#userName", "value": "Overwritten Value",
             "task": "Overwrite the Full Name field with Overwritten Value to test clear behavior."},
            {"action": "verify_input_value", "selector": "#userName", "value": "Overwritten Value",
             "task": "Verify Full Name field now contains Overwritten Value, not First Entry.",
             "is_verify": True},
        ]
    },
    {
        "name": "form_single_special_chars",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to the Text Box form page."},
            {"action": "clear_and_type", "selector": "#currentAddress",
             "value": "O'Brien & Sons, 100% Verified — Apt #5",
             "task": "Enter address with special characters: O'Brien & Sons, 100% Verified — Apt #5."},
            {"action": "verify_input_value", "selector": "#currentAddress",
             "value": "O'Brien & Sons, 100% Verified — Apt #5",
             "task": "Verify address field contains the special character string.", "is_verify": True},
        ]
    },
    {
        "name": "form_single_long_text",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to the Text Box form page."},
            {"action": "clear_and_type", "selector": "#currentAddress",
             "value": "Building 7, Tower C, Suite 4200, International Business Park, "
                      "Sector 18, Noida, Uttar Pradesh, India - 201301",
             "task": "Enter a long multi-part address in the Current Address field."},
            {"action": "verify_input_value", "selector": "#currentAddress",
             "value": "Building 7, Tower C, Suite 4200, International Business Park, "
                      "Sector 18, Noida, Uttar Pradesh, India - 201301",
             "task": "Verify the long address is fully preserved in the Current Address field.",
             "is_verify": True},
        ]
    },
    {
        "name": "form_single_firstname_v2",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/automation-practice-form",
             "task": "Navigate to the Automation Practice Form."},
            {"action": "clear_and_type", "selector": "#firstName", "value": "Sanjay",
             "task": "Enter Sanjay in the First Name field."},
            {"action": "verify_input_value", "selector": "#firstName", "value": "Sanjay",
             "task": "Verify First Name field contains Sanjay.", "is_verify": True},
        ]
    },
    {
        "name": "form_single_phone_boundary",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/automation-practice-form",
             "task": "Navigate to the Automation Practice Form."},
            {"action": "clear_and_type", "selector": "#userNumber", "value": "1234567890",
             "task": "Enter exactly 10 digits (1234567890) in the Mobile Number field — boundary test."},
            {"action": "verify_input_value", "selector": "#userNumber", "value": "1234567890",
             "task": "Verify Mobile Number contains exactly 10 digits 1234567890.", "is_verify": True},
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO TYPE 2: Form Filling — Multi-Field Sequences (60 records target)
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_FORM_MULTI = [

    # 2a. Complete text-box form (4 fields → submit → verify output)
    {
        "name": "form_multi_textbox_complete",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to the Text Box form page. This is a multi-field form filling flow."},
            {"action": "clear_and_type", "selector": "#userName", "value": "John Doe",
             "task": "Step 1 of 6 — Enter John Doe in the Full Name field."},
            {"action": "verify_input_value", "selector": "#userName", "value": "John Doe",
             "task": "Verify Full Name field contains John Doe before moving to next field.",
             "is_verify": True},
            {"action": "clear_and_type", "selector": "#userEmail", "value": "john.doe@test.com",
             "task": "Step 2 of 6 — Enter john.doe@test.com in the Email field."},
            {"action": "verify_input_value", "selector": "#userEmail", "value": "john.doe@test.com",
             "task": "Verify Email field contains john.doe@test.com.", "is_verify": True},
            {"action": "clear_and_type", "selector": "#currentAddress",
             "value": "123 AI Avenue, Silicon Valley",
             "task": "Step 3 of 6 — Enter 123 AI Avenue, Silicon Valley in the Current Address field."},
            {"action": "verify_input_value", "selector": "#currentAddress",
             "value": "123 AI Avenue, Silicon Valley",
             "task": "Verify Current Address contains 123 AI Avenue, Silicon Valley.", "is_verify": True},
            {"action": "clear_and_type", "selector": "#permanentAddress",
             "value": "456 ML Boulevard, San Francisco",
             "task": "Step 4 of 6 — Enter 456 ML Boulevard, San Francisco in the Permanent Address."},
            {"action": "verify_input_value", "selector": "#permanentAddress",
             "value": "456 ML Boulevard, San Francisco",
             "task": "Verify Permanent Address contains 456 ML Boulevard, San Francisco.",
             "is_verify": True},
            {"action": "click", "selector": "#submit",
             "task": "Step 5 of 6 — All fields filled. Click Submit to submit the form."},
            {"action": "verify_text_present", "value": "John Doe",
             "task": "Step 6 of 6 — Verify output section shows John Doe confirming form submitted.",
             "is_verify": True},
        ]
    },

    # 2b. SauceDemo login + add to cart (end-to-end 6-step)
    {
        "name": "form_multi_login_cart",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo. Beginning login + add-to-cart multi-step flow."},
            {"action": "clear_and_type", "selector": "#user-name", "value": "standard_user",
             "task": "Step 1 of 5 — Enter standard_user in the Username field."},
            {"action": "verify_input_value", "selector": "#user-name", "value": "standard_user",
             "task": "Verify Username field contains standard_user.", "is_verify": True},
            {"action": "clear_and_type", "selector": "#password", "value": "secret_sauce",
             "task": "Step 2 of 5 — Enter secret_sauce in the Password field."},
            {"action": "verify_input_value", "selector": "#password", "value": "secret_sauce",
             "task": "Verify Password field is filled.", "is_verify": True},
            {"action": "click", "selector": "#login-button",
             "task": "Step 3 of 5 — Click Login button to submit credentials."},
            {"action": "verify_url_contains", "value": "inventory",
             "task": "Step 4 of 5 — Verify URL contains inventory confirming login succeeded.",
             "is_verify": True},
            {"action": "click", "selector": "#add-to-cart-sauce-labs-backpack",
             "task": "Step 5 of 5 — Click Add to Cart for the Sauce Labs Backpack."},
            {"action": "verify_element_visible", "selector": ".shopping_cart_badge",
             "task": "Verify shopping cart badge is visible with item count after adding product.",
             "is_verify": True},
        ]
    },

    # 2c. Practice form — first name + last name + email + phone (4-field sequence)
    {
        "name": "form_multi_practice_personal",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/automation-practice-form",
             "task": "Navigate to the Automation Practice Form. Beginning personal details entry."},
            {"action": "clear_and_type", "selector": "#firstName", "value": "Emily",
             "task": "Step 1 of 4 — Enter Emily in the First Name field."},
            {"action": "verify_input_value", "selector": "#firstName", "value": "Emily",
             "task": "Verify First Name field contains Emily.", "is_verify": True},
            {"action": "clear_and_type", "selector": "#lastName", "value": "Chen",
             "task": "Step 2 of 4 — Enter Chen in the Last Name field."},
            {"action": "verify_input_value", "selector": "#lastName", "value": "Chen",
             "task": "Verify Last Name field contains Chen.", "is_verify": True},
            {"action": "clear_and_type", "selector": "#userEmail", "value": "emily.chen@qa.org",
             "task": "Step 3 of 4 — Enter emily.chen@qa.org in the Email field."},
            {"action": "verify_input_value", "selector": "#userEmail", "value": "emily.chen@qa.org",
             "task": "Verify Email field contains emily.chen@qa.org.", "is_verify": True},
            {"action": "clear_and_type", "selector": "#userNumber", "value": "8001234567",
             "task": "Step 4 of 4 — Enter 8001234567 in the Mobile Number field."},
            {"action": "verify_input_value", "selector": "#userNumber", "value": "8001234567",
             "task": "Verify Mobile Number field contains 8001234567.", "is_verify": True},
        ]
    },

    # 2d. Multi-field with scroll (fields below fold)
    {
        "name": "form_multi_scroll_required",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to the Text Box form page."},
            {"action": "clear_and_type", "selector": "#userName", "value": "Vikram Singh",
             "task": "Step 1 of 3 — Enter Vikram Singh in the Full Name field."},
            {"action": "verify_input_value", "selector": "#userName", "value": "Vikram Singh",
             "task": "Verify Full Name contains Vikram Singh.", "is_verify": True},
            {"action": "scroll_down",
             "task": "Step 2 of 3 — Scroll down to reveal the Permanent Address field below the fold."},
            {"action": "clear_and_type", "selector": "#permanentAddress",
             "value": "Flat 12B, Sunrise Apartments, Mumbai 400001",
             "task": "Step 3 of 3 — Enter Flat 12B, Sunrise Apartments, Mumbai 400001 in Permanent Address."},
            {"action": "verify_input_value", "selector": "#permanentAddress",
             "value": "Flat 12B, Sunrise Apartments, Mumbai 400001",
             "task": "Verify Permanent Address contains the Mumbai address.", "is_verify": True},
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO TYPE 3: Click Interactions + Wait (60 records target)
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_CLICK_WAIT = [

    {
        "name": "click_button_navigation",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo login page."},
            {"action": "clear_and_type", "selector": "#user-name", "value": "standard_user",
             "task": "Enter standard_user in the Username field."},
            {"action": "clear_and_type", "selector": "#password", "value": "secret_sauce",
             "task": "Enter secret_sauce in the Password field."},
            {"action": "click", "selector": "#login-button",
             "task": "Click the Login button. Expecting page navigation to inventory."},
            {"action": "verify_url_contains", "value": "inventory",
             "task": "Verify URL contains inventory confirming page navigation completed.",
             "is_verify": True},
        ]
    },
    {
        "name": "click_double_click",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/buttons",
             "task": "Navigate to the Buttons interaction page."},
            {"action": "double_click", "selector": "#doubleClickBtn",
             "task": "Double-click the Double Click Me button."},
            {"action": "verify_text_present", "value": "You have done a double click",
             "task": "Verify confirmation message appears after double-click.",
             "is_verify": True},
        ]
    },
    {
        "name": "click_dynamic_button",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/buttons",
             "task": "Navigate to the Buttons interaction page."},
            {"action": "scroll_down",
             "task": "Scroll down to bring the dynamic Click Me button into view."},
            {"action": "click", "selector": "button:last-of-type",
             "task": "Click the dynamic Click Me button at the bottom of the page."},
            {"action": "verify_text_present", "value": "You have done a dynamic click",
             "task": "Verify 'You have done a dynamic click' appears after clicking.",
             "is_verify": True},
        ]
    },
    {
        "name": "click_link_navigation",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com",
             "task": "Navigate to the DemoQA home page."},
            {"action": "click", "selector": "a[href*='text-box']",
             "task": "Click the Text Box link to navigate to the Text Box page."},
            {"action": "verify_url_contains", "value": "text-box",
             "task": "Verify URL contains text-box confirming navigation to Text Box page.",
             "is_verify": True},
        ]
    },
    {
        "name": "click_checkbox_state_change",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/checkbox",
             "task": "Navigate to the Check Box page."},
            {"action": "click", "selector": ".rct-checkbox",
             "task": "Click the Home checkbox to toggle it to checked state."},
            {"action": "verify_text_present", "value": "home",
             "task": "Verify the result output shows 'home' is selected.",
             "is_verify": True},
        ]
    },
    {
        "name": "click_accordion_expand",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/accordian",
             "task": "Navigate to the Accordian page."},
            {"action": "click", "selector": "#section2Heading",
             "task": "Click the second accordion heading to expand it."},
            {"action": "verify_element_visible", "selector": "#section2Content",
             "task": "Verify the second accordion section content is visible after expanding.",
             "is_verify": True},
        ]
    },
    {
        "name": "click_modal_open_close",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/modal-dialogs",
             "task": "Navigate to the Modal Dialogs page."},
            {"action": "click", "selector": "#showSmallModal",
             "task": "Click the Small Modal button to open the dialog."},
            {"action": "verify_element_visible", "selector": ".modal-dialog",
             "task": "Verify the modal dialog is now visible.", "is_verify": True},
            {"action": "click", "selector": "#closeSmallModal",
             "task": "Click the Close button to dismiss the modal dialog."},
            {"action": "verify_element_hidden", "selector": ".modal-dialog",
             "task": "Verify the modal dialog is no longer visible after closing.",
             "is_verify": True},
        ]
    },
    {
        "name": "click_tab_navigation",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/tabs",
             "task": "Navigate to the Tabs page."},
            {"action": "click", "selector": "#demo-tab-origin",
             "task": "Click the Origin tab to switch to it."},
            {"action": "verify_element_visible", "selector": "#demo-tabpane-origin",
             "task": "Verify the Origin tab content panel is visible.",
             "is_verify": True},
        ]
    },
    {
        "name": "click_wait_element_appear",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/dynamic-properties",
             "task": "Navigate to Dynamic Properties page where elements appear after a delay."},
            {"action": "wait_for_element", "selector": "#enableAfter",
             "task": "Wait for the 'Enable After 5 Seconds' button to become present in DOM."},
            {"action": "verify_element_visible", "selector": "#enableAfter",
             "task": "Verify the button is now visible after waiting.", "is_verify": True},
        ]
    },
    {
        "name": "click_add_remove_element",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/add_remove_elements/",
             "task": "Navigate to the Add/Remove Elements page."},
            {"action": "click", "selector": "button[onclick='addElement()']",
             "task": "Click the Add Element button to add a new Delete button to the DOM."},
            {"action": "verify_element_visible", "selector": ".added-manually",
             "task": "Verify the newly added Delete button is visible.",
             "is_verify": True},
            {"action": "click", "selector": ".added-manually",
             "task": "Click the Delete button to remove the added element."},
            {"action": "verify_element_hidden", "selector": ".added-manually",
             "task": "Verify the Delete button is no longer visible after removal.",
             "is_verify": True},
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO TYPE 4 & 5: Color Verification PASS + FAIL/Bug (80 records)
#
# HOW COLOR VERIFICATION WORKS IN TRAINING DATA:
# The generator captures a screenshot. For PASS scenarios, the step definition
# declares what color should be found and we generate a response that "sees"
# it correctly. For FAIL/BUG scenarios, we generate a response where the
# observed color does NOT match expected → raise_bug_ticket fires.
#
# In production, get_element_color() returns the computed CSS color.
# The training teaches the model: look at screenshot → compare → decide.
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_COLOR_PASS = [

    {
        "name": "color_pass_primary_button_blue",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo. Checking button color states."},
            {"action": "verify_color_pass",
             "selector": "#login-button",
             "value": "green",
             "expected_color": "#3ddc91",
             "task": "Verify the Login button background color is green (#3ddc91) as per design spec.",
             "is_verify": True},
            {"action": "mark_step_pass",
             "value": "Login button color verified: green (#3ddc91) matches design specification.",
             "task": "Mark color verification step as passed.",
             "is_verify": True},
        ]
    },
    {
        "name": "color_pass_error_text_red",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo. Testing error state color."},
            {"action": "clear_and_type", "selector": "#user-name", "value": "locked_out_user",
             "task": "Enter locked_out_user to trigger an error state."},
            {"action": "clear_and_type", "selector": "#password", "value": "secret_sauce",
             "task": "Enter secret_sauce in password field."},
            {"action": "click", "selector": "#login-button",
             "task": "Click Login to trigger the locked-out error message."},
            {"action": "verify_color_pass",
             "selector": ".error-message-container",
             "value": "red",
             "expected_color": "#e2231a",
             "task": "Verify the error message container background is red (#e2231a) indicating error state.",
             "is_verify": True},
        ]
    },
    {
        "name": "color_pass_active_nav_link",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to DemoQA Text Box page. Testing active navigation link color."},
            {"action": "verify_color_pass",
             "selector": ".left-pannel .active",
             "value": "blue",
             "expected_color": "#0d6efd",
             "task": "Verify the active sidebar navigation item has blue (#0d6efd) highlight color.",
             "is_verify": True},
        ]
    },
    {
        "name": "color_pass_submit_button",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to DemoQA Text Box page."},
            {"action": "verify_color_pass",
             "selector": "#submit",
             "value": "dark/black",
             "expected_color": "#212529",
             "task": "Verify the Submit button color matches the design specification.",
             "is_verify": True},
        ]
    },
    {
        "name": "color_pass_inventory_item_button",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo login page."},
            {"action": "clear_and_type", "selector": "#user-name", "value": "standard_user",
             "task": "Enter standard_user in the Username field."},
            {"action": "clear_and_type", "selector": "#password", "value": "secret_sauce",
             "task": "Enter secret_sauce in the Password field."},
            {"action": "click", "selector": "#login-button",
             "task": "Click Login to go to the inventory page."},
            {"action": "verify_color_pass",
             "selector": ".btn_inventory",
             "value": "white with dark border",
             "expected_color": "#ffffff",
             "task": "Verify the Add to Cart button has white background color as per spec.",
             "is_verify": True},
        ]
    },
]

FLOWS_COLOR_FAIL = [

    {
        "name": "color_fail_button_wrong_color",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo. Running color assertion — expecting failure."},
            {
                "action": "verify_color_fail",
                "selector": "#login-button",
                "value": "red (#dc3545)",
                "observed_color": "#3ddc91",
                "task": "Verify Login button color is red (#dc3545) as per the test specification. "
                        "This assertion is expected to FAIL — button is actually green.",
                "is_verify": True,
                "raises_bug": True,
                "bug_title": "Login button color mismatch: expected red (#dc3545), found green (#3ddc91)",
                "bug_severity": "High",
            },
        ]
    },
    {
        "name": "color_fail_error_not_red",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo. Verifying error message color after failed login."},
            {"action": "clear_and_type", "selector": "#user-name", "value": "locked_out_user",
             "task": "Enter locked_out_user to trigger error."},
            {"action": "clear_and_type", "selector": "#password", "value": "secret_sauce",
             "task": "Enter secret_sauce in the password field."},
            {"action": "click", "selector": "#login-button",
             "task": "Click Login to trigger the error message."},
            {
                "action": "verify_color_fail",
                "selector": ".error-button",
                "value": "blue (#0d6efd)",
                "observed_color": "#e2231a",
                "task": "Verify error dismiss button is blue (#0d6efd). This assertion FAILS — button is red. Raise a bug.",
                "is_verify": True,
                "raises_bug": True,
                "bug_title": "Error button color wrong: expected blue (#0d6efd), observed red (#e2231a)",
                "bug_severity": "Medium",
            },
        ]
    },
    {
        "name": "color_fail_submit_wrong",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to DemoQA Text Box page. Running Submit button color assertion."},
            {
                "action": "verify_color_fail",
                "selector": "#submit",
                "value": "green (#28a745)",
                "observed_color": "#212529",
                "task": "Verify the Submit button is green (#28a745) per new design. This FAILS — button is dark/black. Raise a bug.",
                "is_verify": True,
                "raises_bug": True,
                "bug_title": "Submit button color incorrect: expected green (#28a745), found dark (#212529)",
                "bug_severity": "Low",
            },
        ]
    },
    {
        "name": "color_fail_nav_not_highlighted",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/buttons",
             "task": "Navigate to DemoQA Buttons page to verify sidebar nav highlight color."},
            {
                "action": "verify_color_fail",
                "selector": ".left-pannel .active",
                "value": "orange (#fd7e14)",
                "observed_color": "#0d6efd",
                "task": "Verify active nav link is orange (#fd7e14). This FAILS — it is blue (#0d6efd). Raise a bug.",
                "is_verify": True,
                "raises_bug": True,
                "bug_title": "Nav highlight color mismatch: expected orange (#fd7e14), found blue (#0d6efd)",
                "bug_severity": "Medium",
            },
        ]
    },
    {
        "name": "color_fail_background_wrong",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo. Checking page header background color."},
            {
                "action": "verify_color_fail",
                "selector": ".login_logo",
                "value": "white (#ffffff)",
                "observed_color": "#132322",
                "task": "Verify login header background is white (#ffffff). This FAILS — background is dark. Raise a bug.",
                "is_verify": True,
                "raises_bug": True,
                "bug_title": "Login header background wrong: expected white, found dark (#132322)",
                "bug_severity": "High",
            },
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO TYPE 6: assert_element_visible / hidden (40 records)
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_VISIBILITY = [

    {
        "name": "visibility_modal_not_open",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/modal-dialogs",
             "task": "Navigate to Modal Dialogs page. Verifying modal is initially hidden."},
            {"action": "verify_element_hidden", "selector": ".modal-dialog",
             "task": "Verify the modal dialog is NOT visible before it has been opened.",
             "is_verify": True},
        ]
    },
    {
        "name": "visibility_modal_after_open",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/modal-dialogs",
             "task": "Navigate to Modal Dialogs page."},
            {"action": "click", "selector": "#showSmallModal",
             "task": "Click Show Small Modal button to open the dialog."},
            {"action": "verify_element_visible", "selector": ".modal-dialog",
             "task": "Verify the modal dialog IS visible after clicking the open button.",
             "is_verify": True},
            {"action": "verify_element_visible", "selector": "#closeSmallModal",
             "task": "Verify the Close button is visible inside the open modal.",
             "is_verify": True},
        ]
    },
    {
        "name": "visibility_accordion_collapsed",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/accordian",
             "task": "Navigate to Accordion page. Verifying collapsed section is hidden."},
            {"action": "verify_element_hidden", "selector": "#section2Content",
             "task": "Verify section 2 content is hidden since the accordion is collapsed.",
             "is_verify": True},
        ]
    },
    {
        "name": "visibility_error_message_absent",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo login. No error should be visible yet."},
            {"action": "verify_element_hidden", "selector": ".error-message-container",
             "task": "Verify no error message container is visible before any login attempt.",
             "is_verify": True},
        ]
    },
    {
        "name": "visibility_error_after_bad_login",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo. Testing error visibility after bad login."},
            {"action": "clear_and_type", "selector": "#user-name", "value": "bad_user",
             "task": "Enter bad_user in the Username field."},
            {"action": "clear_and_type", "selector": "#password", "value": "bad_pass",
             "task": "Enter bad_pass in the Password field."},
            {"action": "click", "selector": "#login-button",
             "task": "Click Login with invalid credentials to trigger error."},
            {"action": "verify_element_visible", "selector": ".error-message-container",
             "task": "Verify error message container IS visible after failed login attempt.",
             "is_verify": True},
        ]
    },
    {
        "name": "visibility_cart_badge_absent",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo and log in."},
            {"action": "clear_and_type", "selector": "#user-name", "value": "standard_user",
             "task": "Enter standard_user."},
            {"action": "clear_and_type", "selector": "#password", "value": "secret_sauce",
             "task": "Enter secret_sauce."},
            {"action": "click", "selector": "#login-button",
             "task": "Click Login."},
            {"action": "verify_element_hidden", "selector": ".shopping_cart_badge",
             "task": "Verify the cart badge counter is NOT visible when cart is empty.",
             "is_verify": True},
        ]
    },
    {
        "name": "visibility_cart_badge_present",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo and log in."},
            {"action": "clear_and_type", "selector": "#user-name", "value": "standard_user",
             "task": "Enter standard_user."},
            {"action": "clear_and_type", "selector": "#password", "value": "secret_sauce",
             "task": "Enter secret_sauce."},
            {"action": "click", "selector": "#login-button",
             "task": "Click Login."},
            {"action": "click", "selector": "#add-to-cart-sauce-labs-backpack",
             "task": "Add the Sauce Labs Backpack to cart."},
            {"action": "verify_element_visible", "selector": ".shopping_cart_badge",
             "task": "Verify the cart badge IS visible with a count after adding an item.",
             "is_verify": True},
        ]
    },
    {
        "name": "visibility_form_output_absent_before_submit",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to Text Box form. Output section should be absent before submit."},
            {"action": "verify_element_hidden", "selector": "#output",
             "task": "Verify the output section is NOT visible before the form is submitted.",
             "is_verify": True},
        ]
    },
    {
        "name": "visibility_form_output_after_submit",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to Text Box form."},
            {"action": "clear_and_type", "selector": "#userName", "value": "Test User",
             "task": "Enter Test User in Full Name."},
            {"action": "click", "selector": "#submit",
             "task": "Click Submit to submit the form."},
            {"action": "verify_element_visible", "selector": "#output",
             "task": "Verify the output section IS visible after form submission.",
             "is_verify": True},
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO TYPE 7: Selector NOT Found — Negative Examples (40 records)
#
# CRITICAL for stopping hallucination. The model must learn:
# "If I cannot find the selector, I raise a bug — I do NOT invent one."
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_NEGATIVE_SELECTOR = [

    {
        "name": "neg_selector_wrong_id",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to Text Box page."},
            {
                "action": "verify_element_hidden",
                "selector": "#fullName",   # Wrong — real id is #userName
                "task": "Verify element #fullName is present. NOTE: this selector does NOT exist on this page.",
                "is_verify": True,
                "raises_bug": True,
                "value": "element #fullName to exist (actual selector is #userName)",
                "bug_title": "Element not found: #fullName does not exist on the page",
                "bug_severity": "Medium",
            },
        ]
    },
    {
        "name": "neg_selector_stale_class",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo login page."},
            {
                "action": "verify_element_hidden",
                "selector": ".login-form__input--username",
                "task": "Verify element .login-form__input--username is present. "
                        "This selector is from an old version and no longer exists.",
                "is_verify": True,
                "raises_bug": True,
                "value": "element .login-form__input--username (stale selector from v1)",
                "bug_title": "Stale selector: .login-form__input--username not found — may have been renamed",
                "bug_severity": "Medium",
            },
        ]
    },
    {
        "name": "neg_selector_typo",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/buttons",
             "task": "Navigate to DemoQA Buttons page."},
            {
                "action": "verify_element_hidden",
                "selector": "#doubleClickButton",   # typo — real is #doubleClickBtn
                "task": "Verify element #doubleClickButton is present. "
                        "This is a typo — the correct selector is #doubleClickBtn.",
                "is_verify": True,
                "raises_bug": True,
                "value": "element #doubleClickButton",
                "bug_title": "Element not found: #doubleClickButton — possible typo, check #doubleClickBtn",
                "bug_severity": "Low",
            },
        ]
    },
    {
        "name": "neg_selector_wrong_page",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to Text Box page."},
            {
                "action": "verify_element_hidden",
                "selector": "#oldSelectMenu",  # belongs to select-menu page, not text-box
                "task": "Verify element #oldSelectMenu is present. "
                        "This element belongs to a different page and should NOT be found here.",
                "is_verify": True,
                "raises_bug": True,
                "value": "element #oldSelectMenu on the Text Box page",
                "bug_title": "Element #oldSelectMenu not found — element belongs to Select Menu page, not Text Box",
                "bug_severity": "High",
            },
        ]
    },
    {
        "name": "neg_selector_dynamic_id_changed",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/dynamic-properties",
             "task": "Navigate to Dynamic Properties page to test element found after wait."},
            {
                "action": "verify_element_hidden",
                "selector": "#visibleAfter",  # only appears after 5 seconds
                "task": "Verify element #visibleAfter is currently visible. "
                        "This element only appears after 5 seconds — it should NOT be visible yet.",
                "is_verify": True,
                "raises_bug": False,  # Not a bug — it's timing. Model should note it's not visible yet.
                "value": "element not yet visible",
            },
        ]
    },
    {
        "name": "neg_selector_cart_nonexistent",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo. Cart is empty."},
            {"action": "clear_and_type", "selector": "#user-name", "value": "standard_user",
             "task": "Enter standard_user."},
            {"action": "clear_and_type", "selector": "#password", "value": "secret_sauce",
             "task": "Enter secret_sauce."},
            {"action": "click", "selector": "#login-button",
             "task": "Click Login."},
            {
                "action": "verify_element_hidden",
                "selector": ".remove-sauce-labs-backpack",   # not in DOM until item is added
                "task": "Verify the Remove button for Sauce Labs Backpack is present. "
                        "Item has not been added yet — selector should NOT exist.",
                "is_verify": True,
                "raises_bug": True,
                "value": "Remove button for Sauce Labs Backpack",
                "bug_title": "Remove button .remove-sauce-labs-backpack not found — item was not added to cart",
                "bug_severity": "High",
            },
        ]
    },
    {
        "name": "neg_selector_casing_wrong",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/automation-practice-form",
             "task": "Navigate to Automation Practice Form."},
            {
                "action": "verify_element_hidden",
                "selector": "#FirstName",   # wrong casing — real is #firstName
                "task": "Verify element #FirstName is present. "
                        "NOTE: CSS IDs are case-sensitive — the real selector is #firstName (lowercase f).",
                "is_verify": True,
                "raises_bug": True,
                "value": "element #FirstName (wrong case — should be #firstName)",
                "bug_title": "Selector case mismatch: #FirstName not found — use #firstName",
                "bug_severity": "Low",
            },
        ]
    },
    {
        "name": "neg_selector_inside_modal_before_open",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/modal-dialogs",
             "task": "Navigate to Modal Dialogs page. Modal is closed."},
            {
                "action": "verify_element_hidden",
                "selector": "#closeSmallModal",
                "task": "Verify the Close Small Modal button is present. "
                        "The modal has not been opened yet — this button should not be accessible.",
                "is_verify": True,
                "raises_bug": False,
                "value": "Close button inside closed modal — expected to be absent",
            },
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO TYPE 8: Dropdown / select_option (30 records)
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_DROPDOWN = [

    {
        "name": "dropdown_old_style_red",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/select-menu",
             "task": "Navigate to the Select Menu page."},
            {"action": "select_option", "selector": "#oldSelectMenu", "value": "Red",
             "task": "Select Red from the Old Style Select Menu dropdown."},
            {"action": "verify_input_value", "selector": "#oldSelectMenu", "value": "1",
             "task": "Verify Old Style Select Menu has Red (value=1) selected.", "is_verify": True},
        ]
    },
    {
        "name": "dropdown_old_style_blue",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/select-menu",
             "task": "Navigate to the Select Menu page."},
            {"action": "select_option", "selector": "#oldSelectMenu", "value": "Blue",
             "task": "Select Blue from the Old Style Select Menu dropdown."},
            {"action": "verify_input_value", "selector": "#oldSelectMenu", "value": "3",
             "task": "Verify Old Style Select Menu has Blue (value=3) selected.", "is_verify": True},
        ]
    },
    {
        "name": "dropdown_old_style_green",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/select-menu",
             "task": "Navigate to the Select Menu page."},
            {"action": "select_option", "selector": "#oldSelectMenu", "value": "Green",
             "task": "Select Green from the Old Style Select Menu dropdown."},
            {"action": "verify_input_value", "selector": "#oldSelectMenu", "value": "2",
             "task": "Verify Old Style Select Menu has Green (value=2) selected.", "is_verify": True},
        ]
    },
    {
        "name": "dropdown_cars_audi",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/select-menu",
             "task": "Navigate to the Select Menu page."},
            {"action": "scroll_down",
             "task": "Scroll down to bring the Cars multi-select into view."},
            {"action": "select_option", "selector": "#cars", "value": "Audi",
             "task": "Select Audi from the Cars select dropdown."},
            {"action": "verify_element_visible", "selector": "#cars",
             "task": "Verify the Cars dropdown is visible with Audi selected.", "is_verify": True},
        ]
    },
    {
        "name": "dropdown_verify_default",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/select-menu",
             "task": "Navigate to the Select Menu page."},
            {"action": "verify_element_visible", "selector": "#oldSelectMenu",
             "task": "Verify the Old Style Select Menu dropdown is visible on page load.",
             "is_verify": True},
            {"action": "verify_input_value", "selector": "#oldSelectMenu", "value": "",
             "task": "Verify the Select Menu defaults to no selection (empty value) on load.",
             "is_verify": True},
        ]
    },
    {
        "name": "dropdown_select_then_change",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/select-menu",
             "task": "Navigate to the Select Menu page."},
            {"action": "select_option", "selector": "#oldSelectMenu", "value": "Red",
             "task": "First, select Red from the dropdown."},
            {"action": "verify_input_value", "selector": "#oldSelectMenu", "value": "1",
             "task": "Verify Red (value=1) is selected.", "is_verify": True},
            {"action": "select_option", "selector": "#oldSelectMenu", "value": "Yellow",
             "task": "Change the selection from Red to Yellow."},
            {"action": "verify_input_value", "selector": "#oldSelectMenu", "value": "4",
             "task": "Verify the dropdown now shows Yellow (value=4) — previous selection overwritten.",
             "is_verify": True},
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO TYPE 9: Scroll + Find Element (30 records)
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_SCROLL = [

    {
        "name": "scroll_to_submit_button",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to Text Box form page."},
            {"action": "scroll_to_element", "selector": "#submit",
             "task": "Scroll the page to bring the Submit button into the visible viewport."},
            {"action": "verify_element_visible", "selector": "#submit",
             "task": "Verify the Submit button is now visible after scrolling.", "is_verify": True},
        ]
    },
    {
        "name": "scroll_to_permanent_address",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to Text Box form page."},
            {"action": "scroll_to_element", "selector": "#permanentAddress",
             "task": "Scroll to bring the Permanent Address textarea into view."},
            {"action": "verify_element_visible", "selector": "#permanentAddress",
             "task": "Verify Permanent Address field is visible after scrolling.", "is_verify": True},
            {"action": "clear_and_type", "selector": "#permanentAddress",
             "value": "Post Box 55, Remote Area",
             "task": "Now that it is visible, type Post Box 55, Remote Area in the Permanent Address field."},
            {"action": "verify_input_value", "selector": "#permanentAddress",
             "value": "Post Box 55, Remote Area",
             "task": "Verify Permanent Address contains Post Box 55, Remote Area.", "is_verify": True},
        ]
    },
    {
        "name": "scroll_down_then_up",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/automation-practice-form",
             "task": "Navigate to the long Automation Practice Form page."},
            {"action": "scroll_down",
             "task": "Scroll down to see the lower portion of the form."},
            {"action": "scroll_to_top",
             "task": "Scroll back to the top of the page."},
            {"action": "verify_element_visible", "selector": "#firstName",
             "task": "Verify the First Name field is visible after scrolling back to top.",
             "is_verify": True},
        ]
    },
    {
        "name": "scroll_find_below_fold",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/automation-practice-form",
             "task": "Navigate to Automation Practice Form."},
            {"action": "scroll_to_element", "selector": "#currentAddress",
             "task": "Scroll to the Current Address textarea which is below the fold."},
            {"action": "verify_element_visible", "selector": "#currentAddress",
             "task": "Verify Current Address textarea is now visible in viewport.", "is_verify": True},
            {"action": "clear_and_type", "selector": "#currentAddress",
             "value": "789 Test Street, Testville",
             "task": "Enter 789 Test Street, Testville in the Current Address field."},
        ]
    },
    {
        "name": "scroll_to_element_then_interact",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/select-menu",
             "task": "Navigate to Select Menu page."},
            {"action": "scroll_to_element", "selector": "#cars",
             "task": "Scroll down to bring the Cars select element into the viewport."},
            {"action": "verify_element_visible", "selector": "#cars",
             "task": "Verify the Cars select element is now visible.", "is_verify": True},
            {"action": "select_option", "selector": "#cars", "value": "Volvo",
             "task": "With Cars select now in view, select Volvo as the option."},
            {"action": "mark_step_pass",
             "value": "Scrolled to element and selected Volvo from Cars dropdown successfully.",
             "task": "Mark scroll + interact step as passed.", "is_verify": True},
        ]
    },
    {
        "name": "scroll_to_bottom_verify",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/automation-practice-form",
             "task": "Navigate to the long Automation Practice Form."},
            {"action": "scroll_to_bottom",
             "task": "Scroll to the very bottom of the page to find the Submit button."},
            {"action": "verify_element_visible", "selector": "#submit",
             "task": "Verify the Submit button is visible at the bottom of the form.",
             "is_verify": True},
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO TYPE 10: Navigation + wait_for_navigation (30 records)
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_NAVIGATION = [

    {
        "name": "nav_direct_url",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/alerts",
             "task": "Navigate directly to https://demoqa.com/alerts."},
            {"action": "verify_url_contains", "value": "alerts",
             "task": "Verify current URL contains 'alerts' confirming successful navigation.",
             "is_verify": True},
            {"action": "verify_page_title", "value": "DEMOQA",
             "task": "Verify the page title is DEMOQA.", "is_verify": True},
        ]
    },
    {
        "name": "nav_click_and_wait",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com",
             "task": "Navigate to DemoQA home page."},
            {"action": "click", "selector": "a[href*='checkbox']",
             "task": "Click the Check Box link in the sidebar to navigate to the Check Box page."},
            {"action": "wait_for_url_change", "value": "checkbox",
             "task": "Wait for the URL to change to the checkbox route after clicking the link."},
            {"action": "verify_url_contains", "value": "checkbox",
             "task": "Verify URL now contains checkbox confirming page transition complete.",
             "is_verify": True},
        ]
    },
    {
        "name": "nav_login_redirect",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo. Testing post-login redirect."},
            {"action": "clear_and_type", "selector": "#user-name", "value": "standard_user",
             "task": "Enter standard_user."},
            {"action": "clear_and_type", "selector": "#password", "value": "secret_sauce",
             "task": "Enter secret_sauce."},
            {"action": "click", "selector": "#login-button",
             "task": "Click Login. Expect redirect to /inventory.html."},
            {"action": "wait_for_url_change", "value": "inventory",
             "task": "Wait for URL to change to inventory route after successful login."},
            {"action": "verify_url_contains", "value": "inventory",
             "task": "Verify URL contains inventory confirming login redirect happened.",
             "is_verify": True},
        ]
    },
    {
        "name": "nav_back_button",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to Text Box page."},
            {"action": "navigate", "value": "https://demoqa.com/checkbox",
             "task": "Navigate forward to the Checkbox page."},
            {"action": "go_back",
             "task": "Click the browser back button to return to the previous page."},
            {"action": "verify_url_contains", "value": "text-box",
             "task": "Verify URL returned to text-box after pressing back.",
             "is_verify": True},
        ]
    },
    {
        "name": "nav_page_title_check",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo. Checking page title."},
            {"action": "verify_page_title", "value": "Swag Labs",
             "task": "Verify the page title is 'Swag Labs' for the SauceDemo login page.",
             "is_verify": True},
        ]
    },
    {
        "name": "nav_current_url_assertion",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/buttons",
             "task": "Navigate to DemoQA Buttons page."},
            {"action": "get_current_url",
             "task": "Get the current URL to confirm we are on the correct page."},
            {"action": "verify_url_contains", "value": "buttons",
             "task": "Verify current URL contains 'buttons' as expected.",
             "is_verify": True},
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO TYPE 11: Full End-to-End Flows (50 records)
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_E2E = [

    {
        "name": "e2e_complete_textbox_form",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "E2E Flow — Complete Text Box Form. Step 1: Navigate to form page."},
            {"action": "clear_and_type", "selector": "#userName", "value": "Diana Prince",
             "task": "Step 2: Enter Diana Prince in Full Name."},
            {"action": "verify_input_value", "selector": "#userName", "value": "Diana Prince",
             "task": "Step 3: Verify Full Name field.", "is_verify": True},
            {"action": "clear_and_type", "selector": "#userEmail", "value": "diana@hero.com",
             "task": "Step 4: Enter diana@hero.com in Email."},
            {"action": "verify_input_value", "selector": "#userEmail", "value": "diana@hero.com",
             "task": "Step 5: Verify Email field.", "is_verify": True},
            {"action": "clear_and_type", "selector": "#currentAddress",
             "value": "Themyscira Island, Atlantic Ocean",
             "task": "Step 6: Enter Themyscira Island, Atlantic Ocean in Current Address."},
            {"action": "verify_input_value", "selector": "#currentAddress",
             "value": "Themyscira Island, Atlantic Ocean",
             "task": "Step 7: Verify Current Address field.", "is_verify": True},
            {"action": "click", "selector": "#submit",
             "task": "Step 8: All fields complete. Click Submit."},
            {"action": "verify_text_present", "value": "Diana Prince",
             "task": "Step 9: Verify output shows Diana Prince.", "is_verify": True},
            {"action": "verify_text_present", "value": "diana@hero.com",
             "task": "Step 10: Verify output shows the email address.", "is_verify": True},
            {"action": "mark_step_pass",
             "value": "Full text-box form flow completed. All fields verified, form submitted, output confirmed.",
             "task": "Step 11: Mark entire form flow as passed.", "is_verify": True},
        ]
    },

    {
        "name": "e2e_login_browse_add_cart",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "E2E Flow — Login + Browse + Add to Cart. Step 1: Navigate to SauceDemo."},
            {"action": "clear_and_type", "selector": "#user-name", "value": "standard_user",
             "task": "Step 2: Enter standard_user in Username."},
            {"action": "clear_and_type", "selector": "#password", "value": "secret_sauce",
             "task": "Step 3: Enter secret_sauce in Password."},
            {"action": "click", "selector": "#login-button",
             "task": "Step 4: Click Login."},
            {"action": "verify_url_contains", "value": "inventory",
             "task": "Step 5: Verify login succeeded — URL shows inventory.", "is_verify": True},
            {"action": "verify_element_visible", "selector": ".inventory_list",
             "task": "Step 6: Verify inventory product list is visible.", "is_verify": True},
            {"action": "click", "selector": "#add-to-cart-sauce-labs-backpack",
             "task": "Step 7: Add Sauce Labs Backpack to cart."},
            {"action": "verify_element_visible", "selector": ".shopping_cart_badge",
             "task": "Step 8: Verify cart badge appears with item count.", "is_verify": True},
            {"action": "click", "selector": ".shopping_cart_link",
             "task": "Step 9: Click cart icon to go to the cart page."},
            {"action": "verify_url_contains", "value": "cart",
             "task": "Step 10: Verify URL contains cart confirming navigation to cart.", "is_verify": True},
            {"action": "verify_text_present", "value": "Sauce Labs Backpack",
             "task": "Step 11: Verify Sauce Labs Backpack is listed in the cart.", "is_verify": True},
            {"action": "mark_step_pass",
             "value": "Login → browse → add to cart → verify cart — full flow passed.",
             "task": "Step 12: Mark the full E2E flow as passed.", "is_verify": True},
        ]
    },

    {
        "name": "e2e_login_wrong_then_correct",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "E2E Flow — Failed login then successful retry. Step 1: Navigate."},
            {"action": "clear_and_type", "selector": "#user-name", "value": "wrong_user",
             "task": "Step 2: Enter wrong_user (intentionally wrong)."},
            {"action": "clear_and_type", "selector": "#password", "value": "wrong_pass",
             "task": "Step 3: Enter wrong_pass."},
            {"action": "click", "selector": "#login-button",
             "task": "Step 4: Click Login — this should fail."},
            {"action": "verify_element_visible", "selector": ".error-message-container",
             "task": "Step 5: Verify error message appears for bad credentials.", "is_verify": True},
            {"action": "clear_and_type", "selector": "#user-name", "value": "standard_user",
             "task": "Step 6: Clear and enter correct username standard_user."},
            {"action": "clear_and_type", "selector": "#password", "value": "secret_sauce",
             "task": "Step 7: Clear and enter correct password secret_sauce."},
            {"action": "click", "selector": "#login-button",
             "task": "Step 8: Click Login again with correct credentials."},
            {"action": "verify_url_contains", "value": "inventory",
             "task": "Step 9: Verify login succeeded this time.", "is_verify": True},
            {"action": "mark_step_pass",
             "value": "Login failure recovery flow passed — error shown, retry succeeded.",
             "task": "Step 10: Mark the full retry flow as passed.", "is_verify": True},
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO TYPE 12: [FLOW BLOCKED] Scenarios (30 records)
# Teaches model when to stop and raise a critical bug vs keep going
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_BLOCKED = [

    {
        "name": "blocked_login_page_missing",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo login page."},
            {
                "action": "verify_element_hidden",
                "selector": "#login-button",  # in a blocked scenario the button doesn't exist
                "task": "Verify the Login button is present on the login page. "
                        "If it is missing, the entire login flow is blocked and cannot continue.",
                "is_verify": True,
                "raises_bug": True,
                "value": "Login button (#login-button) to be present",
                "bug_title": "BLOCKER: Login button not found — entire login flow cannot proceed",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },
    {
        "name": "blocked_form_submit_missing",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/text-box",
             "task": "Navigate to Text Box form page."},
            {"action": "clear_and_type", "selector": "#userName", "value": "Test User",
             "task": "Enter Test User in Full Name — preparing to submit form."},
            {
                "action": "verify_element_hidden",
                "selector": "#submitButton",   # wrong selector — real is #submit
                "task": "Verify the Submit button (#submitButton) is present. "
                        "Cannot complete form submission without it — flow would be blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "Submit button to be findable by selector #submitButton",
                "bug_title": "BLOCKER: Submit button #submitButton not found — form cannot be submitted",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },
    {
        "name": "blocked_inventory_not_loaded",
        "steps": [
            {"action": "navigate", "value": "https://www.saucedemo.com",
             "task": "Navigate to SauceDemo. Running checkout flow."},
            {"action": "clear_and_type", "selector": "#user-name", "value": "standard_user",
             "task": "Enter standard_user."},
            {"action": "clear_and_type", "selector": "#password", "value": "secret_sauce",
             "task": "Enter secret_sauce."},
            {"action": "click", "selector": "#login-button",
             "task": "Click Login."},
            {
                "action": "verify_element_hidden",
                "selector": ".inventory_container",
                "task": "Verify the inventory container loaded. If not visible after login, "
                        "this is a critical bug blocking the entire checkout flow.",
                "is_verify": True,
                "raises_bug": True,
                "value": "inventory container to load after login",
                "bug_title": "BLOCKER: Inventory container not visible after login — checkout flow blocked",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },
    {
        "name": "blocked_required_field_absent",
        "steps": [
            {"action": "navigate", "value": "https://demoqa.com/automation-practice-form",
             "task": "Navigate to Automation Practice Form. Verifying required fields exist."},
            {
                "action": "verify_element_hidden",
                "selector": "#dateOfBirthInput",
                "task": "Verify the Date of Birth field is present — it is required for form completion. "
                        "If missing, the entire registration flow is blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "Date of Birth input field",
                "bug_title": "BLOCKER: Date of Birth field #dateOfBirthInput not found — registration form is incomplete",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# MASTER FLOW LIST — imported by aegis_dataset_generator.py
# ─────────────────────────────────────────────────────────────────────────────

ALL_FLOWS = (
    FLOWS_FORM_SINGLE
    + FLOWS_FORM_SINGLE_VARIANTS
    + FLOWS_FORM_MULTI
    + FLOWS_CLICK_WAIT
    + FLOWS_COLOR_PASS
    + FLOWS_COLOR_FAIL
    + FLOWS_VISIBILITY
    + FLOWS_NEGATIVE_SELECTOR
    + FLOWS_DROPDOWN
    + FLOWS_SCROLL
    + FLOWS_NAVIGATION
    + FLOWS_E2E
    + FLOWS_BLOCKED
)

if __name__ == "__main__":
    # Count records (each step = 1 record)
    by_type = {
        "form_single": FLOWS_FORM_SINGLE + FLOWS_FORM_SINGLE_VARIANTS,
        "form_multi": FLOWS_FORM_MULTI,
        "click_wait": FLOWS_CLICK_WAIT,
        "color_pass": FLOWS_COLOR_PASS,
        "color_fail": FLOWS_COLOR_FAIL,
        "visibility": FLOWS_VISIBILITY,
        "negative": FLOWS_NEGATIVE_SELECTOR,
        "dropdown": FLOWS_DROPDOWN,
        "scroll": FLOWS_SCROLL,
        "navigation": FLOWS_NAVIGATION,
        "e2e": FLOWS_E2E,
        "blocked": FLOWS_BLOCKED,
    }
    total = 0
    print(f"{'Scenario Type':<25} {'Flows':>6} {'Steps/Records':>14}")
    print("-" * 50)
    for name, flows in by_type.items():
        steps = sum(len(f["steps"]) for f in flows)
        total += steps
        print(f"{name:<25} {len(flows):>6} {steps:>14}")
    print("-" * 50)
    print(f"{'TOTAL':<25} {sum(len(v) for v in by_type.values()):>6} {total:>14}")