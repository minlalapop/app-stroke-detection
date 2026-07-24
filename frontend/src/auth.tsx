import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, jsonBody, type User } from "./api";

type AuthValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};
const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!localStorage.getItem("access_token")) {
      setLoading(false);
      return;
    }
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => localStorage.removeItem("access_token"))
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthValue>(
    () => ({
      user,
      loading,
      login: async (email, password) => {
        const token = await api<{ access_token: string }>("/auth/login", {
          method: "POST",
          ...jsonBody({ email, password }),
        });
        localStorage.setItem("access_token", token.access_token);
        setUser(await api<User>("/auth/me"));
      },
      logout: async () => {
        try {
          await api<void>("/auth/logout", { method: "POST" });
        } finally {
          localStorage.removeItem("access_token");
          setUser(null);
        }
      },
    }),
    [loading, user],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("AuthProvider missing");
  return value;
}
