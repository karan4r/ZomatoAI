import { useState } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || ''

export default function App() {
  const [place, setPlace] = useState('Banashankari')
  const [minPrice, setMinPrice] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [minRating, setMinRating] = useState('3.5')
  const [cuisines, setCuisines] = useState('North Indian, Chinese')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResults([])
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
      <div className="results">
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
            <div style={{ marginTop: '0.75rem' }}>
              <button
                type="button"
                className="primary"
                style={{ marginRight: '0.5rem', padding: '0.4rem 0.8rem', fontSize: '0.875rem' }}
                onClick={() => sendFeedback(r.id, 'liked')}
              >
                Like
              </button>
              <button
                type="button"
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.875rem', background: '#404040', color: '#e5e5e5', border: 'none', borderRadius: 6, cursor: 'pointer' }}
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
