"""
AEGIS FLOWS — New Sites Extension
===================================
Adds ~150 records across 3 new sites to increase DOM diversity
and reduce overfitting to DemoQA/SauceDemo patterns.

Sites added:
  1. the-internet.herokuapp.com  — stable, great edge-case coverage
  2. practice.expandtesting.com  — clean forms, different DOM structure
  3. uitestingplayground.com     — built to challenge automation tools

Run standalone to check record counts:
  python3 aegis_flows_new_sites.py

To use: import ALL_NEW_FLOWS and append to your ALL_FLOWS list in aegis_flows.py,
or run aegis_generator_extended.py which imports both.
"""

# ─────────────────────────────────────────────────────────────────────────────
# SITE 1: the-internet.herokuapp.com
# Stable Heroku app with a wide variety of interaction patterns.
# Teaches: hover menus, file upload UI, sortable tables, basic auth UI,
#          dynamic content, iframe text, key presses, floating menus.
# Target: ~55 records
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_HEROKUAPP_FORMS = [

    # Login page — different DOM from SauceDemo, uses Flask/Sinatra style
    {
        "name": "herald_login_valid",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/login",
             "task": "Navigate to The Internet login page."},
            {"action": "clear_and_type", "selector": "#username", "value": "tomsmith",
             "task": "Enter tomsmith in the Username field."},
            {"action": "verify_input_value", "selector": "#username", "value": "tomsmith",
             "task": "Verify Username field contains tomsmith.", "is_verify": True},
            {"action": "clear_and_type", "selector": "#password", "value": "SuperSecretPassword!",
             "task": "Enter SuperSecretPassword! in the Password field."},
            {"action": "click", "selector": "button[type='submit']",
             "task": "Click the Login button to submit credentials."},
            {"action": "verify_url_contains", "value": "secure",
             "task": "Verify URL contains 'secure' confirming successful login redirect.",
             "is_verify": True},
            {"action": "verify_text_present", "value": "You logged into a secure area!",
             "task": "Verify the success flash message appears after login.",
             "is_verify": True},
        ]
    },

    {
        "name": "herald_login_invalid_raises_bug",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/login",
             "task": "Navigate to The Internet login page. Testing invalid credentials."},
            {"action": "clear_and_type", "selector": "#username", "value": "wronguser",
             "task": "Enter wronguser in the Username field."},
            {"action": "clear_and_type", "selector": "#password", "value": "wrongpass",
             "task": "Enter wrongpass in the Password field."},
            {"action": "click", "selector": "button[type='submit']",
             "task": "Click Login with invalid credentials — expecting error message."},
            {"action": "verify_element_visible", "selector": "#flash.error",
             "task": "Verify the error flash message is visible after failed login.",
             "is_verify": True},
            {"action": "verify_text_present", "value": "Your username is invalid!",
             "task": "Verify the error text confirms invalid credentials were rejected.",
             "is_verify": True},
        ]
    },

    {
        "name": "herald_login_then_logout",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/login",
             "task": "Navigate to The Internet login page."},
            {"action": "clear_and_type", "selector": "#username", "value": "tomsmith",
             "task": "Enter tomsmith in the Username field."},
            {"action": "clear_and_type", "selector": "#password", "value": "SuperSecretPassword!",
             "task": "Enter SuperSecretPassword! in the Password field."},
            {"action": "click", "selector": "button[type='submit']",
             "task": "Click Login to access the secure area."},
            {"action": "verify_url_contains", "value": "secure",
             "task": "Verify login succeeded — URL contains 'secure'.", "is_verify": True},
            {"action": "click", "selector": "a[href='/logout']",
             "task": "Click the Logout link to end the session."},
            {"action": "verify_url_contains", "value": "login",
             "task": "Verify URL returned to login page after logout.", "is_verify": True},
            {"action": "verify_text_present", "value": "You logged out of the secure area!",
             "task": "Verify the logout success message appears.", "is_verify": True},
        ]
    },
]

FLOWS_HEROKUAPP_INTERACTIONS = [

    # Checkboxes — different from DemoQA checkbox (plain HTML checkboxes)
    {
        "name": "herald_checkbox_check_uncheck",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/checkboxes",
             "task": "Navigate to the Checkboxes page."},
            {"action": "verify_element_visible", "selector": "form#checkboxes",
             "task": "Verify the checkboxes form is visible on the page.", "is_verify": True},
            {"action": "click", "selector": "input[type='checkbox']:first-of-type",
             "task": "Click the first checkbox to toggle its checked state."},
            {"action": "verify_element_visible", "selector": "input[type='checkbox']:first-of-type",
             "task": "Verify the first checkbox element is still present after toggle.", "is_verify": True},
            {"action": "click", "selector": "input[type='checkbox']:last-of-type",
             "task": "Click the second (already checked) checkbox to uncheck it."},
            {"action": "mark_step_pass", "value": "Both checkboxes toggled successfully.",
             "task": "Mark checkbox interaction flow as passed.", "is_verify": True},
        ]
    },

    # Hover — teaches hover interaction
    {
        "name": "herald_hover_reveal_user_info",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/hovers",
             "task": "Navigate to the Hovers page to test hover reveal behavior."},
            {"action": "verify_element_visible", "selector": ".figure",
             "task": "Verify user figure elements are visible on the page.", "is_verify": True},
            {"action": "hover", "selector": ".figure:first-of-type img",
             "task": "Hover over the first user avatar to reveal hidden info."},
            {"action": "verify_element_visible", "selector": ".figure:first-of-type .figcaption",
             "task": "Verify the hidden caption/info appears after hovering.", "is_verify": True},
            {"action": "verify_text_present", "value": "user1",
             "task": "Verify the revealed info contains 'user1' as expected.", "is_verify": True},
        ]
    },

    # Dropdown — native HTML select, different site context
    {
        "name": "herald_dropdown_select_option1",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/dropdown",
             "task": "Navigate to the Dropdown page."},
            {"action": "verify_element_visible", "selector": "#dropdown",
             "task": "Verify the dropdown element is present on the page.", "is_verify": True},
            {"action": "select_option", "selector": "#dropdown", "value": "Option 1",
             "task": "Select Option 1 from the dropdown list."},
            {"action": "verify_input_value", "selector": "#dropdown", "value": "1",
             "task": "Verify Option 1 (value=1) is now selected in the dropdown.", "is_verify": True},
        ]
    },

    {
        "name": "herald_dropdown_select_option2",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/dropdown",
             "task": "Navigate to the Dropdown page."},
            {"action": "select_option", "selector": "#dropdown", "value": "Option 2",
             "task": "Select Option 2 from the dropdown list."},
            {"action": "verify_input_value", "selector": "#dropdown", "value": "2",
             "task": "Verify Option 2 (value=2) is now selected.", "is_verify": True},
        ]
    },

    {
        "name": "herald_dropdown_change_selection",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/dropdown",
             "task": "Navigate to the Dropdown page."},
            {"action": "select_option", "selector": "#dropdown", "value": "Option 1",
             "task": "First, select Option 1."},
            {"action": "verify_input_value", "selector": "#dropdown", "value": "1",
             "task": "Verify Option 1 is selected.", "is_verify": True},
            {"action": "select_option", "selector": "#dropdown", "value": "Option 2",
             "task": "Now change the selection to Option 2."},
            {"action": "verify_input_value", "selector": "#dropdown", "value": "2",
             "task": "Verify the selection changed to Option 2 — previous value overwritten.",
             "is_verify": True},
        ]
    },

    # Add/Remove Elements — dynamic DOM, tests element appear/disappear
    {
        "name": "herald_add_remove_single",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/add_remove_elements/",
             "task": "Navigate to the Add/Remove Elements page."},
            {"action": "verify_element_hidden", "selector": ".added-manually",
             "task": "Verify no Delete buttons are present before any elements are added.",
             "is_verify": True},
            {"action": "click", "selector": "button[onclick='addElement()']",
             "task": "Click Add Element button to dynamically add a Delete button to the page."},
            {"action": "verify_element_visible", "selector": ".added-manually",
             "task": "Verify the newly added Delete button is now visible.", "is_verify": True},
        ]
    },

    {
        "name": "herald_add_multiple_then_remove",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/add_remove_elements/",
             "task": "Navigate to the Add/Remove Elements page."},
            {"action": "click", "selector": "button[onclick='addElement()']",
             "task": "Step 1: Click Add Element — adds first Delete button."},
            {"action": "click", "selector": "button[onclick='addElement()']",
             "task": "Step 2: Click Add Element again — adds a second Delete button."},
            {"action": "verify_element_visible", "selector": ".added-manually",
             "task": "Verify at least one Delete button is visible after adding elements.",
             "is_verify": True},
            {"action": "click", "selector": ".added-manually",
             "task": "Step 3: Click first Delete button to remove it."},
            {"action": "mark_step_pass", "value": "Add/remove element multi-step flow completed.",
             "task": "Mark the add/remove flow as passed.", "is_verify": True},
        ]
    },

    # Key Presses — teaches press_key tool
    {
        "name": "herald_key_press_enter",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/key_presses",
             "task": "Navigate to the Key Presses page."},
            {"action": "click", "selector": "#target",
             "task": "Click the input field to focus it."},
            {"action": "press_key", "value": "Enter",
             "task": "Press the Enter key while the input field is focused."},
            {"action": "verify_text_present", "value": "ENTER",
             "task": "Verify the result text shows ENTER confirming the key press was detected.",
             "is_verify": True},
        ]
    },

    {
        "name": "herald_key_press_tab",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/key_presses",
             "task": "Navigate to the Key Presses page."},
            {"action": "click", "selector": "#target",
             "task": "Click the input field to set focus."},
            {"action": "press_key", "value": "Tab",
             "task": "Press Tab key to move focus and trigger key press detection."},
            {"action": "verify_text_present", "value": "TAB",
             "task": "Verify result text shows TAB confirming Tab key was registered.",
             "is_verify": True},
        ]
    },

    # Notification Message — different page, tests flash message visibility
    {
        "name": "herald_notification_message_visible",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/notification_message_rendered",
             "task": "Navigate to the Notification Message page."},
            {"action": "click", "selector": "a[href='/notification_message']",
             "task": "Click the link to trigger a notification message."},
            {"action": "verify_element_visible", "selector": "#flash",
             "task": "Verify the notification flash message is visible after the click.",
             "is_verify": True},
        ]
    },

    # Disappearing Elements — dynamic nav items, teaches checking element presence
    {
        "name": "herald_disappearing_elements_check",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/disappearing_elements",
             "task": "Navigate to the Disappearing Elements page — nav items randomly appear/disappear."},
            {"action": "verify_element_visible", "selector": "nav ul",
             "task": "Verify the navigation list is visible on the page.", "is_verify": True},
            {"action": "verify_element_visible", "selector": "a[href='/']",
             "task": "Verify the Home link is present in the nav (stable element).",
             "is_verify": True},
        ]
    },

    # Infinite Scroll — teaches scroll + wait for new content
    {
        "name": "herald_scroll_infinite_content",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/infinite_scroll",
             "task": "Navigate to the Infinite Scroll page."},
            {"action": "verify_element_visible", "selector": ".jscroll-added",
             "task": "Verify initial content paragraph is visible.", "is_verify": True},
            {"action": "scroll_to_bottom",
             "task": "Scroll to the bottom of the page to trigger loading of additional content."},
            {"action": "mark_step_pass", "value": "Scrolled to bottom of infinite scroll page.",
             "task": "Mark infinite scroll step as passed.", "is_verify": True},
        ]
    },
]

FLOWS_HEROKUAPP_NEGATIVE = [

    # Negative: element that appears only after delay — don't hallucinate it early
    {
        "name": "herald_neg_element_not_loaded_yet",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/dynamic_loading/1",
             "task": "Navigate to Dynamic Loading page where element is hidden until Start is clicked."},
            {
                "action": "verify_element_hidden",
                "selector": "#finish h4",
                "task": "Verify the 'Hello World!' finish text is NOT yet visible — it only appears after clicking Start.",
                "is_verify": True,
                "raises_bug": False,
                "value": "element not visible yet",
            },
        ]
    },

    {
        "name": "herald_neg_secure_page_without_login",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/login",
             "task": "Navigate to login page. We will NOT log in — testing unauthenticated access."},
            {
                "action": "verify_element_hidden",
                "selector": "a[href='/logout']",
                "task": "Verify the Logout link is NOT visible — user is not authenticated yet.",
                "is_verify": True,
                "raises_bug": False,
                "value": "Logout link absent when unauthenticated",
            },
        ]
    },

    {
        "name": "herald_neg_stale_selector_raises_bug",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/login",
             "task": "Navigate to login page."},
            {
                "action": "verify_element_hidden",
                "selector": "#signin-button",   # wrong — real is button[type='submit']
                "task": "Verify element #signin-button is present on the login page. "
                        "This selector does not exist — the correct element is button[type='submit'].",
                "is_verify": True,
                "raises_bug": True,
                "value": "#signin-button element",
                "bug_title": "Selector #signin-button not found — actual login button is button[type='submit']",
                "bug_severity": "Medium",
            },
        ]
    },

    {
        "name": "herald_neg_flash_absent_before_action",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/login",
             "task": "Navigate to login page. No flash message should be present yet."},
            {
                "action": "verify_element_hidden",
                "selector": "#flash",
                "task": "Verify no flash message is visible before any login attempt.",
                "is_verify": True,
                "raises_bug": False,
                "value": "no flash message before login",
            },
        ]
    },
]

FLOWS_HEROKUAPP_BLOCKED = [

    {
        "name": "herald_blocked_login_form_missing",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/login",
             "task": "Navigate to login page. Verifying form is present before entering credentials."},
            {
                "action": "verify_element_hidden",
                "selector": "#login",  # correct — but treated as blocked scenario
                "task": "Verify the login form (#login) is present. "
                        "If missing, the authentication flow is completely blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "login form (#login) to be present",
                "bug_title": "BLOCKER: Login form #login not found — authentication flow blocked",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },

    {
        "name": "herald_blocked_wrong_submit_selector",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/login",
             "task": "Navigate to The Internet login page."},
            {"action": "clear_and_type", "selector": "#username", "value": "tomsmith",
             "task": "Enter tomsmith in the Username field."},
            {"action": "clear_and_type", "selector": "#password", "value": "SuperSecretPassword!",
             "task": "Enter the password."},
            {
                "action": "verify_element_hidden",
                "selector": "button#login-btn",  # wrong selector
                "task": "Verify the login submit button (button#login-btn) is present. "
                        "Cannot complete login without a submit button — flow is blocked if missing.",
                "is_verify": True,
                "raises_bug": True,
                "value": "submit button button#login-btn",
                "bug_title": "BLOCKER: Login submit button not found by selector button#login-btn",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# SITE 2: practice.expandtesting.com
# Clean, purpose-built practice site. Very different DOM patterns from DemoQA.
# No ads, stable, great for login/form/note-taking flows.
# Target: ~50 records
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_EXPANDTESTING_FORMS = [

    {
        "name": "expand_login_valid",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/login",
             "task": "Navigate to the Expand Testing login page."},
            {"action": "verify_element_visible", "selector": "#username",
             "task": "Verify the Username input field is visible.", "is_verify": True},
            {"action": "clear_and_type", "selector": "#username", "value": "practice",
             "task": "Enter practice in the Username field."},
            {"action": "verify_input_value", "selector": "#username", "value": "practice",
             "task": "Verify Username field contains 'practice'.", "is_verify": True},
            {"action": "clear_and_type", "selector": "#password", "value": "SuperSecretPassword!",
             "task": "Enter SuperSecretPassword! in the Password field."},
            {"action": "click", "selector": "button[type='submit']",
             "task": "Click the Login button to submit credentials."},
            {"action": "verify_url_contains", "value": "secure",
             "task": "Verify URL contains 'secure' confirming successful login.", "is_verify": True},
            {"action": "verify_text_present", "value": "You logged into a secure area!",
             "task": "Verify success flash message is shown after login.", "is_verify": True},
        ]
    },

    {
        "name": "expand_login_empty_fields",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/login",
             "task": "Navigate to Expand Testing login. Testing empty field submission."},
            {"action": "click", "selector": "button[type='submit']",
             "task": "Click Login without entering any credentials — testing empty form submission."},
            {"action": "verify_element_visible", "selector": "#flash",
             "task": "Verify an error flash message appears after empty form submission.",
             "is_verify": True},
        ]
    },

    {
        "name": "expand_login_wrong_password",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/login",
             "task": "Navigate to Expand Testing login. Testing wrong password."},
            {"action": "clear_and_type", "selector": "#username", "value": "practice",
             "task": "Enter the correct username: practice."},
            {"action": "clear_and_type", "selector": "#password", "value": "wrongpassword",
             "task": "Enter an incorrect password: wrongpassword."},
            {"action": "click", "selector": "button[type='submit']",
             "task": "Click Login — this should fail due to wrong password."},
            {"action": "verify_element_visible", "selector": "#flash.error",
             "task": "Verify error flash message appears for wrong password.", "is_verify": True},
            {"action": "verify_text_present", "value": "Your password is invalid!",
             "task": "Verify error message states the password is invalid.", "is_verify": True},
        ]
    },

    {
        "name": "expand_login_then_logout",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/login",
             "task": "Navigate to Expand Testing login page."},
            {"action": "clear_and_type", "selector": "#username", "value": "practice",
             "task": "Enter practice in the Username field."},
            {"action": "clear_and_type", "selector": "#password", "value": "SuperSecretPassword!",
             "task": "Enter SuperSecretPassword! in the Password field."},
            {"action": "click", "selector": "button[type='submit']",
             "task": "Click Login to authenticate."},
            {"action": "verify_url_contains", "value": "secure",
             "task": "Verify login succeeded.", "is_verify": True},
            {"action": "click", "selector": "a[href='/logout']",
             "task": "Click the Logout link."},
            {"action": "verify_text_present", "value": "You logged out of the secure area!",
             "task": "Verify logout success message is shown.", "is_verify": True},
        ]
    },
]

FLOWS_EXPANDTESTING_INPUTS = [

    {
        "name": "expand_inputs_text_entry",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/inputs",
             "task": "Navigate to the Inputs page."},
            {"action": "verify_element_visible", "selector": "input[type='number']",
             "task": "Verify the number input field is visible on the page.", "is_verify": True},
            {"action": "clear_and_type", "selector": "input[type='number']", "value": "42",
             "task": "Enter the number 42 into the number input field."},
            {"action": "verify_input_value", "selector": "input[type='number']", "value": "42",
             "task": "Verify the input field contains 42.", "is_verify": True},
        ]
    },

    {
        "name": "expand_inputs_key_interaction",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/inputs",
             "task": "Navigate to the Inputs page."},
            {"action": "click", "selector": "input[type='number']",
             "task": "Click to focus the number input field."},
            {"action": "clear_and_type", "selector": "input[type='number']", "value": "10",
             "task": "Enter 10 in the number input field."},
            {"action": "press_key", "value": "ArrowUp",
             "task": "Press the ArrowUp key to increment the number input value by 1."},
            {"action": "mark_step_pass", "value": "Key interaction on number input completed.",
             "task": "Mark key press on input field as passed.", "is_verify": True},
        ]
    },

    {
        "name": "expand_checkboxes_toggle",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/checkboxes",
             "task": "Navigate to the Checkboxes page on Expand Testing."},
            {"action": "verify_element_visible", "selector": "input[type='checkbox']",
             "task": "Verify checkbox elements are present on the page.", "is_verify": True},
            {"action": "click", "selector": "input[type='checkbox']:first-of-type",
             "task": "Click the first checkbox to toggle its state."},
            {"action": "mark_step_pass", "value": "First checkbox toggled on Expand Testing.",
             "task": "Mark checkbox toggle step as passed.", "is_verify": True},
        ]
    },

    {
        "name": "expand_dropdown_select",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/dropdown",
             "task": "Navigate to the Dropdown page on Expand Testing."},
            {"action": "verify_element_visible", "selector": "#dropdown",
             "task": "Verify the dropdown element is visible.", "is_verify": True},
            {"action": "select_option", "selector": "#dropdown", "value": "Option 1",
             "task": "Select Option 1 from the Expand Testing dropdown."},
            {"action": "verify_input_value", "selector": "#dropdown", "value": "1",
             "task": "Verify Option 1 (value=1) is selected.", "is_verify": True},
        ]
    },

    {
        "name": "expand_textarea_entry",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/tinymce",
             "task": "Navigate to the TinyMCE editor page on Expand Testing."},
            {"action": "verify_element_visible", "selector": ".tox-tinymce",
             "task": "Verify the TinyMCE editor container is visible on the page.", "is_verify": True},
            {"action": "mark_step_pass", "value": "TinyMCE editor loaded and visible.",
             "task": "Mark TinyMCE visibility check as passed.", "is_verify": True},
        ]
    },
]

FLOWS_EXPANDTESTING_NAVIGATION = [

    {
        "name": "expand_nav_to_about",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com",
             "task": "Navigate to the Expand Testing home page."},
            {"action": "verify_url_contains", "value": "expandtesting",
             "task": "Verify we are on the Expand Testing domain.", "is_verify": True},
            {"action": "verify_element_visible", "selector": "h1",
             "task": "Verify the main heading is visible on the home page.", "is_verify": True},
        ]
    },

    {
        "name": "expand_nav_login_page_elements",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/login",
             "task": "Navigate to the login page to verify all required elements are present."},
            {"action": "verify_element_visible", "selector": "#username",
             "task": "Verify Username field is present.", "is_verify": True},
            {"action": "verify_element_visible", "selector": "#password",
             "task": "Verify Password field is present.", "is_verify": True},
            {"action": "verify_element_visible", "selector": "button[type='submit']",
             "task": "Verify Login submit button is present.", "is_verify": True},
            {"action": "mark_step_pass",
             "value": "All required login form elements are present and visible.",
             "task": "Mark login page element check as passed.", "is_verify": True},
        ]
    },

    {
        "name": "expand_verify_page_title_login",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/login",
             "task": "Navigate to the Expand Testing login page."},
            {"action": "verify_page_title", "value": "Practice Test Login Page",
             "task": "Verify the page title is 'Practice Test Login Page'.", "is_verify": True},
        ]
    },
]

FLOWS_EXPANDTESTING_NEGATIVE = [

    {
        "name": "expand_neg_wrong_selector",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/login",
             "task": "Navigate to Expand Testing login page."},
            {
                "action": "verify_element_hidden",
                "selector": "#user-name",  # wrong — DemoQA/SauceDemo selector leaked in
                "task": "Verify element #user-name is present on Expand Testing login page. "
                        "This selector belongs to another site and should NOT exist here.",
                "is_verify": True,
                "raises_bug": True,
                "value": "#user-name element (cross-site selector contamination)",
                "bug_title": "Wrong selector: #user-name not found — correct selector is #username on this site",
                "bug_severity": "Medium",
            },
        ]
    },

    {
        "name": "expand_neg_logout_absent_before_login",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/login",
             "task": "Navigate to login page. User is not logged in."},
            {
                "action": "verify_element_hidden",
                "selector": "a[href='/logout']",
                "task": "Verify Logout link is NOT visible — user has not logged in yet.",
                "is_verify": True,
                "raises_bug": False,
                "value": "Logout link should be absent when unauthenticated",
            },
        ]
    },

    {
        "name": "expand_neg_error_absent_before_submit",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/login",
             "task": "Navigate to login page. No error should be visible yet."},
            {
                "action": "verify_element_hidden",
                "selector": "#flash.error",
                "task": "Verify no error flash message is visible before any login attempt.",
                "is_verify": True,
                "raises_bug": False,
                "value": "error flash absent before form submission",
            },
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# SITE 3: uitestingplayground.com
# Specifically designed to challenge automation tools with:
# - Dynamic IDs that change on every page load
# - Overlapping/obscured elements
# - Animations and load delays
# - Shadow DOM and async content
# This teaches the model to use visual + DOM together, not rely on IDs alone.
# Target: ~45 records
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_UITESTINGPLAYGROUND_CLICKS = [

    # Click — primary click test on a stable button
    {
        "name": "uitpg_click_button",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/click",
             "task": "Navigate to the UI Testing Playground Click test page."},
            {"action": "verify_element_visible", "selector": "#ajaxButton",
             "task": "Verify the AJAX button is present and visible on the page.", "is_verify": True},
            {"action": "click", "selector": "#ajaxButton",
             "task": "Click the AJAX button — page will make an async request before showing success."},
            {"action": "wait_for_element", "selector": ".bg-success",
             "task": "Wait for the success element to appear after AJAX completes."},
            {"action": "verify_element_visible", "selector": ".bg-success",
             "task": "Verify the success state element is visible after AJAX button click.",
             "is_verify": True},
        ]
    },

    # Dynamic ID — button has random ID on every load. Model must NOT rely on ID.
    {
        "name": "uitpg_dynamic_id_click",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/dynamicid",
             "task": "Navigate to the Dynamic ID page — button ID changes on every page load."},
            {"action": "verify_element_visible", "selector": "button.btn-primary",
             "task": "Verify the primary button is visible — use class, NOT ID, since ID is random.",
             "is_verify": True},
            {"action": "click", "selector": "button.btn-primary",
             "task": "Click the button using its stable class selector, not the dynamic ID."},
            {"action": "mark_step_pass",
             "value": "Dynamic ID button clicked using stable class selector — not relying on random ID.",
             "task": "Mark dynamic ID click as passed.", "is_verify": True},
        ]
    },

    # Class attribute — button with same text but different classes
    {
        "name": "uitpg_class_attribute_click",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/classattr",
             "task": "Navigate to the Class Attribute page — buttons look similar but have different classes."},
            {"action": "verify_element_visible", "selector": ".btn-primary",
             "task": "Verify the primary (blue) button is visible.", "is_verify": True},
            {"action": "click", "selector": ".btn-primary",
             "task": "Click the primary class button, NOT the warning or success button."},
            {"action": "mark_step_pass",
             "value": "Correct button identified and clicked by class attribute.",
             "task": "Mark class attribute test as passed.", "is_verify": True},
        ]
    },

    # Hidden layers — element is covered by another element
    {
        "name": "uitpg_overlapped_element",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/overlapped",
             "task": "Navigate to the Overlapped Element page — input is partially hidden by a floating header."},
            {"action": "scroll_to_element", "selector": "#id",
             "task": "Scroll the Name input field into clear view to avoid the overlapping header."},
            {"action": "verify_element_visible", "selector": "#id",
             "task": "Verify the ID input field is now visible after scrolling.", "is_verify": True},
            {"action": "clear_and_type", "selector": "#id", "value": "test-user-001",
             "task": "Type test-user-001 into the ID field now that it is in view."},
            {"action": "verify_input_value", "selector": "#id", "value": "test-user-001",
             "task": "Verify the ID field contains test-user-001.", "is_verify": True},
        ]
    },

    {
        "name": "uitpg_overlapped_name_field",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/overlapped",
             "task": "Navigate to the Overlapped Element page."},
            {"action": "scroll_to_element", "selector": "#name",
             "task": "Scroll to bring the Name field into view (clear of overlapping element)."},
            {"action": "clear_and_type", "selector": "#name", "value": "Jane Automation",
             "task": "Enter Jane Automation in the Name field."},
            {"action": "verify_input_value", "selector": "#name", "value": "Jane Automation",
             "task": "Verify Name field contains Jane Automation.", "is_verify": True},
        ]
    },
]

FLOWS_UITESTINGPLAYGROUND_WAITS = [

    # Load delay — button only appears after delay
    {
        "name": "uitpg_load_delay_button",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/loaddelay",
             "task": "Navigate to the Load Delay page — button appears after a 3-second delay."},
            {"action": "wait_for_element", "selector": "button.btn-primary",
             "task": "Wait for the delayed button to appear in the DOM before interacting."},
            {"action": "verify_element_visible", "selector": "button.btn-primary",
             "task": "Verify the button is now visible after the load delay.", "is_verify": True},
            {"action": "click", "selector": "button.btn-primary",
             "task": "Click the button now that it has appeared."},
            {"action": "mark_step_pass", "value": "Load delay button clicked after waiting for it to appear.",
             "task": "Mark delayed button interaction as passed.", "is_verify": True},
        ]
    },

    # AJAX data — content loads asynchronously
    {
        "name": "uitpg_ajax_data_load",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/ajax",
             "task": "Navigate to AJAX Data page — content loads asynchronously after 15 seconds."},
            {"action": "verify_element_visible", "selector": "#ajaxButton",
             "task": "Verify the trigger button is visible before clicking.", "is_verify": True},
            {"action": "click", "selector": "#ajaxButton",
             "task": "Click the button to trigger the AJAX request."},
            {"action": "wait_for_element", "selector": ".bg-success",
             "task": "Wait for the success element to appear once AJAX completes."},
            {"action": "verify_element_visible", "selector": ".bg-success",
             "task": "Verify the AJAX success state is now visible.", "is_verify": True},
        ]
    },

    # Client-side delay — button is disabled then re-enabled after timeout
    {
        "name": "uitpg_client_side_delay",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/clientdelay",
             "task": "Navigate to Client-Side Delay page — button is disabled for 15 seconds."},
            {"action": "verify_element_visible", "selector": "#ajaxButton",
             "task": "Verify the button is present on the page.", "is_verify": True},
            {"action": "click", "selector": "#ajaxButton",
             "task": "Click the button to start the client-side delay timer."},
            {"action": "wait_for_element", "selector": ".bg-success",
             "task": "Wait for the success element to appear after the client-side delay completes."},
            {"action": "verify_element_visible", "selector": ".bg-success",
             "task": "Verify success state is visible after client-side delay resolved.",
             "is_verify": True},
        ]
    },
]

FLOWS_UITESTINGPLAYGROUND_VISIBILITY = [

    {
        "name": "uitpg_visibility_hidden_element",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/visibility",
             "task": "Navigate to the Visibility page — some buttons are hidden, removed, or zero-opacity."},
            {"action": "verify_element_visible", "selector": "#hideButton",
             "task": "Verify the 'Hide' button is visible on page load.", "is_verify": True},
            {"action": "click", "selector": "#hideButton",
             "task": "Click the Hide button to trigger visibility changes on other elements."},
            {"action": "verify_element_hidden", "selector": "#removedButton",
             "task": "Verify the 'Removed' button is no longer visible after clicking Hide.",
             "is_verify": True},
        ]
    },

    {
        "name": "uitpg_visibility_check_initial_state",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/visibility",
             "task": "Navigate to the Visibility page. Checking initial element states."},
            {"action": "verify_element_visible", "selector": "#transparentButton",
             "task": "Verify the transparent button is present in DOM before hiding.",
             "is_verify": True},
            {"action": "verify_element_visible", "selector": "#overlappedButton",
             "task": "Verify the overlapped button is present in DOM initially.",
             "is_verify": True},
            {"action": "verify_element_visible", "selector": "#zeroWidthButton",
             "task": "Verify the zero-width button is present in DOM initially.",
             "is_verify": True},
        ]
    },
]

FLOWS_UITESTINGPLAYGROUND_SCROLL = [

    {
        "name": "uitpg_scroll_and_find",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/scrollbars",
             "task": "Navigate to the Scrollbars page."},
            {"action": "scroll_to_element", "selector": "#hidingButton",
             "task": "Scroll to find the hidden button that requires scrolling to reach."},
            {"action": "verify_element_visible", "selector": "#hidingButton",
             "task": "Verify the button is now visible after scrolling.", "is_verify": True},
            {"action": "click", "selector": "#hidingButton",
             "task": "Click the button now that it is in the viewport."},
            {"action": "mark_step_pass", "value": "Scrolled to and clicked the hidden button.",
             "task": "Mark scrollbar test as passed.", "is_verify": True},
        ]
    },

    {
        "name": "uitpg_scroll_top_bottom",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/",
             "task": "Navigate to UI Testing Playground home page."},
            {"action": "scroll_to_bottom",
             "task": "Scroll to the bottom of the page."},
            {"action": "scroll_to_top",
             "task": "Scroll back to the top of the page."},
            {"action": "verify_element_visible", "selector": "h1",
             "task": "Verify the main heading is visible after scrolling back to top.",
             "is_verify": True},
        ]
    },
]

FLOWS_UITESTINGPLAYGROUND_NEGATIVE = [

    {
        "name": "uitpg_neg_dynamic_id_no_hardcode",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/dynamicid",
             "task": "Navigate to Dynamic ID page."},
            {
                "action": "verify_element_hidden",
                "selector": "#button1",   # dynamic ID — will never be exactly this
                "task": "Verify element #button1 is present. "
                        "NOTE: IDs are randomized on this page — this selector will not resolve. "
                        "The correct approach is to use button.btn-primary instead.",
                "is_verify": True,
                "raises_bug": True,
                "value": "button with stable selector (not hardcoded dynamic ID)",
                "bug_title": "Hardcoded dynamic ID #button1 failed — use stable class selector instead",
                "bug_severity": "Medium",
            },
        ]
    },

    {
        "name": "uitpg_neg_element_not_yet_loaded",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/loaddelay",
             "task": "Navigate to Load Delay page. Button is not yet in DOM immediately after load."},
            {
                "action": "verify_element_hidden",
                "selector": "button.btn-primary",
                "task": "Verify the delayed button is already visible immediately after page load. "
                        "It will NOT be — a wait_for_element is required first. "
                        "Attempting to interact without waiting is a common hallucination error.",
                "is_verify": True,
                "raises_bug": False,
                "value": "button not yet visible — requires wait_for_element first",
            },
        ]
    },

    {
        "name": "uitpg_neg_hidden_button_wrong_assertion",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/visibility",
             "task": "Navigate to Visibility page."},
            {"action": "click", "selector": "#hideButton",
             "task": "Click Hide button to trigger element visibility changes."},
            {
                "action": "verify_element_hidden",
                "selector": "#removedButton",
                "task": "Verify #removedButton is still visible after clicking Hide. "
                        "This assertion FAILS — the button was removed from the DOM. Raise a bug.",
                "is_verify": True,
                "raises_bug": True,
                "value": "#removedButton visible after hide action",
                "bug_title": "#removedButton not found after Hide clicked — element was removed from DOM",
                "bug_severity": "High",
            },
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# EXTENDED BLOCKED — 15 new [FLOW BLOCKED] scenarios across all 3 new sites
# Teaches the model: when a critical element is missing, stop and raise Critical.
# Variety: wrong selectors, missing nav, missing form fields, missing buttons,
#          page not loaded, wrong page entirely.
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_EXTENDED_BLOCKED = [

    # ── the-internet.herokuapp.com ────────────────────────────────────────────

    {
        "name": "blocked_herald_username_field_missing",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/login",
             "task": "Navigate to The Internet login page. Verifying all fields exist before entering credentials."},
            {
                "action": "verify_element_hidden",
                "selector": "#user-name",   # wrong — correct is #username
                "task": "Verify the username input field (#user-name) is present before typing credentials. "
                        "If it cannot be found, the login flow is fully blocked — cannot proceed.",
                "is_verify": True,
                "raises_bug": True,
                "value": "username input field (#user-name)",
                "bug_title": "BLOCKER: Username field #user-name not found on login page — login flow blocked",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },

    {
        "name": "blocked_herald_password_field_missing",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/login",
             "task": "Navigate to The Internet login page."},
            {"action": "clear_and_type", "selector": "#username", "value": "tomsmith",
             "task": "Enter tomsmith in the Username field — preparing for login."},
            {
                "action": "verify_element_hidden",
                "selector": "#passwd",   # wrong — correct is #password
                "task": "Verify password input field (#passwd) is present before entering credentials. "
                        "Cannot complete login without a password field — flow is blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "password input field (#passwd)",
                "bug_title": "BLOCKER: Password field #passwd not found — correct selector is #password",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },

    {
        "name": "blocked_herald_secure_area_missing",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/login",
             "task": "Navigate to The Internet login page."},
            {"action": "clear_and_type", "selector": "#username", "value": "tomsmith",
             "task": "Enter tomsmith in Username."},
            {"action": "clear_and_type", "selector": "#password", "value": "SuperSecretPassword!",
             "task": "Enter SuperSecretPassword! in Password."},
            {"action": "click", "selector": "button[type='submit']",
             "task": "Click Login."},
            {
                "action": "verify_element_hidden",
                "selector": "#content .example h4",   # wrong selector for the secure area heading
                "task": "Verify the secure area welcome heading is present after login. "
                        "If the secure area did not load, the authenticated flow is blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "secure area heading after login",
                "bug_title": "BLOCKER: Secure area heading not found after login — authenticated flow blocked",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },

    {
        "name": "blocked_herald_dropdown_missing",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/dropdown",
             "task": "Navigate to the Dropdown page. Verifying dropdown is present before interaction."},
            {
                "action": "verify_element_hidden",
                "selector": "#select-dropdown",   # wrong — correct is #dropdown
                "task": "Verify the dropdown element (#select-dropdown) is present. "
                        "Cannot run dropdown selection tests if the element is missing — flow blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "dropdown element (#select-dropdown)",
                "bug_title": "BLOCKER: Dropdown #select-dropdown not found — correct selector is #dropdown",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },

    {
        "name": "blocked_herald_add_element_button_missing",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/add_remove_elements/",
             "task": "Navigate to Add/Remove Elements page."},
            {
                "action": "verify_element_hidden",
                "selector": "#add-element-btn",   # wrong — real is button[onclick='addElement()']
                "task": "Verify the Add Element button (#add-element-btn) is present. "
                        "Without this button the entire add/remove flow cannot execute — blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "Add Element button (#add-element-btn)",
                "bug_title": "BLOCKER: Add Element button not found by selector #add-element-btn — flow blocked",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },

    {
        "name": "blocked_herald_logout_link_missing_after_login",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/login",
             "task": "Navigate to login page."},
            {"action": "clear_and_type", "selector": "#username", "value": "tomsmith",
             "task": "Enter tomsmith."},
            {"action": "clear_and_type", "selector": "#password", "value": "SuperSecretPassword!",
             "task": "Enter password."},
            {"action": "click", "selector": "button[type='submit']",
             "task": "Click Login."},
            {
                "action": "verify_element_hidden",
                "selector": "a.logout-btn",   # wrong — real is a[href='/logout']
                "task": "Verify the Logout link (a.logout-btn) is present in the secure area. "
                        "If missing, the user cannot log out — session management flow is blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "Logout link (a.logout-btn) in secure area",
                "bug_title": "BLOCKER: Logout link not found by selector a.logout-btn after login",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },

    # ── practice.expandtesting.com ────────────────────────────────────────────

    {
        "name": "blocked_expand_login_button_missing",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/login",
             "task": "Navigate to Expand Testing login page. Checking all login form elements exist."},
            {
                "action": "verify_element_hidden",
                "selector": "#loginBtn",   # wrong — real is button[type='submit']
                "task": "Verify the login submit button (#loginBtn) is present. "
                        "Cannot complete authentication without a submit button — flow blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "login button (#loginBtn)",
                "bug_title": "BLOCKER: Login button #loginBtn not found — correct selector is button[type='submit']",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },

    {
        "name": "blocked_expand_secure_content_missing",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/login",
             "task": "Navigate to Expand Testing login page."},
            {"action": "clear_and_type", "selector": "#username", "value": "practice",
             "task": "Enter practice in Username."},
            {"action": "clear_and_type", "selector": "#password", "value": "SuperSecretPassword!",
             "task": "Enter SuperSecretPassword! in Password."},
            {"action": "click", "selector": "button[type='submit']",
             "task": "Click Login."},
            {
                "action": "verify_element_hidden",
                "selector": "#secure-content",   # wrong selector for the post-login area
                "task": "Verify the secure content area (#secure-content) loaded after login. "
                        "If missing, the authenticated user flow cannot continue — blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "secure content area (#secure-content)",
                "bug_title": "BLOCKER: Secure content #secure-content not found after login — post-auth flow blocked",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },

    {
        "name": "blocked_expand_password_field_missing",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/login",
             "task": "Navigate to Expand Testing login."},
            {"action": "clear_and_type", "selector": "#username", "value": "practice",
             "task": "Enter practice in Username field."},
            {
                "action": "verify_element_hidden",
                "selector": "#pass",   # wrong — real is #password
                "task": "Verify the password input field (#pass) exists before entering credentials. "
                        "Without it, login cannot be completed — entire auth flow is blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "password field (#pass)",
                "bug_title": "BLOCKER: Password field #pass not found — correct selector is #password",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },

    {
        "name": "blocked_expand_checkbox_form_missing",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/checkboxes",
             "task": "Navigate to Expand Testing Checkboxes page."},
            {
                "action": "verify_element_hidden",
                "selector": "form.checkbox-form",   # wrong — real selector is different
                "task": "Verify the checkbox form (form.checkbox-form) is present. "
                        "Cannot run checkbox interaction tests without the form — flow blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "checkbox form element (form.checkbox-form)",
                "bug_title": "BLOCKER: Checkbox form not found by form.checkbox-form — flow blocked",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },

    # ── uitestingplayground.com ───────────────────────────────────────────────

    {
        "name": "blocked_uitpg_ajax_trigger_missing",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/ajax",
             "task": "Navigate to the AJAX Data page. Verifying trigger button exists before clicking."},
            {
                "action": "verify_element_hidden",
                "selector": "#ajaxBtn",   # wrong — real is #ajaxButton
                "task": "Verify the AJAX trigger button (#ajaxBtn) is present. "
                        "Without this button the async data load flow cannot be initiated — blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "AJAX trigger button (#ajaxBtn)",
                "bug_title": "BLOCKER: AJAX button #ajaxBtn not found — correct selector is #ajaxButton",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },

    {
        "name": "blocked_uitpg_scroll_target_missing",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/scrollbars",
             "task": "Navigate to Scrollbars page. Verifying target button exists before scroll interaction."},
            {
                "action": "verify_element_hidden",
                "selector": "#scrollTarget",   # wrong — real is #hidingButton
                "task": "Verify the scroll target button (#scrollTarget) is present. "
                        "Cannot run scrollbar interaction tests without the target element — flow blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "scroll target button (#scrollTarget)",
                "bug_title": "BLOCKER: Scroll target #scrollTarget not found — correct selector is #hidingButton",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },

    {
        "name": "blocked_uitpg_visibility_hide_btn_missing",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/visibility",
             "task": "Navigate to Visibility page. Verifying Hide button exists to run visibility flow."},
            {
                "action": "verify_element_hidden",
                "selector": "#hide-btn",   # wrong — real is #hideButton
                "task": "Verify the Hide button (#hide-btn) is present. "
                        "Cannot test visibility toggling without this button — entire flow is blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "Hide button (#hide-btn)",
                "bug_title": "BLOCKER: Hide button #hide-btn not found — correct selector is #hideButton",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },

    {
        "name": "blocked_uitpg_overlapped_id_field_missing",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/overlapped",
             "task": "Navigate to Overlapped Element page."},
            {"action": "scroll_to_element", "selector": "#id",
             "task": "Scroll to bring the ID input into view."},
            {
                "action": "verify_element_hidden",
                "selector": "#identifier",   # wrong — real is #id
                "task": "Verify the ID input field (#identifier) is present after scrolling. "
                        "Cannot complete the form without this field — flow is blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "ID input field (#identifier)",
                "bug_title": "BLOCKER: ID input #identifier not found — correct selector is #id",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },

    {
        "name": "blocked_uitpg_load_delay_never_appeared",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/loaddelay",
             "task": "Navigate to Load Delay page."},
            {"action": "wait_for_element", "selector": "button.btn-primary",
             "task": "Wait for the delayed button to appear."},
            {
                "action": "verify_element_hidden",
                "selector": "button#delayed-action-btn",   # wrong — real is button.btn-primary
                "task": "Verify the delayed action button (button#delayed-action-btn) appeared after wait. "
                        "If it cannot be found even after waiting, this is a critical render failure — flow blocked.",
                "is_verify": True,
                "raises_bug": True,
                "value": "delayed action button (button#delayed-action-btn)",
                "bug_title": "BLOCKER: Delayed button #delayed-action-btn never appeared — page render failure",
                "bug_severity": "Critical",
                "is_blocked": True,
            },
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# EXTENDED NEGATIVE — 10 more bug-raise (not blocked) negative selector examples
# Teaches the model: wrong selector → raise_bug_ticket, not hallucinate a fix.
# Variety: stale selectors, cross-site contamination, typos, wrong page context,
#          framework-generated class names that look plausible but don't exist.
# ─────────────────────────────────────────────────────────────────────────────

FLOWS_EXTENDED_NEGATIVE = [

    # ── the-internet.herokuapp.com ────────────────────────────────────────────

    {
        "name": "neg_herald_react_style_selector",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/login",
             "task": "Navigate to The Internet login page."},
            {
                "action": "verify_element_hidden",
                "selector": "[data-testid='username-input']",   # React-style attr not present
                "task": "Verify element [data-testid='username-input'] exists on the login page. "
                        "This is a React data-testid selector — this page uses plain HTML without test attributes.",
                "is_verify": True,
                "raises_bug": True,
                "value": "data-testid username input",
                "bug_title": "Selector [data-testid='username-input'] not found — page has no data-testid attributes",
                "bug_severity": "Medium",
            },
        ]
    },

    {
        "name": "neg_herald_saucedemo_selector_on_wrong_site",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/login",
             "task": "Navigate to The Internet login page."},
            {
                "action": "verify_element_hidden",
                "selector": "#login-button",   # SauceDemo's selector, not valid here
                "task": "Verify element #login-button is present on The Internet login page. "
                        "This selector belongs to SauceDemo and does not exist here.",
                "is_verify": True,
                "raises_bug": True,
                "value": "#login-button (SauceDemo selector on wrong site)",
                "bug_title": "Cross-site selector: #login-button not found — this is SauceDemo's selector, not valid here",
                "bug_severity": "Medium",
            },
        ]
    },

    {
        "name": "neg_herald_checkbox_wrong_selector",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/checkboxes",
             "task": "Navigate to Checkboxes page."},
            {
                "action": "verify_element_hidden",
                "selector": ".rct-checkbox",   # DemoQA's React checkbox class — wrong site
                "task": "Verify .rct-checkbox element is present on The Internet Checkboxes page. "
                        "This is DemoQA's React checkbox class — it does not exist on this plain HTML page.",
                "is_verify": True,
                "raises_bug": True,
                "value": ".rct-checkbox (DemoQA selector on wrong site)",
                "bug_title": "Wrong selector: .rct-checkbox not found — DemoQA class used on The Internet page",
                "bug_severity": "Medium",
            },
        ]
    },

    {
        "name": "neg_herald_hover_caption_absent_no_hover",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/hovers",
             "task": "Navigate to Hovers page. Testing that caption is NOT visible without hover."},
            {
                "action": "verify_element_hidden",
                "selector": ".figure:first-of-type .figcaption",
                "task": "Verify the hover caption is visible WITHOUT hovering first. "
                        "The caption should NOT be visible — it only appears on hover.",
                "is_verify": True,
                "raises_bug": True,
                "value": "figcaption visible without hover (should be hidden)",
                "bug_title": "Hover caption .figcaption is unexpectedly visible without hover — possible CSS regression",
                "bug_severity": "Medium",
            },
        ]
    },

    {
        "name": "neg_herald_success_flash_absent_after_bad_login",
        "steps": [
            {"action": "navigate", "value": "https://the-internet.herokuapp.com/login",
             "task": "Navigate to The Internet login page."},
            {"action": "clear_and_type", "selector": "#username", "value": "baduser",
             "task": "Enter baduser in Username."},
            {"action": "clear_and_type", "selector": "#password", "value": "badpass",
             "task": "Enter badpass in Password."},
            {"action": "click", "selector": "button[type='submit']",
             "task": "Click Login with bad credentials."},
            {
                "action": "verify_element_hidden",
                "selector": "#flash.success",   # should NOT be success — it's an error
                "task": "Verify a success flash message appeared after login with bad credentials. "
                        "This should NOT succeed — a success flash after bad login would be a security bug.",
                "is_verify": True,
                "raises_bug": True,
                "value": "success flash after intentionally bad credentials",
                "bug_title": "Security bug: success flash shown after login with invalid credentials",
                "bug_severity": "High",
            },
        ]
    },

    # ── practice.expandtesting.com ────────────────────────────────────────────

    {
        "name": "neg_expand_aria_label_selector_missing",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/login",
             "task": "Navigate to Expand Testing login page."},
            {
                "action": "verify_element_hidden",
                "selector": "[aria-label='Username']",   # this site doesn't use aria-labels on inputs
                "task": "Verify element with aria-label='Username' is present on the login page. "
                        "This site uses plain id attributes, not aria-labels.",
                "is_verify": True,
                "raises_bug": True,
                "value": "aria-label Username input",
                "bug_title": "Selector [aria-label='Username'] not found — page uses #username id, not aria-label",
                "bug_severity": "Low",
            },
        ]
    },

    {
        "name": "neg_expand_number_input_wrong_selector",
        "steps": [
            {"action": "navigate", "value": "https://practice.expandtesting.com/inputs",
             "task": "Navigate to Expand Testing Inputs page."},
            {
                "action": "verify_element_hidden",
                "selector": "input#numberInput",   # wrong — real is input[type='number']
                "task": "Verify the number input field (input#numberInput) is present. "
                        "This ID does not exist — the correct selector is input[type='number'].",
                "is_verify": True,
                "raises_bug": True,
                "value": "number input (input#numberInput)",
                "bug_title": "Selector input#numberInput not found — correct selector is input[type='number']",
                "bug_severity": "Low",
            },
        ]
    },

    # ── uitestingplayground.com ───────────────────────────────────────────────

    {
        "name": "neg_uitpg_class_primary_after_hide",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/visibility",
             "task": "Navigate to Visibility page."},
            {"action": "click", "selector": "#hideButton",
             "task": "Click Hide to trigger visibility changes."},
            {
                "action": "verify_element_hidden",
                "selector": "#zeroWidthButton",
                "task": "Verify the zero-width button is still fully clickable after Hide is clicked. "
                        "This element has zero width after hiding — it is not interactable.",
                "is_verify": True,
                "raises_bug": True,
                "value": "#zeroWidthButton fully visible and clickable after hide",
                "bug_title": "#zeroWidthButton has zero width after Hide — not interactable, possible regression",
                "bug_severity": "Medium",
            },
        ]
    },

    {
        "name": "neg_uitpg_wrong_success_selector",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/click",
             "task": "Navigate to AJAX click page."},
            {"action": "click", "selector": "#ajaxButton",
             "task": "Click the AJAX button."},
            {"action": "wait_for_element", "selector": ".bg-success",
             "task": "Wait for success element to appear."},
            {
                "action": "verify_element_hidden",
                "selector": "#successMessage",   # wrong — real is .bg-success
                "task": "Verify the success message element (#successMessage) is visible after AJAX completes. "
                        "This ID does not exist — the actual success indicator uses class .bg-success.",
                "is_verify": True,
                "raises_bug": True,
                "value": "success message (#successMessage)",
                "bug_title": "Success element #successMessage not found — correct selector is .bg-success",
                "bug_severity": "Medium",
            },
        ]
    },

    {
        "name": "neg_uitpg_overlapped_before_scroll",
        "steps": [
            {"action": "navigate", "value": "http://www.uitestingplayground.com/overlapped",
             "task": "Navigate to Overlapped Element page. Testing interaction WITHOUT scrolling first."},
            {
                "action": "verify_element_hidden",
                "selector": "#name",
                "task": "Verify the Name field (#name) is fully visible and interactable without scrolling. "
                        "The element is partially obscured by the sticky header — attempting to type "
                        "without scroll_to_element first will fail on real interactions.",
                "is_verify": True,
                "raises_bug": True,
                "value": "#name field fully accessible without scroll",
                "bug_title": "Element #name is obscured by sticky header — requires scroll_to_element before interaction",
                "bug_severity": "Medium",
            },
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# MASTER LIST — all new flows combined
# ─────────────────────────────────────────────────────────────────────────────

ALL_NEW_FLOWS = (
    # Site 1: the-internet.herokuapp.com (~55 records)
    FLOWS_HEROKUAPP_FORMS
    + FLOWS_HEROKUAPP_INTERACTIONS
    + FLOWS_HEROKUAPP_NEGATIVE
    + FLOWS_HEROKUAPP_BLOCKED

    # Site 2: practice.expandtesting.com (~50 records)
    + FLOWS_EXPANDTESTING_FORMS
    + FLOWS_EXPANDTESTING_INPUTS
    + FLOWS_EXPANDTESTING_NAVIGATION
    + FLOWS_EXPANDTESTING_NEGATIVE

    # Site 3: uitestingplayground.com (~45 records)
    + FLOWS_UITESTINGPLAYGROUND_CLICKS
    + FLOWS_UITESTINGPLAYGROUND_WAITS
    + FLOWS_UITESTINGPLAYGROUND_VISIBILITY
    + FLOWS_UITESTINGPLAYGROUND_SCROLL
    + FLOWS_UITESTINGPLAYGROUND_NEGATIVE

    # Extended: blocked + negative across all 3 sites (~65 records)
    + FLOWS_EXTENDED_BLOCKED
    + FLOWS_EXTENDED_NEGATIVE
)


if __name__ == "__main__":
    by_group = {
        "herokuapp_forms":        FLOWS_HEROKUAPP_FORMS,
        "herokuapp_interactions": FLOWS_HEROKUAPP_INTERACTIONS,
        "herokuapp_negative":     FLOWS_HEROKUAPP_NEGATIVE,
        "herokuapp_blocked":      FLOWS_HEROKUAPP_BLOCKED,
        "expand_forms":           FLOWS_EXPANDTESTING_FORMS,
        "expand_inputs":          FLOWS_EXPANDTESTING_INPUTS,
        "expand_navigation":      FLOWS_EXPANDTESTING_NAVIGATION,
        "expand_negative":        FLOWS_EXPANDTESTING_NEGATIVE,
        "uitpg_clicks":           FLOWS_UITESTINGPLAYGROUND_CLICKS,
        "uitpg_waits":            FLOWS_UITESTINGPLAYGROUND_WAITS,
        "uitpg_visibility":       FLOWS_UITESTINGPLAYGROUND_VISIBILITY,
        "uitpg_scroll":           FLOWS_UITESTINGPLAYGROUND_SCROLL,
        "uitpg_negative":         FLOWS_UITESTINGPLAYGROUND_NEGATIVE,
        "extended_blocked":       FLOWS_EXTENDED_BLOCKED,
        "extended_negative":      FLOWS_EXTENDED_NEGATIVE,
    }

    total_flows = 0
    total_steps = 0
    print(f"\n{'Group':<30} {'Flows':>6} {'Records':>8}")
    print("-" * 47)
    for name, flows in by_group.items():
        steps = sum(len(f["steps"]) for f in flows)
        total_flows += len(flows)
        total_steps += steps
        print(f"{name:<30} {len(flows):>6} {steps:>8}")
    print("-" * 47)
    print(f"{'TOTAL':<30} {total_flows:>6} {total_steps:>8}")
    print(f"\nExisting dataset:           ~960 records")
    print(f"New records (this file):    ~{total_steps}")
    print(f"Projected merged total:     ~{960 + total_steps}")