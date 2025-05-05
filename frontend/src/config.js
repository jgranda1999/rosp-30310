   // Config for API endpoints
   const API_URL = process.env.NODE_ENV === 'production' 
     ? 'https://rosp-30310-production.up.railway.app' 
     : 'http://localhost:5001';
   
   export { API_URL };