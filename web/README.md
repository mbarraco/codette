# Codette Web

React frontend built with Vite and TypeScript.

## Development

### Local Setup

```bash
# Install dependencies
npm install

# Start dev server
npm run dev
```

### Docker

```bash
docker build -t codette-web .
docker run -p 5173:5173 codette-web
```

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
