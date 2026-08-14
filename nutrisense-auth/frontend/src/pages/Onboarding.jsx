import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Leaf } from "lucide-react";
import { submitOnboarding } from "../api";
import { useAuth } from "../AuthContext";

const activityLevels = [
  { value: "sedentary", label: "Sedentary — little to no exercise" },
  { value: "lightly_active", label: "Lightly active — light exercise 1-3 days/week" },
  { value: "moderately_active", label: "Moderately active — moderate exercise 3-5 days/week" },
  { value: "very_active", label: "Very active — hard exercise 6-7 days/week" },
];

const restrictionOptions = ["vegetarian", "vegan", "gluten_free", "dairy_free", "nut_allergy"];

export default function Onboarding() {
  const navigate = useNavigate();
  const { token, logOut } = useAuth();

  const [age, setAge] = useState("");
  const [gender, setGender] = useState(1); // 1 = Male, 2 = Female
  const [heightCm, setHeightCm] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [activityLevel, setActivityLevel] = useState("lightly_active");
  const [healthGoal, setHealthGoal] = useState("");
  const [restrictions, setRestrictions] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function toggleRestriction(option) {
    setRestrictions((prev) =>
      prev.includes(option) ? prev.filter((r) => r !== option) : [...prev, option]
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await submitOnboarding(token, {
        age: Number(age),
        gender,
        heightCm: Number(heightCm),
        weightKg: Number(weightKg),
        activityLevel,
        healthGoal,
        dietaryRestrictions: restrictions,
      });
      // Per the required flow: signup -> onboarding -> log out -> log in again to reach the dashboard
      logOut();
      navigate("/login", { state: { justOnboarded: true } });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="onboarding-shell">
      <div className="onboarding-card">
        <div className="onboarding-header">
          <div className="brand-mark small">
            <Leaf size={19} strokeWidth={2.2} />
            nutri<span>sense</span>
          </div>
          <h2>Your health profile</h2>
          <p className="auth-subtitle">We use this to personalize your nutrient targets and meal suggestions.</p>
        </div>

        {error && <div className="form-banner-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field-row">
            <div className="field-group">
              <label htmlFor="age">Age</label>
              <input
                id="age"
                type="number"
                min="1"
                max="120"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                required
              />
            </div>
            <div className="field-group">
              <label>Gender</label>
              <div className="gender-toggle">
                <button
                  type="button"
                  className={gender === 1 ? "gender-btn active" : "gender-btn"}
                  onClick={() => setGender(1)}
                >
                  Male
                </button>
                <button
                  type="button"
                  className={gender === 2 ? "gender-btn active" : "gender-btn"}
                  onClick={() => setGender(2)}
                >
                  Female
                </button>
              </div>
            </div>
          </div>

          <div className="field-row">
            <div className="field-group">
              <label htmlFor="height">Height (cm)</label>
              <input
                id="height"
                type="number"
                step="0.1"
                value={heightCm}
                onChange={(e) => setHeightCm(e.target.value)}
                required
              />
            </div>
            <div className="field-group">
              <label htmlFor="weight">Weight (kg)</label>
              <input
                id="weight"
                type="number"
                step="0.1"
                value={weightKg}
                onChange={(e) => setWeightKg(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="field-group">
            <label htmlFor="activity">Activity level</label>
            <select id="activity" value={activityLevel} onChange={(e) => setActivityLevel(e.target.value)}>
              {activityLevels.map((level) => (
                <option key={level.value} value={level.value}>
                  {level.label}
                </option>
              ))}
            </select>
          </div>

          <div className="field-group">
            <label htmlFor="healthGoal">Health goal</label>
            <input
              id="healthGoal"
              type="text"
              placeholder="e.g. Improve energy, build muscle, manage anemia"
              value={healthGoal}
              onChange={(e) => setHealthGoal(e.target.value)}
            />
          </div>

          <div className="field-group">
            <label>Dietary restrictions (optional)</label>
            <div className="chip-row">
              {restrictionOptions.map((option) => (
                <button
                  type="button"
                  key={option}
                  className={restrictions.includes(option) ? "chip active" : "chip"}
                  onClick={() => toggleRestriction(option)}
                >
                  {option.replace("_", "-")}
                </button>
              ))}
            </div>
          </div>

          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? "Saving..." : "Save & continue to login"}
          </button>
        </form>
      </div>
    </div>
  );
}
