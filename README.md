# SALT — Interactive Brochure

A single self-contained HTML page. No build step, no framework, no dependencies.
`index.html` carries its own CSS, JavaScript, fonts and most of its product
imagery as base64. Vercel serves it as a static file.

---

## Deploy

**Option A — Vercel CLI** (fastest)

```bash
npm i -g vercel
cd salt-brochure
vercel            # preview deployment
vercel --prod     # production
```

**Option B — Git**

```bash
cd salt-brochure
git init && git add . && git commit -m "SALT interactive brochure"
git remote add origin <your-repo-url>
git push -u origin main
```

Then in the Vercel dashboard: **Add New → Project → import the repo.**
Leave every build setting empty — framework preset **Other**, no build
command, no output directory. Vercel will serve `index.html` from the root.

**Option C — drag and drop**

Drop this folder onto the Vercel dashboard. Works, but you lose the git history
and redeploys become manual.

---

## What's in here

| File | Purpose |
|---|---|
| `index.html` | The entire brochure — 645 KB, everything inlined |
| `vercel.json` | Static config: clean URLs, cache and security headers |
| `embed-live-images.py` | Optional: bakes the live product renders into the HTML |

---

## Before you ship: bake in the images

Sixty-nine of the 114 fixtures have their render embedded in the file. The rest
load from `salt-lighting.vercel.app` at runtime, which means the brochure
depends on that site staying up and its filenames staying stable.

To remove that dependency, run this once **before** deploying:

```bash
pip install requests pillow
python3 embed-live-images.py
mv SALT-Interactive-Brochure-embedded.html index.html
```

It downloads every live render, normalises the studio backdrop to match the
rest of the grid, converts to WebP and inlines it. The result is fully
self-contained. Any download that fails keeps its existing fallback rather
than leaving a hole.

Expect the file to land somewhere between 1.5 MB and 3 MB depending on how many
renders resolve. That is still a single request and still cheap on Vercel's
edge, but if you want it leaner, drop `MAX_EDGE` in the script from 1400 to 900.

---

## Known gaps

**45 of 114 fixtures have no specifications yet.** They show the render, the
collection, and a link to the live datasheet — deliberately, rather than
padding them with plausible-looking numbers. They carry a dashed
"Specs on request" chip so they are obvious at a glance. The remaining work is
28 Downlights (the Lumo, Axis, Micro and Mini families) and 17 Snap products
(Nova, the four Linea variants, and the eleven track profiles).

**Some inferred image filenames may 404.** Filenames for products whose pages
haven't been opened individually were reconstructed from listing alt-text, and
your CMS is inconsistent about them — some files have no extension, some are
`.jpg` where the name implies `.png`, one has a double space. Those entries
fall back to a neutral labelled plate rather than a broken image. Each one gets
corrected as its product page is transcribed.

**Photometric curves are indicative.** The polar plots are generated from the
published beam angle, not from measured data, and every datasheet says so.
Request the IES or LDT file for certified photometry.

---

## Editing product data

All 114 products live in a single `const P = [...]` array inside the `<script>`
block. Each record is plain JSON — name, family, wattage, beam angles, colour
temperatures, image URLs. Adding a fixture means appending one object; changing
a specification means editing one field. Nothing else in the page needs to know.

The `fam` key maps to the filter buttons defined in `const FAMS` directly below
the array.

---

## Fonts

Inter Variable and IBM Plex Mono, both SIL OFL 1.1, embedded as base64.
SALT's brand face is Helvetica, which cannot be legally embedded as a webfont.
If FutureDot holds a Helvetica licence, swap the `@font-face` sources and move
`Helvetica Neue` to the front of the `--display` stack.
