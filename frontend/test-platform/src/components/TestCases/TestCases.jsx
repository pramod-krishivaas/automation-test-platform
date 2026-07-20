import React, { useEffect, useMemo, useState } from 'react';
import {
  Search, ListChecks, ChevronDown, AlertCircle, RotateCcw,
  ChevronLeft, ChevronRight,
} from 'lucide-react';
import testCaseService from '../../services/testCaseService';
import catalogService from '../../services/catalogService';
import './TestCases.css';

const TEST_TYPE_OPTIONS = ['Smoke', 'Regression', 'Functional', 'UI', 'Integration', 'Performance'];
const PAGE_SIZE = 10;

const EMPTY_FILTERS = {
  applicationId: '',
  moduleId: '',
  priorityId: '',
  testType: '',
  status: '',
  polarity: '',
  q: '',
};

const PRIORITY_TONE = { Critical: 'red', High: 'red', Medium: 'slate', Low: 'blue' };

function FilterSelect({ value, onChange, options, allLabel, disabled }) {
  return (
    <div className="tcv-select-wrap">
      <select className="tcv-select" value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled}>
        <option value="">{allLabel}</option>
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
      <ChevronDown size={14} />
    </div>
  );
}

function priorityBadgeStyle(color) {
  if (!color) return undefined;
  return { color, background: `${color}1A` };
}

export default function TestCases() {
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [applications, setApplications] = useState([]);
  const [allModules, setAllModules] = useState([]);
  const [priorities, setPriorities] = useState([]);

  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [searchDraft, setSearchDraft] = useState('');
  const [page, setPage] = useState(1);
  const [expandedIds, setExpandedIds] = useState(() => new Set());

  const toggleExpand = (id) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

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

  const moduleOptions = useMemo(() => {
    const list = filters.applicationId
      ? allModules.filter((m) => m.application_id === filters.applicationId)
      : allModules;
    return list.map((m) => ({ value: m.module_id, label: m.module_name }));
  }, [allModules, filters.applicationId]);

  useEffect(() => {
    (async () => {
      try {
        const [appsRes, modulesRes, prioritiesRes] = await Promise.all([
          catalogService.listApplications(),
          catalogService.listModules(),
          catalogService.listPriorities(),
        ]);
        setApplications(appsRes.items || []);
        setAllModules(modulesRes.items || []);
        setPriorities(prioritiesRes.items || []);
      } catch {
        setError('Failed to load reference data. Is the backend running on http://localhost:8000?');
      }
    })();
  }, []);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError('');
      try {
        const params = { page, page_size: PAGE_SIZE };
        if (filters.applicationId) params.application_id = filters.applicationId;
        if (filters.moduleId) params.module_id = filters.moduleId;
        if (filters.priorityId) params.priority_id = filters.priorityId;
        if (filters.testType) params.test_type = filters.testType;
        if (filters.status) params.status = filters.status === 'true';
        if (filters.polarity) params.polarity = filters.polarity;
        if (filters.q.trim()) params.q = filters.q.trim();

        const res = await testCaseService.listTestCases(params);
        setRows(res.items || []);
        setTotal(res.total || 0);
        setTotalPages(res.total_pages || 1);
      } catch {
        setError('Failed to load test cases. Is the backend running on http://localhost:8000?');
      } finally {
        setLoading(false);
      }
    })();
  }, [
    filters.applicationId, filters.moduleId, filters.priorityId,
    filters.testType, filters.status, filters.polarity, filters.q, page,
  ]);

  const updateFilter = (key) => (value) => {
    setFilters((f) => ({ ...f, [key]: value }));
    setPage(1);
  };

  const handleApplicationFilterChange = (value) => {
    setFilters((f) => ({ ...f, applicationId: value, moduleId: '' }));
    setPage(1);
  };

  const commitSearch = () => {
    setFilters((f) => ({ ...f, q: searchDraft }));
    setPage(1);
  };

  const handleResetFilters = () => {
    setFilters(EMPTY_FILTERS);
    setSearchDraft('');
    setPage(1);
  };

  const hasActiveFilters = useMemo(
    () => Object.values(filters).some((v) => v !== ''),
    [filters],
  );

  const rangeStart = rows.length ? (page - 1) * PAGE_SIZE + 1 : 0;
  const rangeEnd = (page - 1) * PAGE_SIZE + rows.length;

  return (
    <div className="tcv-page">
      <div className="tcv-heading">
        <div>
          <h1>Test Cases</h1>
          <p>Browse and filter every test case across applications and modules</p>
        </div>
        <span className="tcv-count-pill"><ListChecks size={14} /> {total} total</span>
      </div>

      {error && (
        <div className="tcv-error-banner">
          <AlertCircle size={15} />
          <span>{error}</span>
        </div>
      )}

      <div className="tcv-filter-card">
        <div className="tcv-filter-grid">
          <div className="tcv-filter-field span-2">
            <span className="tcv-filter-label">Search</span>
            <div className="tcv-search-wrap">
              <Search size={14} />
              <input
                className="tcv-input"
                placeholder="Search by title, key, or description..."
                value={searchDraft}
                onChange={(e) => setSearchDraft(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') commitSearch(); }}
                onBlur={commitSearch}
              />
            </div>
          </div>

          <div className="tcv-filter-field">
            <span className="tcv-filter-label">Application</span>
            <FilterSelect
              value={filters.applicationId}
              onChange={handleApplicationFilterChange}
              options={applications.map((a) => ({ value: a.application_id, label: a.application_name }))}
              allLabel="All Applications"
            />
          </div>

          <div className="tcv-filter-field">
            <span className="tcv-filter-label">Module</span>
            <FilterSelect
              value={filters.moduleId}
              onChange={updateFilter('moduleId')}
              options={moduleOptions}
              allLabel="All Modules"
            />
          </div>

          <div className="tcv-filter-field">
            <span className="tcv-filter-label">Priority</span>
            <FilterSelect
              value={filters.priorityId}
              onChange={updateFilter('priorityId')}
              options={priorities.map((p) => ({ value: p.priority_id, label: p.priority_name }))}
              allLabel="All Priorities"
            />
          </div>

          <div className="tcv-filter-field">
            <span className="tcv-filter-label">Test Type</span>
            <FilterSelect
              value={filters.testType}
              onChange={updateFilter('testType')}
              options={TEST_TYPE_OPTIONS.map((t) => ({ value: t, label: t }))}
              allLabel="All Test Types"
            />
          </div>

          <div className="tcv-filter-field">
            <span className="tcv-filter-label">Status</span>
            <FilterSelect
              value={filters.status}
              onChange={updateFilter('status')}
              options={[{ value: 'true', label: 'Active' }, { value: 'false', label: 'Inactive' }]}
              allLabel="All Statuses"
            />
          </div>

          <div className="tcv-filter-field">
            <span className="tcv-filter-label">Type</span>
            <FilterSelect
              value={filters.polarity}
              onChange={updateFilter('polarity')}
              options={[{ value: 'Positive', label: 'Positive' }, { value: 'Negative', label: 'Negative' }]}
              allLabel="All Types"
            />
          </div>
        </div>

        <div className="tcv-filter-actions">
          <button className="tcv-chip-btn" onClick={handleResetFilters} disabled={!hasActiveFilters && !searchDraft}>
            <RotateCcw size={14} /> Reset Filters
          </button>
        </div>
      </div>

      <div className="tcv-table-card">
        <div className="tcv-table-scroll">
          <table className="tcv-table">
            <thead>
              <tr>
                <th className="cell-expand"></th>
                <th>ID</th>
                <th>Title</th>
                <th>Test Types</th>
                <th>App</th>
                <th>Module</th>
                <th>Priority</th>
                <th>Type</th>
                <th>Status</th>
                <th>Last Updated</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const priority = r.priority_id ? priorityById[r.priority_id] : null;
                const isExpanded = expandedIds.has(r.testcase_id);
                return (
                  <React.Fragment key={r.testcase_id}>
                    <tr>
                      <td className="cell-expand">
                        <button
                          type="button"
                          className="tcv-expand-btn"
                          onClick={() => toggleExpand(r.testcase_id)}
                          aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
                          title={isExpanded ? 'Collapse details' : 'Expand details'}
                        >
                          {isExpanded ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
                        </button>
                      </td>
                      <td className="cell-id">{r.testcase_key}</td>
                      <td className="cell-title">{r.title}</td>
                      <td>
                        {(r.test_types || []).map((t) => (
                          <span key={t} className="tcv-tag blue">{t}</span>
                        ))}
                      </td>
                      <td>{applicationById[r.application_id]?.application_name || '—'}</td>
                      <td>{moduleById[r.module_id]?.module_name || '—'}</td>
                      <td>
                        {priority ? (
                          <span
                            className={`tcv-tag ${PRIORITY_TONE[priority.priority_name] || 'slate'}`}
                            style={priorityBadgeStyle(priority.color)}
                          >
                            {priority.priority_name}
                          </span>
                        ) : '—'}
                      </td>
                      <td>
                        <span className={`tcv-tag ${r.polarity === 'Positive' ? 'green' : 'red'}`}>
                          {r.polarity || '—'}
                        </span>
                      </td>
                      <td>
                        <span className={`tcv-tag ${r.status ? 'green' : 'slate'}`}>
                          {r.status ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="cell-muted">
                        {r.updated_at
                          ? new Date(r.updated_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
                          : '—'}
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr className="tcv-expand-row">
                        <td colSpan={10}>
                          <div className="tcv-expand-content">
                            <div className="tcv-expand-block">
                              <span className="tcv-expand-label">Description</span>
                              <p>{r.description || 'No description provided.'}</p>
                            </div>
                            <div className="tcv-expand-block">
                              <span className="tcv-expand-label">Expected Result</span>
                              <p>{r.expected_result || 'No expected result provided.'}</p>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>

          {!loading && rows.length === 0 && (
            <div className="tcv-table-empty">No test cases match these filters.</div>
          )}
          {loading && <div className="tcv-table-loading">Loading test cases...</div>}
        </div>

        <div className="tcv-table-foot">
          <span>{total === 0 ? 'No results' : `Showing ${rangeStart}–${rangeEnd} of ${total} results`}</span>
          <div className="tcv-pagination">
            <button className="tcv-page-btn" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>
              <ChevronLeft size={14} /> Prev
            </button>
            <span>Page {page} of {totalPages}</span>
            <button className="tcv-page-btn" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>
              Next <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
