import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Eye, EyeOff, Leaf } from "lucide-react";
import { login } from "../api";
import { useAuth } from "../AuthContext";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { logIn } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const justOnboarded = location.state?.justOnboarded;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login({ email, password });
      logIn(data.access_token, data.user);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-brand">
        <div className="brand-mark">
          <Leaf size={22} strokeWidth={2.2} />
          nutri<span>sense</span>
        </div>
        <div className="brand-quote">
          <h1>Welcome back.</h1>
          <p>Pick up right where you left off with your nutrition tracking.</p>
        </div>
        <div className="nutrient-dots">
          <span></span><span></span><span></span><span></span>
        </div>
      </div>

      <div className="auth-form-panel">
        <div className="auth-form-card">
          <h2>Log in</h2>
          <p className="auth-subtitle">Enter your details to continue.</p>

          {justOnboarded && (
            <div className="form-banner-success">
              Profile saved! Log in to reach your dashboard.
            </div>
          )}
          {error && <div className="form-banner-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="field-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="field-group">
              <label htmlFor="password">Password</label>
              <div className="password-field-wrap">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className="eye-toggle"
                  onClick={() => setShowPassword((s) => !s)}
                  tabIndex={-1}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                </button>
              </div>
            </div>

            <button className="btn-primary" type="submit" disabled={loading}>
              {loading ? "Logging in..." : "Log in"}
            </button>
          </form>

          <div className="auth-footer-link">
            Don&apos;t have an account? <Link to="/signup">Sign up</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
