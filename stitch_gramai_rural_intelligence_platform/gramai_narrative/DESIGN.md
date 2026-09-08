---
name: GramAI Narrative
colors:
  surface: '#f9f9ff'
  surface-dim: '#d3daef'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f3ff'
  surface-container: '#e9edff'
  surface-container-high: '#e1e8fd'
  surface-container-highest: '#dce2f7'
  on-surface: '#141b2b'
  on-surface-variant: '#434655'
  inverse-surface: '#293040'
  inverse-on-surface: '#edf0ff'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0053db'
  primary: '#004ac6'
  on-primary: '#ffffff'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#b4c5ff'
  secondary: '#006e2f'
  on-secondary: '#ffffff'
  secondary-container: '#6bff8f'
  on-secondary-container: '#007432'
  tertiary: '#784b00'
  on-tertiary: '#ffffff'
  tertiary-container: '#996100'
  on-tertiary-container: '#ffeedd'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#6bff8f'
  secondary-fixed-dim: '#4ae176'
  on-secondary-fixed: '#002109'
  on-secondary-fixed-variant: '#005321'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#f9f9ff'
  on-background: '#141b2b'
  surface-variant: '#dce2f7'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  title-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  mono-label:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  gutter: 24px
  margin: 32px
---

## Brand & Style
The design system for this rural business intelligence platform is built on a foundation of **Modern Minimalism** fused with **Glassmorphism**. It is designed to evoke a sense of precision, clarity, and technological advancement in a sector often underserved by high-end UI.

The aesthetic mimics the sophisticated transparency of modern developer tools while maintaining the accessibility required for business intelligence. Key visual drivers include:
- **Clarity:** Excessive whitespace to prevent data fatigue.
- **Translucency:** Glassmorphic overlays and frosted surfaces to create a sense of depth and modernism.
- **Precision:** A strict 8px grid system that ensures every element feels engineered rather than placed.

## Colors
The palette is anchored by **Trustworthy Blue**, signaling stability and enterprise-grade reliability. **Growth Green** and **Insight Orange** serve as functional accents for positive trends and critical data callouts respectively.

The background uses a cool **Clean Slate** to allow white glassmorphic cards to pop with subtle contrast. Border colors are kept extremely light to define structure without adding visual noise.

## Typography
This design system utilizes **Inter** exclusively to achieve a systematic, utilitarian aesthetic. 

- **Headlines:** Use tighter letter-spacing and semi-bold weights to create a strong visual anchor.
- **Data Labels:** Use the `mono-label` style for table headers and chart legends to provide a technical, precise feel.
- **Readability:** Line heights are set generously (1.5x for body text) to ensure complex business reports remain legible during long sessions.

## Layout & Spacing
The system employs a **Fluid Grid** with a strict 8px increment spacing scale. 

- **Desktop:** 12-column grid with 24px gutters. Content is typically housed in a max-width container of 1440px.
- **Tablet:** 8-column grid with 16px gutters.
- **Mobile:** 4-column grid with 16px margins.

Spacing should be applied logically: use `md` (16px) for internal card padding and `lg` (24px) for spacing between major layout sections.

## Elevation & Depth
Depth is created through **Glassmorphism** and **Layered Shadows**. 

1.  **Level 0 (Base):** The #F8FAFC background.
2.  **Level 1 (Cards):** Pure white surfaces with a 1px border (#E5E7EB) and a soft, diffused shadow (0px 4px 20px rgba(0,0,0,0.05)).
3.  **Level 2 (Modals/Overlays):** Semi-transparent white surfaces (RGBA 255, 255, 255, 0.8) with a `backdrop-filter: blur(12px)`. These use a more aggressive shadow (0px 12px 40px rgba(0,0,0,0.1)).

## Shapes
The design system uses a consistent **16px (1rem)** corner radius for all primary containers and cards. Smaller elements like buttons and input fields should utilize half the radius (8px) to maintain visual nesting logic. High-interaction elements like the AI assistant widget use a `pill` shape to distinguish them from data containers.

## Components

### Statistics Cards
Cards must include a headline value in `headline-lg`, a `label-sm` title, and a micro-sparkline chart at the bottom. Use `Secondary/Growth Green` for positive trends.

### Data Grids & Tables
- **Header:** Use `mono-label` with a light gray background (#F1F5F9).
- **Rows:** 56px minimum height with a subtle hover state (#F8FAFC).
- **Cells:** Use `body-md` for text and `label-sm` for status badges.

### Floating AI Assistant
A fixed-position element in the bottom-right. It should be a 56x56px circle using the `Primary Blue` color, with a high elevation shadow. Upon expansion, it reveals a glassmorphic chat interface with a 12px backdrop blur.

### Progress Steppers
Horizontal for desktop, vertical for mobile. Active steps use a solid `Primary Blue` circle; completed steps use `Growth Green` with a check icon; upcoming steps use a thin `Border` outline.

### Map UI
Pins should be custom SVG markers with a white border for legibility. Radius filters are rendered as semi-transparent blue circles with a 10% opacity fill and a solid 1px stroke.

### Charts
- **Stroke Width:** 2px for line and area charts.
- **Gradients:** Area charts must use a vertical fade from the brand color (20% opacity) to 0% at the baseline.
- **Interactivity:** Tooltips must follow the Level 2 Glassmorphic elevation rules.