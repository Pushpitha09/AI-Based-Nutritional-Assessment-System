import { useEffect, useState, useCallback } from "react";
import { X } from "lucide-react";
import { useAuth } from "../AuthContext";
import { searchFoods, addDiaryEntry, listDiaryEntries, deleteDiaryEntry } from "../api";
import Sidebar from "./Sidebar";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

export default function Dashboard() {
  const { token } = useAuth();

  const [entryDate, setEntryDate] = useState(todayISO());
  const [meal, setMeal] = useState("breakfast");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [selectedFood, setSelectedFood] = useState(null);
  const [portionGrams, setPortionGrams] = useState(100);
  const [entries, setEntries] = useState([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const loadEntries = useCallback(async () => {
    try {
      const data = await listDiaryEntries(token, entryDate);
      setEntries(data);
    } catch (err) {
      setError(err.message);
    }
  }, [token, entryDate]);

  useEffect(() => {
    loadEntries();
  }, [loadEntries]);

  // Debounced live search against the seeded food dataset
  useEffect(() => {
    if (query.trim().length === 0) {
      setResults([]);
      return;
    }
    setSearching(true);
    const timer = setTimeout(async () => {
      try {
        const data = await searchFoods(token, query.trim());
        setResults(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setSearching(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query, token]);

  function pickFood(food) {
    setSelectedFood(food);
    setQuery(food.name);
    setResults([]);
  }

  async function handleAddToDiary(e) {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    if (!selectedFood) {
      setError("Search for a food and select one from the list first.");
      return;
    }
    try {
      await addDiaryEntry(token, {
        entryDate,
        meal,
        foodItemId: selectedFood.id,
        portionGrams: Number(portionGrams),
      });
      setSuccessMsg("Meal logged.");
      setSelectedFood(null);
      setQuery("");
      setPortionGrams(100);
      loadEntries();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleRemove(entryId) {
    try {
      await deleteDiaryEntry(token, entryId);
      loadEntries();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="dash-shell">
      <Sidebar />

      <main className="dash-main">
        <h1>Food diary</h1>
        <p className="auth-subtitle">Search foods and log portions — nutrients computed automatically.</p>

        <div className="diary-grid">
          <div className="diary-card">
            <h3>Log meal</h3>

            {successMsg && <div className="form-banner-success">{successMsg}</div>}
            {error && <div className="form-banner-error">{error}</div>}

            <form onSubmit={handleAddToDiary}>
              <div className="field-group">
                <label htmlFor="entryDate">Date</label>
                <input
                  id="entryDate"
                  type="date"
                  value={entryDate}
                  onChange={(e) => setEntryDate(e.target.value)}
                  required
                />
              </div>

              <div className="field-group">
                <label htmlFor="meal">Meal</label>
                <select id="meal" value={meal} onChange={(e) => setMeal(e.target.value)}>
                  <option value="breakfast">breakfast</option>
                  <option value="lunch">lunch</option>
                  <option value="dinner">dinner</option>
                  <option value="snack">snack</option>
                </select>
              </div>

              <div className="field-group food-search-group">
                <label htmlFor="foodSearch">Search food</label>
                <input
                  id="foodSearch"
                  type="text"
                  placeholder="Type to search — dal, palak, chawal, paneer..."
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    setSelectedFood(null);
                  }}
                  autoComplete="off"
                />
                {searching && <div className="food-dropdown"><div className="food-option muted">Searching...</div></div>}
                {!searching && results.length > 0 && (
                  <div className="food-dropdown">
                    {results.map((food) => (
                      <button
                        type="button"
                        key={food.id}
                        className="food-option"
                        onClick={() => pickFood(food)}
                      >
                        <span className="food-option-name">{food.name}</span>
                        <span className="food-option-meta">{Math.round(food.calories_kcal)} kcal / 100g</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="field-group">
                <label htmlFor="portion">Portion (grams)</label>
                <input
                  id="portion"
                  type="number"
                  min="1"
                  value={portionGrams}
                  onChange={(e) => setPortionGrams(e.target.value)}
                  required
                />
              </div>

              <button className="btn-primary" type="submit">Add to diary</button>
            </form>
          </div>

          <div className="diary-card entries-card">
            <h3>Entries on {entryDate}</h3>
            {entries.length === 0 && <p className="muted">No meals logged this day.</p>}
            {entries.map((entry) => (
              <div key={entry.id} className="diary-entry-row">
                <div className="diary-entry-food-wrap">
                  <span className="diary-entry-food">{entry.food_name}</span>
                  <div className="entry-meta">{entry.portion_grams}g · {entry.calories_kcal} kcal · Fe {entry.iron_mg}mg</div>
                </div>

                <div className="diary-entry-meal">{entry.meal}</div>

                <button className="entry-remove" onClick={() => handleRemove(entry.id)} aria-label="Remove entry">
                  <X size={15} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
