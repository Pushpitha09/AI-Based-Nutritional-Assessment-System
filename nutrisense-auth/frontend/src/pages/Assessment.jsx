import { useEffect, useState } from "react";
import { useAuth } from "../AuthContext";
import { runAssessment, getLatestAssessment } from "../api";
import Sidebar from "./Sidebar";

const LEVEL_COLOR = {
  HIGH: "#c0392b",
  MODERATE: "#e2934a",
  LOW: "#3f6146",
};

const NUTRIENT_UNIT_LABEL = {
  iron: "Fe",
  vitamin_d: "D",
  vitamin_b12: "B12",
  calcium: "Ca",
  folate: "Folate",
  vitamin_a: "A",
  vitamin_c: "C",
  magnesium: "Mg",
  zinc: "Zn",
  protein: "Protein",
};

export default function Assessment() {
  const { token } = useAuth();

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [loadedOnce, setLoadedOnce] = useState(false);

  // True when the currently displayed assessment
  // was loaded from assessment history rather than
  // created by clicking "Run assessment" in this session.
  const [isPreviousAssessment, setIsPreviousAssessment] =
    useState(false);

  useEffect(() => {
    async function loadLatest() {
      try {
        const existing = await getLatestAssessment(token);

        if (existing) {
          setResult(existing);
          setIsPreviousAssessment(true);
        }
      } catch (err) {
        // No previous assessment is okay.
        // The page will show the empty state.
      } finally {
        setLoadedOnce(true);
      }
    }

    if (token) {
      loadLatest();
    }
  }, [token]);

  async function handleRun() {
    setError("");
    setLoading(true);

    try {
      const data = await runAssessment(token);

      setResult(data);

      // This result was generated from the current
      // diary data, not loaded from history.
      setIsPreviousAssessment(false);
    } catch (err) {
      setError(err.message);

      // Important:
      // Keep the previous assessment visible.
      // It is still valid as a historical assessment,
      // even if there are currently fewer than 3
      // complete days in the rolling 7-day window.
    } finally {
      setLoading(false);
    }
  }

  const hasRecommendations =
    result &&
    Object.keys(result.recommendations || {}).length > 0;

  return (
    <div className="dash-shell">
      <Sidebar />

      <main className="dash-main">
        <div className="assess-header">
          <div>
            <h1>Assessment</h1>

            <p className="auth-subtitle">
              {result ? (
                isPreviousAssessment ? (
                  <>
                    Random Forest model · Latest assessment was
                    based on {result.diary_days_used} complete
                    diary{" "}
                    {result.diary_days_used === 1
                      ? "day"
                      : "days"}
                  </>
                ) : (
                  <>
                    Random Forest model ·{" "}
                    {result.diary_days_used} complete diary{" "}
                    {result.diary_days_used === 1
                      ? "day"
                      : "days"}{" "}
                    used · 3–7 days required
                  </>
                )
              ) : (
                <>
                  Random Forest model · 3–7 complete diary days
                  required
                </>
              )}
            </p>
          </div>

          <button
            className="btn-primary btn-run"
            onClick={handleRun}
            disabled={loading}
          >
            {loading ? "Running..." : "Run assessment"}
          </button>
        </div>

        {error && (
          <div className="form-banner-error">
            {error}
          </div>
        )}

        {!result && loadedOnce && !error && (
          <div className="diary-card">
            <p className="muted">
              No assessment yet. Log breakfast, lunch, snack,
              and dinner on at least 3 days within the last
              7 days, then click "Run assessment."
            </p>
          </div>
        )}

        {result && (
          <>
            {isPreviousAssessment && error && (
              <div className="diary-card" style={{ marginBottom: 22 }}>
                <p className="muted">
                  The assessment shown below is your latest
                  successful assessment and was based on{" "}
                  {result.diary_days_used} complete diary{" "}
                  {result.diary_days_used === 1
                    ? "day"
                    : "days"}.
                  Your current last 7 days do not yet contain
                  enough complete diary days to run a new
                  assessment.
                </p>
              </div>
            )}

            <div className="assess-grid">
              {/* LEFT SIDE — DEFICIENCY RISKS */}

              <div className="diary-card">
                <h3>Deficiency risks</h3>

                <p className="wellness-score">
                  Wellness score:{" "}
                  <strong>
                    {result.overall_score}%
                  </strong>
                </p>

                {result.risks.map((risk) => (
                  <div
                    key={risk.label}
                    className="risk-row"
                  >
                    <div className="risk-row-top">
                      <span className="risk-name">
                        {risk.nutrient.replace(/_/g, " ")}
                      </span>

                      <span
                        className="risk-badge"
                        style={{
                          background:
                            LEVEL_COLOR[risk.ui_level],
                        }}
                      >
                        {risk.ui_percent}%{" "}
                        {risk.ui_level}
                      </span>
                    </div>

                    <div className="risk-bar-track">
                      <div
                        className="risk-bar-fill"
                        style={{
                          width:
                            `${risk.ui_percent}%`,
                          background:
                            LEVEL_COLOR[
                              risk.ui_level
                            ],
                        }}
                      />
                    </div>

                    {risk.tag && (
                      <span className="risk-tag">
                        {risk.tag}
                      </span>
                    )}
                  </div>
                ))}
              </div>

              {/* RIGHT SIDE */}

              <div>
                {/* RECOMMENDED FOODS */}

                <div
                  className="diary-card"
                  style={{ marginBottom: 22 }}
                >
                  <h3>Recommended foods</h3>

                  <p
                    className="muted"
                    style={{ marginBottom: 16 }}
                  >
                    Foods for every high-risk nutrient,
                    filtered by your diet settings.
                  </p>

                  {!hasRecommendations && (
                    <p className="muted">
                      No high-risk nutrients right now —
                      nothing to recommend.
                    </p>
                  )}

                  {hasRecommendations &&
                    Object.entries(
                      result.recommendations
                    ).map(([nutrient, foods]) => (
                      <div
                        key={nutrient}
                        className="rec-section"
                      >
                        <h4 className="rec-nutrient-title">
                          {nutrient.replace(/_/g, " ")}
                        </h4>

                        {foods.length > 0 ? (
                          foods.map((food) => (
                            <div
                              key={food.name}
                              className="rec-food-row"
                            >
                              <span className="rec-food-name">
                                {food.name}
                              </span>

                              <span className="rec-food-amount">
                                {
                                  NUTRIENT_UNIT_LABEL[
                                    nutrient
                                  ] || ""
                                }{" "}
                                {food.amount}
                              </span>
                            </div>
                          ))
                        ) : (
                          <p className="muted">
                            No matching foods available.
                          </p>
                        )}
                      </div>
                    ))}
                </div>

                {/* AVERAGE DAILY INTAKE */}

                <div className="diary-card">
                  <h3>Average daily intake used</h3>

                  <p
                    className="muted"
                    style={{ marginBottom: 16 }}
                  >
                    Averaged across{" "}
                    {result.diary_days_used} complete diary{" "}
                    {result.diary_days_used === 1
                      ? "day"
                      : "days"}.
                  </p>

                  {Object.entries(result.features)
                    .filter(
                      ([key]) =>
                        key !== "gender" &&
                        key !== "age_years"
                    )
                    .map(([key, value]) => (
                      <div
                        key={key}
                        className="feature-row"
                      >
                        <span>
                          {key.replace(/_/g, " ")}
                        </span>

                        <span>
                          {Number(value).toFixed(1)}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}