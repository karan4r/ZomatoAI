import { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || ''

export default function App() {
  const [place, setPlace] = useState('Banashankari')
  const [minPrice, setMinPrice] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [minRating, setMinRating] = useState('3.5')
  const [cuisines, setCuisines] = useState('North Indian, Chinese')
  const [results, setResults] = useState([])
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [health, setHealth] = useState({ status: 'loading', message: 'Checking API…' })

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => res.json())
      .then((data) => {
        setHealth({
          status: data.status === 'ok' ? 'ok' : 'degraded',
          message: data.status === 'ok' ? 'API connected' : `API: ${data.status}`,
          checks: data.checks,
        })
      })
      .catch(() => setHealth({ status: 'error', message: 'Cannot reach API' }))
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResults([])
    setMeta(null)
    const body = {
      place: place || null,
      min_rating: minRating ? parseFloat(minRating) : null,
      cuisines: cuisines ? cuisines.split(',').map((c) => c.trim()).filter(Boolean) : [],
      limit: 5,
    }
    if (minPrice || maxPrice) {
      body.price_range = {
        min: minPrice ? parseInt(minPrice, 10) : null,
        max: maxPrice ? parseInt(maxPrice, 10) : null,
      }
    }
    try {
      const res = await fetch(`${API_BASE}/recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setResults(data.recommendations || [])
      setMeta(data.meta || null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const sendFeedback = async (restaurantId, action) => {
    try {
      await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ restaurant_id: restaurantId, action }),
      })
    } catch (_) {}
  }

  return (
    <div className="app">
      <h1>ZomatoAI – Restaurant recommendations</h1>
      <div className={`health ${health.status}`}>{health.message}</div>

      <form className="form" onSubmit={handleSubmit}>
        <label>
          Place / area
          <input
            type="text"
            value={place}
            onChange={(e) => setPlace(e.target.value)}
            placeholder="e.g. Banashankari"
          />
        </label>
        <div className="row">
          <label>
            Min price (for two)
            <input
              type="number"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
              placeholder="Optional"
            />
          </label>
          <label>
            Max price (for two)
            <input
              type="number"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
              placeholder="Optional"
            />
          </label>
        </div>
        <label>
          Min rating (0–5)
          <input
            type="number"
            min="0"
            max="5"
            step="0.5"
            value={minRating}
            onChange={(e) => setMinRating(e.target.value)}
          />
        </label>
        <label>
          Cuisines (comma-separated)
          <input
            type="text"
            value={cuisines}
            onChange={(e) => setCuisines(e.target.value)}
            placeholder="North Indian, Chinese"
          />
        </label>
        <button type="submit" className="primary" disabled={loading}>
          {loading ? 'Finding recommendations…' : 'Get recommendations'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}
      {loading && <p className="loading">Loading…</p>}

      {meta && !loading && (
        <div className="meta-bar">
          {meta.candidate_count != null && `Candidates: ${meta.candidate_count}`}
          {meta.latency_seconds != null && ` · Latency: ${meta.latency_seconds}s`}
        </div>
      )}

      <div className="results">
        {!loading && results.length === 0 && (meta || error) && !error && (
          <div className="empty-state">No recommendations found. Try different filters or run Phase 1 ingestion.</div>
        )}
        {results.map((r) => (
          <div key={r.id} className="card">
            <h3>{r.name}</h3>
            <div className="meta">
              {r.avg_rating != null && `Rating: ${r.avg_rating} · `}
              {r.avg_cost_for_two != null && `Cost for two: ₹${r.avg_cost_for_two}`}
              {r.location && ` · ${r.location}`}
            </div>
            {r.summary_reason && <p className="reason">{r.summary_reason}</p>}
            {r.cuisines?.length > 0 && (
              <div className="tags">
                {r.cuisines.map((c) => (
                  <span key={c} className="tag">{c}</span>
                ))}
                {r.best_for?.map((b) => (
                  <span key={b} className="tag">Best for: {b}</span>
                ))}
              </div>
            )}
            <div className="actions">
              <button
                type="button"
                className="primary"
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.875rem' }}
                onClick={() => sendFeedback(r.id, 'liked')}
              >
                Like
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => sendFeedback(r.id, 'dismissed')}
              >
                Dismiss
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
