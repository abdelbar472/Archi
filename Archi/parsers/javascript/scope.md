# Language: JavaScript / TypeScript
## Parser Status: In Progress (Tree‑sitter + Regex Fallback)
## Primary Parser: Tree‑sitter (optional) + Regex

---

## Domain & Main Use Cases

- Web frontends (React, Vue, Angular, Svelte)
- Node.js backends (Express, NestJS, Fastify, Koa)
- Full‑stack applications (Next.js, Nuxt)
- CLI tools, build scripts, and utilities
- TypeScript libraries & monorepos

---

## Key Frameworks & Patterns to Recognize

| Framework / Area | Patterns |
|------------------|----------|
| **React** | `function Component()`, `const Component = () =>`, `export default`, `useState`, `useEffect`, custom hooks (`use*`), HOCs, context providers |
| **Vue** | `export default { ... }`, `defineComponent`, `setup()`, `computed`, `watch`, Vuex/Pinia stores |
| **Angular** | `@Component`, `@Injectable`, `@NgModule`, `@Directive`, `@Pipe`, services, guards |
| **NestJS** | `@Controller`, `@Injectable`, `@Module`, `@Get`, `@Post`, `@Body`, `@Param`, middlewares, guards, interceptors |
| **Express / Fastify** | `app.get()`, `app.post()`, `router.get()`, middleware functions, `next()`, `req`, `res` |
| **Next.js** | `pages/`, `app/` directory, API routes (`/api/`), `getServerSideProps`, `getStaticProps`, middleware |
| **TypeScript** | `interface`, `type`, `enum`, generics, decorators (experimental) |
| **Testing** | Jest, Mocha, Vitest: `describe()`, `it()`, `test()`, `expect()`, `beforeEach` |

---

## Node Types Parser Must Detect

- `react_component` – functional or class component
- `react_hook` – custom hook (function starting with `use`)
- `vue_component` – Vue component definition
- `angular_component` – class with `@Component` decorator
- `nestjs_controller` – class with `@Controller`
- `nestjs_service` – class with `@Injectable` (or used as service)
- `nestjs_module` – class with `@Module`
- `express_route` – route handler (e.g., `app.get('/path', ...)`)
- `class` – ES6 class
- `function` – named function, arrow function (assigned)
- `method` – class method
- `interface` – TypeScript interface
- `type_alias` – TypeScript type alias
- `enum` – TypeScript enum
- `module` – file as a module
- `router` – Express router or Next.js router
- `service` – generic service class/function

---

## What to Skip / Low Priority

- Minified or obfuscated code (heuristic: long single-line files)
- Vendor libraries in `node_modules` (already ignored)
- Test files (but we may still want to capture test utilities)
- Configuration files (`.config.js`, `webpack.config.js` – unless they contain logic)
- Large generated files (e.g., `*.generated.ts`)

---

## Parser Strategy

- **Primary:** Tree‑sitter (if installed) gives AST‑level accuracy for imports/exports, function definitions, class declarations, decorators, etc.
- **Fallback:** Regex‑based scanner for quick extraction of common patterns (functions, classes, `export`, `import`, etc.) – less precise but works without extra dependencies.
- **Import Resolution:** Use `resolve_path_alias()` to map import statements (relative paths, aliases like `@/`, `~`) to actual file nodes.
- **Cross‑file References:** Use edges `imports`, `calls`, `defines` to connect files and definitions.

---

## Test Repositories Suggestions

- [facebook/react](https://github.com/facebook/react) – React
- [vuejs/core](https://github.com/vuejs/core) – Vue
- [angular/angular](https://github.com/angular/angular) – Angular
- [nestjs/nest](https://github.com/nestjs/nest) – NestJS
- [vercel/next.js](https://github.com/vercel/next.js) – Next.js
- Any internal React/Node monorepo

---

## Additional Considerations

- **TypeScript support:** Parse `.ts` and `.tsx` files. Type information may be used to enrich nodes (but not required).
- **Decorators:** Detect and attach `@` metadata to nodes (e.g., `@Controller`).
- **Exports:** Track `export default` and named exports to determine the primary symbol of a file.
- **Aliases:** Handle common path aliases (`@/`, `~`, `@app`, etc.) via the `resolve_path_alias` method.

---

This spec guides the development of a robust JavaScript/TypeScript parser that integrates seamlessly into the Archi toolchain.