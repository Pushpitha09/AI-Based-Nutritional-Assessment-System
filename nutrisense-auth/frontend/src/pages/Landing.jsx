import { Link } from "react-router-dom";
import { Leaf, ArrowRight, CheckCircle2 } from "lucide-react";

export default function Landing() {
  return (
    <div className="landing-page">

      {/* Navigation */}
      <header className="landing-nav">
        <Link to="/" className="landing-logo">
          <Leaf size={22} strokeWidth={2.2} />
          <span>AI-Based<span> Nutritional Assessment System</span></span>
        </Link>

        <div className="landing-nav-actions">
          <Link to="/login" className="landing-login">
            Log in
          </Link>

          <Link to="/signup" className="landing-signup">
            Get started
          </Link>
        </div>
      </header>

      {/* Hero */}
      <main>

        <section className="landing-hero">
          <div className="landing-hero-content">

            <div className="landing-eyebrow">
              <Leaf size={15} />
              Personalized nutrition, made simple
            </div>

            <h1>
              Understand your nutrition.
              <br />
              <span>Build a healthier you.</span>
            </h1>

            <p>
              NutriSense brings your health information, nutrition tracking,
              assessments and personalized meal planning together in one place.
            </p>

            <div className="landing-hero-buttons">
              <Link to="/signup" className="landing-primary-btn">
                Get started
                <ArrowRight size={18} />
              </Link>

              <Link to="/login" className="landing-secondary-btn">
                I already have an account
              </Link>
            </div>

            <div className="landing-trust">
              <div>
                <CheckCircle2 size={16} />
                Personalized recommendations
              </div>

              <div>
                <CheckCircle2 size={16} />
                Nutrition tracking
              </div>

              <div>
                <CheckCircle2 size={16} />
                Health insights
              </div>
            </div>

          </div>

          {/* Visual card */}
          <div className="landing-visual">

            <div className="landing-circle landing-circle-one"></div>
            <div className="landing-circle landing-circle-two"></div>

            <div className="nutrition-card">

              <div className="nutrition-card-header">
                <div>
                  <span>Today's nutrition</span>
                  <strong>Good progress</strong>
                </div>

                <div className="nutrition-leaf">
                  <Leaf size={20} />
                </div>
              </div>

              <div className="nutrition-score">
                <div className="score-ring">
                  <strong>78</strong>
                  <span>score</span>
                </div>

                <div className="score-text">
                  <strong>You're doing well</strong>
                  <p>
                    Keep your meals balanced throughout the day.
                  </p>
                </div>
              </div>

              <div className="nutrition-bars">

                <div className="nutrition-bar-item">
                  <div>
                    <span>Protein</span>
                    <strong>72%</strong>
                  </div>
                  <div className="nutrition-bar">
                    <span style={{ width: "72%" }}></span>
                  </div>
                </div>

                <div className="nutrition-bar-item">
                  <div>
                    <span>Iron</span>
                    <strong>64%</strong>
                  </div>
                  <div className="nutrition-bar">
                    <span style={{ width: "64%" }}></span>
                  </div>
                </div>

                <div className="nutrition-bar-item">
                  <div>
                    <span>Vitamin D</span>
                    <strong>81%</strong>
                  </div>
                  <div className="nutrition-bar">
                    <span style={{ width: "81%" }}></span>
                  </div>
                </div>

              </div>

            </div>

            <div className="floating-food-card">
              <span className="floating-food-icon">🥗</span>

              <div>
                <strong>Meal suggestion</strong>
                <span> Paneer · balanced</span>
              </div>
            </div>

          </div>
        </section>

        {/* Features */}
        <section className="landing-features">

          <div className="landing-section-heading">
            <p className="eyebrow">Everything in one place</p>

            <h2>
              Your nutrition journey,
              <br />
              <span>thoughtfully organized.</span>
            </h2>

            <p>
              Track what matters, understand your health and get recommendations
              that fit your personal goals.
            </p>
          </div>

          <div className="landing-feature-grid">

            <div className="landing-feature-card">
              <div className="feature-number">01</div>
              <Leaf size={22} />

              <h3>Track your food</h3>

              <p>
                Log your meals and portions while NutriSense automatically
                calculates the nutritional values.
              </p>
            </div>

            <div className="landing-feature-card">
              <div className="feature-number">02</div>
              <Leaf size={22} />

              <h3>Understand your health</h3>

              <p>
                Combine your health profile and lab results to identify
                nutritional areas that may need attention.
              </p>
            </div>

            <div className="landing-feature-card">
              <div className="feature-number">03</div>
              <Leaf size={22} />

              <h3>Get personalized meals</h3>

              <p>
                Receive meal suggestions designed around your goals,
                nutritional needs and dietary preferences.
              </p>
            </div>

          </div>

        </section>

        {/* CTA */}
        <section className="landing-cta">

          <div>
            <p className="eyebrow">Start your journey</p>

            <h2>
              Small choices.
              <br />
              Better nutrition.
            </h2>

            <p>
              Create your NutriSense account and start building a clearer
              picture of your nutrition.
            </p>
          </div>

          <Link to="/signup" className="landing-cta-button">
            Create your account
            <ArrowRight size={18} />
          </Link>

        </section>

      </main>

      {/* Footer */}
      <footer className="landing-footer">
        <Link to="/" className="landing-logo">
          <Leaf size={18} />
          <span>AI-Based<span> Nutritional Assessment System</span></span>
        </Link>

        <p>
          Personalized nutrition assessment and meal planning.
        </p>

        <span>© 2026 NutriSense</span>
      </footer>

    </div>
  );
}