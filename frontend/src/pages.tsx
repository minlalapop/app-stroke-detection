import { useEffect, useMemo, useState, type FormEvent } from "react";
import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom";
import {
  api,
  ApiError,
  downloadExport,
  jsonBody,
  type Analysis,
  type AuditEvent,
  type ClinicalData,
  type ImagingStudy,
  type Patient,
  type Report,
} from "./api";
import { useAuth } from "./auth";
import {
  EmptyState,
  Icon,
  PageHeader,
  Spinner,
  StatusBadge,
} from "./components";

function useLoad<T>(loader: () => Promise<T>, dependencies: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const reload = () => {
    setLoading(true);
    setError("");
    loader()
      .then(setData)
      .catch((reason: unknown) =>
        setError(
          reason instanceof Error ? reason.message : "Chargement impossible.",
        ),
      )
      .finally(() => setLoading(false));
  };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(reload, dependencies);
  return { data, setData, error, loading, reload };
}

export function LandingPage() {
  const { user } = useAuth();
  return (
    <div className="landing mesh-bg">
      <nav className="landing-nav">
        <span className="brand">
          <span className="brand-mark">
            <Icon>neurology</Icon>
          </span>
          <span>
            NeuroFlow <b>Clinical</b>
          </span>
        </span>
        <div className="landing-nav-actions">
          {!user && <Link className="text-link" to="/login">Se connecter</Link>}
          <Link className="button button-dark" to={user ? "/dashboard" : "/register"}>
            {user ? "Ouvrir l’espace" : "Créer un compte"}<Icon>arrow_forward</Icon>
          </Link>
        </div>
      </nav>
      <main className="hero">
        <div className="hero-copy">
          <span className="eyebrow">Aide à l’analyse de l’AVC</span>
          <h1>
            Une analyse AVC.
            <br />
            <em>Une lecture clinique claire.</em>
          </h1>
          <p>
            Centralisez les données cliniques et les images DICOM, lancez
            l’analyse et conservez la validation médicale au cœur de chaque
            rapport.
          </p>
          <div className="hero-actions">
            <Link
              className="button button-dark button-large"
              to={user ? "/dashboard" : "/register"}
            >
              {user ? "Ouvrir mon espace" : "Créer un compte"}<Icon>arrow_forward</Icon>
            </Link>
            <a className="text-link" href="#workflow">
              Voir le fonctionnement
            </a>
          </div>
        </div>
        <div className="hero-visual glass-panel">
          <div className="visual-orbit">
            <span className="orbit orbit-one" />
            <span className="orbit orbit-two" />
            <div className="brain-core">
              <Icon>neurology</Icon>
            </div>
          </div>
          <div className="visual-caption">
            <span className="eyebrow">NeuroFlow Clinical</span>
            <h2>Du dossier au rapport</h2>
            <p>Un espace calme et clair pour accompagner chaque analyse.</p>
          </div>
        </div>
      </main>
      <section id="workflow" className="landing-strip">
        <div className="landing-feature">
          <Icon>lock</Icon>
          <span>
            <b>Votre espace</b>
            <small>Retrouvez facilement vos dossiers</small>
          </span>
        </div>
        <div className="landing-feature">
          <Icon>neurology</Icon>
          <span>
            <b>Analyse AVC</b>
            <small>À partir des données cliniques ou d’une IRM</small>
          </span>
        </div>
        <div className="landing-feature">
          <Icon>history</Icon>
          <span>
            <b>Rapport médical</b>
            <small>Validé par le médecin avant export</small>
          </span>
        </div>
      </section>
    </div>
  );
}

export function LoginPage() {
  const { user, login } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const registrationSucceeded = Boolean(
    (location.state as { registered?: boolean } | null)?.registered,
  );
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [visible, setVisible] = useState(false);
  if (user) return <Navigate to="/dashboard" replace />;
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Connexion impossible.",
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="login-page mesh-bg">
      <Link className="back-link" to="/">
        <Icon>arrow_back</Icon>Accueil
      </Link>
      <div className="login-card glass-panel">
        <div className="login-brand">
          <span className="brand-mark brand-mark-large">
            <Icon>neurology</Icon>
          </span>
          <h1>NeuroFlow Clinical</h1>
          <p>ESPACE MÉDECIN</p>
        </div>
        <form onSubmit={(event) => void submit(event)}>
          {registrationSucceeded && (
            <div className="alert">
              <Icon>check_circle</Icon>
              Compte créé. Vous pouvez maintenant vous connecter.
            </div>
          )}
          <label>
            Email
            <input
              autoFocus
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="nom@exemple.com"
              required
            />
          </label>
          <label>
            Mot de passe
            <div className="password-field">
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type={visible ? "text" : "password"}
                placeholder="••••••••"
                required
              />
              <button type="button" onClick={() => setVisible(!visible)}>
                <Icon>{visible ? "visibility_off" : "visibility"}</Icon>
              </button>
            </div>
          </label>
          {error && (
            <div className="alert alert-error">
              <Icon>error</Icon>
              {error}
            </div>
          )}
          <button className="button button-dark button-full" disabled={busy}>
            {busy ? "Connexion…" : "Se connecter"}
            <Icon>arrow_forward</Icon>
          </button>
        </form>
        <p className="auth-switch">
          Pas encore de compte ? <Link to="/register">Créer un compte</Link>
        </p>
      </div>
    </div>
  );
}

export function RegisterPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email);
  const passwordChecks = {
    length: form.password.length >= 8,
    lowercase: /[a-z]/.test(form.password),
    uppercase: /[A-Z]/.test(form.password),
    number: /\d/.test(form.password),
  };
  const passwordValid = Object.values(passwordChecks).every(Boolean);
  if (user) return <Navigate to="/dashboard" replace />;
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!emailValid || !passwordValid) {
      setError("Vérifiez l’email et les critères du mot de passe.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await api("/auth/register", { method: "POST", ...jsonBody(form) });
      navigate("/login", { state: { registered: true } });
    } catch (reason) {
      setError(errorText(reason));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="login-page mesh-bg">
      <Link className="back-link" to="/login">
        <Icon>arrow_back</Icon>Connexion
      </Link>
      <div className="login-card glass-panel">
        <div className="login-brand">
          <span className="brand-mark brand-mark-large">
            <Icon>person_add</Icon>
          </span>
          <h1>Créer un compte</h1>
          <p>ESPACE MÉDECIN</p>
        </div>
        <form onSubmit={(e) => void submit(e)}>
          <label>
            Nom complet
            <input
              autoFocus
              required
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
          </label>
          <label>
            Email
            <input
              required
              type="email"
              value={form.email}
              placeholder="nom@exemple.com"
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
            {form.email && !emailValid && (
              <small className="field-error">Saisissez une adresse email valide.</small>
            )}
          </label>
          <label>
            Mot de passe
            <input
              required
              minLength={8}
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
            <small className="password-rules">
              8 caractères minimum, avec une minuscule, une majuscule et un chiffre.
            </small>
          </label>
          {error && (
            <div className="alert alert-error">
              <Icon>error</Icon>
              {error}
            </div>
          )}
          <button
            className="button button-dark button-full"
            disabled={busy || !emailValid || !passwordValid}
          >
            {busy ? "Création…" : "Créer mon compte"}
            <Icon>arrow_forward</Icon>
          </button>
        </form>
        <p className="auth-switch">
          Déjà inscrit(e) ? <Link to="/login">Se connecter</Link>
        </p>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { user } = useAuth();
  const patients = useLoad(() => api<Patient[]>("/patients"), []);
  if (patients.loading) return <Spinner label="Chargement" />;
  return (
    <>
      <PageHeader
        eyebrow="Accueil"
        title={`Bonjour, ${user?.full_name.split(" ")[0]}`}
        text="Retrouvez vos dossiers et commencez une nouvelle analyse."
        action={
          <Link className="button button-primary" to="/patients">
            <Icon>add</Icon>Nouveau patient
          </Link>
        }
      />
      {patients.error && (
        <div className="alert alert-error">{patients.error}</div>
      )}
      <div className="dashboard-intro glass-panel">
        <div>
          <span className="eyebrow">Dossiers patients</span>
          <strong>{patients.data?.length ?? 0}</strong>
          <p>Accédez simplement aux dossiers enregistrés.</p>
        </div>
        <Link
          className="round-action"
          to="/patients"
          aria-label="Ouvrir les patients"
        >
          <Icon>arrow_forward</Icon>
        </Link>
      </div>
      <section className="panel">
        <div className="section-head">
          <div>
            <h2>Patients récents</h2>
            <p>
              Accédez au dossier pour saisir les données et lancer une analyse.
            </p>
          </div>
          <Link className="text-link" to="/patients">
            Voir tous
          </Link>
        </div>
        {patients.data?.length ? (
          <div className="patient-list">
            {patients.data
              .slice(0, 5)
              .map((patient) => (
                <Link
                  to={`/patients/${patient.id}`}
                  className="patient-row"
                  key={patient.id}
                >
                  <span className="patient-avatar">
                    {patient.first_name[0]}
                    {patient.last_name[0]}
                  </span>
                  <div>
                    <b>
                      {patient.first_name} {patient.last_name}
                    </b>
                    <small>Né(e) le {formatDate(patient.birth_date)}</small>
                  </div>
                  <Icon>chevron_right</Icon>
                </Link>
              ))}
          </div>
        ) : (
          <EmptyState
            icon="folder_shared"
            title="Aucun patient"
            text="Créez le premier dossier patient pour commencer."
          />
        )}
      </section>
    </>
  );
}

export function PatientsPage() {
  const { data, loading, error, reload } = useLoad(
    () => api<Patient[]>("/patients"),
    [],
  );
  const [showForm, setShowForm] = useState(false);
  const [editTarget, setEditTarget] = useState<Patient | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Patient | null>(null);
  const [actionError, setActionError] = useState("");
  const [actionBusy, setActionBusy] = useState(false);
  const [search, setSearch] = useState("");
  const filtered = useMemo(
    () =>
      (data ?? []).filter((patient) =>
        `${patient.first_name} ${patient.last_name}`
          .toLowerCase()
          .includes(search.toLowerCase()),
      ),
    [data, search],
  );
  return (
    <>
      <PageHeader
        eyebrow="Dossiers"
        title="Patients"
        text="Consultez ou créez un dossier patient."
        action={
          <button
            className="button button-primary"
            onClick={() => setShowForm(true)}
          >
            <Icon>person_add</Icon>Créer un patient
          </button>
        }
      />
      {showForm && (
        <PatientForm
          onClose={() => setShowForm(false)}
          onSaved={() => {
            setShowForm(false);
            reload();
          }}
        />
      )}
      {editTarget && (
        <PatientForm
          patient={editTarget}
          onClose={() => setEditTarget(null)}
          onSaved={() => {
            setEditTarget(null);
            reload();
          }}
        />
      )}
      {deleteTarget && (
        <div className="modal-backdrop" onMouseDown={() => setDeleteTarget(null)}>
          <div
            className="modal modal-confirm panel"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <span className="confirm-icon"><Icon>delete</Icon></span>
            <h2>Supprimer ce patient ?</h2>
            <p>
              Le dossier de {deleteTarget.first_name} {deleteTarget.last_name} et
              ses données associées seront supprimés.
            </p>
            {actionError && <div className="alert alert-error">{actionError}</div>}
            <div className="form-actions">
              <button
                className="button button-ghost"
                onClick={() => setDeleteTarget(null)}
              >
                Annuler
              </button>
              <button
                className="button button-danger"
                disabled={actionBusy}
                onClick={() => {
                  setActionBusy(true);
                  setActionError("");
                  void api(`/patients/${deleteTarget.id}`, { method: "DELETE" })
                    .then(() => {
                      setDeleteTarget(null);
                      reload();
                    })
                    .catch((reason) => setActionError(errorText(reason)))
                    .finally(() => setActionBusy(false));
                }}
              >
                {actionBusy ? "Suppression…" : "Supprimer"}
              </button>
            </div>
          </div>
        </div>
      )}
      <section className="panel">
        <div className="toolbar">
          <label className="search">
            <Icon>search</Icon>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher un patient"
            />
          </label>
          <span>
            {filtered.length} dossier{filtered.length > 1 ? "s" : ""}
          </span>
        </div>
        {loading ? (
          <Spinner />
        ) : error ? (
          <div className="alert alert-error">{error}</div>
        ) : filtered.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Date de naissance</th>
                  <th>Sexe</th>
                  <th>Créé le</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {filtered.map((patient) => (
                  <tr key={patient.id}>
                    <td>
                      <b>
                        {patient.first_name} {patient.last_name}
                      </b>
                    </td>
                    <td>{formatDate(patient.birth_date)}</td>
                    <td>{patient.sex}</td>
                    <td>{formatDate(patient.created_at)}</td>
                    <td>
                      <div className="table-actions">
                        <button
                          className="icon-button"
                          title="Modifier"
                          onClick={() => setEditTarget(patient)}
                        >
                          <Icon>edit</Icon>
                        </button>
                        <button
                          className="icon-button icon-button-danger"
                          title="Supprimer"
                          onClick={() => setDeleteTarget(patient)}
                        >
                          <Icon>delete</Icon>
                        </button>
                        <Link
                          className="icon-button"
                          title="Ouvrir"
                          to={`/patients/${patient.id}`}
                        >
                          <Icon>arrow_forward</Icon>
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon="search_off"
            title="Aucun résultat"
            text="Aucun dossier ne correspond à votre recherche."
          />
        )}
      </section>
    </>
  );
}

function PatientForm({
  onClose,
  onSaved,
  patient,
}: {
  onClose: () => void;
  onSaved: () => void;
  patient?: Patient;
}) {
  const [form, setForm] = useState({
    first_name: patient?.first_name ?? "",
    last_name: patient?.last_name ?? "",
    birth_date: patient?.birth_date ?? "",
    sex: patient?.sex ?? "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(patient ? `/patients/${patient.id}` : "/patients", {
        method: patient ? "PUT" : "POST",
        ...jsonBody(form),
      });
      onSaved();
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Création impossible.",
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <form
        className="modal panel"
        onMouseDown={(e) => e.stopPropagation()}
        onSubmit={(e) => void submit(e)}
      >
        <div className="section-head">
          <div>
            <span className="eyebrow">
              {patient ? "Modifier le dossier" : "Nouveau dossier"}
            </span>
            <h2>Informations patient</h2>
          </div>
          <button type="button" className="icon-button" onClick={onClose}>
            <Icon>close</Icon>
          </button>
        </div>
        <div className="form-grid">
          <label>
            Prénom
            <input
              required
              value={form.first_name}
              onChange={(e) => setForm({ ...form, first_name: e.target.value })}
            />
          </label>
          <label>
            Nom
            <input
              required
              value={form.last_name}
              onChange={(e) => setForm({ ...form, last_name: e.target.value })}
            />
          </label>
          <label>
            Date de naissance
            <input
              required
              type="date"
              max={new Date().toISOString().slice(0, 10)}
              value={form.birth_date}
              onChange={(e) => setForm({ ...form, birth_date: e.target.value })}
            />
          </label>
          <label>
            Sexe
            <select
              required
              value={form.sex}
              onChange={(e) => setForm({ ...form, sex: e.target.value })}
            >
              <option value="">Sélectionner</option>
              <option value="Female">Femme</option>
              <option value="Male">Homme</option>
            </select>
          </label>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        <div className="form-actions">
          <button
            type="button"
            className="button button-ghost"
            onClick={onClose}
          >
            Annuler
          </button>
          <button className="button button-primary" disabled={busy}>
            {busy
              ? "Enregistrement…"
              : patient
                ? "Enregistrer"
                : "Créer le dossier"}
          </button>
        </div>
      </form>
    </div>
  );
}

export function PatientPage() {
  const { patientId = "" } = useParams();
  const navigate = useNavigate();
  const patient = useLoad(
    () => api<Patient>(`/patients/${patientId}`),
    [patientId],
  );
  const clinical = useLoad(
    () => api<ClinicalData[]>(`/patients/${patientId}/clinical-data`),
    [patientId],
  );
  const studies = useLoad(
    () => api<ImagingStudy[]>(`/patients/${patientId}/imaging-studies`),
    [patientId],
  );
  const analyses = useLoad(
    () => api<Analysis[]>(`/patients/${patientId}/analyses`),
    [patientId],
  );
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [clinicalEditing, setClinicalEditing] = useState(false);
  const [showEditPatient, setShowEditPatient] = useState(false);
  const [showDeletePatient, setShowDeletePatient] = useState(false);
  const [clinicalForm, setClinicalForm] = useState({
    age: "",
    hypertension: "",
    heart_disease: "",
    ever_married: "",
    work_type: "",
    residence_type: "",
    avg_glucose_level: "",
    bmi: "",
    smoking_status: "",
  });
  const [clinicalId, setClinicalId] = useState("");
  const [studyId, setStudyId] = useState("");
  useEffect(() => {
    const record = clinical.data?.at(-1);
    if (!record) {
      setClinicalForm((current) => ({
        ...current,
        age: patient.data ? String(calculateAge(patient.data.birth_date)) : "",
      }));
      return;
    }
    setClinicalId(record.id);
    setClinicalForm(
      clinicalFormValues(record, patient.data?.birth_date ?? ""),
    );
  }, [clinical.data, patient.data]);
  useEffect(() => {
    if (studies.data?.length && !studyId)
      setStudyId(studies.data.at(-1)?.id ?? "");
  }, [studies.data, studyId]);
  if (patient.loading) return <Spinner label="Chargement du dossier" />;
  if (!patient.data)
    return (
      <div className="alert alert-error">
        {patient.error || "Patient introuvable."}
      </div>
    );
  const currentPatient = patient.data;
  const saveClinical = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const payload = {
        age: calculateAge(currentPatient.birth_date),
        hypertension: optionalBoolean(clinicalForm.hypertension),
        heart_disease: optionalBoolean(clinicalForm.heart_disease),
        ever_married: clinicalForm.ever_married || null,
        work_type: clinicalForm.work_type || null,
        residence_type: clinicalForm.residence_type || null,
        avg_glucose_level: optionalNumber(clinicalForm.avg_glucose_level),
        bmi: optionalNumber(clinicalForm.bmi),
        smoking_status: clinicalForm.smoking_status.trim() || null,
      };
      await api(
        clinicalId
          ? `/patients/${patientId}/clinical-data/${clinicalId}`
          : `/patients/${patientId}/clinical-data`,
        {
        method: clinicalId ? "PUT" : "POST",
        ...jsonBody(payload),
        },
      );
      clinical.reload();
      setClinicalEditing(false);
      setNotice(
        clinicalId
          ? "Les données cliniques ont été modifiées."
          : "Les données cliniques ont été enregistrées.",
      );
    } catch (reason) {
      setError(errorText(reason));
    } finally {
      setBusy(false);
    }
  };
  const upload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem(
      "dicom",
    ) as HTMLInputElement;
    if (!input.files?.[0]) return;
    setBusy(true);
    setError("");
    try {
      const body = new FormData();
      body.append("file", input.files[0]);
      await api(`/patients/${patientId}/imaging-studies`, {
        method: "POST",
        body,
      });
      event.currentTarget.reset();
      studies.reload();
    } catch (reason) {
      setError(errorText(reason));
    } finally {
      setBusy(false);
    }
  };
  const createAnalysis = async () => {
    if (!clinicalId && !studyId) {
      setError("Sélectionnez des données cliniques ou une étude DICOM.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const created = await api<Analysis>("/analyses", {
        method: "POST",
        ...jsonBody({
          patient_id: patientId,
          clinical_data_id: clinicalId || null,
          imaging_study_id: studyId || null,
        }),
      });
      navigate(`/analyses/${created.id}`);
    } catch (reason) {
      setError(errorText(reason));
    } finally {
      setBusy(false);
    }
  };
  const deletePatient = async () => {
    setBusy(true);
    setError("");
    try {
      await api(`/patients/${patientId}`, { method: "DELETE" });
      navigate("/patients");
    } catch (reason) {
      setError(errorText(reason));
      setShowDeletePatient(false);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      {showEditPatient && (
        <PatientForm
          patient={patient.data}
          onClose={() => setShowEditPatient(false)}
          onSaved={() => {
            setShowEditPatient(false);
            patient.reload();
          }}
        />
      )}
      {showDeletePatient && (
        <div className="modal-backdrop" onMouseDown={() => setShowDeletePatient(false)}>
          <div
            className="modal modal-confirm panel"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <span className="confirm-icon"><Icon>delete</Icon></span>
            <h2>Supprimer ce patient ?</h2>
            <p>
              Le dossier de {patient.data.first_name} {patient.data.last_name} et
              ses données associées seront supprimés.
            </p>
            <div className="form-actions">
              <button
                className="button button-ghost"
                onClick={() => setShowDeletePatient(false)}
              >
                Annuler
              </button>
              <button
                className="button button-danger"
                disabled={busy}
                onClick={() => void deletePatient()}
              >
                {busy ? "Suppression…" : "Supprimer"}
              </button>
            </div>
          </div>
        </div>
      )}
      <PageHeader
        eyebrow="Dossier patient"
        title={`${patient.data.first_name} ${patient.data.last_name}`}
        text={`Né(e) le ${formatDate(patient.data.birth_date)} · ${patient.data.sex}`}
        action={
          <div className="header-actions">
            <button
              className="button button-ghost"
              onClick={() => setShowEditPatient(true)}
            >
              <Icon>edit</Icon>Modifier
            </button>
            <button
              className="icon-button icon-button-danger"
              title="Supprimer le patient"
              onClick={() => setShowDeletePatient(true)}
            >
              <Icon>delete</Icon>
            </button>
            <Link className="button button-ghost" to="/patients">
              <Icon>arrow_back</Icon>Patients
            </Link>
          </div>
        }
      />
      {error && <div className="alert alert-error">{error}</div>}
      {notice && (
        <div className="alert">
          <Icon>check_circle</Icon>
          {notice}
        </div>
      )}
      <div className="content-grid">
        <section className="panel">
          <div className="section-head">
            <div>
              <h2>Données cliniques</h2>
              <p>
                Renseignez les informations disponibles.
              </p>
            </div>
          </div>
          <form onSubmit={(e) => void saveClinical(e)}>
            <div className="form-grid compact">
              <label>
                Âge
                <input
                  type="number"
                  readOnly
                  aria-readonly="true"
                  value={clinicalForm.age}
                />
              </label>
              <label>
                Hypertension
                <select
                  disabled={Boolean(clinicalId) && !clinicalEditing}
                  value={clinicalForm.hypertension}
                  onChange={(e) =>
                    setClinicalForm({
                      ...clinicalForm,
                      hypertension: e.target.value,
                    })
                  }
                >
                  <option value="">Non renseigné</option>
                  <option value="true">Oui</option>
                  <option value="false">Non</option>
                </select>
              </label>
              <label>
                Maladie cardiaque
                <select
                  disabled={Boolean(clinicalId) && !clinicalEditing}
                  value={clinicalForm.heart_disease}
                  onChange={(e) =>
                    setClinicalForm({
                      ...clinicalForm,
                      heart_disease: e.target.value,
                    })
                  }
                >
                  <option value="">Non renseigné</option>
                  <option value="true">Oui</option>
                  <option value="false">Non</option>
                </select>
              </label>
              <label>
                Déjà marié(e)
                <select
                  disabled={Boolean(clinicalId) && !clinicalEditing}
                  value={clinicalForm.ever_married}
                  onChange={(e) =>
                    setClinicalForm({
                      ...clinicalForm,
                      ever_married: e.target.value,
                    })
                  }
                >
                  <option value="">Non renseigné</option>
                  <option value="Yes">Oui</option>
                  <option value="No">Non</option>
                </select>
              </label>
              <label>
                Type de travail
                <select
                  disabled={Boolean(clinicalId) && !clinicalEditing}
                  value={clinicalForm.work_type}
                  onChange={(e) =>
                    setClinicalForm({
                      ...clinicalForm,
                      work_type: e.target.value,
                    })
                  }
                >
                  <option value="">Non renseigné</option>
                  <option value="Private">Privé</option>
                  <option value="Self-employed">Indépendant</option>
                  <option value="children">Enfant</option>
                  <option value="Govt_job">Secteur public</option>
                  <option value="Never_worked">N’a jamais travaillé</option>
                </select>
              </label>
              <label>
                Type de résidence
                <select
                  disabled={Boolean(clinicalId) && !clinicalEditing}
                  value={clinicalForm.residence_type}
                  onChange={(e) =>
                    setClinicalForm({
                      ...clinicalForm,
                      residence_type: e.target.value,
                    })
                  }
                >
                  <option value="">Non renseigné</option>
                  <option value="Urban">Urbaine</option>
                  <option value="Rural">Rurale</option>
                </select>
              </label>
              <label>
                Glycémie moyenne
                <input
                  disabled={Boolean(clinicalId) && !clinicalEditing}
                  type="number"
                  min="0"
                  step="any"
                  value={clinicalForm.avg_glucose_level}
                  onChange={(e) =>
                    setClinicalForm({
                      ...clinicalForm,
                      avg_glucose_level: e.target.value,
                    })
                  }
                />
              </label>
              <label>
                IMC
                <input
                  disabled={Boolean(clinicalId) && !clinicalEditing}
                  type="number"
                  min="0"
                  step="any"
                  value={clinicalForm.bmi}
                  onChange={(e) =>
                    setClinicalForm({ ...clinicalForm, bmi: e.target.value })
                  }
                />
              </label>
              <label>
                Statut tabagique
                <select
                  disabled={Boolean(clinicalId) && !clinicalEditing}
                  value={clinicalForm.smoking_status}
                  onChange={(e) =>
                    setClinicalForm({
                      ...clinicalForm,
                      smoking_status: e.target.value,
                    })
                  }
                >
                  <option value="">Non renseigné</option>
                  <option value="never smoked">N’a jamais fumé</option>
                  <option value="Unknown">Inconnu</option>
                  <option value="formerly smoked">Ancien fumeur</option>
                  <option value="smokes">Fume</option>
                </select>
              </label>
            </div>
            <div className="form-actions">
              {clinicalId && !clinicalEditing ? (
                <button
                  type="button"
                  className="button button-primary"
                  onClick={() => {
                    setNotice("");
                    setClinicalEditing(true);
                  }}
                >
                  <Icon>edit</Icon>Modifier
                </button>
              ) : (
                <>
                  {clinicalId && (
                    <button
                      type="button"
                      className="button button-ghost"
                      onClick={() => {
                        const saved = clinical.data?.at(-1);
                        if (saved) {
                          setClinicalForm(
                            clinicalFormValues(saved, currentPatient.birth_date),
                          );
                        }
                        setClinicalEditing(false);
                      }}
                    >
                      Annuler
                    </button>
                  )}
                  <button className="button button-primary" disabled={busy}>
                    <Icon>check</Icon>
                    {busy ? "Validation…" : "Valider"}
                  </button>
                </>
              )}
            </div>
          </form>
          {!clinical.data?.length && (
            <EmptyState
              icon="clinical_notes"
              title="Aucune donnée clinique"
              text="Le formulaire peut rester partiel si une information n’est pas disponible."
            />
          )}
        </section>
        <section className="panel">
          <div className="section-head">
            <div>
              <h2>Études DICOM</h2>
              <p>Le fichier original .dcm est validé et conservé.</p>
            </div>
          </div>
          <form className="upload-box" onSubmit={(e) => void upload(e)}>
            <Icon>upload_file</Icon>
            <label>
              Choisir un fichier DICOM
              <input
                name="dicom"
                type="file"
                accept=".dcm,application/dicom"
                required
              />
            </label>
            <button className="button button-primary" disabled={busy}>
              Uploader
            </button>
          </form>
          {studies.data?.length ? (
            <RecordSelect
              label="Études disponibles"
              value={studyId}
              onChange={setStudyId}
              items={studies.data.map((item) => ({
                id: item.id,
                label: `${item.original_filename} · ${formatBytes(item.file_size)}`,
              }))}
            />
          ) : (
            <EmptyState
              icon="radiology"
              title="Aucune étude DICOM"
              text="Ajoutez un fichier DICOM valide pour l’analyse d’image."
            />
          )}
        </section>
      </div>
      <section className="panel analysis-create">
        <div>
          <span className="eyebrow">Analyse AVC</span>
          <h2>Créer une analyse</h2>
          <p>Sélectionnez les données disponibles puis lancez le traitement.</p>
        </div>
        <button
          className="button button-dark"
          disabled={busy || (!clinicalId && !studyId)}
          onClick={() => void createAnalysis()}
        >
          Créer l’analyse<Icon>arrow_forward</Icon>
        </button>
      </section>
      <section className="panel">
        <div className="section-head">
          <div>
            <h2>Analyses du patient</h2>
            <p>Historique réel enregistré par l’application.</p>
          </div>
        </div>
        {analyses.data?.length ? (
          <div className="patient-list">
            {analyses.data.map((item) => (
              <Link
                key={item.id}
                className="patient-row"
                to={`/analyses/${item.id}`}
              >
                <StatusBadge status={item.status} />
                <div>
                  <b>Analyse du {formatDate(item.created_at)}</b>
                  <small>
                    {item.clinical_data_id ? "Données cliniques" : ""}
                    {item.clinical_data_id && item.imaging_study_id
                      ? " + "
                      : ""}
                    {item.imaging_study_id ? "DICOM" : ""}
                  </small>
                </div>
                <Icon>chevron_right</Icon>
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState
            icon="science"
            title="Aucune analyse"
            text="Sélectionnez une entrée ci-dessus pour commencer."
          />
        )}
      </section>
    </>
  );
}

function RecordSelect({
  label,
  value,
  onChange,
  items,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  items: { id: string; label: string }[];
}) {
  return (
    <label className="record-select">
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {items.map((item) => (
          <option key={item.id} value={item.id}>
            {item.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function AnalysesPage() {
  const analyses = useLoad(() => api<Analysis[]>("/analyses"), []);
  const patients = useLoad(() => api<Patient[]>("/patients"), []);
  const patientNames = new Map(
    (patients.data ?? []).map((patient) => [
      patient.id,
      `${patient.first_name} ${patient.last_name}`,
    ]),
  );
  return (
    <>
      <PageHeader
        eyebrow="Suivi"
        title="Analyses"
        text="Consultez les analyses ou démarrez-en une depuis un dossier patient."
        action={
          <Link className="button button-primary" to="/patients">
            <Icon>add</Icon>Nouvelle analyse
          </Link>
        }
      />
      <section className="panel">
        {analyses.loading || patients.loading ? (
          <Spinner />
        ) : analyses.error || patients.error ? (
          <div className="alert alert-error">
            {analyses.error || patients.error}
          </div>
        ) : analyses.data?.length ? (
          <div className="patient-list">
            {analyses.data.map((item) => (
              <Link
                key={item.id}
                className="patient-row"
                to={`/analyses/${item.id}`}
              >
                <StatusBadge status={item.status} />
                <div>
                  <b>{patientNames.get(item.patient_id) ?? "Patient"}</b>
                  <small>Analyse du {formatDate(item.created_at)}</small>
                </div>
                <Icon>chevron_right</Icon>
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState
            icon="monitor_heart"
            title="Aucune analyse"
            text="Choisissez un patient pour commencer une analyse."
          />
        )}
      </section>
    </>
  );
}

export function AnalysisPage() {
  const { analysisId = "" } = useParams();
  const { user } = useAuth();
  const analysis = useLoad(
    () => api<Analysis>(`/analyses/${analysisId}`),
    [analysisId],
  );
  const [validation, setValidation] = useState<
    import("./api").Validation | null
  >(null);
  const [report, setReport] = useState<Report | null>(null);
  const [comment, setComment] = useState("");
  const [decision, setDecision] = useState("VALIDATED");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const loadRelated = async () => {
    try {
      setValidation(await api(`/analyses/${analysisId}/validation`));
    } catch (e) {
      if (!(e instanceof ApiError && e.status === 404)) setError(errorText(e));
    }
    try {
      setReport(await api(`/analyses/${analysisId}/report`));
    } catch (e) {
      if (!(e instanceof ApiError && e.status === 404)) setError(errorText(e));
    }
  };
  useEffect(() => {
    void loadRelated();
  }, [analysisId]);
  const action = async (operation: () => Promise<unknown>) => {
    setBusy(true);
    setError("");
    try {
      await operation();
      analysis.reload();
      await loadRelated();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  };
  if (analysis.loading) return <Spinner label="Chargement de l’analyse" />;
  if (!analysis.data)
    return (
      <div className="alert alert-error">
        {analysis.error || "Analyse introuvable."}
      </div>
    );
  const item = analysis.data;
  return (
    <>
      <PageHeader
        eyebrow="Analyse AVC"
        title="Résultats"
        text={`Créée le ${formatDate(item.created_at)}`}
        action={<StatusBadge status={item.status} />}
      />
      {error && <div className="alert alert-error">{error}</div>}
      <section className="panel analysis-summary">
        <div>
          <b>Données cliniques</b>
          <span>{item.clinical_data_id ? "Incluses" : "Non incluses"}</span>
        </div>
        <div>
          <b>Étude DICOM</b>
          <span>{item.imaging_study_id ? "Incluse" : "Non incluse"}</span>
        </div>
        <button
          className="button button-primary"
          disabled={busy}
          onClick={() =>
            void action(() =>
              api(`/analyses/${analysisId}/run`, { method: "POST" }),
            )
          }
        >
          <Icon>play_arrow</Icon>Lancer l’analyse
        </button>
      </section>
      <div className="result-grid">
        {item.clinical_data_id && (
          <ResultCard
            title="Analyse clinique"
            icon="clinical_notes"
            result={item.tabular_result}
            image={false}
          />
        )}
        {item.imaging_study_id && (
          <ResultCard
            title="Analyse de l’IRM"
            icon="radiology"
            result={item.imaging_result}
            image
          />
        )}
      </div>
      <section className="panel">
        <div className="section-head">
          <div>
            <h2>Validation médicale</h2>
            <p>Le rapport reste bloqué jusqu’à validation par un médecin.</p>
          </div>
          {validation && <StatusBadge status={validation.validation_status} />}
        </div>
        {validation ? (
          <div className="validation-copy">
            <p>{validation.comment || "Aucun commentaire."}</p>
            <small>Validé le {formatDate(validation.validated_at)}</small>
          </div>
        ) : user?.role === "doctor" ? (
          <div className="validation-form">
            <select
              value={decision}
              onChange={(e) => setDecision(e.target.value)}
            >
              <option value="VALIDATED">Valider</option>
              <option value="REJECTED">Rejeter</option>
            </select>
            <textarea
              placeholder="Commentaire médical (facultatif)"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
            <button
              className="button button-primary"
              disabled={busy}
              onClick={() =>
                void action(() =>
                  api(`/analyses/${analysisId}/validate`, {
                    method: "POST",
                    ...jsonBody({
                      validation_status: decision,
                      comment: comment || null,
                    }),
                  }),
                )
              }
            >
              Enregistrer la décision
            </button>
          </div>
        ) : (
          <div className="alert">
            <Icon>info</Icon>Un compte médecin doit effectuer cette validation.
          </div>
        )}
      </section>
      <section className="panel">
        <div className="section-head">
          <div>
            <h2>Rapport</h2>
            <p>Disponible après validation médicale.</p>
          </div>
          {report && <StatusBadge status={report.status} />}
        </div>
        {!report ? (
          <button
            className="button button-dark"
            disabled={busy || validation?.validation_status !== "VALIDATED"}
            onClick={() =>
              void action(() =>
                api(`/analyses/${analysisId}/report`, { method: "POST" }),
              )
            }
          >
            Générer le rapport
          </button>
        ) : (
          <div className="report-actions">
            <div>
              <b>Rapport généré</b>
              <small>
                {report.llm_status === "COMPLETED"
                  ? "Une version enrichie est disponible"
                  : "Prêt à être exporté"}
              </small>
            </div>
            {report.llm_status === "COMPLETED" &&
              !report.llm_approved_by &&
              user?.role === "doctor" && (
                <button
                  className="button button-ghost"
                  onClick={() =>
                    void action(() =>
                      api(`/reports/${report.id}/approve-llm`, {
                        method: "POST",
                      }),
                    )
                  }
                >
                  Approuver la version enrichie
                </button>
              )}
            <div className="export-buttons">
              {(["pdf", "docx", "xlsx"] as const).map((format) => (
                <button
                  key={format}
                  className="button button-ghost"
                  disabled={busy}
                  onClick={() =>
                    void action(async () => {
                      const exported = await api<{ id: string }>(
                        `/reports/${report.id}/exports/${format}`,
                        { method: "POST" },
                      );
                      await downloadExport(exported.id);
                    })
                  }
                >
                  {format.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        )}
      </section>
    </>
  );
}

function ResultCard({
  title,
  icon,
  result,
  image,
}: {
  title: string;
  icon: string;
  result: Analysis["tabular_result"];
  image: boolean;
}) {
  return (
    <section className="panel result-card">
      <div className="section-head">
        <div className="result-title">
          <Icon>{icon}</Icon>
          <h2>{title}</h2>
        </div>
        {result && <StatusBadge status={result.status} />}
      </div>
      {!result ? (
        <EmptyState
          icon={icon}
          title="En attente"
          text="Lancez l’analyse pour obtenir le résultat."
        />
      ) : result.status === "MODEL_NOT_AVAILABLE" ? (
        <div className="model-unavailable">
          <Icon>hourglass_empty</Icon>
          <b>Analyse temporairement indisponible</b>
          <p>Aucun résultat n’a été généré.</p>
        </div>
      ) : (
        <dl className="result-values">
          {!image && (
            <>
              <dt>Risque estimé</dt>
              <dd>{display(result.risk_score)}</dd>
              <dt>Niveau</dt>
              <dd>{display(result.risk_label)}</dd>
            </>
          )}
          {image && (
            <>
              <dt>Lésion détectée</dt>
              <dd>
                {result.lesion_detected == null
                  ? "Non disponible"
                  : result.lesion_detected
                    ? "Oui"
                    : "Non"}
              </dd>
              <dt>Volume de la lésion</dt>
              <dd>
                {result.lesion_volume_ml == null
                  ? "Non disponible"
                  : `${result.lesion_volume_ml} ml`}
              </dd>
            </>
          )}
        </dl>
      )}
    </section>
  );
}

export function AuditPage() {
  const { user } = useAuth();
  const events = useLoad(() => api<AuditEvent[]>("/audit-events"), []);
  if (user?.role !== "admin") return <Navigate to="/dashboard" replace />;
  return (
    <>
      <PageHeader
        eyebrow="Traçabilité"
        title="Historique d’audit"
        text="Actions importantes enregistrées par le backend."
      />
      <section className="panel">
        {events.loading ? (
          <Spinner />
        ) : events.error ? (
          <div className="alert alert-error">{events.error}</div>
        ) : events.data?.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Entité</th>
                  <th>Identifiant</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {events.data.map((event) => (
                  <tr key={event.id}>
                    <td>
                      <b>{event.action.replaceAll("_", " ")}</b>
                    </td>
                    <td>{event.entity_type}</td>
                    <td className="id-copy">{event.entity_id || "—"}</td>
                    <td>{formatDate(event.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon="history"
            title="Aucun événement"
            text="L’historique apparaîtra à mesure que l’application est utilisée."
          />
        )}
      </section>
    </>
  );
}

function errorText(reason: unknown) {
  return reason instanceof Error ? reason.message : "Une erreur est survenue.";
}
function optionalNumber(value: string) {
  return value === "" ? null : Number(value);
}
function optionalBoolean(value: string) {
  return value === "" ? null : value === "true";
}
function booleanInput(value: boolean | null) {
  return value === null ? "" : String(value);
}
function numberInput(value: number | null) {
  return value === null ? "" : String(value);
}
function clinicalFormValues(record: ClinicalData, birthDate: string) {
  return {
    age: birthDate ? String(calculateAge(birthDate)) : "",
    hypertension: booleanInput(record.hypertension),
    heart_disease: booleanInput(record.heart_disease),
    ever_married: record.ever_married ?? "",
    work_type: record.work_type ?? "",
    residence_type: record.residence_type ?? "",
    avg_glucose_level: numberInput(record.avg_glucose_level),
    bmi: numberInput(record.bmi),
    smoking_status: record.smoking_status ?? "",
  };
}
function calculateAge(birthDate: string) {
  const birth = new Date(`${birthDate}T00:00:00`);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const birthdayNotReached =
    today.getMonth() < birth.getMonth() ||
    (today.getMonth() === birth.getMonth() &&
      today.getDate() < birth.getDate());
  if (birthdayNotReached) age -= 1;
  return age;
}
function display(value: unknown) {
  return value === null || value === undefined || value === ""
    ? "Non disponible"
    : String(value);
}
function formatDate(value: string) {
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    ...(value.includes("T") ? { timeStyle: "short" as const } : {}),
  }).format(new Date(value));
}
function formatBytes(value: number) {
  if (value < 1024) return `${value} o`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} Ko`;
  return `${(value / (1024 * 1024)).toFixed(1)} Mo`;
}
