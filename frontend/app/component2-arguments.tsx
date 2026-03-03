import {
  View,
  Text,
  Pressable,
  StyleSheet,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Layout } from '../components/Layout';
import { Container, Card, PageHeader } from '../components/ui';
import { useComp2 } from '../components/Comp2Context';
import { colors, spacing } from '../theme';
import React, { useState, useEffect } from 'react';
import {
  generateArgumentsOnly,
  saveComp2History,
  NormalizedAnalysisResponse,
} from '../api';

// ─── Perspective & Strategy configs ───────────────────────────────────
const PERSPECTIVE_CONFIG: Record<string, { label: string; color: string; bg: string; icon: string }> = {
  prosecution: { label: 'Prosecution', color: '#DC2626', bg: '#FEF2F2', icon: '⚖️' },
  defense: { label: 'Defense', color: '#2563EB', bg: '#EFF6FF', icon: '🛡️' },
  mitigating: { label: 'Mitigating', color: '#059669', bg: '#ECFDF5', icon: '🕊️' },
  aggressive: { label: 'Aggressive', color: '#D97706', bg: '#FFFBEB', icon: '🔥' },
};

const STRATEGY_CONFIG: Record<string, { label: string; color: string }> = {
  distinguish_precedent: { label: 'Distinguish Precedent', color: '#7C3AED' },
  challenge_evidence: { label: 'Challenge Evidence', color: '#DC2626' },
  procedural_challenge: { label: 'Procedural Challenge', color: '#D97706' },
  cite_precedent: { label: 'Cite Precedent', color: '#2563EB' },
};

// ─── Sub-components ──────────────────────────────────────────────────

function StrengthMeter({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = pct >= 75 ? '#059669' : pct >= 50 ? '#D97706' : '#DC2626';
  return (
    <View style={s.meterRow}>
      <Text style={s.meterLabel}>Strength</Text>
      <View style={s.meterTrack}>
        <View style={[s.meterFill, { width: `${pct}%` as any, backgroundColor: color }]} />
      </View>
      <Text style={[s.meterPct, { color }]}>{pct}%</Text>
    </View>
  );
}

function Badge({ text, color, bg }: { text: string; color: string; bg: string }) {
  return (
    <View style={[s.badge, { backgroundColor: bg, borderColor: color }]}>
      <Text style={[s.badgeText, { color }]}>{text}</Text>
    </View>
  );
}

function JudgeCitation({ judge, statement }: { judge: string; statement: string }) {
  return (
    <View style={s.citationBox}>
      <Text style={s.citationQuote}>"</Text>
      <Text style={s.citationText}>{statement}</Text>
      <Text style={s.citationJudge}>— {judge}</Text>
    </View>
  );
}

function ArgumentCard({ arg, adversarial }: { arg: any; adversarial?: any }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = PERSPECTIVE_CONFIG[arg.perspective] ?? { label: arg.perspective, color: '#6B7280', bg: '#F9FAFB', icon: '📋' };

  return (
    <View style={[s.argCard, { borderLeftColor: cfg.color }]}>
      <View style={s.argCardHeader}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, flex: 1 }}>
          <Text style={s.argCardIcon}>{cfg.icon}</Text>
          <Text style={s.argCardTitle}>{arg.title}</Text>
        </View>
        <Badge text={cfg.label} color={cfg.color} bg={cfg.bg} />
      </View>

      <StrengthMeter score={arg.strength_score ?? 0.8} />
      <Text style={s.argContent}>{arg.content}</Text>

      {arg.argument_points?.length > 0 && (
        <View style={s.section}>
          <Text style={s.sectionTitle}>Key Argument Points</Text>
          {arg.argument_points.map((pt: string, i: number) => (
            <View key={i} style={s.pointRow}>
              <View style={[s.pointDot, { backgroundColor: cfg.color }]} />
              <Text style={s.pointText}>{pt}</Text>
            </View>
          ))}
        </View>
      )}

      {arg.legal_principles?.length > 0 && (
        <View style={s.section}>
          <Text style={s.sectionTitle}>Legal Principles</Text>
          <View style={s.tagRow}>
            {arg.legal_principles.map((lp: string, i: number) => (
              <View key={i} style={s.legalTag}>
                <Text style={s.legalTagText}>{lp}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {arg.judge_names?.length > 0 && arg.judge_statements?.length > 0 && (
        <View style={s.section}>
          <Text style={s.sectionTitle}>Judge Statements</Text>
          {arg.judge_names.slice(0, 2).map((judge: string, i: number) => (
            arg.judge_statements[i] ? (
              <JudgeCitation key={i} judge={judge} statement={arg.judge_statements[i]} />
            ) : null
          ))}
        </View>
      )}

      {arg.supporting_cases?.length > 0 && (
        <View style={s.section}>
          <Text style={s.sectionTitle}>Supporting Precedents</Text>
          <View style={s.tagRow}>
            {arg.supporting_cases.map((c: string, i: number) => (
              <View key={i} style={s.caseTag}>
                <Text style={s.caseTagText}>{c.replace(/_/g, ' ').substring(0, 35)}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {adversarial?.counter_arguments?.length > 0 && (
        <>
          <Pressable
            style={[s.adversarialToggle, { borderColor: cfg.color }]}
            onPress={() => setExpanded(!expanded)}
          >
            <Text style={[s.adversarialToggleText, { color: cfg.color }]}>
              {expanded ? '▲ Hide' : '▼ Show'} Adversarial Simulation ({adversarial.counter_arguments.length} counter-arguments)
            </Text>
          </Pressable>

          {expanded && (
            <View style={s.adversarialPanel}>
              <Text style={s.adversarialPanelTitle}>Adversarial Simulation</Text>
              {adversarial.counter_arguments.map((ca: any, i: number) => {
                const strat = STRATEGY_CONFIG[ca.strategy] ?? { label: ca.strategy, color: '#6B7280' };
                return (
                  <View key={i} style={s.counterBlock}>
                    <View style={[s.strategyBadge, { backgroundColor: strat.color + '18', borderColor: strat.color }]}>
                      <Text style={[s.strategyBadgeText, { color: strat.color }]}>
                        Strategy: {strat.label}
                      </Text>
                      <Text style={[s.strategyStrength, { color: strat.color }]}>
                        Score: {Math.round((ca.strength_score ?? 0.6) * 100)}%
                      </Text>
                    </View>
                    <View style={s.counterBox}>
                      <Text style={s.counterLabel}>Counter-Argument</Text>
                      <Text style={s.counterText}>{ca.counter_content}</Text>
                    </View>
                    <View style={s.rebuttalBox}>
                      <Text style={s.rebuttalLabel}>Rebuttal</Text>
                      <Text style={s.rebuttalText}>{ca.rebuttal}</Text>
                    </View>
                    {ca.weak_points?.length > 0 && (
                      <View style={s.weakPointsBox}>
                        <Text style={s.weakPointsLabel}>Weak Points to Address</Text>
                        <View style={s.tagRow}>
                          {ca.weak_points.map((wp: string, wi: number) => (
                            <View key={wi} style={s.weakTag}>
                              <Text style={s.weakTagText}>{wp}</Text>
                            </View>
                          ))}
                        </View>
                      </View>
                    )}
                  </View>
                );
              })}
            </View>
          )}
        </>
      )}
    </View>
  );
}

function SimulationSummary({ summary, recs }: { summary?: any; recs?: string[] }) {
  if (!summary && !recs?.length) return null;
  return (
    <Card title="Simulation Summary" style={s.resultCard}>
      {summary && (
        <View style={s.summaryGrid}>
          <View style={s.summaryGridItem}>
            <Text style={s.summaryGridNum}>{summary.total_arguments_tested ?? 0}</Text>
            <Text style={s.summaryGridLabel}>Arguments Tested</Text>
          </View>
          <View style={s.summaryGridItem}>
            <Text style={s.summaryGridNum}>{summary.total_counter_arguments ?? 0}</Text>
            <Text style={s.summaryGridLabel}>Counter-Arguments</Text>
          </View>
          <View style={s.summaryGridItem}>
            <Text numberOfLines={2} style={[s.summaryGridNum, { fontSize: 11 }]}>
              {summary.most_common_counter_strategy?.replace(/_/g, ' ') ?? '—'}
            </Text>
            <Text style={s.summaryGridLabel}>Top Strategy</Text>
          </View>
        </View>
      )}
      {(recs ?? []).length > 0 && (
        <View style={{ marginTop: spacing.md }}>
          <Text style={s.sectionTitle}>Strategic Recommendations</Text>
          {(recs ?? []).map((r: string, i: number) => (
            <View key={i} style={s.recRow}>
              <Text style={s.recBullet}>→</Text>
              <Text style={s.recText}>{r}</Text>
            </View>
          ))}
        </View>
      )}
    </Card>
  );
}

// ─── Main Screen ─────────────────────────────────────────────────────

export default function ArgumentsScreen() {
  const router = useRouter();
  const { file, textInput, argumentsResult, setArgumentsResult } = useComp2();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'arguments' | 'adversarial'>('arguments');

  useEffect(() => {
    if (argumentsResult) return;
    if (!file && !textInput) {
      setError('No document selected. Go back and upload a file first.');
      return;
    }
    runGeneration();
  }, []);

  const runGeneration = async () => {
    setLoading(true);
    setError(null);
    try {
      if (file) {
        const result = await generateArgumentsOnly(file.uri, file.name);
        setArgumentsResult(result);
        autoSave(result);
      } else {
        setError('Text-based argument generation requires a document file. Please upload a document on the previous page.');
      }
    } catch (err: any) {
      console.error('Argument generation failed:', err);
      setError(err?.message || 'Argument generation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const autoSave = async (data: NormalizedAnalysisResponse) => {
    if (!data.arguments_report) return;
    try {
      const report = data.arguments_report;
      const cf = data.analyzed_case?.analyzed_case_file;
      await saveComp2History({
        case_id: `C2_${report.case_id || Date.now()}`,
        case_name: cf?.case_header?.subject || report.case_id || 'Untitled Analysis',
        payload: report,
        subject: cf?.case_header?.subject || 'N/A',
        accused: cf?.parties_and_roles?.accused || 'N/A',
      });
    } catch (err) {
      console.error('Auto-save comp2 failed:', err);
    }
  };

  const report = argumentsResult?.arguments_report;
  const args: any[] = report?.arguments ?? [];
  const adversarialEnhanced: any[] = report?.adversarial_results?.enhanced_arguments ?? [];
  const simSummary = report?.adversarial_results?.simulation_summary;
  const stratRecs: string[] = report?.adversarial_results?.strategic_recommendations ?? [];
  const similarCases: any[] = report?.similar_cases ?? [];

  const getAdversarialForArg = (arg: any) =>
    adversarialEnhanced.find((a: any) => a.original?.title === arg.title);

  // ─── Report Generation ─────────────────────────────────────────────
  const generateReport = () => {
    if (!report) return;
    const cf = argumentsResult?.analyzed_case?.analyzed_case_file;
    const caseId = report.case_id ?? 'N/A';
    const now = new Date().toLocaleString('en-US', { dateStyle: 'long', timeStyle: 'short' });

    const perspColors: Record<string, string> = {
      prosecution: '#DC2626', defense: '#2563EB', mitigating: '#059669', aggressive: '#D97706',
    };
    const perspIcons: Record<string, string> = {
      prosecution: '⚖️', defense: '🛡️', mitigating: '🕊️', aggressive: '🔥',
    };
    const stratColors: Record<string, string> = {
      distinguish_precedent: '#7C3AED', challenge_evidence: '#DC2626',
      procedural_challenge: '#D97706', cite_precedent: '#2563EB',
    };

    const safe = (v: any) => v ?? '—';
    const list = (items: string[] | undefined, color = '#374151') =>
      (items ?? []).map(i => `<li style="color:${color};margin-bottom:4px">${i}</li>`).join('');

    const argSections = args.map(arg => {
      const pColor = perspColors[arg.perspective] ?? '#6B7280';
      const pIcon = perspIcons[arg.perspective] ?? '📋';
      const adversarial = adversarialEnhanced.find((a: any) => a.original?.title === arg.title);
      const counterHtml = (adversarial?.counter_arguments ?? []).map((ca: any) => {
        const sColor = stratColors[ca.strategy] ?? '#6B7280';
        const stratLabel = (ca.strategy ?? '').replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase());
        return `
          <div style="border:1px solid #E5E7EB;border-radius:8px;padding:14px;margin-bottom:12px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
              <span style="background:${sColor}18;color:${sColor};border:1px solid ${sColor};border-radius:6px;padding:3px 10px;font-size:11px;font-weight:700;text-transform:uppercase">${stratLabel}</span>
              <span style="font-size:11px;color:#6B7280">Score: ${Math.round((ca.strength_score ?? 0.6) * 100)}%</span>
            </div>
            <div style="background:#FEF2F2;border-left:3px solid #DC2626;border-radius:6px;padding:10px;margin-bottom:8px">
              <div style="font-size:10px;font-weight:700;color:#DC2626;text-transform:uppercase;margin-bottom:4px">Counter-Argument</div>
              <p style="color:#7F1D1D;font-size:13px;line-height:1.6;margin:0">${safe(ca.counter_content)}</p>
            </div>
            <div style="background:#ECFDF5;border-left:3px solid #059669;border-radius:6px;padding:10px;margin-bottom:8px">
              <div style="font-size:10px;font-weight:700;color:#059669;text-transform:uppercase;margin-bottom:4px">Rebuttal</div>
              <p style="color:#064E3B;font-size:13px;line-height:1.6;margin:0">${safe(ca.rebuttal)}</p>
            </div>
            ${(ca.weak_points ?? []).length > 0 ? `<div style="margin-top:6px"><span style="font-size:10px;font-weight:700;color:#D97706;text-transform:uppercase">Weak Points: </span>${(ca.weak_points ?? []).map((w: string) => `<span style="background:#FEF3C7;border:1px solid #FCD34D;border-radius:4px;padding:2px 7px;font-size:11px;color:#92400E;margin-right:4px">${w}</span>`).join('')}</div>` : ''}
          </div>`;
      }).join('');

      return `
        <div style="border:1px solid #E5E7EB;border-radius:12px;padding:24px;margin-bottom:24px;border-left:5px solid ${pColor}">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <h3 style="margin:0;font-size:18px;color:#1E293B">${pIcon} ${safe(arg.title)}</h3>
            <span style="background:${pColor}18;color:${pColor};border:1px solid ${pColor};border-radius:20px;padding:4px 14px;font-size:12px;font-weight:700">${(arg.perspective ?? '').toUpperCase()}</span>
          </div>
          <div style="background:#F8FAFC;border-radius:8px;padding:4px 10px;margin-bottom:12px;display:flex;align-items:center;gap:10px">
            <span style="font-size:12px;color:#6B7280;font-weight:600">Strength:</span>
            <div style="flex:1;background:#E5E7EB;border-radius:4px;height:8px"><div style="background:${pColor};width:${Math.round((arg.strength_score ?? 0.8) * 100)}%;height:8px;border-radius:4px"></div></div>
            <span style="font-size:13px;font-weight:700;color:${pColor}">${Math.round((arg.strength_score ?? 0.8) * 100)}%</span>
          </div>
          <p style="color:#475569;line-height:1.7;font-size:14px;margin-bottom:16px">${safe(arg.content)}</p>
          ${(arg.argument_points ?? []).length > 0 ? `
          <div style="margin-bottom:14px">
            <div style="font-size:11px;font-weight:700;color:#1E293B;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px">Key Argument Points</div>
            <ul style="padding-left:18px;margin:0">${list(arg.argument_points, '#374151')}</ul>
          </div>` : ''}
          ${(arg.legal_principles ?? []).length > 0 ? `
          <div style="margin-bottom:14px">
            <div style="font-size:11px;font-weight:700;color:#1E293B;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px">Legal Principles</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px">${(arg.legal_principles ?? []).map((lp: string) => `<span style="background:#EDE9FE;color:#5B21B6;border-radius:6px;padding:3px 8px;font-size:11px;font-weight:600">${lp}</span>`).join('')}</div>
          </div>` : ''}
          ${(arg.judge_names ?? []).length > 0 ? `
          <div style="margin-bottom:14px">
            <div style="font-size:11px;font-weight:700;color:#1E293B;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px">Judge Statements</div>
            ${(arg.judge_names ?? []).slice(0, 2).map((judge: string, i: number) => `
              <blockquote style="border-left:3px solid #CBD5E1;margin:0 0 10px 0;padding:10px 14px;background:#F8FAFC;border-radius:6px">
                <p style="font-style:italic;color:#475569;margin:0 0 6px 0;font-size:13px;line-height:1.6">&ldquo;${safe((arg.judge_statements ?? [])[i])}&rdquo;</p>
                <cite style="font-size:12px;font-weight:700;color:#334155">— ${judge}</cite>
              </blockquote>`).join('')}
          </div>` : ''}
          ${(arg.supporting_cases ?? []).length > 0 ? `
          <div style="margin-bottom:14px">
            <div style="font-size:11px;font-weight:700;color:#1E293B;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px">Supporting Precedents</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px">${(arg.supporting_cases ?? []).map((c: string) => `<span style="background:#E0F2FE;color:#0369A1;border-radius:6px;padding:3px 8px;font-size:11px;font-weight:600">${c.replace(/_/g, ' ')}</span>`).join('')}</div>
          </div>` : ''}
          ${counterHtml ? `
          <div style="margin-top:16px;padding-top:16px;border-top:1px dashed #E5E7EB">
            <div style="font-size:13px;font-weight:700;color:#1E293B;margin-bottom:12px">Adversarial Analysis</div>
            ${counterHtml}
          </div>` : ''}
        </div>`;
    }).join('');

    const simHtml = simSummary ? `
      <div style="display:flex;gap:16px;margin-bottom:20px">
        <div style="flex:1;background:#F8FAFC;border-radius:10px;padding:16px;text-align:center">
          <div style="font-size:28px;font-weight:800;color:#1E293B">${simSummary.total_arguments_tested ?? 0}</div>
          <div style="font-size:12px;color:#6B7280;font-weight:500">Arguments Tested</div>
        </div>
        <div style="flex:1;background:#F8FAFC;border-radius:10px;padding:16px;text-align:center">
          <div style="font-size:28px;font-weight:800;color:#1E293B">${simSummary.total_counter_arguments ?? 0}</div>
          <div style="font-size:12px;color:#6B7280;font-weight:500">Counter-Arguments</div>
        </div>
        <div style="flex:1;background:#F8FAFC;border-radius:10px;padding:16px;text-align:center">
          <div style="font-size:15px;font-weight:800;color:#1E293B">${(simSummary.most_common_counter_strategy ?? '—').replace(/_/g, ' ')}</div>
          <div style="font-size:12px;color:#6B7280;font-weight:500">Top Strategy</div>
        </div>
      </div>` : '';

    const recsHtml = (stratRecs ?? []).length > 0 ? `
      <div style="margin-top:12px">
        <div style="font-size:13px;font-weight:700;color:#1E293B;margin-bottom:10px">Strategic Recommendations</div>
        <ul style="padding-left:18px;margin:0">${list(stratRecs, '#374151')}</ul>
      </div>` : '';

    const casesHtml = similarCases.length > 0 ? `
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead>
          <tr style="background:#F1F5F9">
            <th style="padding:10px 12px;text-align:left;font-weight:700;color:#1E293B;border-bottom:2px solid #E2E8F0">#</th>
            <th style="padding:10px 12px;text-align:left;font-weight:700;color:#1E293B;border-bottom:2px solid #E2E8F0">Case ID</th>
            <th style="padding:10px 12px;text-align:center;font-weight:700;color:#1E293B;border-bottom:2px solid #E2E8F0">Year</th>
            <th style="padding:10px 12px;text-align:center;font-weight:700;color:#1E293B;border-bottom:2px solid #E2E8F0">Similarity</th>
          </tr>
        </thead>
        <tbody>
          ${similarCases.map((c, i) => `
            <tr style="border-bottom:1px solid #F1F5F9">
              <td style="padding:10px 12px;color:#6B7280;font-weight:700">${i + 1}</td>
              <td style="padding:10px 12px;color:#1E293B;font-weight:600">${(c.case_id ?? '').replace(/_/g, ' ')}</td>
              <td style="padding:10px 12px;color:#6B7280;text-align:center">${safe(c.year)}</td>
              <td style="padding:10px 12px;text-align:center">
                <span style="background:#DBEAFE;color:#1D4ED8;border-radius:12px;padding:2px 8px;font-weight:700;font-size:12px">${Math.round((1 - (c.distance ?? 0)) * 100)}%</span>
              </td>
            </tr>`).join('')}
        </tbody>
      </table>` : '<p style="color:#6B7280;font-style:italic">No similar cases found.</p>';

    const caseSummaryHtml = cf ? `
      <section style="margin-bottom:32px">
        <h2 style="font-size:16px;font-weight:700;color:#7C3AED;border-bottom:2px solid #EDE9FE;padding-bottom:8px;margin-bottom:16px">Case Summary</h2>
        <table style="width:100%;font-size:14px">
          <tr><td style="padding:6px 0;font-weight:600;color:#6B7280;width:140px">Subject</td><td style="color:#1E293B">${safe(cf.case_header?.subject)}</td></tr>
          <tr><td style="padding:6px 0;font-weight:600;color:#6B7280">Accused</td><td style="color:#1E293B">${safe(cf.parties_and_roles?.accused)}</td></tr>
          <tr><td style="padding:6px 0;font-weight:600;color:#6B7280">Complainant</td><td style="color:#1E293B">${safe(cf.parties_and_roles?.complainant)}</td></tr>
          <tr><td style="padding:6px 0;font-weight:600;color:#6B7280;vertical-align:top">Incident</td><td style="color:#1E293B;line-height:1.6">${safe(cf.incident_timeline?.what_happened)}</td></tr>
          <tr><td style="padding:6px 0;font-weight:600;color:#6B7280">Location</td><td style="color:#1E293B">${safe(cf.incident_timeline?.where_it_happened)}</td></tr>
          ${cf.final_judicial_opinion ? `<tr><td style="padding:6px 0;font-weight:600;color:#6B7280;vertical-align:top">Judicial Opinion</td><td style="color:#1E293B;line-height:1.6">${cf.final_judicial_opinion}</td></tr>` : ''}
        </table>
      </section>` : '';

    const filename = `Legal_Report_${caseId.replace(/[^a-z0-9]/gi, '_').replace(/_+/g, '_')}`;
    const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${filename}</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
  <style>
    * { box-sizing: border-box; }
    body { font-family: 'Georgia', serif; margin: 0; padding: 0; color: #1E293B; background: #fff; }
    @media print {
      body { font-size: 12pt; }
      .no-print { display: none !important; }
      section { page-break-inside: avoid; }
    }
    .cover { background: linear-gradient(135deg,#1E1B4B 0%,#4338CA 60%,#7C3AED 100%); color:#fff; padding: 60px 40px; min-height: 200px; }
    .cover h1 { font-size: 24px; font-weight: 900; margin: 0 0 8px; letter-spacing: -0.5px; }
    .cover p { margin: 0; opacity: 0.75; font-size: 13px; }
    .cover .meta { margin-top: 20px; display: flex; gap: 24px; flex-wrap: wrap; }
    .cover .meta-label { font-size: 9px; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.6; margin-bottom: 2px; font-family: sans-serif; }
    .cover .meta-value { font-size: 14px; font-weight: 700; font-family: sans-serif; }
    .body { padding: 30px 40px; max-width: 900px; margin: 0 auto; }
    h2 { font-size: 15px; }
    .btn-row { display: flex; gap: 12px; margin-bottom: 20px; background: #F8FAFC; padding: 12px 20px; border-bottom: 1px solid #E2E8F0; position: sticky; top: 0; z-index: 100; }
    .btn { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; font-size: 12px; font-weight: 700; font-family: sans-serif; display: flex; align-items: center; gap: 6px; }
    .btn-primary { background: #4338CA; color: #fff; }
    .btn-secondary { background: #fff; color: #1E293B; border: 1px solid #E2E8F0; }
    .disclaimer { background: #FFFBEB; border: 1px solid #FCD34D; border-radius: 8px; padding: 12px 16px; margin-bottom: 24px; font-family: sans-serif; }
    .disclaimer p { margin: 0; font-size: 11px; color: #92400E; line-height: 1.5; }
    #download-status { position: fixed; bottom: 20px; right: 20px; background: #1E293B; color: #fff; padding: 10px 20px; border-radius: 30px; font-family: sans-serif; font-size: 12px; display: none; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
  </style>
</head>
<body>
  <div class="btn-row no-print">
    <button class="btn btn-primary" onclick="downloadPDF()">Download PDF</button>
    <button class="btn btn-secondary" onclick="window.print()">Print View</button>
    <button class="btn btn-secondary" onclick="window.close()">Close</button>
  </div>

  <div id="report-content">
    <div class="cover">
      <h1>Legal Argument Analysis Report</h1>
      <p>Smart Criminal Judgement Analysis System — Argument Synthesis Engine</p>
      <div class="meta">
        <div class="meta-item"><div class="meta-label">Case Reference</div><div class="meta-value">${caseId}</div></div>
        <div class="meta-item"><div class="meta-label">Generated</div><div class="meta-value">${now}</div></div>
        <div class="meta-item"><div class="meta-label">Arguments</div><div class="meta-value">${args.length} Perspectives</div></div>
        <div class="meta-item"><div class="meta-label">Similar Precedents</div><div class="meta-value">${similarCases.length} Cases</div></div>
      </div>
    </div>
    <div class="body">
      <div class="disclaimer">
        <p><strong>Disclaimer:</strong> This report is generated by an AI-assisted legal analysis system for reference purposes only. It does not constitute legal advice. Qualitative verification by a legal professional is required.</p>
      </div>
      ${caseSummaryHtml}
      <section style="margin-bottom:32px">
        <h2 style="font-size:16px;font-weight:700;color:#7C3AED;border-bottom:2px solid #EDE9FE;padding-bottom:8px;margin-bottom:20px">Argument Analysis by Perspective</h2>
        ${argSections}
      </section>
      <section style="margin-bottom:32px">
        <h2 style="font-size:16px;font-weight:700;color:#7C3AED;border-bottom:2px solid #EDE9FE;padding-bottom:8px;margin-bottom:16px">Adversarial Simulation Summary</h2>
        ${simHtml}
        ${recsHtml}
      </section>
      <section style="margin-bottom:32px">
        <h2 style="font-size:16px;font-weight:700;color:#7C3AED;border-bottom:2px solid #EDE9FE;padding-bottom:8px;margin-bottom:16px">Similar Precedent Cases</h2>
        ${casesHtml}
      </section>
      <footer style="margin-top:40px;padding-top:20px;border-top:1px solid #E2E8F0;font-size:11px;color:#94A3B8;font-family:sans-serif;text-align:center">
        Generated by Smart Criminal Judgement Analysis System • ${now}
      </footer>
    </div>
  </div>

  <div id="download-status">Generating PDF...</div>

  <script>
    function downloadPDF() {
      const element = document.getElementById('report-content');
      const status = document.getElementById('download-status');
      status.style.display = 'block';
      
      const opt = {
        margin: [0.5, 0.5],
        filename: '${filename}.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, letterRendering: true },
        jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
      };

      html2pdf().set(opt).from(element).save().then(() => {
        status.innerText = 'Download Complete';
        setTimeout(() => { status.style.display = 'none'; }, 3000);
      }).catch(err => {
        console.error(err);
        status.innerText = 'Download Failed';
        status.style.background = '#DC2626';
      });
    }
  </script>
</body>
</html>`;

    const w = window.open('', '_blank');
    if (w) {
      w.document.write(html);
      w.document.close();
    }
  };

  return (
    <Layout>
      <Container>
        <PageHeader
          title="Strategic Arguments"
          breadcrumb="Argument Synthesis Engine → Generate Arguments"
        />

        <Pressable onPress={() => router.back()} style={s.backRow}>
          <Text style={s.backLink}>← Back to Hub</Text>
        </Pressable>

        {loading && (
          <View style={s.center}>
            <ActivityIndicator size="large" color={colors.accent} />
            <Text style={s.loadingText}>Generating strategic arguments...</Text>
            <Text style={s.loadingHint}>Finding similar cases, building perspectives, running adversarial simulation...</Text>
          </View>
        )}

        {error && !loading && (
          <Card title="Error" style={{ marginVertical: spacing.lg }}>
            <Text style={s.errorText}>{error}</Text>
            <Pressable onPress={() => router.back()} style={s.retryBtn}>
              <Text style={s.retryText}>← Go Back</Text>
            </Pressable>
          </Card>
        )}

        {!loading && !error && report && (
          <View style={s.row}>
            <View style={s.mainCol}>
              {/* Report Generate Button */}
              {args.length > 0 && (
                <Pressable style={s.reportBtn} onPress={generateReport}>
                  <Text style={s.reportBtnIcon}>📄</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={s.reportBtnTitle}>Generate Lawyer's Reference Report</Text>
                    <Text style={s.reportBtnSub}>Opens a print-ready HTML report with all arguments, counter-arguments & precedents</Text>
                  </View>
                  <Text style={s.reportBtnArrow}>→</Text>
                </Pressable>
              )}

              {/* Tabs */}
              {args.length > 0 && (
                <>
                  <View style={s.tabs}>
                    {(['arguments', 'adversarial'] as const).map(tab => (
                      <Pressable
                        key={tab}
                        style={[s.tab, activeTab === tab && s.tabActive]}
                        onPress={() => setActiveTab(tab)}
                      >
                        <Text style={[s.tabText, activeTab === tab && s.tabTextActive]}>
                          {tab === 'arguments' ? `Synthesized Arguments (${args.length})` :
                            `Adversarial Simulation (${adversarialEnhanced.length})`}
                        </Text>
                      </Pressable>
                    ))}
                  </View>

                  {activeTab === 'arguments' && (
                    <View>
                      {args.map((arg, i) => (
                        <ArgumentCard key={i} arg={arg} adversarial={getAdversarialForArg(arg)} />
                      ))}
                    </View>
                  )}

                  {activeTab === 'adversarial' && (
                    <View>
                      <SimulationSummary summary={simSummary} recs={stratRecs} />
                      {adversarialEnhanced.map((ae: any, i: number) => (
                        <ArgumentCard
                          key={i}
                          arg={{
                            ...ae.original,
                            argument_points: args.find(a => a.title === ae.original?.title)?.argument_points ?? [],
                            legal_principles: args.find(a => a.title === ae.original?.title)?.legal_principles ?? [],
                            judge_names: args.find(a => a.title === ae.original?.title)?.judge_names ?? [],
                            judge_statements: args.find(a => a.title === ae.original?.title)?.judge_statements ?? [],
                            supporting_cases: args.find(a => a.title === ae.original?.title)?.supporting_cases ?? [],
                            model_extracted_points: args.find(a => a.title === ae.original?.title)?.model_extracted_points ?? [],
                          }}
                          adversarial={ae}
                        />
                      ))}
                    </View>
                  )}
                </>
              )}

              {args.length === 0 && (
                <Card title="Strategic Argument Points">
                  <Text style={s.noData}>No arguments generated. The uploaded document may not contain sufficient legal content.</Text>
                </Card>
              )}
            </View>

            {/* RIGHT SIDEBAR */}
            <View style={s.sideCol}>
              {args.length > 0 && (
                <Card title="Strategy Dashboard">
                  {args.map((arg, i) => {
                    const cfg = PERSPECTIVE_CONFIG[arg.perspective] ?? { label: arg.perspective, color: '#6B7280', bg: '#F9FAFB', icon: '📋' };
                    return (
                      <View key={i} style={[s.overviewRow, { borderLeftColor: cfg.color }]}>
                        <Text style={s.overviewIcon}>{cfg.icon}</Text>
                        <View style={{ flex: 1 }}>
                          <Text style={[s.overviewPerspective, { color: cfg.color }]}>{cfg.label}</Text>
                          <Text style={s.overviewPoints}>
                            {arg.argument_points?.length ?? 0} points · {arg.supporting_cases?.length ?? 0} cases
                          </Text>
                        </View>
                        <Text style={[s.overviewScore, { color: cfg.color }]}>
                          {Math.round((arg.strength_score ?? 0.8) * 100)}%
                        </Text>
                      </View>
                    );
                  })}
                </Card>
              )}
            </View>
          </View>
        )}
      </Container>
    </Layout>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────
const s = StyleSheet.create({
  row: { flexDirection: Platform.OS === 'web' ? 'row' : 'column', gap: spacing.lg, alignItems: 'flex-start' },
  mainCol: { flex: 2, minWidth: 0 },
  sideCol: { flex: 1, minWidth: 260 },
  backRow: { marginBottom: spacing.md },
  backLink: { color: colors.accent, fontWeight: '600', fontSize: 14 },
  center: { alignItems: 'center', justifyContent: 'center', paddingVertical: 80, gap: 12 },
  loadingText: { fontSize: 16, fontWeight: '700', color: colors.primary, marginTop: 12 },
  loadingHint: { fontSize: 12, color: colors.textMuted, textAlign: 'center', maxWidth: 400 },
  errorText: { fontSize: 14, color: '#DC2626', lineHeight: 22, marginBottom: 12 },
  retryBtn: { paddingVertical: 8, paddingHorizontal: 16, backgroundColor: '#F1F5F9', borderRadius: 8, alignSelf: 'flex-start' },
  retryText: { fontSize: 13, fontWeight: '600', color: colors.primary },
  noData: { color: colors.textMuted, fontStyle: 'italic', textAlign: 'center', padding: 20 },
  resultCard: { marginTop: spacing.lg },

  // Tabs
  tabs: { flexDirection: 'row', gap: 4, marginVertical: spacing.md, borderBottomWidth: 1, borderBottomColor: '#E5E7EB' },
  tab: { paddingHorizontal: 14, paddingVertical: 10, borderBottomWidth: 2, borderBottomColor: 'transparent' },
  tabActive: { borderBottomColor: colors.accent },
  tabText: { fontSize: 13, fontWeight: '500', color: colors.textMuted },
  tabTextActive: { color: colors.accent, fontWeight: '700' },

  // Argument Card
  argCard: {
    backgroundColor: '#FFFFFF', borderRadius: 12, borderLeftWidth: 4, padding: 18, marginBottom: 16,
    shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 8, shadowOffset: { width: 0, height: 2 }, elevation: 2,
  },
  argCardHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 12, gap: 8, flexWrap: 'wrap' },
  argCardIcon: { fontSize: 20 },
  argCardTitle: { fontSize: 16, fontWeight: '700', color: colors.primary, flex: 1 },
  argContent: { fontSize: 14, color: colors.textSecondary, lineHeight: 22, marginBottom: 12 },

  // Strength Meter
  meterRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  meterLabel: { fontSize: 11, color: colors.textMuted, width: 52, fontWeight: '600' },
  meterTrack: { flex: 1, height: 6, backgroundColor: '#F3F4F6', borderRadius: 4, overflow: 'hidden' },
  meterFill: { height: '100%', borderRadius: 4 },
  meterPct: { fontSize: 12, fontWeight: '700', width: 36, textAlign: 'right' },

  // Badge
  badge: { borderRadius: 20, paddingHorizontal: 10, paddingVertical: 3, borderWidth: 1 },
  badgeText: { fontSize: 11, fontWeight: '700' },

  // Section
  section: { marginTop: 14, paddingTop: 12, borderTopWidth: 1, borderTopColor: '#F3F4F6' },
  sectionTitle: { fontSize: 12, fontWeight: '700', color: colors.primary, marginBottom: 8, opacity: 0.7, textTransform: 'uppercase', letterSpacing: 0.5 },

  // Points
  pointRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, marginBottom: 6 },
  pointDot: { width: 7, height: 7, borderRadius: 3.5, marginTop: 5 },
  pointText: { flex: 1, fontSize: 13, color: colors.textSecondary, lineHeight: 19 },

  // Tags
  tagRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  legalTag: { backgroundColor: '#EDE9FE', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  legalTagText: { fontSize: 11, color: '#5B21B6', fontWeight: '600' },
  caseTag: { backgroundColor: '#E0F2FE', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3, maxWidth: 220 },
  caseTagText: { fontSize: 11, color: '#0369A1', fontWeight: '600' },

  // Citation
  citationBox: { backgroundColor: '#F8FAFC', borderRadius: 8, padding: 12, marginBottom: 8, borderLeftWidth: 3, borderLeftColor: '#CBD5E1' },
  citationQuote: { fontSize: 36, color: '#CBD5E1', lineHeight: 30, fontFamily: 'Georgia, serif' },
  citationText: { fontSize: 13, color: '#475569', fontStyle: 'italic', lineHeight: 20, marginBottom: 6 },
  citationJudge: { fontSize: 12, fontWeight: '700', color: '#334155' },

  // Adversarial
  adversarialToggle: { marginTop: 14, paddingVertical: 10, borderRadius: 8, borderWidth: 1, alignItems: 'center' },
  adversarialToggleText: { fontSize: 13, fontWeight: '600' },
  adversarialPanel: { marginTop: 12, backgroundColor: '#F8FAFC', borderRadius: 10, padding: 14 },
  adversarialPanelTitle: { fontSize: 14, fontWeight: '700', color: colors.primary, marginBottom: 12 },

  // Counter Block
  counterBlock: { marginBottom: 16, paddingBottom: 16, borderBottomWidth: 1, borderBottomColor: '#E5E7EB' },
  strategyBadge: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', borderRadius: 6, paddingHorizontal: 10, paddingVertical: 6, marginBottom: 10, borderWidth: 1 },
  strategyBadgeText: { fontSize: 12, fontWeight: '700' },
  strategyStrength: { fontSize: 12, fontWeight: '600' },
  counterBox: { backgroundColor: '#FEF2F2', borderRadius: 8, padding: 12, marginBottom: 8, borderLeftWidth: 3, borderLeftColor: '#DC2626' },
  counterLabel: { fontSize: 11, fontWeight: '700', color: '#DC2626', marginBottom: 4, textTransform: 'uppercase' },
  counterText: { fontSize: 13, color: '#7F1D1D', lineHeight: 19 },
  rebuttalBox: { backgroundColor: '#ECFDF5', borderRadius: 8, padding: 12, marginBottom: 8, borderLeftWidth: 3, borderLeftColor: '#059669' },
  rebuttalLabel: { fontSize: 11, fontWeight: '700', color: '#059669', marginBottom: 4, textTransform: 'uppercase' },
  rebuttalText: { fontSize: 13, color: '#064E3B', lineHeight: 19 },
  weakPointsBox: { marginTop: 6 },
  weakPointsLabel: { fontSize: 11, fontWeight: '700', color: '#D97706', marginBottom: 6, textTransform: 'uppercase' },
  weakTag: { backgroundColor: '#FEF3C7', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3, borderWidth: 1, borderColor: '#FCD34D' },
  weakTagText: { fontSize: 11, color: '#92400E', fontWeight: '600' },

  // Overview (sidebar)
  overviewRow: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 10, borderLeftWidth: 3, backgroundColor: '#F9FAFB', borderRadius: 6, marginBottom: 8 },
  overviewIcon: { fontSize: 18 },
  overviewPerspective: { fontSize: 13, fontWeight: '700' },
  overviewPoints: { fontSize: 11, color: colors.textMuted, marginTop: 1 },
  overviewScore: { fontSize: 15, fontWeight: '800' },

  // Simulation Summary
  summaryGrid: { flexDirection: 'row', gap: 8 },
  summaryGridItem: { flex: 1, backgroundColor: '#F8FAFC', borderRadius: 8, padding: 10, alignItems: 'center' },
  summaryGridNum: { fontSize: 22, fontWeight: '800', color: colors.primary, textAlign: 'center', marginBottom: 4 },
  summaryGridLabel: { fontSize: 11, color: colors.textMuted, textAlign: 'center', fontWeight: '500' },
  recRow: { flexDirection: 'row', gap: 8, marginBottom: 6, alignItems: 'flex-start' },
  recBullet: { fontSize: 14, color: colors.accent, fontWeight: '700' },
  recText: { flex: 1, fontSize: 13, color: colors.textSecondary, lineHeight: 19 },

  // Report Button
  reportBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 12, marginVertical: spacing.md,
    backgroundColor: '#1E1B4B', borderRadius: 12, padding: 16,
    shadowColor: '#1E1B4B', shadowOpacity: 0.25, shadowRadius: 10, shadowOffset: { width: 0, height: 4 },
    elevation: 4,
  },
  reportBtnIcon: { fontSize: 28 },
  reportBtnTitle: { fontSize: 15, fontWeight: '800', color: '#FFFFFF', marginBottom: 2 },
  reportBtnSub: { fontSize: 12, color: 'rgba(255,255,255,0.65)', lineHeight: 17 },
  reportBtnArrow: { fontSize: 20, color: '#A5B4FC', fontWeight: '900', marginLeft: 4 },
});
