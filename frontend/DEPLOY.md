# Deploying PharmAI

## Two common issues and fixes

### 1. `Failed to load resource: 404` on `/dash` (or any route)

**Cause:** This is a **Single Page App (SPA)**. When you open or refresh a URL like `yoursite.com/dash`, the browser asks the **server** for `/dash`. There is no file at that path, so the server returns 404.

**Fix (standard practice):** Configure your host so that for any path it **serves `index.html`** (with status 200). The React app loads once, then React Router handles `/dash` on the client. This is called **SPA fallback** or **rewrite rules**.

This repo already includes config for common hosts (see “Fix by platform” below). After adding the config, **redeploy** so the server uses it.

---

### 2. `Unchecked runtime.lastError: The message port closed before a response was received`

**Cause:** This comes from a **browser extension** (e.g. React DevTools, Redux DevTools, ad blockers, password managers, Grammarly), not from your app. The extension injects a script and talks to its background page; sometimes that connection closes before a response, and Chrome logs this.

**Fix (standard practice):** You can safely **ignore** this in production. It does not affect your app. If it bothers you during development:

- Test in **Incognito/Private** (most extensions are disabled), or  
- Disable extensions one by one to find which one logs it.

No code changes in your project are required.

---

## Fix 404 by platform

### Vercel
`vercel.json` in this repo rewrites all routes to `index.html`. Deploy as usual.

### Netlify
`public/_redirects` is copied to `dist/` on build. Deploy with build command `npm run build` and publish directory `dist`.

### Firebase Hosting
1. `npm run build`
2. Deploy: `firebase deploy` (this repo’s `firebase.json` rewrites all routes to `index.html`; set `public` to `dist`).

### Google Cloud Run / nginx
Use the included `nginx.conf`: it has `try_files $uri $uri/ /index.html` so every path serves the SPA. Use it in your Docker image and redeploy.

### Other static hosts
Configure a **rewrite** or **SPA fallback** so that all (or all non-asset) requests return `index.html` with status **200**.

---

## Build

```bash
npm run build
```

Output is in `dist/`. Point your host’s document root to `dist` and ensure SPA fallback is enabled as above.
