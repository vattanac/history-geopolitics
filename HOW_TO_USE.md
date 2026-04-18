# History & Geopolitics — Library Hub

Open `index.html` in a browser. That is the central page.

## Adding a new piece

1. Drop your new `.html` file into this folder (same folder as `index.html`).
2. Inside that file's `<head>`, add a small block of meta tags:

   ```html
   <meta name="category"        content="War">
   <meta name="subcategory"     content="World War II">
   <meta name="nav-title"       content="The Second World War — a short book">
   <meta name="nav-description" content="Causes, major fronts, and how it ended.">
   <meta name="nav-added"       content="2026-05-02">
   ```

   Only `category` is really needed. Everything else has sensible fallbacks.

3. Regenerate the sidebar with **one** of these:

   - **Python (works everywhere):**
     ```bash
     python3 regenerate.py
     ```
     Re-open `index.html` and the new piece is in the sidebar.

   - **Browser (Chrome / Edge only):** click **Rescan** in the sidebar footer
     and choose this folder. The change is shown immediately but lives only in
     that browser tab — run the Python script if you want to save it.

## How grouping works

- Files are grouped by their `category` meta tag, then by `subcategory`.
- `_overrides.json` in this folder lets you hand-curate titles, descriptions,
  and categories for files that don't have their own meta tags (the existing
  `Israel_Book_Easy.html` is set up this way).
- Files with no category end up in **Uncategorized** at the bottom.

## Example category tree

```
War
  └ World War I
  └ World War II
  └ Cold War
Middle East
  └ Israel & Palestine
  └ Iran
  └ Syria
Asia
  └ China
  └ Korea
Europe
  └ EU
  └ Russia & Ukraine
```

Any `category` / `subcategory` string you use becomes a new section in the
sidebar automatically — no other setup needed.

## Keyboard

- `/` focuses the search box.
- `Esc` clears it.

## Files in this folder

| File | What it is |
| --- | --- |
| `index.html` | The hub. Open this one. |
| `regenerate.py` | Rebuilds the sidebar by scanning the folder. |
| `_overrides.json` | Hand-curated info for files that lack meta tags. |
| `Israel_Book_Easy.html` | The first piece of content. |
| `HOW_TO_USE.md` | This file. |
