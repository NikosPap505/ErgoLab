# Μετάβαση από Create React App σε Vite

## 🎯 Βελτιώσεις

### Ταχύτητα Development
- **Instant Server Start**: ~50ms αντί για 10-30s
- **Hot Module Replacement (HMR)**: Άμεση ενημέρωση χωρίς reload
- **Fast Refresh**: Διατήρηση state κατά την ενημέρωση

### Ταχύτητα Build
- **Production Build**: 3-5x ταχύτερο build
- **Optimized Bundling**: Καλύτερο code splitting
- **Tree Shaking**: Πιο αποδοτικό

## 🔄 Αλλαγές που Έγιναν

### 1. Package.json
- ✅ Αφαίρεση `react-scripts`
- ✅ Προσθήκη `vite` και `@vitejs/plugin-react`
- ✅ Νέα scripts: `dev`, `build`, `preview`
- ✅ Προσθήκη `"type": "module"`

### 2. Configuration Files
- ✅ Δημιουργία `vite.config.js`
- ✅ Μετακίνηση `index.html` στο root
- ✅ Rename `index.js` → `index.jsx`

### 3. Environment Variables
- ✅ `process.env.REACT_APP_*` → `import.meta.env.VITE_*`
- ✅ `process.env.NODE_ENV` → `import.meta.env.MODE`

### 4. Dockerfile
- ✅ Update commands για Vite

## 📦 Εγκατάσταση

```bash
cd portal-web

# Διαγραφή παλιών dependencies
rm -rf node_modules package-lock.json

# Εγκατάσταση νέων dependencies
npm install
```

## 🚀 Development

```bash
# Local development
npm run dev

# Docker development
docker compose -f docker-compose.dev.yml up portal --build
```

## 🏗️ Production Build

```bash
# Local build
npm run build

# Preview production build
npm run preview

# Docker production build
docker compose build portal
```

## ⚡ Performance Comparison

| Μετρική | Create React App | Vite | Βελτίωση |
|---------|------------------|------|----------|
| Dev Server Start | 15-30s | 50-200ms | **~100x** |
| Hot Reload | 1-3s | 50-150ms | **~20x** |
| Production Build | 60-90s | 15-25s | **~4x** |
| Bundle Size | Baseline | -10-20% | Smaller |

## 🔧 Troubleshooting

### Issue: Import errors
**Λύση**: Βεβαιωθείτε ότι όλα τα imports χρησιμοποιούν `.jsx` extension όπου χρειάζεται

### Issue: Environment variables δεν φορτώνουν
**Λύση**: Χρησιμοποιήστε `VITE_` prefix και restart dev server

### Issue: Global variables undefined
**Λύση**: Προσθέστε στο `vite.config.js`:
```javascript
define: {
  global: 'window',
}
```

## 📚 Πόροι

- [Vite Documentation](https://vitejs.dev/)
- [Migration from CRA](https://vitejs.dev/guide/migration.html)
- [Vite Plugins](https://vitejs.dev/plugins/)
