const API_BASE_URL = "http://localhost:8000";

async function handleResponse(res) {
  const data = await res.json();
  if (!res.ok) {
    const message = Array.isArray(data.detail)
      ? data.detail.map((d) => d.msg).join(", ")
      : data.detail || "Something went wrong";
    throw new Error(message);
  }
  return data;
}

function authHeaders(token) {
  return { Authorization: `Bearer ${token}` };
}

// --- Auth ---

export async function signup({ firstName, lastName, email, password, confirmPassword }) {
  const res = await fetch(`${API_BASE_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      first_name: firstName,
      last_name: lastName,
      email,
      password,
      confirm_password: confirmPassword,
    }),
  });
  return handleResponse(res);
}

export async function login({ email, password }) {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse(res);
}

export async function getMe(token) {
  const res = await fetch(`${API_BASE_URL}/auth/me`, { headers: authHeaders(token) });
  return handleResponse(res);
}

export async function updateProfile(token, { firstName, lastName, email }) {
  const res = await fetch(`${API_BASE_URL}/auth/me`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({
      first_name: firstName,
      last_name: lastName,
      email,
    }),
  });
  return handleResponse(res);
}

export async function changePassword(token, { currentPassword, newPassword, confirmPassword }) {
  const res = await fetch(`${API_BASE_URL}/auth/password`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
      confirm_password: confirmPassword,
    }),
  });
  return handleResponse(res);
}

// --- Onboarding / health profile ---

export async function getHealthProfile(token) {
  const res = await fetch(`${API_BASE_URL}/profile/me`, { headers: authHeaders(token) });
  if (res.status === 404) return null;
  return handleResponse(res);
}

export async function saveHealthProfile(token, { age, gender, heightCm, weightKg, activityLevel, healthGoal, dietaryRestrictions }) {
  const res = await fetch(`${API_BASE_URL}/profile/me`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({
      age,
      gender,
      height_cm: heightCm,
      weight_kg: weightKg,
      activity_level: activityLevel,
      health_goal: healthGoal,
      dietary_restrictions: dietaryRestrictions,
    }),
  });
  return handleResponse(res);
}

export async function submitOnboarding(token, { age, gender, heightCm, weightKg, activityLevel, healthGoal, dietaryRestrictions }) {
  const res = await fetch(`${API_BASE_URL}/profile/onboarding`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({
      age,
      gender,
      height_cm: heightCm,
      weight_kg: weightKg,
      activity_level: activityLevel,
      health_goal: healthGoal,
      dietary_restrictions: dietaryRestrictions,
    }),
  });
  return handleResponse(res);
}

// --- Lab results ---

export async function saveLabResults(token, { hemoglobin, serumVitaminD, ferritin, vitaminB12, calcium }) {
  const res = await fetch(`${API_BASE_URL}/labs`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({
      hemoglobin_g_dl: hemoglobin,
      serum_vitamin_d: serumVitaminD,
      ferritin,
      vitamin_b12: vitaminB12,
      calcium,
    }),
  });
  return handleResponse(res);
}

export async function getMyLabResults(token) {
  const res = await fetch(`${API_BASE_URL}/labs/me`, { headers: authHeaders(token) });
  return handleResponse(res);
}

// --- Assessment ---

export async function runAssessment(token) {
  const res = await fetch(`${API_BASE_URL}/assess`, {
    method: "POST",
    headers: authHeaders(token),
  });
  return handleResponse(res);
}

export async function getLatestAssessment(token) {
  const res = await fetch(`${API_BASE_URL}/assess/latest`, { headers: authHeaders(token) });
  if (res.status === 404) return null;
  return handleResponse(res);
}

export async function getAssessmentHistory(token) {
  const res = await fetch(
    `${API_BASE_URL}/assess/history`,
    {
      headers: authHeaders(token),
    }
  );

  return handleResponse(res);
}
// --- Meal plan ---

export async function getLatestMealPlan(token) {
  const res = await fetch(`${API_BASE_URL}/meal-plan/latest`, { headers: authHeaders(token) });
  if (res.status === 404) return null;
  return handleResponse(res);
}

export async function regenerateMealPlan(token) {
  const res = await fetch(`${API_BASE_URL}/meal-plan/regenerate`, {
    method: "POST",
    headers: authHeaders(token),
  });
  return handleResponse(res);
}

// --- Foods ---

export async function searchFoods(token, query) {
  const url = new URL(`${API_BASE_URL}/foods/search`);
  url.searchParams.set("q", query);
  const res = await fetch(url, { headers: authHeaders(token) });
  return handleResponse(res);
}

// --- Diary ---

export async function addDiaryEntry(token, { entryDate, meal, foodItemId, portionGrams }) {
  const res = await fetch(`${API_BASE_URL}/diary/entries`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({
      entry_date: entryDate,
      meal,
      food_item_id: foodItemId,
      portion_grams: portionGrams,
    }),
  });
  return handleResponse(res);
}

export async function listDiaryEntries(token, entryDate) {
  const url = new URL(`${API_BASE_URL}/diary/entries`);
  url.searchParams.set("entry_date", entryDate);
  const res = await fetch(url, { headers: authHeaders(token) });
  return handleResponse(res);
}

export async function deleteDiaryEntry(token, entryId) {
  const res = await fetch(`${API_BASE_URL}/diary/entries/${entryId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  return handleResponse(res);
}
