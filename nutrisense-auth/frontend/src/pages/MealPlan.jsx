import { useEffect, useState } from "react";
import { CalendarDays, RefreshCw } from "lucide-react";
import { useAuth } from "../AuthContext";
import { getLatestMealPlan, regenerateMealPlan } from "../api";
import Sidebar from "./Sidebar";

export default function MealPlan() {
  const { token } = useAuth();
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    getLatestMealPlan(token)
      .then((data) => {
        if (!cancelled) setPlan(data);
      })
      .catch((err) => {
        if (!cancelled && !err.message.includes("No meal plan")) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function handleRegenerate() {
    setError("");
    setRegenerating(true);
    try {
      setPlan(await regenerateMealPlan(token));
    } catch (err) {
      setError(err.message);
    } finally {
      setRegenerating(false);
    }
  }

  return (
    <div className="dash-shell">
      <Sidebar />
      <main className="dash-main meal-plan-main">
        <div className="meal-plan-header">
          <div>
            <p className="eyebrow">Personalized nutrition</p>
            <h1>7-day meal plan</h1>
            <p className="profile-subtitle">
              Two foods for every meal, built from your latest deficiency assessment and dietary preferences.
            </p>
          </div>
          <button className="btn-primary meal-plan-regenerate" onClick={handleRegenerate} disabled={regenerating}>
            <RefreshCw size={16} className={regenerating ? "spin" : ""} />
            {regenerating ? "Regenerating..." : "Regenerate plan"}
          </button>
        </div>

        {error && <div className="form-banner-error">{error}</div>}
        {loading && <div className="profile-loading">Loading your meal plan...</div>}

        {!loading && !plan && !error && (
          <div className="diary-card meal-plan-empty">
            <CalendarDays size={30} />
            <h3>Generate your first plan</h3>
            <p>Run an assessment first, then regenerate your personalized seven-day plan.</p>
            <button className="btn-primary" onClick={handleRegenerate} disabled={regenerating}>
              {regenerating ? "Generating..." : "Generate meal plan"}
            </button>
          </div>
        )}

        {plan && (
          <>
            <div className="meal-plan-meta">
              <span>Based on deficiencies: <strong>{plan.focus_nutrients.join(", ").replaceAll("_", " ")}</strong></span>
              <span>Diet: <strong>{plan.dietary_restrictions.length ? plan.dietary_restrictions.join(", ").replaceAll("_", "-") : "No restrictions"}</strong></span>
            </div>
            <div className="meal-plan-week">
              {plan.days.map((day) => (
                <section className="meal-day" key={day.day}>
                  <div className="meal-day-heading">
                    <h2>{day.day}</h2>
                    <span>4 meals</span>
                  </div>
                  <div className="meal-day-grid">
                    {day.meals.map((meal) => (
                      <article className="meal-slot" key={meal.meal}>
                        <h3>{meal.meal}</h3>
                        <div className="meal-foods">
                          {meal.foods.map((food) => (
                            <div className="meal-food" key={food.id}>
                              <span>{food.name}</span>
                              <small>{food.portion_grams} g</small>
                            </div>
                          ))}
                        </div>
                      </article>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
