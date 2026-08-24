import { createContext, useContext, useState } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => {
    return localStorage.getItem("nutrisense_token");
  });

  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("nutrisense_user");

    try {
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });

  function logIn(newToken, newUser) {
    setToken(newToken);
    setUser(newUser);

    localStorage.setItem("nutrisense_token", newToken);
    localStorage.setItem("nutrisense_user", JSON.stringify(newUser));
  }

  function logOut() {
    setToken(null);
    setUser(null);

    localStorage.removeItem("nutrisense_token");
    localStorage.removeItem("nutrisense_user");
  }

  return (
    <AuthContext.Provider value={{ token, user, logIn, logOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}