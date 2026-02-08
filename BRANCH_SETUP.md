# Main Branch Setup Instructions

## Purpose
This document provides instructions for setting up the main branch of this repository.

## Current State
- The repository currently has the initial files (README.md, .gitignore)
- A main branch needs to be created to allow pushes from local repositories

## Setup Steps

### Option 1: Merge this PR to main (Recommended)
1. When merging this Pull Request, select "main" as the target branch
2. If the main branch doesn't exist, GitHub will create it automatically
3. Set main as the default branch in repository settings

### Option 2: Manual Creation via GitHub UI
1. Go to the repository on GitHub
2. Click on the branch dropdown
3. Type "main" and press Enter to create the branch
4. Go to Settings → Branches
5. Set "main" as the default branch

### Option 3: Command Line (for repository owner with write access)
```bash
# Clone the repository
git clone https://github.com/sainbind/pico2_plotter.git
cd pico2_plotter

# Create and push main branch
git checkout -b main
git push -u origin main

# Set main as default branch (requires GitHub CLI or web UI)
gh repo edit --default-branch main
```

## Verification
Once the main branch is created, you can verify it by:
```bash
git ls-remote --heads https://github.com/sainbind/pico2_plotter.git
```

You should see `refs/heads/main` in the output.

## Next Steps
After the main branch is set up, developers can:
1. Clone the repository: `git clone https://github.com/sainbind/pico2_plotter.git`
2. Make changes locally
3. Push to main: `git push origin main`
