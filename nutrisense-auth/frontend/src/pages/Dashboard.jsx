import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import {
  Activity,
  Apple,
  ClipboardCheck,
  FlaskConical,
  ArrowRight,
  UtensilsCrossed,
} from "lucide-react";
import { useAuth } from "../AuthContext";
import {
  getHealthProfile,
  getMyLabResults,
  getLatestAssessment,
  listDiaryEntries,
} from "../api";
import Sidebar from "./Sidebar";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

function getLastSevenDays() {
  const days = [];

  for (let i = 6; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    days.push(date.toISOString().slice(0, 10));
  }

  return days;
}

const REQUIRED_MEALS = ["breakfast", "lunch", "snack", "dinner"];

export default function Dashboard() {
  const { token, user } = useAuth();

  const [healthProfile, setHealthProfile] = useState(null);
  const [labResults, setLabResults] = useState(null);
  const [assessment, setAssessment] = useState(null);

  const [todayEntries, setTodayEntries] = useState([]);
  const [averageNutrition, setAverageNutrition] = useState(null);
  const [completeDaysCount, setCompleteDaysCount] = useState(0);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      if (!token) return;

      setLoading(true);
      setError("");

      try {
        const lastSevenDays = getLastSevenDays();

        const [
          profile,
          labs,
          latestAssessment,
          ...weeklyDiaryResults
        ] = await Promise.all([
          getHealthProfile(token),
          getMyLabResults(token),
          getLatestAssessment(token),
          ...lastSevenDays.map((date) =>
            listDiaryEntries(token, date)
          ),
        ]);

        setHealthProfile(profile);
        setLabResults(labs);
        setAssessment(latestAssessment);

        const todayIndex = lastSevenDays.indexOf(todayISO());

        if (todayIndex !== -1) {
          setTodayEntries(
            weeklyDiaryResults[todayIndex] || []
          );
        }

        const completeDays = weeklyDiaryResults.filter(
          (dayEntries) => {
            if (!dayEntries || dayEntries.length === 0) {
              return false;
            }

            const mealsLogged = new Set(
              dayEntries.map((entry) =>
                String(entry.meal).toLowerCase()
              )
            );

            return REQUIRED_MEALS.every((meal) =>
              mealsLogged.has(meal)
            );
          }
        );

        setCompleteDaysCount(completeDays.length);

        if (completeDays.length > 0) {
          const totals = {
            calories_kcal: 0,
            protein_g: 0,
            iron_mg: 0,
            calcium_mg: 0,
            vitamin_d_mcg: 0,
            vitamin_b12_mcg: 0,
            folate_mcg: 0,
            vitamin_a_mcg: 0,
            vitamin_c_mg: 0,
            magnesium_mg: 0,
            zinc_mg: 0,
          };

          completeDays.forEach((dayEntries) => {
            dayEntries.forEach((entry) => {
              totals.calories_kcal += Number(
                entry.calories_kcal || 0
              );

              totals.protein_g += Number(
                entry.protein_g || 0
              );

              totals.iron_mg += Number(
                entry.iron_mg || 0
              );

              totals.calcium_mg += Number(
                entry.calcium_mg || 0
              );

              totals.vitamin_d_mcg += Number(
                entry.vitamin_d_mcg || 0
              );

              totals.vitamin_b12_mcg += Number(
                entry.vitamin_b12_mcg || 0
              );

              totals.folate_mcg += Number(
                entry.folate_mcg || 0
              );

              totals.vitamin_a_mcg += Number(
                entry.vitamin_a_mcg || 0
              );

              totals.vitamin_c_mg += Number(
                entry.vitamin_c_mg || 0
              );

              totals.magnesium_mg += Number(
                entry.magnesium_mg || 0
              );

              totals.zinc_mg += Number(
                entry.zinc_mg || 0
              );
            });
          });

          const averages = {};

          Object.keys(totals).forEach((key) => {
            averages[key] =
              totals[key] / completeDays.length;
          });

          setAverageNutrition(averages);
        } else {
          setAverageNutrition(null);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, [token]);

  const firstName = user?.first_name || "there";

  const totalCalories = todayEntries.reduce(
    (sum, entry) =>
      sum + Number(entry.calories_kcal || 0),
    0
  );

  return (
    <div className="dash-shell">
      <Sidebar />

      <main className="dash-main dashboard-main">
        <div className="dashboard-header">
          <div>
            <p className="eyebrow">
              Your nutrition overview
            </p>

            <h1>
              Good morning, {firstName}
            </h1>

            <p className="dashboard-subtitle">
              A simple snapshot of your nutrition, health
              profile, and progress.
            </p>
          </div>
        </div>

        {error && (
          <div className="form-banner-error dashboard-error">
            {error}
          </div>
        )}

        {loading ? (
          <div className="dashboard-loading">
            Loading your nutrition overview...
          </div>
        ) : (
          <>
            <section className="dashboard-summary-grid">
              <div className="dashboard-stat-card">
                <div className="dashboard-stat-icon">
                  <Activity size={19} />
                </div>

                <div>
                  <span className="dashboard-stat-label">
                    Wellness score
                  </span>

                  <strong>
                    {assessment?.overall_score ?? "—"}
                  </strong>

                  <small>
                    {assessment
                      ? "Latest assessment"
                      : "Run an assessment"}
                  </small>
                </div>
              </div>

              <div className="dashboard-stat-card">
                <div className="dashboard-stat-icon">
                  <Apple size={19} />
                </div>

                <div>
                  <span className="dashboard-stat-label">
                    Today's calories
                  </span>

                  <strong>
                    {todayEntries.length > 0
                      ? Math.round(totalCalories)
                      : "—"}
                  </strong>

                  <small>
                    {todayEntries.length > 0
                      ? "kcal logged"
                      : "No meals logged yet"}
                  </small>
                </div>
              </div>

              <div className="dashboard-stat-card">
                <div className="dashboard-stat-icon">
                  <UtensilsCrossed size={19} />
                </div>

                <div>
                  <span className="dashboard-stat-label">
                    Meals logged
                  </span>

                  <strong>
                    {todayEntries.length}
                  </strong>

                  <small>Today</small>
                </div>
              </div>

              <div className="dashboard-stat-card">
                <div className="dashboard-stat-icon">
                  <ClipboardCheck size={19} />
                </div>

                <div>
                  <span className="dashboard-stat-label">
                    Health profile
                  </span>

                  <strong>
                    {healthProfile
                      ? "Ready"
                      : "Incomplete"}
                  </strong>

                  <small>
                    {healthProfile
                      ? "Personalization enabled"
                      : "Complete your profile"}
                  </small>
                </div>
              </div>
            </section>

            <section className="dashboard-content-grid">
              <div className="diary-card dashboard-card">
                <div className="dashboard-card-heading">
                  <div>
                    <p className="eyebrow">
                      Recent nutrition
                    </p>

                    <h2>
                      Average daily nutrition
                    </h2>
                  </div>

                  <Apple size={21} />
                </div>

                <p className="nutrition-average-note">
                  {completeDaysCount > 0
                    ? `Based on ${completeDaysCount} complete diary ${
                        completeDaysCount === 1
                          ? "day"
                          : "days"
                      } from the last 7 days`
                    : "No complete diary days in the last 7 days"}
                </p>

                {averageNutrition ? (
                  <div className="nutrition-list">
                    <div className="nutrition-row">
                      <span>Calories</span>
                      <strong>
                        {Math.round(
                          averageNutrition.calories_kcal
                        )} kcal
                      </strong>
                    </div>

                    <div className="nutrition-row">
                      <span>Protein</span>
                      <strong>
                        {averageNutrition.protein_g.toFixed(1)} g
                      </strong>
                    </div>

                    <div className="nutrition-row">
                      <span>Iron</span>
                      <strong>
                        {averageNutrition.iron_mg.toFixed(1)} mg
                      </strong>
                    </div>

                    <div className="nutrition-row">
                      <span>Calcium</span>
                      <strong>
                        {Math.round(
                          averageNutrition.calcium_mg
                        )} mg
                      </strong>
                    </div>

                    <div className="nutrition-row">
                      <span>Vitamin D</span>
                      <strong>
                        {averageNutrition.vitamin_d_mcg.toFixed(1)} mcg
                      </strong>
                    </div>

                    <div className="nutrition-row">
                      <span>Vitamin B12</span>
                      <strong>
                        {averageNutrition.vitamin_b12_mcg.toFixed(1)} mcg
                      </strong>
                    </div>

                    <div className="nutrition-row">
                      <span>Folate</span>
                      <strong>
                        {Math.round(
                          averageNutrition.folate_mcg
                        )} mcg
                      </strong>
                    </div>
                  </div>
                ) : (
                  <div className="dashboard-empty">
                    <p>
                      Log breakfast, lunch, snack, and dinner
                      for at least one day to see your average
                      nutrition.
                    </p>
                  </div>
                )}

                <Link
                  to="/food-diary"
                  className="dashboard-card-link"
                >
                  View food diary
                  <ArrowRight size={15} />
                </Link>
              </div>

              <div className="diary-card dashboard-card">
                <div className="dashboard-card-heading">
                  <div>
                    <p className="eyebrow">
                      Personalization
                    </p>

                    <h2>Your health profile</h2>
                  </div>

                  <Activity size={21} />
                </div>

                {healthProfile ? (
                  <div className="profile-summary">
                    <div>
                      <span>Age</span>
                      <strong>
                        {healthProfile.age}
                      </strong>
                    </div>

                    <div>
                      <span>Height</span>
                      <strong>
                        {healthProfile.height_cm} cm
                      </strong>
                    </div>

                    <div>
                      <span>Weight</span>
                      <strong>
                        {healthProfile.weight_kg} kg
                      </strong>
                    </div>

                    <div>
                      <span>Activity</span>
                      <strong>
                        {healthProfile.activity_level?.replaceAll(
                          "_",
                          " "
                        )}
                      </strong>
                    </div>
                  </div>
                ) : (
                  <div className="dashboard-empty">
                    <p>
                      Complete your health profile so
                      NutriSense can personalize your
                      nutrition insights.
                    </p>

                    <Link
                      to="/profile"
                      className="dashboard-card-link"
                    >
                      Complete profile
                      <ArrowRight size={15} />
                    </Link>
                  </div>
                )}
              </div>

              <div className="diary-card dashboard-card">
                <div className="dashboard-card-heading">
                  <div>
                    <p className="eyebrow">
                      Health data
                    </p>

                    <h2>Latest lab results</h2>
                  </div>

                  <FlaskConical size={21} />
                </div>

                {labResults ? (
                  <div className="lab-summary">
                    <div>
                      <span>Hemoglobin</span>
                      <strong>
                        {labResults.hemoglobin_g_dl ?? "—"}
                      </strong>
                    </div>

                    <div>
                      <span>Vitamin D</span>
                      <strong>
                        {labResults.serum_vitamin_d ?? "—"}
                      </strong>
                    </div>

                    <div>
                      <span>Ferritin</span>
                      <strong>
                        {labResults.ferritin ?? "—"}
                      </strong>
                    </div>
                  </div>
                ) : (
                  <div className="dashboard-empty">
                    <p>
                      No lab results have been added yet.
                    </p>
                  </div>
                )}

                <Link
                  to="/lab-results"
                  className="dashboard-card-link"
                >
                  View lab results
                  <ArrowRight size={15} />
                </Link>
              </div>

              <div className="diary-card dashboard-card">
                <div className="dashboard-card-heading">
                  <div>
                    <p className="eyebrow">
                      AI assessment
                    </p>

                    <h2>Nutrition assessment</h2>
                  </div>

                  <ClipboardCheck size={21} />
                </div>

                {assessment ? (
                  <div className="assessment-summary">
                    <p>
                      Your latest wellness score is
                    </p>

                    <strong className="assessment-score">
                      {assessment.overall_score}
                    </strong>

                    <p className="assessment-note">
                      Review your assessment to understand
                      your nutrition risks and recommendations.
                    </p>
                  </div>
                ) : (
                  <div className="dashboard-empty">
                    <p>
                      You haven't completed a nutrition
                      assessment yet.
                    </p>
                  </div>
                )}

                <Link
                  to="/assessment"
                  className="dashboard-card-link"
                >
                  View assessment
                  <ArrowRight size={15} />
                </Link>
              </div>
            </section>

            <section className="diary-card dashboard-meals-card">
              <div className="dashboard-card-heading">
                <div>
                  <p className="eyebrow">
                    Today
                  </p>

                  <h2>Recent meals</h2>
                </div>

                <Link
                  to="/food-diary"
                  className="dashboard-card-link"
                >
                  Food diary
                  <ArrowRight size={15} />
                </Link>
              </div>

              {todayEntries.length === 0 ? (
                <div className="dashboard-empty">
                  <p>
                    No meals logged today. Start building
                    your nutrition history by adding your
                    first meal.
                  </p>

                  <Link
                    to="/food-diary"
                    className="dashboard-card-link"
                  >
                    Log a meal
                    <ArrowRight size={15} />
                  </Link>
                </div>
              ) : (
                <div className="dashboard-meals-list">
                  {todayEntries
                    .slice(0, 5)
                    .map((entry) => (
                      <div
                        key={entry.id}
                        className="dashboard-meal-row"
                      >
                        <div>
                          <strong>
                            {entry.food_name}
                          </strong>

                          <span>
                            {entry.meal} ·{" "}
                            {entry.portion_grams}g
                          </span>
                        </div>

                        <span>
                          {Math.round(
                            Number(
                              entry.calories_kcal || 0
                            )
                          )}{" "}
                          kcal
                        </span>
                      </div>
                    ))}
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}