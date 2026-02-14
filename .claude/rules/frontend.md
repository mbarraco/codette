# Frontend Rules

## Project Structure
- Frontend lives under `web/src/` with these packages: `components/`, `hooks/`, `pages/`, `types/`, `utils/`.
- Entry point is `main.tsx` (routing + layout). `App.tsx` is the home page component.
- Build: `npm run build` (runs `tsc && vite build`). Must pass with zero errors before any PR.
- Dev server: `npm run dev` from `web/` — never run the frontend in Docker for development.

## Component Rules
- Use function components — never class components.
- One component per file, PascalCase filename matching the component name.
- Export components as `export default`.
- Define props as a `type` named `<Component>Props`. Destructure in the function signature.
- Place reusable components in `web/src/components/`.
- Place page-level components in `web/src/pages/`.
- Pair each component with a `.module.css` file when it needs styling.

```tsx
// web/src/components/StatusBadge.tsx
import styles from "./StatusBadge.module.css";

type StatusBadgeProps = {
  status: string;
  variant?: "queue" | "run";
};

function StatusBadge({ status, variant = "queue" }: StatusBadgeProps) {
  return <span className={styles.badge}>{status}</span>;
}

export default StatusBadge;
```

## Type Rules
- Keep all API response types in `web/src/types/api.ts`.
- Use `snake_case` for type fields that map to backend JSON responses.
- Never redeclare API types inline in page or component files — import from `types/api.ts`.
- Use `import type { ... }` for type-only imports.

## Data Fetching Rules
- Use `useFetch<T>(url, opts?)` from `hooks/useFetch.ts` for read operations.
- Use `{ pollingInterval: number }` for real-time data (e.g., monitor page).
- Call `refetch()` after mutations (POST, PATCH, DELETE) to re-sync with the server.
- Never write raw `useState` + `useEffect` + `fetch` for data loading — that pattern is encapsulated in `useFetch`.
- For write operations (form submissions, deletes), use `fetch()` directly with proper error handling — `useFetch` is for reads only.

```tsx
// Read
const { data: problems, loading, refetch } = useFetch<Problem[]>("/api/v1/problems/");

// Write then re-sync
const handleDelete = async (p: Problem) => {
  await fetch(`/api/v1/problems/${p.uuid}`, { method: "DELETE" });
  refetch();
};
```

> **When to outgrow useFetch:** If the app needs optimistic updates, dependent queries, cache invalidation across components, or mutation state tracking, adopt React Query (TanStack Query) rather than extending `useFetch`. It follows the same `{ data, loading, error }` pattern but handles these edge cases.

## Hook Rules
- Place custom hooks in `web/src/hooks/`, one hook per file.
- Use named exports for hooks.
- Hooks must start with `use` and follow the [Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks).

## Utility Rules
- Place utility functions in `web/src/utils/`, one file per concern.
- Use named exports for utility functions.
- Utilities must be framework-agnostic — never import React in utility files.

## Styling Rules
- Use CSS modules (`.module.css`) for component-scoped styles.
- Use `camelCase` for class names in CSS modules.
- Use CSS custom properties from `:root` in `index.css` for design tokens (colors, spacing scale) — never hardcode palette hex values in module CSS.
- Use `rem` for spacing — reserve `px` for borders and fine visual details (box-shadows, outlines).

### Global styles (`web/src/index.css`)
- CSS variables, resets, base element styles.
- Shared classes reused across 2+ components (`.btn-primary`, `.btn-danger`, `.page`, `.cellActions`, `.error-text`).
- Table, form element, modal/overlay base styles.

### Module styles (`.module.css`)
- Anything used by a single component or page.
- If a pattern appears in 2+ modules, extract it to a shared component or promote it to `index.css`.

## Shared Component Inventory
Before building page-specific UI, check if a shared component already exists:

| Component | Purpose | Use instead of... |
|-----------|---------|-------------------|
| `<PageHeader>` | Page title + optional action button | Duplicating a flex header div |
| `<DataTable>` | Loading / empty / content wrapper | `loading ? ... : empty ? ... : <table>` ternary chains |
| `<StatusBadge>` | Color-coded status pills | Inline badge class switching logic |
| `<CopyButton>` | Clipboard copy with feedback | Inline clipboard API + setTimeout logic |

Utilities: `truncateUuid()` from `utils/format.ts`, `copyToClipboard()` from `utils/clipboard.ts`.

## Accessibility
- Use semantic HTML elements (`<button>`, `<table>`, `<nav>`, `<section>`, `<form>`) — never `<div onClick>` for interactive elements.
- Every `<button>` without visible text must have an `aria-label`.
- Form inputs must be associated with `<label>` elements (wrapping or `htmlFor`).
- Destructive actions (delete) must have a confirmation step before executing.
- Ensure focus is visible — never remove `:focus` outlines without providing an alternative.
- Use `type="button"` on buttons that are not form submits to prevent accidental submission.

## Error Handling
- Display user-facing errors inline near the action that caused them — never silently swallow `catch` blocks.
- Show error text with the `.error-text` class or a styled `<p>` in the form area.
- For fetch errors in `useFetch`, the `error` field is available — surface it in the UI when relevant.
- Never show raw stack traces or internal error objects to the user — extract `.message` or provide a fallback string.

## Performance
- Wrap expensive computations in `useMemo` and stable callback references in `useCallback` only when they are passed as props to child components or used as `useEffect` dependencies. Do not memoize by default.
- For pages with large tables, consider pagination from the API before reaching for client-side virtualization.
- When the app grows past 5-6 routes, add `React.lazy()` + `<Suspense>` for route-level code splitting.

## Security
- Never use `dangerouslySetInnerHTML` unless the content has been sanitized with a library like DOMPurify.
- Never interpolate user input into URLs without encoding — use `encodeURIComponent()`.
- API calls go through the Vite proxy (`/api/...`) — never hardcode backend URLs or expose internal hostnames.

## Routing
- Register every new page route in `web/src/main.tsx` inside `<Routes>`.
- Add a `<NavLink>` in the `<Layout>` component for every user-facing page.
- Use `:uuid` for dynamic route parameters — never expose internal integer IDs in URLs.

## State Management
- Use React hooks (`useState`, `useReducer`, `useRef`, `useCallback`, `useMemo`).
- Keep form state local to the component that owns the form.
- Use React Context for cross-cutting concerns when needed (auth, theme, toast notifications) — not for data fetching or page-level state.

## Form Handling
- Prevent default with `e.preventDefault()`.
- Track `submitting` state and disable the submit button while in progress.
- Show feedback in button text (e.g., `"Saving..."` → `"Save"`).
- After successful mutation, call `refetch()` to re-sync — never manually update local arrays to mirror server state.
- Display validation/API errors inline near the form.

## Conditional Rendering
- Prefer `{condition ? <Element /> : null}` over `{condition && <Element />}` to avoid accidentally rendering falsy values (`0`, `""`).

## Testing (when tests are added)
- Use Vitest + React Testing Library.
- Test behavior, not implementation — query by role, label, and text, not by CSS class or test ID.
- One test file per component/page: `ComponentName.test.tsx` alongside the source file or mirrored under `__tests__/`.
- Mock API calls at the `fetch` level (e.g., MSW) — never mock hooks or internal functions.

## Vite Proxy
- `/api` requests are proxied to the backend by `vite.config.ts`.
- Docker vs localhost detection is automatic — never hardcode proxy targets.
- Override with `VITE_PROXY_TARGET` env var when needed.
