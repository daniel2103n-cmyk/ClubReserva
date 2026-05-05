---
name: ClubReserva
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#3c4a42'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#6c7a71'
  outline-variant: '#bbcabf'
  surface-tint: '#006c49'
  primary: '#006c49'
  on-primary: '#ffffff'
  primary-container: '#10b981'
  on-primary-container: '#00422b'
  inverse-primary: '#4edea3'
  secondary: '#575e70'
  on-secondary: '#ffffff'
  secondary-container: '#d9dff5'
  on-secondary-container: '#5c6274'
  tertiary: '#555f6f'
  on-tertiary: '#ffffff'
  tertiary-container: '#99a3b5'
  on-tertiary-container: '#2f3948'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#6ffbbe'
  primary-fixed-dim: '#4edea3'
  on-primary-fixed: '#002113'
  on-primary-fixed-variant: '#005236'
  secondary-fixed: '#dce2f7'
  secondary-fixed-dim: '#c0c6db'
  on-secondary-fixed: '#141b2b'
  on-secondary-fixed-variant: '#404758'
  tertiary-fixed: '#d9e3f6'
  tertiary-fixed-dim: '#bdc7d9'
  on-tertiary-fixed: '#121c2a'
  on-tertiary-fixed-variant: '#3d4756'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
typography:
  display:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  h1:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  h2:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  h3:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: '0'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  sidebar_width: 280px
  container_padding: 32px
  gutter: 24px
  card_gap: 24px
---

## Brand & Style
The brand personality is defined by exclusivity, precision, and athletic excellence. This design system employs a **Modern Corporate** style with high-contrast surfaces to distinguish between administrative navigation and active management workspaces. 

The aesthetic is designed to evoke a sense of "Premium Club Membership"—organized, calm, and high-end. It utilizes a sophisticated duality: deep, dark navigational elements that frame a clean, light-filled content canvas. This approach ensures that while the environment feels prestigious, the actual data and management tasks remain highly legible and professional.

## Colors
This design system uses a strategic split-palette. The **Primary Emerald** is used sparingly for actions, highlights, and success states to maintain its visual impact.

- **Navigation & Chrome:** Utilizes the dark palette (#111827 and #1F2937) to create a fixed "frame" for the application. This anchors the user and reinforces the premium, nocturnal feel of elite sports lounge environments.
- **Main Content Area:** Transitions to a light grey (#F9FAFB) background. This provides maximum contrast for data-heavy tables, booking calendars, and member profiles.
- **Accents:** Text on dark surfaces is pure white or high-opacity grey. Text on light surfaces follows a deep slate scale for optimal readability.

## Typography
**Inter** is the sole typeface, chosen for its exceptional legibility in data-dense interfaces. 

Tight letter spacing and heavier weights are reserved for headings to give them a modern, assertive feel. Labels and small data points use a slightly increased letter spacing and medium/semi-bold weights to ensure they remain scannable on both dark sidebar backgrounds and light content cards.

## Layout & Spacing
The layout follows a **Desktop-First Sidebar** architecture. 

- **The Sidebar:** Fixed at 280px. It uses the dark background palette. Navigation items are spaced generously to allow for touch-friendly interaction on tablets.
- **The Grid:** A 12-column fluid grid system for the main content area. 
- **Rhythm:** An 8px baseline grid governs all padding and margins. Consistent 32px padding is applied to the main viewport container, while internal card components use 24px padding to create a breathable, high-end feel.

## Elevation & Depth
Depth is conveyed through **Tonal Layers** rather than heavy shadows.

- **Level 0 (Background):** The light grey (#F9FAFB) workspace.
- **Level 1 (Cards/Surface):** Pure white containers with a very subtle, diffused 4% opacity black shadow (blur: 10px, y: 4px).
- **Level 2 (Overlays/Dropdowns):** Elevated surfaces with a more pronounced 8% opacity shadow and a 1px soft border (#E5E7EB).
- **Active States:** Subtle inner shadows or 2px emerald borders are used to denote focus, avoiding overwhelming the clean aesthetic.

## Shapes
The shape language is defined by large, inviting radii. Standard containers and cards utilize **rounded-2xl (1rem)** to soften the professional tone and make the platform feel modern and accessible.

Buttons and input fields follow a **rounded-xl (0.75rem)** pattern. This creates a visual hierarchy where larger structural elements are more rounded than the interactive components contained within them.

## Components
Consistent component styling ensures the premium feel is maintained across the entire management suite.

- **Buttons:** Primary buttons use the Emerald Green background with white text. Secondary buttons use a clean outline style with a 1px border. All buttons use `rounded-xl`.
- **Inputs:** Fields use a white background on the light canvas with a soft grey border. Upon focus, the border transitions to Emerald with a subtle glow.
- **Cards:** The primary container for information. Cards must have `rounded-2xl` corners, white backgrounds, and the Level 1 subtle shadow.
- **Badges/Chips:** Used for "Membership Status" or "Booking Confirmed." These use a light tint of the status color (e.g., 10% opacity Emerald) with high-contrast text.
- **Sidebar Nav:** Items use a hover state with a 4px vertical Emerald "pill" on the left edge to indicate the active section.
- **Icons:** Use Lucide/Heroicons with a 1.5px or 2px stroke weight. Avoid solid icons to maintain the "clean and airy" professional aesthetic.
- **Data Tables:** Clean rows with no vertical borders. Use horizontal dividers in #F3F4F6. The header row should use `label-sm` typography in a muted grey.