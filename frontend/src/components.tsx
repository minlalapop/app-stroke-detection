import { NavLink, Navigate, Outlet } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "./auth";

export function Icon({ children }: { children: string }) {
  return (
    <span className="material-symbols-outlined" aria-hidden="true">
      {children}
    </span>
  );
}

export function Spinner({ label = "Chargement" }: { label?: string }) {
  return (
    <div className="center-state">
      <span className="spinner" />
      <span>{label}</span>
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase().replaceAll("_", "-");
  const labels: Record<string, string> = {
    CREATED: "Créée",
    WAITING_FOR_INPUT: "Informations requises",
    READY: "Prête",
    PROCESSING: "En cours",
    COMPLETED: "Terminée",
    PARTIAL_COMPLETED: "Partiellement terminée",
    MODEL_NOT_AVAILABLE: "Indisponible",
    FAILED: "Échec",
    VALIDATED_BY_DOCTOR: "Validée",
    REPORT_GENERATED: "Rapport généré",
    VALIDATED: "Validée",
    REJECTED: "Rejetée",
  };
  return (
    <span className={`status status-${normalized}`}>
      {labels[status] ?? status.replaceAll("_", " ")}
    </span>
  );
}

export function EmptyState({
  icon,
  title,
  text,
}: {
  icon: string;
  title: string;
  text: string;
}) {
  return (
    <div className="empty-state">
      <Icon>{icon}</Icon>
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}

export function ProtectedLayout() {
  const { user, loading, logout } = useAuth();
  if (loading) return <Spinner label="Ouverture de l’espace clinique" />;
  if (!user) return <Navigate to="/login" replace />;
  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink to="/dashboard" className="brand">
          <span className="brand-mark">
            <Icon>neurology</Icon>
          </span>
          <span>
            NeuroFlow <b>Clinical</b>
          </span>
        </NavLink>
        <nav className="top-nav" aria-label="Navigation principale">
          <NavLink to="/dashboard">
            <Icon>dashboard</Icon>
            <span>Accueil</span>
          </NavLink>
          <NavLink to="/patients">
            <Icon>folder_shared</Icon>
            <span>Patients</span>
          </NavLink>
          <NavLink to="/analyses">
            <Icon>monitor_heart</Icon>
            <span>Analyses</span>
          </NavLink>
          {user.role === "admin" && (
            <NavLink to="/audit">
              <Icon>history</Icon>
              <span>Audit</span>
            </NavLink>
          )}
        </nav>
        <div className="profile">
          <div className="profile-copy">
            <strong>{user.full_name}</strong>
            <span>{user.role === "admin" ? "Administrateur" : "Médecin"}</span>
          </div>
          <span className="avatar">
            {user.full_name.slice(0, 1).toUpperCase()}
          </span>
          <button
            className="icon-button"
            onClick={() => void logout()}
            title="Se déconnecter"
          >
            <Icon>logout</Icon>
          </button>
        </div>
      </header>
      <aside className="sidebar glass-panel">
        <div className="sidebar-heading">
          <span>Espace clinique</span>
          <small>Analyse AVC</small>
        </div>
        <nav aria-label="Navigation secondaire">
          <NavLink to="/dashboard">
            <Icon>dashboard</Icon>
            <span>Vue d’ensemble</span>
          </NavLink>
          <NavLink to="/patients">
            <Icon>folder_shared</Icon>
            <span>Patients</span>
          </NavLink>
          <NavLink to="/analyses">
            <Icon>monitor_heart</Icon>
            <span>Analyses</span>
          </NavLink>
          {user.role === "admin" && (
            <NavLink to="/audit">
              <Icon>history</Icon>
              <span>Historique</span>
            </NavLink>
          )}
        </nav>
      </aside>
      <main className="page">
        <Outlet />
      </main>
    </div>
  );
}

export function PageHeader({
  eyebrow,
  title,
  text,
  action,
}: {
  eyebrow?: string;
  title: string;
  text?: string;
  action?: ReactNode;
}) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h1>{title}</h1>
        {text && <p>{text}</p>}
      </div>
      {action}
    </div>
  );
}
