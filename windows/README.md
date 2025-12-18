# Windows Installer Assets

This directory contains assets for the Inno Setup installer.

## Required Files

### icon.ico
Application icon file (256x256 recommended, with multiple sizes: 16x16, 32x32, 48x48, 256x256)
- Used for: Application icon, uninstaller icon, desktop shortcuts
- Format: ICO file with multiple resolutions
- Tool: Use an online converter or GIMP to create from PNG

### wizard-image.bmp
Large wizard image displayed on the left side of the installer wizard
- Dimensions: 164x314 pixels
- Format: BMP (24-bit)
- Content: Branding image or product screenshot

### wizard-small-image.bmp
Small wizard image displayed in the top-right corner
- Dimensions: 55x58 pixels
- Format: BMP (24-bit)
- Content: Logo or icon

## Creating Placeholder Files

If you don't have custom graphics yet, you can create simple placeholder files:

### For icon.ico:
1. Create a 256x256 PNG with your logo or a simple design
2. Convert to ICO format using an online tool like:
   - https://convertio.co/png-ico/
   - https://www.icoconverter.com/
3. Ensure multiple sizes are included (16, 32, 48, 256)

### For wizard images:
1. Create BMP files with the specified dimensions
2. Use solid colors or simple gradients as placeholders
3. Add your logo or branding when ready

## Temporary Solution

For testing purposes, you can comment out the icon lines in scanner_watcher2.iss:
```
; SetupIconFile=windows\icon.ico
; WizardImageFile=windows\wizard-image.bmp
; WizardSmallImageFile=windows\wizard-small-image.bmp
```

The installer will work without these files, but will use default Inno Setup graphics.
