'use client';

import { useEffect, useState } from 'react';

export default function Page() {
  const [serverData, setServerData] = useState<{ message: string } | null>(null);
  const [clientData, setClientData] = useState<{ message: string } | null>(null);

  useEffect(() => {
    // Client-side fetch to test CORS
    fetch('http://127.0.0.1:8000/api/hello')
      .then((res) => res.json())
      .then((data) => setClientData(data))
      .catch((err) => console.error('Client-side fetch error:', err));
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>Next.js + FastAPI Connection</h1>
      
      <section style={{ marginBottom: '20px' }}>
        <h2>Client-side Fetch (CORS Test)</h2>
        {clientData ? (
          <p>Response from backend: <strong>{clientData.message}</strong></p>
        ) : (
          <p>Loading client-side data...</p>
        )}
      </section>
    </div>
  );
}