# Layout and visual review

## Inherited production defaults

These values were used across previous decks. They are a starting point, not universal design rules. Preserve the current series or explicit brief when it differs.

| Element | Starting value at 1080 × 1350 |
|---|---|
| Safe margin | 64 px on all sides |
| Alignment grid | 8 px, with optical corrections when needed |
| Display title | Roughly 78 to 96 px; two or three short lines |
| Body | Roughly 32 to 36 px, with comfortable leading |
| Small label | Roughly 20 to 24 px; avoid critical information here |
| Gap between independent text and artwork | At least 24 px |
| Gap between Figma slide frames | 32 px |

Use the available brand face. SF Pro was used in earlier Apple-influenced campaigns, but do not require an unavailable proprietary font or redistribute it. Choose a compatible licensed face when necessary. Set real text and measure it; font size alone does not guarantee fit.

## Hierarchy

Keep one focal element per card. Use size, weight, alignment, and space to lead from the title to the explanation and then the example. Photos, logos, a mascot, and decorative shapes must not all compete at equal strength.

Group elements that belong together and leave more space between separate ideas. Keep the brand header and page counter on a shared baseline. Align stacked text to a common edge. Repeat components for equivalent information, with controlled changes for long names or wide marks.

Allow light and dark slides when the series supports them. Each needs its own readable text and logo variant. Do not add gradients, glass, sticker-like shapes, or loose drawings just to make the card feel designed. Depth should clarify grouping.

## Dense rows and code

Shrink the row's elements together when density gets high: logo, heading, supporting text, and chart marks. Use the gained space between rows. Do not squeeze all spacing to preserve a large heading.

One later ranking deck used at least 24 px of visible separation between chart rows and about 50 px between text rows. Those values are a repair example for that deck, not requirements for every list. Judge the real rendered bounds at phone size.

Use a table for comparable properties such as tuple versus list. Show functions, decorators, generators, arguments, and mutable defaults as code when code is the clearest explanation. Wrap signatures at sensible points, preserve indentation, and leave a visible inset around every line. Never shrink code until it is unreadable.

Diagrams need correct geometry and readable labels. Repeatedly repairing a weak drawing is a reason to change representation. Use tested geometry, a consistent licensed asset family, or a clear code example. If the brief says code only, remove decorative drawings throughout the deck.

## Containment and contrast

Center pill and button labels from their real text bounds. Check horizontal and vertical padding, including long labels and descenders. No label should protrude from its shape. Test unusual strings such as `O(log n)` and wide function signatures at full resolution.

White text on a photograph must survive the brightest part of the crop. Change the crop, add an appropriate scrim or opaque panel, or move the text. Aim for at least 4.5:1 for body and 3:1 for large text, then inspect the actual result. Numeric contrast checks cannot catch every textured-photo problem.

## Review the whole deck

Use a contact sheet to find drift, sequence problems, and repetitive compositions. Inspect every slide individually for overflow, alignment, image crop, broken glyphs, logo balance, and factual clarity. Also view the cover and densest slide at a realistic phone width.

Fix the discovered defects together and confirm the changed slides once. Verify export dimensions and file order separately. Record concrete remaining issues instead of calling an uninspected result "perfect."
