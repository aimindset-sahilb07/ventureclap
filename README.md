# VentureClap website

A single-page static site for GitHub Pages. It has no build step: plain HTML, CSS and a small amount of JS.

## Adding your photos
Put the photos in `images/` using these exact names:

| File | Used for | Suggested size |
|---|---|---|
| `hero.jpg` | Full-screen photo at the top | 2400px wide, landscape, under 500 KB |
| `work-01.jpg` … `work-09.jpg` | Recent work gallery | 1600px on the long side, under 300 KB each |
| `og.jpg` | Preview image when the link is shared | exactly 1200×630 |

You can mix portrait and landscape photos. The gallery is a masonry layout.
A photo that isn't there yet appears as a dark placeholder tile.
To add or remove gallery photos, copy or delete a `<button class="shot">` line in `index.html`.
You can compress photos for free at squoosh.app.

## Placeholders to edit
Search `index.html` for `EDIT:`. That covers the headline, email, social links and the `og:image` URL, which must be the full `https://…` address once the site is live.

## Brand
VentureClap, short form **V/C**. Palette: green `#2EE59D` (`#0A8F57` on light), gold `#F5B82E`, white and black `#0B0B0D`. Typeface: Inter Tight 800.
Open `brand.html` to see everything on one page.

| File | Use |
|---|---|
| `images/logo.svg` / `logo-light.svg` | Full logo for dark / light backgrounds |
| `images/logo-mark.svg` / `logo-mark-light.svg` | V/C clapper icon |
| `images/favicon.svg`, `favicon-16/32.png` | Simplified icon for small sizes (browser tab) |
| `images/apple-touch-icon.png` | iPhone home screen icon |
| `images/avatar-1080.png` | Instagram / LinkedIn profile picture |

The logo text is converted to shapes, so the logo files don't need any font installed.
To change the logo, edit `brand/build_logo.py`, download the Inter Tight font (`InterTight[wght].ttf` from github.com/google/fonts, `ofl/intertight`) and save it next to the script as `InterTight.ttf`, then run it with `fonttools`, `skia-pathops` and `pillow` installed:
```
python brand/build_logo.py images
```
Site colors and fonts are set at the top of `styles.css` (`:root`).

## Preview locally
```
python -m http.server 8000
```
Then open http://localhost:8000

## Deploy to GitHub Pages
```
gh repo create ventureclap --public --source . --push
gh api -X POST repos/{owner}/ventureclap/pages -f "source[branch]=main" -f "source[path]=/"
```
The site goes live at `https://<username>.github.io/ventureclap/` within about a minute.
