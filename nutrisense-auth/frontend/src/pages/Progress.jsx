import { useEffect, useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Award,
  CalendarDays,
  BarChart3,
} from "lucide-react";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

import { useAuth } from "../AuthContext";
import { getAssessmentHistory } from "../api";
import Sidebar from "./Sidebar";

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export default function Progress() {
  const { token } = useAuth();

  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadProgress() {
      if (!token) return;

      setLoading(true);
      setError("");

      try {
        const data = await getAssessmentHistory(token);
        setHistory(data || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadProgress();
  }, [token]);

  const scores = history.map((item) =>
    Number(item.overall_score)
  );

  const latestScore =
    scores.length > 0
      ? scores[scores.length - 1]
      : null;

  const firstScore =
    scores.length > 0
      ? scores[0]
      : null;

  const bestScore =
    scores.length > 0
      ? Math.max(...scores)
      : null;

  const averageScore =
    scores.length > 0
      ? scores.reduce(
          (sum, score) => sum + score,
          0
        ) / scores.length
      : null;

  const improvement =
    scores.length >= 2
      ? latestScore - firstScore
      : null;

  // Get only the latest 10 assessments for the chart
  const recentHistory = history.slice(-10);

  // Prepare data for the line chart
  const chartData = recentHistory.map((item, index) => ({
    name: `A${history.length - recentHistory.length + index + 1}`,
    score: Number(item.overall_score),
    date: formatDate(item.created_at),
  }));

  return (
    <div className="dash-shell">
      <Sidebar />

      <main className="dash-main progress-main">
        <div className="progress-header">
          <div>
            <p className="eyebrow">
              Your journey
            </p>

            <h1>Progress</h1>

            <p className="dashboard-subtitle">
              Track how your nutrition wellness score changes over time.
            </p>
          </div>
        </div>

        {error && (
          <div className="form-banner-error">
            {error}
          </div>
        )}

        {loading ? (
          <div className="dashboard-loading">
            Loading your progress...
          </div>
        ) : history.length === 0 ? (
          <div className="diary-card progress-empty">
            <Activity size={32} />

            <h2>No progress data yet</h2>

            <p>
              Complete your first nutrition assessment to start tracking
              your wellness score over time.
            </p>

            <a
              href="/assessment"
              className="btn-primary"
            >
              Run assessment
            </a>
          </div>
        ) : (
          <>
            {/* Summary cards */}

            <section className="progress-summary-grid">
              <div className="dashboard-stat-card">
                <div className="dashboard-stat-icon">
                  <Activity size={19} />
                </div>

                <div>
                  <span className="dashboard-stat-label">
                    Latest score
                  </span>

                  <strong>
                    {latestScore.toFixed(1)}%
                  </strong>

                  <small>
                    Latest assessment
                  </small>
                </div>
              </div>

              <div className="dashboard-stat-card">
                <div className="dashboard-stat-icon">
                  <Award size={19} />
                </div>

                <div>
                  <span className="dashboard-stat-label">
                    Best score
                  </span>

                  <strong>
                    {bestScore.toFixed(1)}%
                  </strong>

                  <small>
                    Your highest wellness score
                  </small>
                </div>
              </div>

              <div className="dashboard-stat-card">
                <div className="dashboard-stat-icon">
                  <BarChart3 size={19} />
                </div>

                <div>
                  <span className="dashboard-stat-label">
                    Average score
                  </span>

                  <strong>
                    {averageScore.toFixed(1)}%
                  </strong>

                  <small>
                    Across all assessments
                  </small>
                </div>
              </div>

              <div className="dashboard-stat-card">
                <div className="dashboard-stat-icon">
                  {improvement !== null &&
                  improvement >= 0 ? (
                    <TrendingUp size={19} />
                  ) : (
                    <TrendingDown size={19} />
                  )}
                </div>

                <div>
                  <span className="dashboard-stat-label">
                    Overall change
                  </span>

                  <strong>
                    {improvement === null
                      ? "—"
                      : `${improvement >= 0 ? "+" : ""}${improvement.toFixed(1)}%`}
                  </strong>

                  <small>
                    {history.length < 2
                      ? "Complete another assessment"
                      : "Since your first assessment"}
                  </small>
                </div>
              </div>
            </section>

            {/* Score visualization */}

            <section className="diary-card progress-chart-card">
              <div className="dashboard-card-heading">
                <div>
                  <p className="eyebrow">
                    Wellness trend
                  </p>

                  <h2>Your assessment history</h2>

                  <p className="progress-chart-subtitle">
                    Showing your latest{" "}
                    {Math.min(history.length, 10)} assessments
                  </p>
                </div>

                <TrendingUp size={21} />
              </div>

              {history.length === 1 ? (
                <div className="progress-single-score">
                  <strong>
                    {latestScore.toFixed(1)}%
                  </strong>

                  <p>
                    This is your starting point. Complete more
                    assessments to see your wellness trend.
                  </p>
                </div>
              ) : (
                <div className="progress-line-chart">
                  <ResponsiveContainer
                    width="100%"
                    height={320}
                  >
                    <LineChart
                      data={chartData}
                      margin={{
                        top: 20,
                        right: 30,
                        left: 0,
                        bottom: 10,
                      }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        vertical={false}
                      />

                      <XAxis
                        dataKey="name"
                      />

                      <YAxis
                        domain={[0, 100]}
                        tickFormatter={(value) =>
                          `${value}%`
                        }
                      />

                      <Tooltip
                        formatter={(value) => [
                          `${Number(value).toFixed(1)}%`,
                          "Wellness score",
                        ]}
                        labelFormatter={(
                          label,
                          payload
                        ) =>
                          payload?.[0]?.payload?.date
                            ? `${label} • ${payload[0].payload.date}`
                            : label
                        }
                      />

                      <Line
                        type="monotone"
                        dataKey="score"
                        strokeWidth={3}
                        dot={{
                          r: 5,
                        }}
                        activeDot={{
                          r: 7,
                        }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </section>

            {/* Insight */}

            {improvement !== null && (
              <section className="diary-card progress-insight-card">
                <div className="progress-insight-icon">
                  {improvement >= 0 ? (
                    <TrendingUp size={22} />
                  ) : (
                    <TrendingDown size={22} />
                  )}
                </div>

                <div>
                  <p className="eyebrow">
                    Progress insight
                  </p>

                  <h2>
                    {improvement > 0
                      ? "You're moving in the right direction"
                      : improvement < 0
                      ? "Your wellness score has changed"
                      : "Your wellness score is stable"}
                  </h2>

                  <p>
                    {improvement > 0 &&
                      `Your wellness score has improved by ${improvement.toFixed(
                        1
                      )}% since your first assessment.`}

                    {improvement < 0 &&
                      `Your latest wellness score is ${Math.abs(
                        improvement
                      ).toFixed(
                        1
                      )}% lower than your first recorded assessment. Review your nutrition habits and recommendations.`}

                    {improvement === 0 &&
                      "Your latest assessment is at the same level as your first recorded score."}
                  </p>
                </div>
              </section>
            )}

            {/* Recent history */}

            <section className="diary-card progress-history-card">
              <div className="dashboard-card-heading">
                <div>
                  <p className="eyebrow">
                    Assessment records
                  </p>

                  <h2>Recent history</h2>

                  <p className="progress-chart-subtitle">
                    Showing your latest{" "}
                    {Math.min(history.length, 10)} assessments
                  </p>
                </div>

                <CalendarDays size={21} />
              </div>

              <div className="progress-history-list">
                {[...history]
                  .slice(-10)
                  .reverse()
                  .map((item, index) => (
                    <div
                      className="progress-history-row"
                      key={item.id}
                    >
                      <div className="progress-history-info">
                        <strong>
                          Assessment {history.length - index}
                        </strong>

                        <span>
                          {formatDate(item.created_at)}
                        </span>
                      </div>

                      <div className="progress-history-score">
                        <strong>
                          {Number(
                            item.overall_score
                          ).toFixed(1)}%
                        </strong>

                        <span>
                          {item.diary_days_used} diary days used
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}