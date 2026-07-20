import React, { useEffect, useMemo, useState } from 'react';
import {
  Search, ClipboardList, Info, Eye, CheckCircle2, AlertCircle,
  ThumbsUp, ThumbsDown, Save, RotateCcw, Type, AlignLeft, ChevronDown,
  Filter, ArrowUpDown, Pencil, Trash2, ClipboardCheck, ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import testCaseService from '../../services/testCaseService';
import catalogService from '../../services/catalogService';
import './AddTestCase.css';

const TEST_TYPE_OPTIONS = ['Smoke', 'Regression', 'Functional', 'UI', 'Integration', 'Performance'];

const EMPTY_FORM = {
  testcaseKey: '',
  applicationId: '',
  moduleId: '',
  priorityId: '',
  testTypes: [],
  polarity: 'Positive',
  title: '',
  description: '',
  expectedResult: '',
};

/* ── Reusable field label ──────────────────────────────────────────────────── */
function Label({ children, required, info }) {
  return (
    <span className="atc-label">
      {children}
      {required && <span className="req">*</span>}
      {info && <span className="info-dot" title={info}><Info size={13} /></span>}
    </span>
  );
}

/* ── ID-backed select field ───────────────────────────────────────────────── */
function Select({ value, onChange, options, placeholder, disabled }) {
  return (
    <div className="atc-select-wrap">
      <select
        className={`atc-select ${value ? '' : 'placeholder'}`}
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

/* ── Multi-select chip group (test_types is a JSON array server-side) ───────── */
function MultiSelectChips({ value, onChange, options }) {
  const toggle = (opt) => {
    onChange(value.includes(opt) ? value.filter((v) => v !== opt) : [...value, opt]);
  };
  return (
    <div className="atc-multiselect">
      {options.map((opt) => (
        <button
          key={opt}
          type="button"
          className={`atc-chip-toggle ${value.includes(opt) ? 'active' : ''}`}
          onClick={() => toggle(opt)}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

function priorityBadgeStyle(color) {
  if (!color) return undefined;
  return { color, background: `${color}1A` };
}

export default function AddTestCase() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);

  const [applications, setApplications] = useState([]);
  const [allModules, setAllModules] = useState([]);
  const [modules, setModules] = useState([]);
  const [priorities, setPriorities] = useState([]);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const set = (key) => (val) => setForm((f) => ({ ...f, [key]: val }));

  const applicationById = useMemo(
    () => Object.fromEntries(applications.map((a) => [a.application_id, a])),
    [applications],
  );
  const moduleById = useMemo(
    () => Object.fromEntries(allModules.map((m) => [m.module_id, m])),
    [allModules],
  );
  const priorityById = useMemo(
    () => Object.fromEntries(priorities.map((p) => [p.priority_id, p])),
    [priorities],
  );

  const refreshTestCases = async () => {
    try {
      const res = await testCaseService.listTestCases({ page: 1, page_size: 20 });
      setRows(res.items || []);
      setTotal(res.total || 0);
    } catch {
      setError('Failed to load test cases. Is the backend running on http://localhost:8000?');
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const [appsRes, prioritiesRes, modulesRes] = await Promise.all([
          catalogService.listApplications(),
          catalogService.listPriorities(),
          catalogService.listModules(),
        ]);
        setApplications(appsRes.items || []);
        setPriorities(prioritiesRes.items || []);
        setAllModules(modulesRes.items || []);
      } catch {
        setError('Failed to load reference data. Is the backend running on http://localhost:8000?');
      }
    })();
    refreshTestCases();
  }, []);

  useEffect(() => {
    if (!form.applicationId) {
      setModules([]);
      return;
    }
    (async () => {
      try {
        const res = await catalogService.listModules(form.applicationId);
        setModules(res.items || []);
      } catch {
        setModules([]);
      }
    })();
  }, [form.applicationId]);

  const isDirty = useMemo(
    () => JSON.stringify(form) !== JSON.stringify(EMPTY_FORM),
    [form],
  );

  const hasPreview = form.title.trim() || form.testcaseKey.trim();

  const handleReset = () => setForm(EMPTY_FORM);

  const handleApplicationChange = (applicationId) => {
    setForm((f) => ({ ...f, applicationId, moduleId: '' }));
  };

  const handleSave = async () => {
    if (!form.title.trim() || !form.applicationId || !form.moduleId) return;
    setSaving(true);
    setError('');
    try {
      await testCaseService.createTestCase({
        testcase_key: form.testcaseKey.trim() || undefined,
        title: form.title.trim(),
        application_id: form.applicationId,
        module_id: form.moduleId,
        priority_id: form.priorityId || null,
        test_types: form.testTypes,
        polarity: form.polarity,
        description: form.description.trim() || null,
        expected_result: form.expectedResult.trim() || null,
      });
      setForm(EMPTY_FORM);
      await refreshTestCases();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to save test case.');
    } finally {
      setSaving(false);
    }
  };

  const applicationOptions = applications.map((a) => ({ value: a.application_id, label: a.application_name }));
  const moduleOptions = modules.map((m) => ({ value: m.module_id, label: m.module_name }));
  const priorityOptions = priorities.map((p) => ({ value: p.priority_id, label: p.priority_name }));

  return (
    <div className="atc-page">
      {/* ── Heading ── */}
      <div className="atc-heading">
        <h1>Add New Test Case</h1>
        <p>Create a new test case with all necessary details</p>
      </div>

      {error && (
        <div className="atc-error-banner">
          <AlertCircle size={15} />
          <span>{error}</span>
        </div>
      )}

      {/* ── Main grid ── */}
      <div className="atc-grid">
        {/* Left — the form */}
        <div className="atc-card">
          <div className="atc-card-head">
            <span className="atc-card-icon blue"><ClipboardList size={17} /></span>
            <h2>Test Case Details</h2>
          </div>

          <div className="atc-form-grid">
            {/* Row 1 */}
            <div className="atc-field">
              <Label info="Unique identifier for this test case — auto-generated if left blank">Test Case ID</Label>
              <input
                className="atc-input"
                placeholder="e.g. RF_AUTH_001"
                value={form.testcaseKey}
                onChange={(e) => set('testcaseKey')(e.target.value)}
              />
              <span className="atc-hint">Leave blank to auto-generate</span>
            </div>

            <div className="atc-field">
              <Label required>App</Label>
              <Select
                value={form.applicationId}
                onChange={handleApplicationChange}
                options={applicationOptions}
                placeholder="Select App"
              />
              <span className="atc-hint">Select the application</span>
            </div>

            <div className="atc-field">
              <Label required>Module</Label>
              <Select
                value={form.moduleId}
                onChange={set('moduleId')}
                options={moduleOptions}
                placeholder={form.applicationId ? 'Select Module' : 'Select an app first'}
                disabled={!form.applicationId}
              />
              <span className="atc-hint">Select the module</span>
            </div>

            <div className="atc-field">
              <Label>Priority</Label>
              <Select
                value={form.priorityId}
                onChange={set('priorityId')}
                options={priorityOptions}
                placeholder="Select Priority"
              />
              <span className="atc-hint">Set the priority level</span>
            </div>

            {/* Row 2 */}
            <div className="atc-field span-2">
              <Label required>Test Types</Label>
              <MultiSelectChips value={form.testTypes} onChange={set('testTypes')} options={TEST_TYPE_OPTIONS} />
              <span className="atc-hint">Select one or more test types</span>
            </div>

            <div className="atc-field span-2">
              <Label required>Test Type (Positive / Negative)</Label>
              <div className="atc-toggle-row">
                <button
                  type="button"
                  className={`atc-toggle pos ${form.polarity === 'Positive' ? 'active' : ''}`}
                  onClick={() => set('polarity')('Positive')}
                >
                  <ThumbsUp size={15} />
                  <span>Positive</span>
                  <span className="atc-radio" />
                </button>
                <button
                  type="button"
                  className={`atc-toggle neg ${form.polarity === 'Negative' ? 'active' : ''}`}
                  onClick={() => set('polarity')('Negative')}
                >
                  <ThumbsDown size={15} />
                  <span>Negative</span>
                  <span className="atc-radio" />
                </button>
              </div>
              <span className="atc-hint">Choose whether this is a positive or negative test case</span>
            </div>

            {/* Title */}
            <div className="atc-field span-full">
              <Label required>Title</Label>
              <div className="atc-input-icon">
                <Type size={15} />
                <input
                  className="atc-input"
                  placeholder="Enter test case title"
                  value={form.title}
                  onChange={(e) => set('title')(e.target.value)}
                />
              </div>
              <span className="atc-hint">A clear and concise title for this test case</span>
            </div>

            {/* Description */}
            <div className="atc-field span-full">
              <Label>Description</Label>
              <div className="atc-input-icon">
                <AlignLeft size={15} />
                <textarea
                  className="atc-textarea"
                  rows={3}
                  placeholder="Enter detailed description of the test case"
                  value={form.description}
                  onChange={(e) => set('description')(e.target.value)}
                />
              </div>
              <span className="atc-hint">Step by step description, preconditions, test data etc.</span>
            </div>

            {/* Expected Result */}
            <div className="atc-field span-full">
              <Label>Expected Result</Label>
              <div className="atc-input-icon">
                <CheckCircle2 size={15} color="var(--status-green)" />
                <textarea
                  className="atc-textarea"
                  rows={2}
                  placeholder="Enter the expected result"
                  value={form.expectedResult}
                  onChange={(e) => set('expectedResult')(e.target.value)}
                />
              </div>
              <span className="atc-hint">Expected outcome after executing the test case</span>
            </div>
          </div>

          {/* Actions */}
          <div className="atc-actions">
            <button className="atc-btn ghost" onClick={handleReset}>Cancel</button>
            <button className="atc-btn ghost" onClick={handleReset} disabled={!isDirty}>
              <RotateCcw size={15} /> Reset
            </button>
            <span className="spacer" />
            <button
              className="atc-btn primary"
              onClick={handleSave}
              disabled={saving || !form.title.trim() || !form.applicationId || !form.moduleId}
            >
              <Save size={15} /> {saving ? 'Saving...' : 'Save Test Case'}
            </button>
          </div>
        </div>

        {/* Right — preview */}
        <div className="atc-side">
          <div className="atc-card">
            <div className="atc-card-head">
              <span className="atc-card-icon slate"><Eye size={17} /></span>
              <h2>Test Case Preview</h2>
            </div>

            {!hasPreview ? (
              <div className="atc-preview-empty">
                <div className="icon"><ClipboardCheck size={30} /></div>
                <h3>Preview will appear here</h3>
                <p>Fill in the details to see a preview of your test case.</p>
              </div>
            ) : (
              <div className="atc-preview-filled">
                {form.testcaseKey.trim() && <div className="pv-id">{form.testcaseKey.trim()}</div>}
                <div className="pv-title">{form.title.trim() || 'Untitled test case'}</div>
                <div className="atc-preview-badges">
                  {form.testTypes.map((t) => <span key={t} className="atc-tag blue">{t}</span>)}
                  <span className={`atc-tag ${form.polarity === 'Positive' ? 'green' : 'red'}`}>
                    {form.polarity}
                  </span>
                  {form.priorityId && priorityById[form.priorityId] && (
                    <span
                      className="atc-tag slate"
                      style={priorityBadgeStyle(priorityById[form.priorityId].color)}
                    >
                      {priorityById[form.priorityId].priority_name}
                    </span>
                  )}
                </div>
                {form.applicationId && (
                  <div className="pv-block">
                    <span className="pv-lbl">App / Module</span>
                    {applicationById[form.applicationId]?.application_name}
                    {form.moduleId && moduleById[form.moduleId] ? ` · ${moduleById[form.moduleId].module_name}` : ''}
                  </div>
                )}
                {form.description.trim() && (
                  <div className="pv-block"><span className="pv-lbl">Description</span>{form.description.trim()}</div>
                )}
                {form.expectedResult.trim() && (
                  <div className="pv-block"><span className="pv-lbl">Expected Result</span>{form.expectedResult.trim()}</div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Existing Test Cases ── */}
      <div className="atc-card atc-table-card">
        <div className="atc-table-head">
          <h2>Existing Test Cases</h2>
          <div className="atc-table-tools">
            <div className="atc-table-search">
              <Search size={15} />
              <input placeholder="Search test cases..." />
            </div>
            <button className="atc-chip-btn"><Filter size={15} /> Filters</button>
            <button className="atc-chip-btn"><ArrowUpDown size={15} /> Sort</button>
          </div>
        </div>

        <div className="atc-table-scroll">
          <table className="atc-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Test Types</th>
                <th>App</th>
                <th>Module</th>
                <th>Priority</th>
                <th>Type</th>
                <th>Last Updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const priority = r.priority_id ? priorityById[r.priority_id] : null;
                return (
                  <tr key={r.testcase_id}>
                    <td className="cell-id">{r.testcase_key}</td>
                    <td className="cell-title">{r.title}</td>
                    <td>
                      {(r.test_types || []).map((t) => (
                        <span key={t} className="atc-tag blue" style={{ marginRight: 4 }}>{t}</span>
                      ))}
                    </td>
                    <td>{applicationById[r.application_id]?.application_name || '—'}</td>
                    <td>{moduleById[r.module_id]?.module_name || '—'}</td>
                    <td>
                      {priority ? (
                        <span className="atc-tag slate" style={priorityBadgeStyle(priority.color)}>
                          {priority.priority_name}
                        </span>
                      ) : '—'}
                    </td>
                    <td>
                      <span className={`atc-tag ${r.polarity === 'Positive' ? 'green' : 'red'}`}>
                        {r.polarity || '—'}
                      </span>
                    </td>
                    <td>{r.updated_at ? new Date(r.updated_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}</td>
                    <td>
                      <div className="atc-row-actions">
                        <button className="atc-icon-btn view" title="View"><Eye size={15} /></button>
                        <button className="atc-icon-btn edit" title="Edit"><Pencil size={15} /></button>
                        <button className="atc-icon-btn del" title="Delete"><Trash2 size={15} /></button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="atc-table-foot">
          <span>Showing 1 to {rows.length} of {total} results</span>
          <div className="atc-pagination">
            <button className="atc-page-btn" disabled><ChevronLeft size={15} /></button>
            <button className="atc-page-btn active">1</button>
            <button className="atc-page-btn" disabled><ChevronRight size={15} /></button>
          </div>
        </div>
      </div>
    </div>
  );
}
