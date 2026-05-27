// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";

export interface AccountingTransaction {
  transaction_id?: string;
  date?: string;
  document_type?: string;
  counterparty?: string;
  description?: string;
  amount?: number;
  currency?: string;
  tax_amount?: number;
  source_pages?: number[];
  confidence?: number;
  notes?: string;
}

export interface JournalLine {
  account_code?: string;
  account_name?: string;
  debit?: number;
  credit?: number;
}

export interface JournalEntry {
  entry_id?: string;
  date?: string;
  memo?: string;
  source_transaction_id?: string;
  lines?: JournalLine[];
}

export interface TrialBalanceRow {
  account_code?: string;
  account_name?: string;
  debit?: number;
  credit?: number;
  net_debit?: number;
  net_credit?: number;
}

export interface AccountingReport {
  transactions?: AccountingTransaction[];
  journal_entries?: JournalEntry[];
  trial_balance?: TrialBalanceRow[];
  financial_statements?: {
    income_statement?: Record<string, number>;
    balance_sheet?: Record<string, number | string>;
    basis?: string;
  };
}

export type ReviewIssue = AccountingReport;

export interface ActivityEntry {
  timestamp: string;
  icon: string;
  label: string;
  detail?: string;
  status: "running" | "done";
  output?: string;
}

export interface PreviewDoc {
  name: string;
  url: string;
  kind: "content" | "reference";
}

interface ReviewResultsPanelProps {
  issues: AccountingReport | null;
  isLoading: boolean;
  activityLog?: ActivityEntry[];
  phaseStarted?: number[];
  phaseDone?: number[];
  startedAt?: number | null;
  documentUrl?: string | null;
  previewDocs?: PreviewDoc[];
  onNewReview: () => void;
}

const PHASES: { icon: string; text: string }[] = [
  { icon: "📄", text: "Reading financial documents" },
  { icon: "✂️", text: "Preparing document batches" },
  { icon: "🧾", text: "Extracting transactions" },
  { icon: "📚", text: "Posting journal entries" },
  { icon: "📊", text: "Building TB and statements" },
];

function money(value: unknown): string {
  const n = Number(value || 0);
  return n.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatElapsed(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

function ElapsedTimer({ startedAt }: { startedAt: number }) {
  const [now, setNow] = useState<number>(() => Date.now());
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);
  return (
    <span className="tabular-nums font-mono text-indigo-600 font-bold">
      {formatElapsed(now - startedAt)}
    </span>
  );
}

function DocumentPreviewHeader({
  tabs,
  activeIdx,
  onSelect,
}: {
  tabs: PreviewDoc[];
  activeIdx: number;
  onSelect: (idx: number) => void;
}) {
  if (tabs.length === 0) {
    return (
      <div className="bg-slate-50 px-6 py-4 border-b border-gray-200 shrink-0">
        <h3 className="text-lg font-semibold text-gray-900">
          Source Document
        </h3>
      </div>
    );
  }
  return (
    <div className="bg-slate-50 border-b border-gray-200 shrink-0">
      <div className="flex items-end gap-1 px-3 pt-3 overflow-x-auto">
        {tabs.map((tab, idx) => {
          const isActive = idx === activeIdx;
          return (
            <button
              key={idx}
              type="button"
              onClick={() => onSelect(idx)}
              className={`max-w-[18rem] shrink-0 px-3 py-2 rounded-t-lg text-xs font-medium flex items-center gap-1.5 border-t border-x transition-colors ${
                isActive
                  ? "bg-white text-gray-900 border-gray-200 shadow-sm"
                  : "bg-transparent text-gray-600 hover:text-gray-900 hover:bg-white/60 border-transparent"
              }`}
              title={tab.name}
            >
              <span>{tab.kind === "content" ? "📄" : "📎"}</span>
              <span className="truncate">{tab.name}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function ProgressPanel({
  activityLog,
  phaseStarted,
  phaseDone,
  startedAt,
}: {
  activityLog: ActivityEntry[];
  phaseStarted: number[];
  phaseDone: number[];
  startedAt: number | null;
}) {
  const activityScrollRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const el = activityScrollRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    if (nearBottom) el.scrollTop = el.scrollHeight;
  }, [activityLog]);

  return (
    <div className="bg-white rounded-lg shadow-2xl border border-gray-200 overflow-hidden flex flex-col h-[800px] lg:h-full">
      <div className="bg-slate-50 px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Accounting Intake in Progress
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Sequential accrual workflow running
          </p>
        </div>
        {startedAt !== null && (
          <div className="text-right">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Elapsed
            </p>
            <p className="text-2xl">
              <ElapsedTimer startedAt={startedAt} />
            </p>
          </div>
        )}
      </div>
      <div className="p-6 flex-1 flex flex-col gap-6 overflow-hidden">
        <div className="space-y-2">
          {PHASES.map((step, idx) => {
            const started = phaseStarted[idx] ?? 0;
            const done = phaseDone[idx] ?? 0;
            const isDone = started > 0 && started === done;
            const isActive = started > done;
            return (
              <div
                key={idx}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 border ${
                  isActive
                    ? "bg-indigo-50 border-indigo-300"
                    : isDone
                      ? "bg-green-50 border-green-200"
                      : "bg-gray-50 border-gray-200 opacity-70"
                }`}
              >
                <span className="text-xl">{step.icon}</span>
                <span className="flex-1 text-sm font-medium text-gray-800">
                  {step.text}
                </span>
                {isActive && (
                  <span className="w-3 h-3 rounded-full border-2 border-indigo-600 border-t-transparent animate-spin" />
                )}
                {isDone && <span className="text-green-700 text-sm">Done</span>}
              </div>
            );
          })}
        </div>

        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Ledger Activity
            </p>
            <p className="text-xs text-gray-400">{activityLog.length} events</p>
          </div>
          <div
            ref={activityScrollRef}
            className="flex-1 overflow-auto space-y-1.5 bg-gray-50 rounded-lg px-3 pt-3 pb-4 border border-gray-200 min-h-[200px]"
          >
            {activityLog.length === 0 ? (
              <p className="text-xs text-gray-400 italic text-center py-6">
                Waiting for first ledger event
              </p>
            ) : (
              activityLog.map((entry, idx) => (
                <div key={idx} className="text-xs rounded px-2 py-1.5 bg-white border border-gray-200">
                  <div className="flex items-start gap-2">
                    <span className="font-mono text-gray-400 tabular-nums">
                      {entry.timestamp}
                    </span>
                    <span className="text-base leading-none">{entry.icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-800 font-semibold">{entry.label}</p>
                      {entry.detail && (
                        <p className="text-gray-500 font-mono truncate">
                          {entry.detail}
                        </p>
                      )}
                    </div>
                    <span className={entry.status === "running" ? "text-indigo-600" : "text-green-700"}>
                      {entry.status === "running" ? "Running" : "Done"}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden">
      <div className="bg-slate-50 px-5 py-3 border-b border-gray-200">
        <h3 className="text-base font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="p-4 overflow-auto">{children}</div>
    </div>
  );
}

export function ReviewResultsPanel({
  issues,
  isLoading,
  activityLog = [],
  phaseStarted = [0, 0, 0, 0, 0],
  phaseDone = [0, 0, 0, 0, 0],
  startedAt = null,
  documentUrl,
  previewDocs,
  onNewReview,
}: ReviewResultsPanelProps) {
  const [activePreviewIdx, setActivePreviewIdx] = useState<number>(0);
  const previewTabs: PreviewDoc[] = useMemo(() => {
    if (previewDocs && previewDocs.length > 0) return previewDocs;
    if (documentUrl)
      return [{ name: "Financial document", url: documentUrl, kind: "content" as const }];
    return [];
  }, [previewDocs, documentUrl]);

  const activeDocUrl = previewTabs[activePreviewIdx]?.url ?? null;
  const report = issues || {};
  const transactions = report.transactions || [];
  const journalEntries = report.journal_entries || [];
  const trialBalance = report.trial_balance || [];
  const financialStatements = report.financial_statements || {};

  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "accounting_intake_results.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="h-full overflow-auto bg-slate-800">
        <div className="container mx-auto px-6 py-8 max-w-7xl">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:h-[800px]">
            <div className="bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden flex flex-col h-[800px] lg:h-full">
              <DocumentPreviewHeader
                tabs={previewTabs}
                activeIdx={activePreviewIdx}
                onSelect={setActivePreviewIdx}
              />
              <div className="flex-1 overflow-hidden">
                {activeDocUrl ? (
                  <iframe src={activeDocUrl} className="w-full h-full" title="Source Document" />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <p className="text-gray-400">No document loaded</p>
                  </div>
                )}
              </div>
            </div>
            <ProgressPanel
              activityLog={activityLog}
              phaseStarted={phaseStarted}
              phaseDone={phaseDone}
              startedAt={startedAt}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto bg-slate-800">
      <div className="container mx-auto px-6 py-8 max-w-7xl space-y-6">
        <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-6">
          <div className="flex justify-between items-center gap-4 flex-wrap">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                Accounting Intake Complete
              </h2>
              <p className="text-gray-600 mt-1">
                {transactions.length} transactions, {journalEntries.length} journal entries, {trialBalance.length} trial balance rows
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleDownload}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
              >
                Download JSON
              </button>
              <button
                onClick={onNewReview}
                className="bg-gray-600 hover:bg-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
              >
                New Intake
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden">
            <DocumentPreviewHeader
              tabs={previewTabs}
              activeIdx={activePreviewIdx}
              onSelect={setActivePreviewIdx}
            />
            <div className="h-[760px] overflow-hidden">
              {activeDocUrl ? (
                <iframe src={activeDocUrl} className="w-full h-full" title="Source Document" />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <p className="text-gray-400">No document loaded</p>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <Section title="Transactions">
              <div className="space-y-3 max-h-72 overflow-auto">
                {transactions.map((tx, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex justify-between gap-3">
                      <p className="font-semibold text-gray-900">
                        {tx.counterparty || tx.description || "Transaction"}
                      </p>
                      <p className="font-mono font-bold">{money(tx.amount)}</p>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {tx.date || "No date"} · {tx.document_type || "document"} · {tx.currency || "CAD"}
                    </p>
                    <p className="text-sm text-gray-700 mt-2">{tx.description}</p>
                  </div>
                ))}
                {transactions.length === 0 && (
                  <p className="text-sm text-gray-500">No transactions extracted.</p>
                )}
              </div>
            </Section>

            <Section title="Journal Entries">
              <div className="space-y-3 max-h-80 overflow-auto">
                {journalEntries.map((entry, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-3">
                    <p className="font-semibold text-gray-900">
                      {entry.entry_id || `JE-${idx + 1}`} · {entry.memo || "Journal entry"}
                    </p>
                    <table className="w-full mt-2 text-xs">
                      <thead className="text-gray-500">
                        <tr>
                          <th className="text-left py-1">Account</th>
                          <th className="text-right py-1">Debit</th>
                          <th className="text-right py-1">Credit</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(entry.lines || []).map((line, lineIdx) => (
                          <tr key={lineIdx} className="border-t border-gray-100">
                            <td className="py-1">{line.account_code} {line.account_name}</td>
                            <td className="py-1 text-right font-mono">{money(line.debit)}</td>
                            <td className="py-1 text-right font-mono">{money(line.credit)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ))}
                {journalEntries.length === 0 && (
                  <p className="text-sm text-gray-500">No journal entries created.</p>
                )}
              </div>
            </Section>

            <Section title="Trial Balance">
              <table className="w-full text-xs">
                <thead className="text-gray-500">
                  <tr>
                    <th className="text-left py-1">Account</th>
                    <th className="text-right py-1">Debit</th>
                    <th className="text-right py-1">Credit</th>
                  </tr>
                </thead>
                <tbody>
                  {trialBalance.map((row, idx) => (
                    <tr key={idx} className="border-t border-gray-100">
                      <td className="py-1">{row.account_code} {row.account_name}</td>
                      <td className="py-1 text-right font-mono">{money(row.net_debit ?? row.debit)}</td>
                      <td className="py-1 text-right font-mono">{money(row.net_credit ?? row.credit)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>

            <Section title="Financial Statements">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Income Statement</h4>
                  {Object.entries(financialStatements.income_statement || {}).map(([key, value]) => (
                    <div key={key} className="flex justify-between border-t border-gray-100 py-1">
                      <span className="capitalize">{key.replace(/_/g, " ")}</span>
                      <span className="font-mono">{money(value)}</span>
                    </div>
                  ))}
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Balance Sheet</h4>
                  {Object.entries(financialStatements.balance_sheet || {}).map(([key, value]) => (
                    <div key={key} className="flex justify-between border-t border-gray-100 py-1">
                      <span className="capitalize">{key.replace(/_/g, " ")}</span>
                      <span className="font-mono">{typeof value === "number" ? money(value) : value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </Section>
          </div>
        </div>
      </div>
    </div>
  );
}
