import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Eye, EyeOff, Leaf } from "lucide-react";
import { signup } from "../api";
import { useAuth } from "../AuthContext";

const passwordRules = [
  { label: "At least 8 characters", test: (v) => v.length >= 8 },
  { label: "One uppercase letter", test: (v) => /[A-Z]/.test(v) },
  { label: "One lowercase letter", test: (v) => /[a-z]/.test(v) },
  { label: "One number", test: (v) => /[0-9]/.test(v) },
  { label: "One special character", test: (v) => /[!@#$%^&*(),.?":{}|<>]/.test(v) },
];

export default function Signup() {
  const navigate = useNavigate();
  const { logIn } = useAuth();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const allRulesMet = passwordRules.every((rule) => rule.test(password));
  const passwordsMatch = confirmPassword.length === 0 || confirmPassword === password;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (!allRulesMet) {
      setError("Please meet all password requirements below.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const data = await signup({ firstName, lastName, email, password, confirmPassword });
      // Log in just long enough to carry the token into onboarding, which requires auth.
      logIn(data.access_token, data.user);
      navigate("/onboarding");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <aside className="auth-brand">
        <div className="brand-mark">
          <Leaf size={22} strokeWidth={2.2} />
          nutri<span>sense</span>
        </div>
        <div className="brand-quote">
          <h1>Know what your body is actually asking for.</h1>
          <p>Track meals, spot gaps early, and get plans built around your real nutrient needs.</p>
        </div>
        <div className="nutrient-dots">
          <span></span><span></span><span></span><span></span>
        </div>
      </aside>

      <div className="auth-form-panel">
        <div className="auth-form-card">
          <h2>Create your account</h2>
          <p className="auth-subtitle">Step 1 of 2 — we'll ask about your health next.</p>

          {error && <div className="form-banner-error">{error}</div>}

          <form onSubmit={handleSubmit} noValidate>
            <div className="field-row">
              <div className="field-group">
                <label htmlFor="firstName">First name</label>
                <input
                  id="firstName"
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                />
              </div>
              <div className="field-group">
                <label htmlFor="lastName">Last name</label>
                <input
                  id="lastName"
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                />
              </div>
            </div>

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
                  onFocus={() => setPasswordTouched(true)}
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
              {passwordTouched && (
                <ul className="password-checklist">
                  {passwordRules.map((rule) => {
                    const met = rule.test(password);
                    return (
                      <li key={rule.label} className={met ? "met" : ""}>
                        <span className="check-dot"></span>
                        {rule.label}
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>

            <div className="field-group">
              <label htmlFor="confirmPassword">Confirm password</label>
              <div className="password-field-wrap">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className={!passwordsMatch ? "input-error" : ""}
                  required
                />
                <button
                  type="button"
                  className="eye-toggle"
                  onClick={() => setShowConfirmPassword((s) => !s)}
                  tabIndex={-1}
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                >
                  {showConfirmPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                </button>
              </div>
              {!passwordsMatch && <p className="field-error">Passwords don't match yet.</p>}
            </div>

            <button className="btn-primary" type="submit" disabled={loading}>
              {loading ? "Creating account..." : "Continue"}
            </button>
          </form>

          <p className="auth-footer-link">
            Already have an account? <Link to="/login">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
