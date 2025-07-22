# Running OpenAI Agent Tool with Playwright

## Browser Mode Configuration

The `openai_agent_tool.py` script supports two browser modes:
- **Headless mode** (`"browser_headless": true`, default): Browser runs invisibly, no display required
- **Non-headless mode** (`"browser_headless": false`): Browser shows UI, requires a display (physical or virtual)

## When You Need Xvfb

You need Xvfb (X Virtual Framebuffer) when:
1. Your config has `"browser_headless": false` (you want to see/debug the browser)
2. AND you're on a system without a display (like a server, SSH session, or container)

If you get this error:
```
RuntimeError: No display available for non-headless browser
```

You have two options:
1. Use xvfb-run (recommended for debugging)
2. Change your config to `"browser_headless": true` (recommended for production)

## Installation

Install Xvfb:
```bash
# Ubuntu/Debian
sudo apt-get install xvfb

# CentOS/RHEL/Fedora
sudo yum install xorg-x11-server-Xvfb

# macOS (using Homebrew)
brew install --cask xquartz
```

## Running the Script

### Option 1: Using xvfb-run (Recommended)
```bash
xvfb-run -a python openai_agent_tool.py --url https://example.com --task "Extract data"
```

### Option 2: Using the helper script
```bash
./run_with_xvfb.sh --url https://example.com --task "Extract data"
```

### Option 3: Starting Xvfb manually
```bash
# Start Xvfb on display :99
Xvfb :99 -screen 0 1024x768x24 &

# Set the DISPLAY environment variable
export DISPLAY=:99

# Run the script
python openai_agent_tool.py --url https://example.com --task "Extract data"
```

### Option 4: Disable headless mode
If you have a GUI available, you can disable headless mode in the configuration:
```python
browser_headless: bool = False
```

## Troubleshooting

If you see the error:
```
ERROR:ozone_platform_x11.cc:249] Missing X server or $DISPLAY
```

This means the script cannot find a display. Use one of the methods above to provide a virtual display.