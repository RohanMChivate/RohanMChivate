<div align="center">

# ⚡ TERMINAL OS // PROFILE TELEMETRY ⚡

[![Refresh Telemetry](https://github.com/RohanMChivate/RohanMChivate/actions/workflows/update-profile-art.yml/badge.svg)](../../actions)
![Status](https://img.shields.io/badge/SYS_STATUS-OPTIMAL-39d353?style=flat-square&logo=gnubash&logoColor=white)
![SVG](https://img.shields.io/badge/GRAPHICS-PURE_SVG-58a6ff?style=flat-square&logo=svg&logoColor=white)
![Tokenless](https://img.shields.io/badge/AUTHENTICATION-ZERO_TOKEN-bc8cff?style=flat-square&logo=github&logoColor=white)

<br />

<h3><code>user@github ~ $ ./contributions.sh</code></h3>

<img src="./contrib-heatmap.svg" width="860" alt="GitHub Contribution Heatmap" />

<br /><br />

<h3><code>user@github ~ $ whoami</code></h3>

<table border="0" cellpadding="0" cellspacing="0">
  <tr>
    <td valign="top" width="370" align="center">
      <img src="./avi-ascii.svg" width="370" alt="Terminal ASCII Portrait" />
    </td>
    <td valign="top" width="490" align="center">
      <img src="./info-card.svg" width="490" alt="Terminal Info Card" />
    </td>
  </tr>
</table>

</div>

---

### ⚙️ Architecture & Design Principles

1. **Pure SVG Animation**: Zero client-side JavaScript or external stylesheets. All animations are self-contained inside the generated SVGs using native SMIL (`<animate>`, `<clipPath>`) and inline CSS `@keyframes`, ensuring unhindered rendering inside GitHub's sanitized markdown image tags.
2. **Zero External Tokens**: Public GitHub profile HTML (`https://github.com/users/<username>/contributions`) is parsed via `BeautifulSoup` to extract streaks, calendar mappings, and activity levels without requiring a Personal Access Token.
3. **Execution Separation**: Heavy computer vision & AI dependencies (`rembg`, `opencv-python`, `pillow`) run exclusively on local development machines for one-time photo prep. The daily automated GitHub Actions CI pipeline remains ultra-minimal, installing only `requests` and `beautifulsoup4`.

---

### 🛠️ Local Generation & Customization

```bash
# 1. Install local dependencies
pip install -r scripts/requirements.txt

# 2. Process your profile picture (rembg background removal, white canvas composite, CLAHE contrast enhancement)
python scripts/prep_photo.py assets/my_photo.jpg --output source-prepped.png

# 3. Generate animated ASCII portrait SVG (staggered horizontal SMIL wipe animation)
python scripts/make_ascii_svg.py --input source-prepped.png --output avi-ascii.svg

# 4. Generate system info card SVG
python scripts/make_info_card.py --output info-card.svg

# 5. Scrape public telemetry & render contribution heatmap
python scripts/fetch_contributions.py <your-github-username>
python scripts/render_heatmap_svg.py
```

---

### 🔄 CI Automation Workflow

The GitHub Actions workflow in [`.github/workflows/update-profile-art.yml`](.github/workflows/update-profile-art.yml) runs daily at `06:17 UTC`, scrapes the user's latest contributions, re-renders `contrib-heatmap.svg`, and auto-commits the updated assets using `stefanzweifel/git-auto-commit-action@v5`.
