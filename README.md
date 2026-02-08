# pico2_plotter
Pico2 Plotter

## Initial Setup

This repository is initialized and ready to receive pushes from local repositories.

### Setting up the main branch

To create a main branch that can be pushed to from a local repository:

1. **From GitHub UI**: 
   - Go to repository Settings → Branches
   - Change the default branch to `main` (create it if needed)

2. **From command line** (for repository owner):
   ```bash
   git checkout -b main
   git push -u origin main
   ```

### Pushing from a local repository

Once the main branch is set up, you can push to it from your local repository:

```bash
git remote add origin https://github.com/sainbind/pico2_plotter.git
git push -u origin main
```
