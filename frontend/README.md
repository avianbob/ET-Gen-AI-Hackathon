# PharmAI - Frontend Application

React-based frontend application for the PharmAI pharmaceutical analysis platform, built with Vite for fast development and optimized builds.

## 🚀 Quick Start

### Prerequisites

- Node.js 18 or higher
- npm (comes with Node.js)

### Installation

1. **Install dependencies:**

```bash
npm install
```

2. **Configure environment variables:**

```bash
cp .env.example .env
# Edit .env and set VITE_API_URL to your backend URL
```

3. **Start the development server:**

```bash
npm run dev
```

The application will start on `http://localhost:5173` (default Vite port).

## 📋 Environment Variables

Create a `.env` file in the root directory with the following variables:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `VITE_API_URL` | Backend API URL | **Yes** | `http://localhost:8000` |

> **Important**: In Vite, environment variables must be prefixed with `VITE_` to be accessible in the frontend code.

### Example `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

## 🏗️ Project Structure

```
PharmAI-main/
├── src/
│   ├── api/
│   │   └── endpoints.ts      # API client and endpoints
│   ├── components/
│   │   ├── ReportComponents.tsx  # Report-related components
│   │   └── sidebar.tsx           # Sidebar navigation
│   ├── pages/
│   │   └── Dashboard.tsx     # Main dashboard page
│   ├── App.tsx               # Root component
│   ├── main.jsx              # Application entry point
│   └── index.css             # Global styles
├── public/                   # Static assets
├── package.json              # Dependencies and scripts
└── vite.config.js            # Vite configuration
```

## 🛠️ Available Scripts

### `npm run dev`
Start the development server with hot module replacement (HMR).

### `npm run build`
Build the application for production. Output will be in the `dist/` directory.

### `npm run preview`
Preview the production build locally.

### `npm run lint`
Run ESLint to check code quality.

## 🔌 API Integration

The frontend communicates with the backend through the API client defined in `src/api/endpoints.ts`.

### API Client Usage

```typescript
import { AgentAPI } from './api/endpoints';

// Run an agent analysis
const response = await AgentAPI.runAgent({
  query: "Analyze drug X",
  complexity: 5
});
```

## 🎨 Technologies Used

- **React 19**: UI library
- **Vite**: Build tool and dev server
- **TypeScript**: Type safety
- **Axios**: HTTP client
- **Recharts**: Data visualization
- **Lucide React**: Icon library

## 🐛 Troubleshooting

### Common Issues

**Error: `Cannot connect to API`**
- Verify the backend server is running
- Check `VITE_API_URL` in `.env` matches your backend URL
- Ensure CORS is properly configured on the backend

**Error: Environment variables not loading**
- Restart the dev server after creating/modifying `.env`
- Ensure variables are prefixed with `VITE_`
- Check for typos in variable names

**Error: `Module not found`**
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again
- Clear npm cache: `npm cache clean --force`

**Error: Port 5173 already in use**
- Change the port in `vite.config.js` or use `npm run dev -- --port 3000`

**Build errors**
- Ensure all TypeScript types are properly defined
- Check for missing dependencies
- Review ESLint errors: `npm run lint`

## 🔧 Development

### Adding New Components

1. Create component file in `src/components/`
2. Import and use in your pages
3. Follow React best practices and TypeScript types

### Adding New API Endpoints

1. Update `src/api/endpoints.ts`
2. Add new interface types if needed
3. Export new API functions

### Styling

- Global styles: `src/index.css`
- Component-specific styles: Use CSS modules or inline styles
- Consider adding a CSS framework if needed

## 📦 Dependencies

Key dependencies:
- `react` & `react-dom`: UI framework
- `axios`: HTTP client
- `recharts`: Chart library
- `lucide-react`: Icons
- `vite`: Build tool

See `package.json` for complete list.

## 🚀 Production Build

1. **Build the application:**

```bash
npm run build
```

2. **Preview the build:**

```bash
npm run preview
```

3. **Deploy:**

The `dist/` directory contains the production-ready files. Deploy this directory to your hosting service (Vercel, Netlify, etc.).

## 🔐 Security Notes

- Never commit `.env` files with sensitive data
- API keys should be handled server-side when possible
- Use HTTPS in production
- Implement proper authentication for production use

## 📄 License

[Add license information]

---

For backend setup, see [Agentichost README](../Agentichost-main/README.md)
