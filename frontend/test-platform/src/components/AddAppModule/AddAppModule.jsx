import React, { useEffect, useMemo, useState } from 'react';
import {
  AppWindow, Boxes, AlertCircle, ChevronDown, Save, RotateCcw,
} from 'lucide-react';
import catalogService from '../../services/catalogService';
import './AddAppModule.css';

const PLATFORM_OPTIONS = ['Android', 'iOS', 'Web'];

const EMPTY_APP_FORM = {
  applicationName: '',
  platform: '',
  packageName: '',
  description: '',
};

const EMPTY_MODULE_FORM = {
  applicationId: '',
  moduleName: '',
  description: '',
  displayOrder: '',
};

/* ── Reusable field label ──────────────────────────────────────────────────── */
function Label({ children, required }) {
  return (
    <span className="aam-label">
      {children}
      {required && <span className="req">*</span>}
    </span>
  );
}

/* ── ID-backed select field ───────────────────────────────────────────────── */
function Select({ value, onChange, options, placeholder, disabled }) {
  return (
    <div className="aam-select-wrap">
      <select
        className={`aam-select ${value ? '' : 'placeholder'}`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      >
        <option value="" disabled hidden>{placeholder}</option>
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
      <ChevronDown size={16} />
    </div>
  );
}

export default function AddAppModule() {
  const [applications, setApplications] = useState([]);
  const [modules, setModules] = useState([]);

  const [appForm, setAppForm] = useState(EMPTY_APP_FORM);
  const [moduleForm, setModuleForm] = useState(EMPTY_MODULE_FORM);

  const [savingApp, setSavingApp] = useState(false);
  const [savingModule, setSavingModule] = useState(false);
  const [error, setError] = useState('');

  const setAppField = (key) => (val) => setAppForm((f) => ({ ...f, [key]: val }));
  const setModuleField = (key) => (val) => setModuleForm((f) => ({ ...f, [key]: val }));

  const applicationById = useMemo(
    () => Object.fromEntries(applications.map((a) => [a.application_id, a])),
    [applications],
  );

  const refreshApplications = async () => {
    try {
      const res = await catalogService.listApplications();
      setApplications(res.items || []);
    } catch {
      setError('Failed to load applications. Is the backend running on http://localhost:8000?');
    }
  };

  const refreshModules = async () => {
    try {
      const res = await catalogService.listModules();
      setModules(res.items || []);
    } catch {
      setError('Failed to load modules. Is the backend running on http://localhost:8000?');
    }
  };

  useEffect(() => {
    refreshApplications();
    refreshModules();
  }, []);

  const handleSaveApplication = async () => {
    if (!appForm.applicationName.trim() || !appForm.platform) return;
    setSavingApp(true);
    setError('');
    try {
      await catalogService.createApplication({
        application_name: appForm.applicationName.trim(),
        platform: appForm.platform,
        package_name: appForm.packageName.trim() || null,
        description: appForm.description.trim() || null,
      });
      setAppForm(EMPTY_APP_FORM);
      await refreshApplications();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to save application.');
    } finally {
      setSavingApp(false);
    }
  };

  const handleSaveModule = async () => {
    if (!moduleForm.applicationId || !moduleForm.moduleName.trim()) return;
    setSavingModule(true);
    setError('');
    try {
      await catalogService.createModule({
        application_id: moduleForm.applicationId,
        module_name: moduleForm.moduleName.trim(),
        description: moduleForm.description.trim() || null,
        display_order: moduleForm.displayOrder === '' ? 0 : Number(moduleForm.displayOrder),
      });
      setModuleForm(EMPTY_MODULE_FORM);
      await refreshModules();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to save module.');
    } finally {
      setSavingModule(false);
    }
  };

  const applicationOptions = applications.map((a) => ({ value: a.application_id, label: a.application_name }));

  return (
    <div className="aam-page">
      <div className="aam-heading">
        <h1>Applications &amp; Modules</h1>
        <p>Manage the applications and modules used across test cases</p>
      </div>

      {error && (
        <div className="aam-error-banner">
          <AlertCircle size={15} />
          <span>{error}</span>
        </div>
      )}

      {/* ── Applications ── */}
      <div className="aam-section">
        <h2 className="aam-section-title"><AppWindow size={18} /> Applications</h2>

        <div className="aam-card">
          <div className="aam-form-grid">
            <div className="aam-field span-2">
              <Label required>Application Name</Label>
              <input
                className="aam-input"
                placeholder="e.g. Regular Farmer App"
                value={appForm.applicationName}
                onChange={(e) => setAppField('applicationName')(e.target.value)}
              />
            </div>

            <div className="aam-field">
              <Label required>Platform</Label>
              <Select
                value={appForm.platform}
                onChange={setAppField('platform')}
                options={PLATFORM_OPTIONS.map((p) => ({ value: p, label: p }))}
                placeholder="Select Platform"
              />
            </div>

            <div className="aam-field">
              <Label>Package Name</Label>
              <input
                className="aam-input"
                placeholder="e.g. com.krishivaas.regular"
                value={appForm.packageName}
                onChange={(e) => setAppField('packageName')(e.target.value)}
              />
            </div>

            <div className="aam-field span-full">
              <Label>Description</Label>
              <textarea
                className="aam-textarea"
                rows={2}
                placeholder="What this application is for"
                value={appForm.description}
                onChange={(e) => setAppField('description')(e.target.value)}
              />
            </div>
          </div>

          <div className="aam-actions">
            <button className="aam-btn ghost" onClick={() => setAppForm(EMPTY_APP_FORM)}>
              <RotateCcw size={15} /> Reset
            </button>
            <span style={{ flex: 1 }} />
            <button
              className="aam-btn primary"
              onClick={handleSaveApplication}
              disabled={savingApp || !appForm.applicationName.trim() || !appForm.platform}
            >
              <Save size={15} /> {savingApp ? 'Saving...' : 'Save Application'}
            </button>
          </div>
        </div>

        <div className="aam-card">
          <div className="aam-table-scroll">
            <table className="aam-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Platform</th>
                  <th>Package Name</th>
                  <th>Description</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((a) => (
                  <tr key={a.application_id}>
                    <td className="cell-name">{a.application_name}</td>
                    <td><span className="aam-tag blue">{a.platform}</span></td>
                    <td className="cell-muted">{a.package_name || '—'}</td>
                    <td className="cell-muted">{a.description || '—'}</td>
                    <td><span className="aam-tag green">{a.status ? 'Active' : 'Inactive'}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {applications.length === 0 && <div className="aam-table-empty">No applications yet.</div>}
          </div>
        </div>
      </div>

      {/* ── Modules ── */}
      <div className="aam-section">
        <h2 className="aam-section-title"><Boxes size={18} /> Modules</h2>

        <div className="aam-card">
          <div className="aam-form-grid">
            <div className="aam-field">
              <Label required>Application</Label>
              <Select
                value={moduleForm.applicationId}
                onChange={setModuleField('applicationId')}
                options={applicationOptions}
                placeholder="Select App"
              />
            </div>

            <div className="aam-field span-2">
              <Label required>Module Name</Label>
              <input
                className="aam-input"
                placeholder="e.g. Authentication"
                value={moduleForm.moduleName}
                onChange={(e) => setModuleField('moduleName')(e.target.value)}
              />
            </div>

            <div className="aam-field">
              <Label>Display Order</Label>
              <input
                className="aam-input"
                type="number"
                placeholder="0"
                value={moduleForm.displayOrder}
                onChange={(e) => setModuleField('displayOrder')(e.target.value)}
              />
            </div>

            <div className="aam-field span-full">
              <Label>Description</Label>
              <textarea
                className="aam-textarea"
                rows={2}
                placeholder="What this module covers"
                value={moduleForm.description}
                onChange={(e) => setModuleField('description')(e.target.value)}
              />
            </div>
          </div>

          <div className="aam-actions">
            <button className="aam-btn ghost" onClick={() => setModuleForm(EMPTY_MODULE_FORM)}>
              <RotateCcw size={15} /> Reset
            </button>
            <span style={{ flex: 1 }} />
            <button
              className="aam-btn primary"
              onClick={handleSaveModule}
              disabled={savingModule || !moduleForm.applicationId || !moduleForm.moduleName.trim()}
            >
              <Save size={15} /> {savingModule ? 'Saving...' : 'Save Module'}
            </button>
          </div>
        </div>

        <div className="aam-card">
          <div className="aam-table-scroll">
            <table className="aam-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Application</th>
                  <th>Description</th>
                  <th>Display Order</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {modules.map((m) => (
                  <tr key={m.module_id}>
                    <td className="cell-name">{m.module_name}</td>
                    <td>{applicationById[m.application_id]?.application_name || '—'}</td>
                    <td className="cell-muted">{m.description || '—'}</td>
                    <td className="cell-muted">{m.display_order}</td>
                    <td><span className="aam-tag green">{m.status ? 'Active' : 'Inactive'}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {modules.length === 0 && <div className="aam-table-empty">No modules yet.</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
