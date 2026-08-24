import { useEffect, useState } from "react";
import { Eye, EyeOff, Leaf } from "lucide-react";
import { useAuth } from "../AuthContext";
import { changePassword, getHealthProfile, getMe, saveHealthProfile, updateProfile } from "../api";
import Sidebar from "./Sidebar";

const activityLevels = [
  { value: "sedentary", label: "Sedentary - little to no exercise" },
  { value: "lightly_active", label: "Lightly active - light exercise 1-3 days/week" },
  { value: "moderately_active", label: "Moderately active - moderate exercise 3-5 days/week" },
  { value: "very_active", label: "Very active - hard exercise 6-7 days/week" },
];

const restrictionOptions = ["vegetarian", "vegan", "gluten_free", "dairy_free", "nut_allergy"];

const passwordRules = [
  { label: "At least 8 characters", test: (v) => v.length >= 8 },
  { label: "One uppercase letter", test: (v) => /[A-Z]/.test(v) },
  { label: "One lowercase letter", test: (v) => /[a-z]/.test(v) },
  { label: "One number", test: (v) => /[0-9]/.test(v) },
  { label: "One special character", test: (v) => /[!@#$%^&*(),.?":{}|<>]/.test(v) },
];

function parseRestrictions(value) {
  if (!value) return [];
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function Profile() {
  const { token, user, logIn } = useAuth();

  const [loadingProfile, setLoadingProfile] = useState(true);

  const [firstName, setFirstName] = useState(user?.first_name || "");
  const [lastName, setLastName] = useState(user?.last_name || "");
  const [email, setEmail] = useState(user?.email || "");

  const [age, setAge] = useState("");
  const [gender, setGender] = useState(1);
  const [heightCm, setHeightCm] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [activityLevel, setActivityLevel] = useState("lightly_active");
  const [healthGoal, setHealthGoal] = useState("");
  const [restrictions, setRestrictions] = useState([]);
  const [hasProfile, setHasProfile] = useState(false);

  const [accountError, setAccountError] = useState("");
  const [accountSuccess, setAccountSuccess] = useState("");
  const [accountLoading, setAccountLoading] = useState(false);

  const [profileError, setProfileError] = useState("");
  const [profileSuccess, setProfileSuccess] = useState("");
  const [profileLoading, setProfileLoading] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");
  const [passwordLoading, setPasswordLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadProfile() {
      if (!token) return;

      setLoadingProfile(true);
      try {
        const account = await getMe(token);
        if (cancelled) return;

        setFirstName(account.first_name || "");
        setLastName(account.last_name || "");
        setEmail(account.email || "");
      } catch (err) {
        if (!cancelled) setAccountError(err.message);
      }

      try {
        const profile = await getHealthProfile(token);
        if (cancelled) return;

        if (profile) {
          setAge(profile.age?.toString() || "");
          setGender(profile.gender || 1);
          setHeightCm(profile.height_cm?.toString() || "");
          setWeightKg(profile.weight_kg?.toString() || "");
          setActivityLevel(profile.activity_level || "lightly_active");
          setHealthGoal(profile.health_goal || "");
          setRestrictions(parseRestrictions(profile.dietary_restrictions));
          setHasProfile(true);
        } else {
          setHasProfile(false);
        }
      } catch (err) {
        if (!cancelled) setProfileError(err.message);
      } finally {
        if (!cancelled) setLoadingProfile(false);
      }
    }

    loadProfile();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const allRulesMet = passwordRules.every((rule) => rule.test(newPassword));
  const passwordsMatch = confirmPassword.length === 0 || confirmPassword === newPassword;

  function toggleRestriction(option) {
    setRestrictions((prev) =>
      prev.includes(option) ? prev.filter((item) => item !== option) : [...prev, option]
    );
  }

  async function handleAccountSubmit(e) {
    e.preventDefault();
    setAccountError("");
    setAccountSuccess("");

    if (!firstName.trim() || !lastName.trim() || !email.trim()) {
      setAccountError("Please complete all account fields.");
      return;
    }

    setAccountLoading(true);
    try {
      const updatedAccount = await updateProfile(token, {
        firstName: firstName.trim(),
        lastName: lastName.trim(),
        email: email.trim(),
      });
      logIn(updatedAccount.access_token, updatedAccount.user);
      setAccountSuccess("Account details updated successfully.");
    } catch (err) {
      setAccountError(err.message);
    } finally {
      setAccountLoading(false);
    }
  }

  async function handleProfileSubmit(e) {
    e.preventDefault();
    setProfileError("");
    setProfileSuccess("");

    if (!age || !heightCm || !weightKg) {
      setProfileError("Please complete the required health profile fields.");
      return;
    }

    setProfileLoading(true);
    try {
      await saveHealthProfile(token, {
        age: Number(age),
        gender,
        heightCm: Number(heightCm),
        weightKg: Number(weightKg),
        activityLevel,
        healthGoal,
        dietaryRestrictions: restrictions,
      });
      setHasProfile(true);
      setProfileSuccess("Health profile saved successfully.");
    } catch (err) {
      setProfileError(err.message);
    } finally {
      setProfileLoading(false);
    }
  }

  async function handlePasswordSubmit(e) {
    e.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");

    if (!allRulesMet) {
      setPasswordError("Please meet all password requirements below.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("New passwords do not match.");
      return;
    }

    setPasswordLoading(true);
    try {
      await changePassword(token, {
        currentPassword,
        newPassword,
        confirmPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordTouched(false);
      setPasswordSuccess("Password changed successfully.");
    } catch (err) {
      setPasswordError(err.message);
    } finally {
      setPasswordLoading(false);
    }
  }

  return (
    <div className="dash-shell">
      <Sidebar />

      <main className="dash-main profile-main">
        <div className="profile-header">
          <div>
            <p className="eyebrow">Account</p>
            <h1>Profile settings</h1>
            <p className="profile-subtitle">Edit your account details, health profile, and password from one place.</p>
          </div>

          <div className="profile-status-card">
            <span className="profile-status-label">Signed in as</span>
            <strong>{user?.first_name} {user?.last_name}</strong>
            <span>{user?.email}</span>
          </div>
        </div>

        {loadingProfile && <div className="profile-loading">Loading your profile...</div>}

        <div className="profile-grid">
          <section className="diary-card profile-card">
            <div className="profile-card-header">
              <h3>Account details</h3>
              <p>Update the identity details tied to your login.</p>
            </div>

            {accountSuccess && <div className="form-banner-success">{accountSuccess}</div>}
            {accountError && <div className="form-banner-error">{accountError}</div>}

            <form onSubmit={handleAccountSubmit}>
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
                <label htmlFor="email">Email address</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <button className="btn-primary" type="submit" disabled={accountLoading}>
                {accountLoading ? "Saving..." : "Save account changes"}
              </button>
            </form>

            <div className="profile-password-section">
              <div className="profile-card-header">
                <h3>Change password</h3>
                <p>Keep your account secure with a new password.</p>
              </div>

              {passwordSuccess && <div className="form-banner-success">{passwordSuccess}</div>}
              {passwordError && <div className="form-banner-error">{passwordError}</div>}

              <form onSubmit={handlePasswordSubmit}>
                <div className="field-group">
                  <label htmlFor="currentPassword">Current password</label>
                  <div className="password-field-wrap">
                    <input
                      id="currentPassword"
                      type={showCurrentPassword ? "text" : "password"}
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      required
                    />
                    <button
                      type="button"
                      className="eye-toggle"
                      onClick={() => setShowCurrentPassword((s) => !s)}
                      tabIndex={-1}
                      aria-label={showCurrentPassword ? "Hide password" : "Show password"}
                    >
                      {showCurrentPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                    </button>
                  </div>
                </div>

                <div className="field-group">
                  <label htmlFor="newPassword">New password</label>
                  <div className="password-field-wrap">
                    <input
                      id="newPassword"
                      type={showNewPassword ? "text" : "password"}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      onFocus={() => setPasswordTouched(true)}
                      required
                    />
                    <button
                      type="button"
                      className="eye-toggle"
                      onClick={() => setShowNewPassword((s) => !s)}
                      tabIndex={-1}
                      aria-label={showNewPassword ? "Hide password" : "Show password"}
                    >
                      {showNewPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                    </button>
                  </div>
                  {passwordTouched && (
                    <ul className="password-checklist">
                      {passwordRules.map((rule) => {
                        const met = rule.test(newPassword);
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
                  <label htmlFor="confirmPassword">Confirm new password</label>
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

                <button className="btn-primary" type="submit" disabled={passwordLoading}>
                  {passwordLoading ? "Updating..." : "Update password"}
                </button>
              </form>
            </div>
          </section>

          <section className="diary-card profile-card">
            <div className="profile-card-header">
              <h3>Health profile</h3>
              <p>{hasProfile ? "Adjust the values used for nutrient targets and recommendations." : "Complete your health profile to personalize recommendations."}</p>
            </div>

            {profileSuccess && <div className="form-banner-success">{profileSuccess}</div>}
            {profileError && <div className="form-banner-error">{profileError}</div>}

            <form onSubmit={handleProfileSubmit}>
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

              <button className="btn-primary" type="submit" disabled={profileLoading}>
                {profileLoading ? "Saving..." : hasProfile ? "Update health profile" : "Save health profile"}
              </button>
            </form>
          </section>

        </div>
      </main>
    </div>
  );
}