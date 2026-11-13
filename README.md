# Kaleem Rehman — AI Automation Engineer Portfolio

A responsive one-page portfolio in plain HTML, CSS and JavaScript. No build step, framework or API key.

## Files

- `index.html` — the whole site
- `images/` — every image the site uses: project screenshots, `og-image.png` (the preview shown when the link is shared on LinkedIn, WhatsApp, X, etc.), `favicon.svg` and the `grain.svg` background texture.
  Always upload this folder together with `index.html`. Personal data in the screenshots is protected: the lead's phone number is blurred and student emails are removed.

## Before publishing — fill in the settings

All settings are near the end of `index.html`, inside `<script>`. Anything left empty stays hidden or shows a friendly "not set up yet" notice, so nothing fake is ever shown.

```js
const PHOTO = 'kaleem.jpg';            // your portrait (4:5 ratio), placed next to index.html

const SHOTS = {                        // real screenshots / GIFs — they replace the mockups
  cinephile: 'cinephile.gif',
  lead: 'lead-responder.png',
  classroom: 'classroom.png'
};

const LINKS = {                        // buttons appear automatically once filled
  cinephile: { demo: 'https://youtu.be/...', live: 'https://...', github: 'https://github.com/...' },
  lead:      { demo: '', github: '' },
  classroom: { demo: '', github: '' }
};

const TESTIMONIAL = {                  // only shown once a REAL quote is added (with permission)
  quote: '...', name: 'Prof. ...', role: 'University lecturer'
};

const CONTACT = {
  email: 'you@example.com',
  whatsapp: 'https://wa.me/923001234567',
  linkedin: 'https://www.linkedin.com/in/...',
  github: 'https://github.com/...',
  booking: 'https://cal.com/...'
};
```

WhatsApp is the main call-to-action (navbar, hero and contact section), so fill that in first.

## Social preview image

After publishing, open `index.html` and change both `images/og-image.png` references in the `<head>` to the full URL,
e.g. `https://yourname.github.io/images/og-image.png` — LinkedIn and WhatsApp need the full URL to show the image.

## Publish (free)

- **GitHub Pages:** push the files to a public repo → Settings → Pages → deploy from `main`.
- **Netlify:** drag the folder into app.netlify.com/drop.
- **Vercel:** import the GitHub repo.

## Features

- Animated hero showing how the AI Lead Responder handles a lead (respects reduced-motion settings)
- Featured Cinephile case study (Problem → Solution → Result) plus two project cards
- Project detail dialogs, tool-stack filters, accessible mobile menu
- Photo slot with "Available for new projects" badge
- Services grouped by outcome: "Win more customers" and "Save hours every week"
- "How I work" section: a layered diagram (your tools → automations → AI agents → optional app),
  "Your data stays yours" and "You work with me directly". Edit the four data promises in that section
  so they match exactly how you work.
- Logos of the tools you build with (n8n, HubSpot, Python, FastAPI, Docker, Supabase, PostgreSQL, Google Sheets,
  GitHub Actions) floating around the hero photo. They come from the free Simple Icons set (simpleicons.org);
  to swap one, copy its SVG path from there into the `tool-icons` block in `index.html`.

## Interactive n8n workflows

Project cards can switch between **Result** (screenshot) and **n8n workflow** (an interactive diagram generated from the real workflow export).
Clicking the diagram opens a full-screen viewer: zoom, drag to pan, and click any step to read what it does.
The diagrams are built only from node names, types and connections — no credentials, IDs or API keys are included.

## All projects page (inside `index.html`)

The whole site is one file. The home page shows only your chosen projects (the "Selected work" section).
The full list is a separate page inside the same file, at `index.html#all-projects`: when that link is opened,
the home sections are hidden and only the projects page is shown, with filters by type, search by name or tool,
and a details pop-up for each project. The "View all projects" button and the footer link open it, and
"Back to home" (or any menu link) returns to the home page.

**To add a project:** open `index.html`, find the `ALL_PROJECTS` list near the end (inside `<script>`), copy one `{ ... }` block,
paste it at the end of the list (keep the comma between blocks) and fill it in. The comments above the list explain each field.
- Put the screenshot in the `images/` folder and set `image: 'images/your-file.png'`. Leave it empty for a clean placeholder.
- `category` becomes a filter button automatically, so reuse a name to group projects together.
- Empty links stay hidden, and empty Problem / Solution / Result / steps are left out of the pop-up.
- `index.html#all-projects/key` (e.g. `index.html#all-projects/kaleemgpt`) opens that project's details directly, which is handy for sending a client one project.

When publishing, upload the `images/` folder together with `index.html`.

**Screenshot tabs on a home card:** the KaleemGPT card has Home / Web search / Models buttons that swap its screenshot.
To do the same on another card, copy its `<span class="shot-tabs">…</span>` block and set each button's `data-src` (image) and `data-alt` (description).

## Adding a new project

**1. Add the card**
Open `index.html` and search for `PROJECT CARD TEMPLATE`. Copy the block between the dashed lines, paste it just
above that comment (outside it), and replace the CAPITALISED parts:
- `KEY` (in two places) — a short id with no spaces, e.g. `invoicebot`
- the screenshot path, e.g. `images/invoicebot.png` (put the file in the `images` folder)
- name, description, result line, tech tags, demo/GitHub links (delete any link you don't have)

Each existing project is wrapped in `PROJECT: … START / END` comments, so you can also copy one of those.
If your new card makes the grid uneven, that's fine — it wraps automatically.

**2. Add its n8n workflow (optional)**
In n8n: rename nodes to plain English, add a note to each node (⚙ Settings → Notes — this becomes the
description clients see), then ⋯ menu → **Download**. Then run:

```bash
python3 tools/add_workflow.py index.html my-workflow.json KEY "Project name — n8n workflow" "One-line summary"
```

The **n8n workflow** tab appears on that card automatically. Run it again any time to update the diagram.
The `workflows` folder holds the plain-English labels and stages for the two existing diagrams
(`lead.labels.json`, `classroom.labels.json`). To update a diagram after changing the workflow in n8n, save the new export
next to its labels file with the same name (e.g. `workflows/classroom.json`) and run the script again with that key.
A labels file can also split a long workflow into numbered rows with `"__stages__"` — see `classroom.labels.json`.

**3. Check it** — open `index.html` in your browser, then publish as before.
(Upload the `images` folder together with `index.html`.)
