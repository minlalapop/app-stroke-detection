import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth";
import { ProtectedLayout } from "./components";
import {
  AnalysisPage,
  AnalysesPage,
  AuditPage,
  DashboardPage,
  LandingPage,
  LoginPage,
  PatientPage,
  PatientsPage,
  RegisterPage,
} from "./pages";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<ProtectedLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/patients" element={<PatientsPage />} />
          <Route path="/patients/:patientId" element={<PatientPage />} />
          <Route path="/analyses" element={<AnalysesPage />} />
          <Route path="/analyses/:analysisId" element={<AnalysisPage />} />
          <Route path="/audit" element={<AuditPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
