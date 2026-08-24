import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

import { AuthProvider } from "./AuthContext";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/Dashboard";
import FoodDiary from "./pages/FoodDiary";
import LabResults from "./pages/LabResults";
import Assessment from "./pages/Assessment";
import Profile from "./pages/Profile";
import MealPlan from "./pages/MealPlan";
import Landing from "./pages/Landing";
import ProtectedRoute from "./pages/ProtectedRoute";
import Progress from "./pages/Progress";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>

          {/* Public pages */}

          <Route
            path="/"
            element={<Landing />}
          />

          <Route
            path="/login"
            element={<Login />}
          />

          <Route
            path="/signup"
            element={<Signup />}
          />

          {/* Protected pages */}

          <Route
            path="/onboarding"
            element={
              <ProtectedRoute>
                <Onboarding />
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/food-diary"
            element={
              <ProtectedRoute>
                <FoodDiary />
              </ProtectedRoute>
            }
          />

          <Route
            path="/lab-results"
            element={
              <ProtectedRoute>
                <LabResults />
              </ProtectedRoute>
            }
          />

          <Route
            path="/assessment"
            element={
              <ProtectedRoute>
                <Assessment />
              </ProtectedRoute>
            }
          />

          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />

          <Route
            path="/meal-plan"
            element={
              <ProtectedRoute>
                <MealPlan />
              </ProtectedRoute>
            }
          />
          <Route
            path="/progress"
            element={
              <ProtectedRoute>
                <Progress />
              </ProtectedRoute>
            }
          />  

          {/* Fallback */}

          <Route
            path="*"
            element={<Navigate to="/" replace />}
          />

        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}