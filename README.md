# VentureClap website

A single-page static site for GitHub Pages. It has no build step: plain HTML, CSS and a small amount of JS.

## Adding your photos
Put the photos in `assets/` using these exact names:

| File | Used for | Suggested size |
|---|---|---|
| `hero-1000.jpg`, `hero-2000.jpg` | Full-screen photo at the top (phone / larger screens) | 1000px and 2000px wide |
| `work-01.jpg` … `work-05.jpg` | Recent work gallery | 1600px on the long side, under 300 KB each |
| `og.jpg` | Preview image when the link is shared | exactly 1200×630 |

On phones, gallery photos show at their own shape. On wider screens they're cropped into tidy rows: portrait tiles at 4:5, and tiles marked `wide` span two columns at 8:5.
A photo that isn't there yet appears as a dark placeholder tile.
To add or remove gallery photos, copy or delete a `<button class="shot">` line in `index.html`. Add `wide` to a landscape photo's class to make it span two columns.
The original full-size photos are kept in `assets/harenmehta_images_website_2026-09-28_2025/`.
You can compress photos for free at squoosh.app.

## Placeholders to edit
Search `index.html` for `EDIT:`. That covers the headline, email, social links and the `og:image` URL, which must be the full `https://…` address once the site is live.

## Brand
VentureClap, short form **V/C**: a serif monogram with a brass slash.
Palette: forest `#0F2A22`, ivory `#F4F1EA`, brass `#C9A35A` (`#A8823A` on ivory) and black `#0B0B0D`.
Type: Cormorant Garamond for the monogram and headings, and Inter for the wordmark and body text.
Open `brand.html` to see everything on one page.

| File | Use |
|---|---|
| `assets/logo-stacked.svg` / `logo-stacked-light.svg` | Main logo (monogram above the wordmark) |
| `assets/logo.svg` / `logo-light.svg` | Horizontal logo (website header, email signature) |
| `assets/logo-mark.svg` / `logo-mark-light.svg` | V/C monogram only |
| `assets/favicon.svg`, `favicon-16/32.png` | Browser tab icon (bolder cut) |
| `assets/apple-touch-icon.png` | iPhone home screen icon |
| `assets/avatar-1080.png` | Instagram / LinkedIn profile picture |

`-light` versions are for ivory or white backgrounds.
The logo text is converted to shapes, so the logo files don't need any font installed.
To change the logo, edit `brand/build_logo.py`. Download `CormorantGaramond[wght].ttf` and `Inter[opsz,wght].ttf` from github.com/google/fonts (`ofl/cormorantgaramond`, `ofl/inter`) and save them next to the script as `CormorantGaramond.ttf` and `Inter.ttf`. Then run it with `fonttools`, `skia-pathops` and `pillow` installed:
```
python brand/build_logo.py assets
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
