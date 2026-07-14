---
name: spendly-ui-designer
description: "Generate modern, production-ready UI components and pages for Spendly, the personal expense tracker. Automatically trigger when the user mentions designing, creating, or redesigning pages/components for Spendly (e.g., 'design the dashboard page', 'create a transaction card', 'build a category selector', 'improve the budget page'). Outputs clean, responsive HTML + Vanilla CSS + little JS code that matches Spendly's minimalist fintech aesthetic. Always use Spendly's design system: dark green branding (#1a472a), neutral backgrounds (#f3f1ed, #eeebe4), minimal icons, card-based layouts, 8-12-16px spacing scale, rounded corners, and soft shadows. Focus on clarity, usability, and consistency with existing Spendly design."
compatibility: "Flask + Vanilla HTML/CSS + little.js"
---

# Spendly Frontend UI Designer

A skill for generating production-ready UI components and pages for Spendly, the personal expense tracker application.

## Design System Reference

### Color Palette

**Primary Brand Color:**
- Dark Green: `#1a472a` — used for icons, accents, active states, and brand elements

**Neutral Backgrounds & Text:**
- Primary Background: `#ffffff` (white) or `#f3f1ed` (off-white for sections)
- Secondary Background: `#eeebe4` (light beige/sand for cards, secondary areas)
- Tertiary Background: `#e4e1da` (soft gray for hover states, borders)
- Text (Primary): `#1a1a1a` or `#2a2a2a` (dark gray for headings and body)
- Text (Secondary): `#6b6b6b` (medium gray for subtext, labels, hints)

**Status/Accent Colors:**
- Success/Positive: Green shades (for budget on track, positive metrics)
- Warning/Increase: Red/Orange (e.g., "+12% vs last" in red)
- Neutral: Grays for inactive states

### Typography

- **Headings:** Bold, dark gray (#1a1a1a), good hierarchy
- **Body Text:** Regular weight, #2a2a2a or #6b6b6b
- **Labels:** Small, secondary gray (#6b6b6b)
- **Font Family:** System fonts or clean sans-serif (e.g., -apple-system, BlinkMacSystemFont, "Segoe UI")

### Layout & Spacing

- **Spacing Scale:** 8px, 12px, 16px, 24px, 32px (compact but comfortable)
- **Card Padding:** 16px internal padding
- **Border Radius:** 8-12px (soft rounded corners)
- **Shadows:** Subtle: `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1)` or `0 2px 4px rgba(0, 0, 0, 0.08)`
- **Container Max-Width:** 1200px (or responsive for mobile)

### Component Style Guide

**Cards:**
- Background: `#eeebe4` or `#f3f1ed`
- Padding: 16px
- Border radius: 8-12px
- Subtle shadow for depth
- Hover: Slight shadow increase or background shift to `#e4e1da`

**Buttons:**
- Primary: Dark green background (#1a472a), white text, rounded corners
- Secondary: Bordered or light background with dark text
- Padding: 10-12px horizontal, 8-10px vertical (compact)
- Hover: Slight opacity change or darker shade

**Input Fields:**
- Border: 1px solid #e4e1da
- Background: #ffffff
- Focus: Dark green border or outline
- Padding: 8-12px
- Border radius: 6-8px

**Icons:**
- Use simple, minimal line icons (like Lucide or Heroicons)
- Size: 20px for inline, 24px for larger, 16px for small
- Color: #1a472a for primary, #6b6b6b for secondary
- Consistent weight and style

**Transaction List:**
- Card-based layout, each transaction in a soft card
- Left: Category icon (#1a472a)
- Middle: Category name + description
- Right: Amount (bold, right-aligned)
- Bottom border or shadow for separation

### Design Principles

1. **Minimal & Clean:** No unnecessary elements. Every component has a clear purpose.
2. **Fintech Aesthetic:** Professional, trustworthy, modern. Avoid playful or casual styles.
3. **Clarity & Usability:** Clear hierarchy, readable text, intuitive actions.
4. **Consistency:** Match existing Spendly components in style, spacing, and behavior.
5. **Responsive:** Works on desktop and mobile without major layout shifts.
6. **Accessibility:** Good contrast ratios, clear labels, keyboard navigation where applicable.

## How to Use This Skill

When a user asks to design or build a UI component/page for Spendly:

1. **Identify what's being requested:** Page (e.g., dashboard, settings), component (e.g., transaction card, budget card), or feature (e.g., expense filter).
2. **Understand the context:** What data does it show? What actions should users perform? Any constraints mentioned?
3. **Structure the output:**
   - **Brief UI Description:** Key sections, layout, and UX decisions
   - **HTML:** Clean, semantic markup (no React, use vanilla HTML)
   - **CSS:** Organized, follows design system, minimal boilerplate
   - **JavaScript (if needed):** Minimal interactivity using little.js or vanilla JS

4. **Follow the design system:** Always use Spendly's colors, spacing, typography, and component patterns.
5. **Avoid generic UI:** No default Bootstrap/Tailwind look. Make it distinctly Spendly.
6. **Include comments only where UX/design decisions are non-obvious.**

## Common Components Reference

### Transaction Card

```
┌─────────────────────────────────────────┐
│ 🍕 Food              ₹450.00            │
│    Lunch at XYZ      Today at 1:30 PM   │
└─────────────────────────────────────────┘
```

**Structure:** Icon + category name on left, amount on right, description on second row. Card background: `#eeebe4`, padding: 12-16px, subtle shadow.

### Summary Card

```
┌────────────────────────┐
│ This Month             │
│ ₹18,240               │
│ +12% vs last (red)    │
└────────────────────────┘
```

**Structure:** Label (small, gray), large amount (bold, dark), secondary stat (smaller, colored). Card with border radius, light shadow.

### Category Breakdown

```
Food    ████████ 40%    ₹7,296
Travel  ███████  35%    ₹6,384
Bills   ████     25%    ₹4,560
```

**Structure:** Category icon + name, horizontal bar (width = % of total), percentage, amount. Minimal styling, easy to scan.

### Expense Form

**Fields:**
- Category dropdown (icon + label)
- Amount (numeric input, right-aligned)
- Date picker
- Description (optional text input)
- Submit button

**Layout:** Vertical stack on mobile, horizontal on desktop. Clear labels, compact spacing.

### Budget Progress

```
Budget: ₹25,000
Spent:  ₹18,240 (73%)
Left:   ₹6,760  (27%)

████████████░░░ 73%
```

**Structure:** Summary numbers, progress bar below. Color the bar green if on track, red if over budget.

## Output Format Example

When generating code, structure it like this:

```
## UI Structure
[Brief description of layout, key sections, and design decisions]

## HTML Code
[Clean, semantic HTML]

## CSS Code
[Organized styles following the design system]

## JavaScript (if needed)
[Minimal interactivity for user interactions]
```

## Notes for Developers

- Always use Flask-compatible HTML (Jinja2 syntax if needed, but keep it simple).
- No external dependencies beyond little.js (if already in project).
- Use data attributes (`data-*`) for hooking JavaScript to HTML.
- Keep CSS scoped to component classes to avoid conflicts.
- Ensure mobile responsiveness with simple media queries or flexbox.
- Test color contrast for accessibility (WCAG AA standard).

