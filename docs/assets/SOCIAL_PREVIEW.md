# Social Preview Image Guide

## Current Status
⚠️ **TODO:** Create and upload social preview image to GitHub repository settings.

## Recommended Specifications

- **Dimensions:** 1280x640 pixels (2:1 aspect ratio)
- **Format:** PNG or JPG
- **File size:** < 1 MB
- **Safe zone:** Keep important content within 1200x600px center area

## Design Elements

### Layout Suggestion
```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  🛡️  Security Assistant                            │
│                                                     │
│  Enterprise-grade security orchestration           │
│  for everyone. No license required.                │
│                                                     │
│  ✓ Multi-scanner orchestration                     │
│  ✓ KEV + Reachability + FP Detection               │
│  ✓ GitLab Ultimate-level intelligence              │
│                                                     │
│  github.com/AMEOBIUS/security-assistant            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Color Scheme
- **Background:** Dark gradient (#1a1a2e → #16213e)
- **Primary text:** White (#ffffff)
- **Accent:** Cyan/Blue (#00d4ff or #4a90e2)
- **Shield icon:** Gradient (cyan → blue)

### Typography
- **Title:** Bold, 72-80px (e.g., Inter Bold, Roboto Bold)
- **Tagline:** Regular, 36-40px
- **Features:** Regular, 28-32px
- **URL:** Light, 24px

## Tools for Creation

### Online (No Design Skills Required)
1. **Canva** (https://canva.com)
   - Use "GitHub Social Media" template (1280x640)
   - Free tier sufficient

2. **Figma** (https://figma.com)
   - Community templates available
   - More control over design

### Command-Line (Automated)
```bash
# Using ImageMagick
convert -size 1280x640 gradient:#1a1a2e-#16213e \
  -font Arial-Bold -pointsize 72 -fill white \
  -gravity center -annotate +0-100 "🛡️ Security Assistant" \
  -pointsize 36 -annotate +0+0 "Enterprise-grade security orchestration" \
  -pointsize 28 -annotate +0+100 "✓ Multi-scanner ✓ KEV ✓ Reachability" \
  social-preview.png
```

### Python Script (Pillow)
```python
from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGB', (1280, 640), color='#1a1a2e')
draw = ImageDraw.Draw(img)

# Add text layers
font_title = ImageFont.truetype("arial.ttf", 72)
font_subtitle = ImageFont.truetype("arial.ttf", 36)

draw.text((640, 200), "🛡️ Security Assistant", 
          fill='white', font=font_title, anchor='mm')
draw.text((640, 300), "Enterprise-grade security orchestration",
          fill='white', font=font_subtitle, anchor='mm')

img.save('social-preview.png')
```

## Upload Instructions

1. Go to: https://github.com/AMEOBIUS/security-assistant/settings
2. Scroll to "Social preview"
3. Click "Edit" → "Upload an image"
4. Upload `social-preview.png`
5. Verify preview looks good

## Testing

After upload, test the preview by sharing the repo URL in:
- Slack
- Discord
- Twitter/X
- Telegram
- LinkedIn

The preview should display automatically with the image, title, and description.

## Example References

Good examples from popular projects:
- https://github.com/microsoft/vscode (clean, professional)
- https://github.com/vercel/next.js (modern, gradient)
- https://github.com/tailwindlabs/tailwindcss (bold, colorful)
