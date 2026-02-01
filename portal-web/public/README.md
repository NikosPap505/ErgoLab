# ErgoLab - Demo

This is a demo deployment of the ErgoLab frontend application.

## Backend Required

This frontend application requires a backend API server to function. The backend is not deployed in this demo.

### To run locally with backend:

1. Clone the repository
2. Start the backend: `docker compose -f docker-compose.dev.yml up`
3. Start the frontend: `cd portal-web && npm run dev`
4. Access at `http://localhost:3000`

### To deploy with backend:

Set the `VITE_API_URL` environment variable to your deployed backend URL during build:

```bash
VITE_API_URL=https://your-backend-api.com npm run build
```

## Repository

https://github.com/nikospap505/ErgoLab
