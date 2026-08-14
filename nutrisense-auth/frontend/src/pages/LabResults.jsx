import { useEffect, useState } from "react";
import { useAuth } from "../AuthContext";
import { saveLabResults, getMyLabResults } from "../api";
import Sidebar from "./Sidebar";

export default function LabResults() {
  const { token } = useAuth();

  const [hemoglobin, setHemoglobin] = useState("");
  const [serumVitaminD, setSerumVitaminD] = useState("");
  const [ferritin, setFerritin] = useState("");
  const [vitaminB12, setVitaminB12] = useState("");
  const [calcium, setCalcium] = useState("");
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadExisting() {
      try {
        const data = await getMyLabResults(token);
        setHemoglobin(data.hemoglobin_g_dl ?? "");
        setSerumVitaminD(data.serum_vitamin_d ?? "");
        setFerritin(data.ferritin ?? "");
        setVitaminB12(data.vitamin_b12 ?? "");
        setCalcium(data.calcium ?? "");
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadExisting();
  }, [token]);

  function toNumberOrNull(value) {
    return value === "" ? null : Number(value);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    try {
      await saveLabResults(token, {
        hemoglobin: toNumberOrNull(hemoglobin),
        serumVitaminD: toNumberOrNull(serumVitaminD),
        ferritin: toNumberOrNull(ferritin),
        vitaminB12: toNumberOrNull(vitaminB12),
        calcium: toNumberOrNull(calcium),
      });
      setSuccessMsg("Labs saved.");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="dash-shell">
      <Sidebar />

      <main className="dash-main">
        <h1>Lab results</h1>

        <div className="diary-card labs-card">
          <p className="labs-hint">Optional — improves iron &amp; vitamin D confidence after ML prediction.</p>

          {successMsg && <div className="form-banner-success">{successMsg}</div>}
          {error && <div className="form-banner-error">{error}</div>}

          {!loading && (
            <form onSubmit={handleSubmit}>
              <div className="field-row">
                <div className="field-group">
                  <label htmlFor="hemoglobin">Hemoglobin (g/dL)</label>
                  <input
                    id="hemoglobin"
                    type="number"
                    step="0.1"
                    value={hemoglobin}
                    onChange={(e) => setHemoglobin(e.target.value)}
                  />
                </div>
                <div className="field-group">
                  <label htmlFor="vitaminD">Serum Vitamin D</label>
                  <input
                    id="vitaminD"
                    type="number"
                    step="0.1"
                    value={serumVitaminD}
                    onChange={(e) => setSerumVitaminD(e.target.value)}
                  />
                </div>
              </div>

              <div className="field-row">
                <div className="field-group">
                  <label htmlFor="ferritin">Ferritin</label>
                  <input
                    id="ferritin"
                    type="number"
                    step="0.1"
                    value={ferritin}
                    onChange={(e) => setFerritin(e.target.value)}
                  />
                </div>
                <div className="field-group">
                  <label htmlFor="b12">Vitamin B12</label>
                  <input
                    id="b12"
                    type="number"
                    step="0.1"
                    value={vitaminB12}
                    onChange={(e) => setVitaminB12(e.target.value)}
                  />
                </div>
              </div>

              <div className="field-group">
                <label htmlFor="calcium">Calcium</label>
                <input
                  id="calcium"
                  type="number"
                  step="0.1"
                  value={calcium}
                  onChange={(e) => setCalcium(e.target.value)}
                />
              </div>

              <button className="btn-primary" type="submit">Save labs</button>
            </form>
          )}
        </div>
      </main>
    </div>
  );
}
