"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";

interface User {
  id: string;
  email: string;
  is_verified: boolean;
  provider: string;
}

interface AuthContextType {
  user: User | null;
  guestSessionId: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [guestSessionId, setGuestSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  // Initialize Guest Session ID
  useEffect(() => {
    if (typeof window !== 'undefined') {
      let gid = localStorage.getItem('guestSessionId');
      if (!gid) {
        gid = crypto.randomUUID();
        localStorage.setItem('guestSessionId', gid);
      }
      setGuestSessionId(gid);
    }
  }, []);

  const checkAuth = async () => {
    try {
      const res = await fetch("/api/auth/me", { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error("Auth check failed", error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      credentials: 'include'
    });

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || "Login failed");
    }

    await checkAuth();
    router.push("/");
  };

  const signup = async (email: string, password: string) => {
    const res = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      credentials: 'include'
    });

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || "Signup failed");
    }
    
    // Usually redirect to verify page or login
    router.push("/login?message=check-email");
  };

  const logout = async () => {
    await fetch("/api/auth/logout", { method: "POST", credentials: 'include' });
    setUser(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider value={{ user, guestSessionId, loading, login, signup, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
