import {
  View,
  Text,
  TextInput,
  Pressable,
  StyleSheet,
  Platform,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Layout } from '../components/Layout';
import { Container, Card, PageHeader, Button } from '../components/ui';
import { colors, typography, spacing, borderRadius } from '../theme';
import React, { useState } from 'react';
import {
  predictAppealOutcomeDetailed,
  saveComp3History,
  DetailedPredictionRequest,
  AppealPredictionResponse,
  DetailedPredictionResponse,
} from '../api';

// ─── Types ───────────────────────────────────────────────────────────────────

type AnyPredictionResult = AppealPredictionResponse | DetailedPredictionResponse;

interface ContextStat {
  allowed_rate: number;
  partly_rate: number;
  dismissed_rate: number;
  count: number;
}

interface ContextAnalysis {
  offence?: ContextStat;
  location?: ContextStat;
  year?: ContextStat;
}

interface GroundStat {
  allowed_rate: number;
  partly_rate: number;
  dismissed_rate: number;
  count: number;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Safely sum all arrays inside detected_features */
function countDetectedFeatures(features: Record<string, string[]> | undefined): number {
  if (!features) return 0;
  return Object.values(features).reduce((sum, arr) => sum + (Array.isArray(arr) ? arr.length : 0), 0);
}

/** Collect all detected feature strings into a flat array */
function flatFeatures(features: Record<string, string[]> | undefined): string[] {
  if (!features) return [];
  return [
    ...(features.grounds ?? []),
    ...(features.evidence ?? []),
    ...(features.offence ?? []),
    ...(features.other ?? []),
  ].slice(0, 6);
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function TemplateSection({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <View style={styles.templateSection}>
      <Text style={styles.sectionNumber}>{number}.</Text>
      <View style={styles.sectionContent}>
        <Text style={styles.templateSectionTitle}>{title}</Text>
        <Text style={styles.sectionDesc}>{description}</Text>
      </View>
    </View>
  );
}

function ProgressTracker({ step, text }: { step: number; text: string }) {
  const steps = ['Extract Features', 'Generate Embeddings', 'Run Model', 'Complete'];
  return (
    <Card style={styles.progressCard} title="🔄 Processing Analysis">
      <View style={styles.progressContainer}>
        <Text style={styles.progressText}>{text}</Text>

        <View style={styles.progressSteps}>
          {steps.map((label, idx) => (
            <View key={idx} style={[styles.progressStep, step >= idx && styles.progressStepActive]}>
              <View style={[styles.progressStepCircle, step >= idx && styles.progressStepCircleActive]}>
                <Text style={[styles.progressStepNum, step >= idx && styles.progressStepNumActive]}>
                  {idx + 1}
                </Text>
              </View>
              <Text style={styles.progressStepLabel}>{label}</Text>
            </View>
          ))}
        </View>

        <View style={styles.progressBarContainer}>
          <View style={[styles.progressBar, { width: `${((step + 1) / 4) * 100}%` as any }]} />
        </View>
      </View>
    </Card>
  );
}

function OutcomeColor(prediction: string): string {
  if (prediction === 'Appeal_Allowed') return colors.success;
  if (prediction === 'Appeal_Dismissed') return colors.error;
  return colors.accent;
}

function ProbabilityMeters({ probabilities }: { probabilities: Record<string, number> }) {
  const config: Record<string, { label: string; color: string }> = {
    Appeal_Allowed: { label: 'Appeal Allowed', color: colors.success },
    Appeal_Dismissed: { label: 'Appeal Dismissed', color: colors.error },
    Partly_Allowed: { label: 'Partly Allowed', color: colors.accent },
  };

  return (
    <Card style={styles.resultCard} title="📊 Probability Distribution">
      {Object.entries(probabilities).map(([key, value]) => {
        const cfg = config[key] ?? { label: key, color: colors.textMuted };
        return (
          <View key={key} style={styles.meterRow}>
            <Text style={styles.meterLabel}>{cfg.label}</Text>
            <View style={styles.meterTrack}>
              <View style={[styles.meterFill, { width: `${value}%` as any, backgroundColor: cfg.color }]} />
            </View>
            <Text style={[styles.meterPct, { color: cfg.color }]}>{value.toFixed(1)}%</Text>
          </View>
        );
      })}
    </Card>
  );
}

function ContextSection({ context }: { context: ContextAnalysis }) {
  const rows: Array<{ label: string; stat: ContextStat }> = [];
  if (context.offence) rows.push({ label: 'Offence Group', stat: context.offence });
  if (context.location) rows.push({ label: 'High Court Location', stat: context.location });
  if (context.year) rows.push({ label: 'Appeal Year', stat: context.year });
  if (rows.length === 0) return null;

  return (
    <Card style={styles.resultCard} title="📈 Contextual Analysis">
      {rows.map(({ label, stat }) => (
        <View key={label} style={styles.analysisRow}>
          <View style={styles.analysisRowHeader}>
            <Text style={styles.analysisLabel}>{label}</Text>
            <Text style={styles.analysisCases}>Cases: {stat.count}</Text>
          </View>
          <View style={styles.analysisBarContainer}>
            <View style={[styles.analysisBarSegment, { flex: stat.allowed_rate || 0, backgroundColor: colors.success }]} />
            <View style={[styles.analysisBarSegment, { flex: stat.partly_rate || 0, backgroundColor: colors.accent }]} />
            <View style={[styles.analysisBarSegment, { flex: stat.dismissed_rate || 0, backgroundColor: colors.error }]} />
          </View>
          <View style={styles.analysisLegend}>
            <Text style={[styles.legendItem, { color: colors.success }]}>Allowed {(stat.allowed_rate * 100).toFixed(1)}%</Text>
            <Text style={[styles.legendItem, { color: colors.accent }]}>Partly {(stat.partly_rate * 100).toFixed(1)}%</Text>
            <Text style={[styles.legendItem, { color: colors.error }]}>Dismissed {(stat.dismissed_rate * 100).toFixed(1)}%</Text>
          </View>
        </View>
      ))}
    </Card>
  );
}

function GroundsOrEvidenceSection({
  title,
  data,
}: {
  title: string;
  data: Record<string, GroundStat>;
}) {
  const entries = Object.entries(data);
  if (entries.length === 0) return null;

  return (
    <Card style={styles.resultCard} title={title}>
      {entries.map(([name, stats]) => (
        <View key={name} style={styles.analysisRow}>
          <View style={styles.analysisRowHeader}>
            <Text style={styles.analysisLabel}>{name}</Text>
            <Text style={styles.analysisCases}>Cases: {stats.count}</Text>
          </View>
          <View style={styles.analysisBarContainer}>
            <View style={[styles.analysisBarSegment, { flex: stats.allowed_rate || 0, backgroundColor: colors.success }]} />
            <View style={[styles.analysisBarSegment, { flex: stats.partly_rate || 0, backgroundColor: colors.accent }]} />
            <View style={[styles.analysisBarSegment, { flex: stats.dismissed_rate || 0, backgroundColor: colors.error }]} />
          </View>
          <View style={styles.analysisLegend}>
            <Text style={[styles.legendItem, { color: colors.success }]}>Allowed {(stats.allowed_rate * 100).toFixed(1)}%</Text>
            <Text style={[styles.legendItem, { color: colors.accent }]}>Partly {(stats.partly_rate * 100).toFixed(1)}%</Text>
            <Text style={[styles.legendItem, { color: colors.error }]}>Dismissed {(stats.dismissed_rate * 100).toFixed(1)}%</Text>
          </View>
        </View>
      ))}
    </Card>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function Component3Screen() {
  const router = useRouter();
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AnyPredictionResult | null>(null);
  const [caseDescription, setCaseDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [progressStep, setProgressStep] = useState(0);
  const [progressText, setProgressText] = useState('');

  const isDetailed = (r: AnyPredictionResult): r is DetailedPredictionResponse =>
    'legal_reasoning' in r;

  const handlePredict = async () => {
    if (!caseDescription.trim() || caseDescription.length < 50) {
      setError('Please provide a detailed case description (at least 50 characters)');
      return;
    }

    setAnalyzing(true);
    setError(null);
    setResult(null);
    setProgressStep(0);
    setProgressText('⏳ Step 1/4: Extracting features...');

    try {
      await new Promise(resolve => setTimeout(resolve, 800));
      setProgressStep(1);
      setProgressText('⏳ Step 2/4: Analyzing legal patterns...');

      await new Promise(resolve => setTimeout(resolve, 800));
      setProgressStep(2);
      setProgressText('⏳ Step 3/4: Running ensemble model...');

      const request: DetailedPredictionRequest = {
        case_description: caseDescription,
        user_type: 'general',
        analysis_level: 'detailed',
        include_precedents: true,
        language: 'en',
      };

      const predictionResult = await predictAppealOutcomeDetailed(request);

      setProgressStep(3);
      setProgressText('⏳ Step 4/4: Complete!');
      await new Promise(resolve => setTimeout(resolve, 500));

      if (predictionResult) {
        setResult(predictionResult);
        await saveComp3History({
          case_id: `case_${Date.now()}`,
          case_name:
            caseDescription.substring(0, 50) + (caseDescription.length > 50 ? '...' : ''),
          payload: predictionResult,
          user_type: 'general',
          analysis_level: 'detailed',
          timestamp: new Date().toISOString(),
        });
      } else {
        setError('Failed to get prediction. Please try again.');
      }
    } catch (err) {
      setError('Error connecting to prediction service.');
      console.error('Prediction error:', err);
    } finally {
      setAnalyzing(false);
      setProgressStep(0);
      setProgressText('');
    }
  };

  const wordCount = caseDescription.split(/\s+/).filter(w => w.length > 0).length;

  // Cast extended fields safely
  const extResult = result as any;

  return (
    <Layout>
      <Container>
        <PageHeader
          title="Outcome Prediction Model"
          breadcrumb="Analytical Tools → Probability Analysis"
        />

        <View style={styles.mainCol}>
          {/* ── Input Card ── */}
          <Card style={styles.inputCard} title="📋 Case Analysis Template">
            <Text style={styles.templateTitle}>
              Please include the following in your case description:
            </Text>

            <TemplateSection
              number="1"
              title="📄 Basic Information"
              description="Offence type & penal code section, original sentence/conviction"
            />
            <TemplateSection
              number="2"
              title="⚖️ Case Facts"
              description="Brief description of the incident, date, location, parties involved"
            />
            <TemplateSection
              number="3"
              title="🔬 Evidence"
              description="Eyewitness testimony, medical/forensic evidence, documentary evidence, expert evidence (JMO, analysts)"
            />
            <TemplateSection
              number="4"
              title="⚖️ Grounds of Appeal"
              description="Contradictions in evidence, procedural errors, misdirection on law, chain of custody issues, wrong identification"
            />
            <TemplateSection
              number="5"
              title="🛡️ Defence Position"
              description="Accused's statement, defence witnesses, alibi or alternative theories"
            />

            <TextInput
              style={styles.textArea}
              placeholder="Enter your case description following the template above..."
              placeholderTextColor={colors.textMuted}
              value={caseDescription}
              onChangeText={setCaseDescription}
              multiline
              editable={!analyzing}
              textAlignVertical="top"
            />

            <View style={styles.countRow}>
              <Text style={styles.countText}>📊 Characters: {caseDescription.length}</Text>
              <Text style={styles.countText}>📊 Words: {wordCount}</Text>
            </View>

            {caseDescription.length > 0 && caseDescription.length < 100 && (
              <Text style={styles.warningText}>
                ⚠️ Please provide at least 100 characters for accurate prediction
              </Text>
            )}

            {error && <Text style={styles.errorText}>{error}</Text>}

            <Button
              onPress={handlePredict}
              disabled={analyzing || !caseDescription.trim()}
              style={styles.analyzeBtn}
            >
              {analyzing ? 'Analyzing...' : '🔮 Predict Appeal Outcome'}
            </Button>
          </Card>

          {/* ── Progress ── */}
          {analyzing && <ProgressTracker step={progressStep} text={progressText} />}

          {/* ── Results ── */}
          {result && (
            <>
              <View style={styles.resultsSeparator}>
                <Text style={styles.resultsSeparatorText}>📊 Prediction Results</Text>
              </View>

              {/* Summary Grid */}
              <Card
                style={[
                  styles.resultCard,
                  { borderColor: OutcomeColor(result.prediction), borderWidth: 2 },
                ]}
                title="📊 Prediction Analysis"
              >
                <View style={styles.summaryGrid}>
                  <View style={styles.summaryGridItem}>
                    <Text style={[styles.summaryGridNum, { color: OutcomeColor(result.prediction) }]}>
                      {result.confidence.toFixed(1)}%
                    </Text>
                    <Text style={styles.summaryGridLabel}>Confidence</Text>
                  </View>

                  <View style={styles.summaryGridItem}>
                    <Text style={styles.summaryGridNum}>
                      {isDetailed(result) ? 'Enhanced' : countDetectedFeatures(result.detected_features)}
                    </Text>
                    <Text style={styles.summaryGridLabel}>
                      {isDetailed(result) ? 'Analysis Level' : 'Features Detected'}
                    </Text>
                  </View>

                  <View
                    style={[
                      styles.summaryGridItem,
                      { backgroundColor: OutcomeColor(result.prediction) + '20' },
                    ]}
                  >
                    <Text
                      style={[
                        styles.summaryGridNum,
                        { fontSize: 11, fontWeight: '700', color: OutcomeColor(result.prediction) },
                      ]}
                    >
                      {result.prediction.replace(/_/g, ' ')}
                    </Text>
                    <Text style={styles.summaryGridLabel}>Predicted Outcome</Text>
                  </View>
                </View>
              </Card>

              {/* Detected Features */}
              <Card style={styles.resultCard} title="🔍 What the AI Detected in Your Case">
                {isDetailed(result) ? (
                  <View style={styles.enhancedSection}>
                    <View style={styles.legalReasoningBox}>
                      <Text style={styles.legalReasoning}>{result.legal_reasoning}</Text>
                    </View>

                    <View style={styles.detectedFeaturesGrid}>
                      <View style={styles.featureCol}>
                        <Text style={styles.featureSectionTitle}>⚖️ Grounds of Appeal</Text>
                        {result.key_factors && result.key_factors.length > 0 ? (
                          result.key_factors.slice(0, 3).map((factor: any, i: number) => (
                            <View key={i} style={styles.featureBadge}>
                              <Text style={styles.featureBadgeText}>🟢 {factor.factor_name}</Text>
                            </View>
                          ))
                        ) : (
                          <Text style={styles.noFeaturesText}>⚠️ No specific grounds detected</Text>
                        )}
                      </View>

                      <View style={styles.featureCol}>
                        <Text style={styles.featureSectionTitle}>🔬 Evidence Types</Text>
                        {result.detected_features?.evidence && result.detected_features.evidence.length > 0 ? (
                          result.detected_features.evidence.slice(0, 3).map((ev: string, i: number) => (
                            <View key={i} style={styles.featureBadge}>
                              <Text style={styles.featureBadgeText}>🟡 {ev}</Text>
                            </View>
                          ))
                        ) : (
                          <Text style={styles.noFeaturesText}>⚠️ No evidence types detected</Text>
                        )}
                      </View>
                    </View>

                    <View style={styles.compactRow}>
                      {result.risk_assessment && (
                        <View style={styles.compactItem}>
                          <Text style={styles.compactLabel}>⚠️ Risk Assessment</Text>
                          <Text style={styles.compactValue}>
                            {result.risk_assessment.split(':')[0]}
                          </Text>
                        </View>
                      )}
                      {result.strategy_recommendations && result.strategy_recommendations.length > 0 && (
                        <View style={styles.compactItem}>
                          <Text style={styles.compactLabel}>💡 Strategy</Text>
                          <Text style={styles.compactValue}>
                            {result.strategy_recommendations[0].recommendation.split(' ')[0]}
                          </Text>
                        </View>
                      )}
                    </View>
                  </View>
                ) : (
                  <View>
                    {result.detected_features && countDetectedFeatures(result.detected_features) > 0 ? (
                      <>
                        <View style={styles.featuresSuccessRow}>
                          <Text style={styles.featuresSuccessText}>✅ Successfully detected </Text>
                          <Text style={[styles.featuresSuccessText, { fontWeight: '700' }]}>
                            {countDetectedFeatures(result.detected_features)} key features
                          </Text>
                          <Text style={styles.featuresSuccessText}> from your case description</Text>
                        </View>

                        <View style={styles.detectedFeaturesGrid}>
                          {result.detected_features.grounds && result.detected_features.grounds.length > 0 && (
                            <View style={styles.featureCol}>
                              <Text style={styles.featureSectionTitle}>⚖️ Grounds of Appeal</Text>
                              {result.detected_features.grounds.slice(0, 3).map((g: string, i: number) => (
                                <View key={i} style={styles.featureBadge}>
                                  <Text style={styles.featureBadgeText}>🟢 {g}</Text>
                                </View>
                              ))}
                            </View>
                          )}
                          {result.detected_features.evidence && result.detected_features.evidence.length > 0 && (
                            <View style={styles.featureCol}>
                              <Text style={styles.featureSectionTitle}>🔬 Evidence Detected</Text>
                              {result.detected_features.evidence.slice(0, 3).map((e: string, i: number) => (
                                <View key={i} style={styles.featureBadge}>
                                  <Text style={styles.featureBadgeText}>🟡 {e}</Text>
                                </View>
                              ))}
                            </View>
                          )}
                          {result.detected_features.offence && result.detected_features.offence.length > 0 && (
                            <View style={styles.featureCol}>
                              <Text style={styles.featureSectionTitle}>📋 Offence Category</Text>
                              {result.detected_features.offence.slice(0, 2).map((o: string, i: number) => (
                                <View key={i} style={styles.featureBadge}>
                                  <Text style={styles.featureBadgeText}>🔵 {o}</Text>
                                </View>
                              ))}
                            </View>
                          )}
                        </View>
                      </>
                    ) : (
                      <View style={styles.limitedInfoBox}>
                        <Text style={styles.limitedInfoTitle}>⚠️ Limited Information Detected</Text>
                        <Text style={styles.limitedInfoText}>
                          {`The AI couldn't identify specific legal features. For better predictions, please include:\n• Specific grounds of appeal (contradictions, chain of custody, identification issues)\n• Evidence types (eyewitness, medical, forensic, confession)\n• Offence category (murder, rape, drug trafficking, etc.)`}
                        </Text>
                      </View>
                    )}
                  </View>
                )}
              </Card>

              {/* Enhanced Legal Analysis */}
              {isDetailed(result) && (
                <Card style={styles.resultCard} title="⚖️ Legal Analysis">
                  <View style={styles.enhancedSection}>
                    <View style={styles.legalReasoningBox}>
                      <Text style={styles.legalReasoning}>{result.legal_reasoning}</Text>
                    </View>

                    {result.key_factors && result.key_factors.length > 0 && (
                      <View style={styles.compactSection}>
                        <Text style={styles.compactSectionLabel}>🎯 Key Factors</Text>
                        {result.key_factors.slice(0, 3).map((factor: any, i: number) => (
                          <View key={i} style={styles.factorItem}>
                            <Text style={styles.factorName}>{factor.factor_name}</Text>
                          </View>
                        ))}
                      </View>
                    )}

                    <View style={styles.compactRow}>
                      {result.risk_assessment && (
                        <View style={styles.compactItem}>
                          <Text style={styles.compactLabel}>⚠️ Risk</Text>
                          <Text style={styles.compactValue}>
                            {result.risk_assessment.split(':')[0]}
                          </Text>
                        </View>
                      )}
                      {result.strategy_recommendations && result.strategy_recommendations.length > 0 && (
                        <View style={styles.compactItem}>
                          <Text style={styles.compactLabel}>💡 Strategy</Text>
                          <Text style={styles.compactValue}>
                            {result.strategy_recommendations[0].recommendation.split(' ')[0]}
                          </Text>
                        </View>
                      )}
                    </View>
                  </View>
                </Card>
              )}

              {/* Probability Distribution */}
              <ProbabilityMeters probabilities={result.probabilities} />

              {/* Contextual Analysis */}
              {extResult?.context_analysis && (
                <ContextSection context={extResult.context_analysis} />
              )}

              {/* Grounds Analysis */}
              {extResult?.grounds_analysis && Object.keys(extResult.grounds_analysis).length > 0 && (
                <GroundsOrEvidenceSection
                  title="⚖️ Grounds Analysis"
                  data={extResult.grounds_analysis}
                />
              )}

              {/* Evidence Analysis */}
              {extResult?.evidence_analysis && Object.keys(extResult.evidence_analysis).length > 0 && (
                <GroundsOrEvidenceSection
                  title="🔬 Evidence Impact"
                  data={extResult.evidence_analysis}
                />
              )}

              {/* Why This Prediction */}
              <Card style={styles.resultCard} title="💡 Why This Prediction?">
                <View style={styles.reasoningSection}>
                  <Text style={styles.reasoningText}>
                    {'Based on analysis of '}
                    <Text style={{ fontWeight: '700' }}>
                      {flatFeatures(result.detected_features).join(', ')}
                    </Text>
                    {' and legal pattern analysis, the model predicts:'}
                  </Text>

                  {result.prediction === 'Appeal_Allowed' && result.confidence > 60 && (
                    <View style={[styles.reasoningBlock, { borderLeftColor: colors.success }]}>
                      <Text style={[styles.reasoningTitle, { color: colors.success }]}>
                        🟢 Strong indicators for Appeal Allowed:
                      </Text>
                      <Text style={styles.reasoningPoints}>
                        {`• Detected grounds: ${result.detected_features?.grounds?.slice(0, 3).join(', ') || 'Procedural/evidentiary issues'}\n• Pattern matches similar cases where appeals succeeded\n• High confidence (${result.confidence.toFixed(1)}%) suggests strong legal grounds`}
                      </Text>
                    </View>
                  )}

                  {result.prediction === 'Appeal_Dismissed' && result.confidence > 60 && (
                    <View style={[styles.reasoningBlock, { borderLeftColor: colors.error }]}>
                      <Text style={[styles.reasoningTitle, { color: colors.error }]}>
                        🔴 Strong indicators for Appeal Dismissed:
                      </Text>
                      <Text style={styles.reasoningPoints}>
                        {`• Evidence pattern: ${result.detected_features?.evidence?.slice(0, 3).join(', ') || 'Strong prosecution evidence'}\n• Similar historical cases were mostly dismissed\n• High confidence (${result.confidence.toFixed(1)}%) suggests solid conviction basis`}
                      </Text>
                    </View>
                  )}

                  {result.confidence < 55 && (
                    <View style={[styles.reasoningBlock, { borderLeftColor: colors.accent }]}>
                      <Text style={[styles.reasoningTitle, { color: colors.accent }]}>
                        🟡 Mixed signals detected:
                      </Text>
                      <Text style={styles.reasoningPoints}>
                        {`• Competing factors make outcome uncertain\n• Both prosecution strengths and defence grounds present\n• Medium/low confidence (${result.confidence.toFixed(1)}%) indicates borderline case`}
                      </Text>
                    </View>
                  )}
                </View>
              </Card>

              {/* Feature Detection Tree */}
              <Card style={styles.resultCard} title="🔍 Feature Detection">
                <View style={styles.zoneRoot}>
                  <View style={styles.zoneRootBadge}>
                    <Text style={styles.zoneRootBadgeText}>⚖</Text>
                  </View>
                  <View>
                    <Text style={styles.zoneRootTitle}>Legal Analysis</Text>
                    <Text style={styles.zoneRootSub}>Feature extraction complete</Text>
                  </View>
                </View>

                <View style={styles.zoneTwoCol}>
                  <View style={styles.zoneSection}>
                    <View style={styles.zoneLabelRow}>
                      <View style={[styles.zoneLabelDot, { backgroundColor: colors.prosecution }]} />
                      <Text style={[styles.zoneLabel, { color: colors.prosecution }]}>
                        ⚖️ Grounds of Appeal
                      </Text>
                    </View>
                    {result.detected_features?.grounds && result.detected_features.grounds.length > 0 ? (
                      result.detected_features.grounds.map((g: string, i: number) => (
                        <View key={i} style={styles.treeItem}>
                          <Text style={styles.treeItemTitle}>{g}</Text>
                        </View>
                      ))
                    ) : (
                      <Text style={styles.emptyState}>No grounds detected</Text>
                    )}
                  </View>

                  <View style={styles.zoneSection}>
                    <View style={styles.zoneLabelRow}>
                      <View style={[styles.zoneLabelDot, { backgroundColor: colors.defense }]} />
                      <Text style={[styles.zoneLabel, { color: colors.defense }]}>
                        🔬 Evidence Types
                      </Text>
                    </View>
                    {result.detected_features?.evidence && result.detected_features.evidence.length > 0 ? (
                      result.detected_features.evidence.map((e: string, i: number) => (
                        <View key={i} style={styles.treeItem}>
                          <Text style={styles.treeItemTitle}>{e}</Text>
                        </View>
                      ))
                    ) : (
                      <Text style={styles.emptyState}>No evidence detected</Text>
                    )}
                  </View>
                </View>

                <View style={styles.zoneSection}>
                  <View style={styles.zoneLabelRow}>
                    <View style={[styles.zoneLabelDot, { backgroundColor: colors.accent }]} />
                    <Text style={[styles.zoneLabel, { color: colors.accent }]}>📋 Case Details</Text>
                  </View>
                  <View style={styles.zoneSideBySide}>
                    {result.detected_features?.offence && result.detected_features.offence.length > 0 && (
                      <View style={styles.zoneColumn}>
                        <Text style={styles.zoneSubLabel}>Offence Category</Text>
                        {result.detected_features.offence.map((o: string, i: number) => (
                          <View key={i} style={styles.treeItem}>
                            <Text style={styles.treeItemTitle}>{o}</Text>
                          </View>
                        ))}
                      </View>
                    )}
                    {result.detected_features?.other && result.detected_features.other.length > 0 && (
                      <View style={styles.zoneColumn}>
                        <Text style={styles.zoneSubLabel}>Other Factors</Text>
                        {result.detected_features.other.slice(0, 3).map((o: string, i: number) => (
                          <View key={i} style={styles.treeItem}>
                            <Text style={styles.treeItemTitle}>{o}</Text>
                          </View>
                        ))}
                      </View>
                    )}
                  </View>
                </View>
              </Card>

              {/* Similar Cases */}
              <Card style={styles.resultCard} title="📚 Similar Historical Cases">
                <Text style={styles.sectionSubtitle}>Based on analysis of similar court cases</Text>

                {result.similar_cases.slice(0, 3).map((c, idx) => {
                  const simPct = c.similarity_score
                    ? (c.similarity_score * 100).toFixed(0)
                    : '0';
                  const summary = c.case_summary || c.facts || 'Details not available';
                  const outcomeColor =
                    c.outcome === 'Appeal_Allowed'
                      ? { bg: '#D1FAE5', text: '#065F46' }
                      : c.outcome === 'Appeal_Dismissed'
                      ? { bg: '#FEE2E2', text: '#7F1D1D' }
                      : { bg: '#FEF3C7', text: '#92400E' };

                  return (
                    <View key={idx} style={styles.caseCard}>
                      {/* Header */}
                      <View style={styles.caseHeader}>
                        <View style={{ flex: 1 }}>
                          <Text style={styles.caseId}>#{idx + 1} {c.case_id}</Text>
                          <Text style={styles.caseSimilarity}>
                            {c.outcome?.replace(/_/g, ' ')} • {simPct}% Similar
                          </Text>
                        </View>
                        <View style={[styles.caseOutcome, { backgroundColor: outcomeColor.bg }]}>
                          <Text style={[styles.caseOutcomeText, { color: outcomeColor.text }]}>
                            {c.outcome?.replace(/_/g, ' ')}
                          </Text>
                        </View>
                      </View>

                      {/* Decision Date */}
                      {c.decision_date && (
                        <View style={styles.caseInfo}>
                          <Text style={styles.caseInfoLabel}>📅 Decision Date:</Text>
                          <Text style={styles.caseInfoValue}>{c.decision_date}</Text>
                        </View>
                      )}

                      {/* Metadata */}
                      {c.offence && c.offence !== 'Not specified' && (
                        <View style={styles.caseInfo}>
                          <Text style={styles.caseInfoLabel}>📋 Offence:</Text>
                          <Text style={styles.caseInfoValue}>{c.offence}</Text>
                        </View>
                      )}
                      {c.high_court && c.high_court !== 'Not specified' && (
                        <View style={styles.caseInfo}>
                          <Text style={styles.caseInfoLabel}>🏛️ High Court:</Text>
                          <Text style={styles.caseInfoValue}>{c.high_court}</Text>
                        </View>
                      )}
                      {c.conviction_status && c.conviction_status !== 'Not specified' && (
                        <View style={styles.caseInfo}>
                          <Text style={styles.caseInfoLabel}>✓ Conviction:</Text>
                          <Text style={styles.caseInfoValue}>{c.conviction_status}</Text>
                        </View>
                      )}

                      {/* Facts */}
                      <View style={styles.caseFacts}>
                        <Text style={styles.caseFactsLabel}>📖 Case Details:</Text>
                        <Text style={styles.caseFactsText}>
                          {summary.length > 200 ? summary.substring(0, 200) + '...' : summary}
                        </Text>
                      </View>

                      {/* Verdict Reasoning */}
                      {c.verdict_reasoning && c.verdict_reasoning !== 'Not specified' && (
                        <View style={[styles.reasoningBlock, { marginTop: 12, borderLeftColor: colors.primary }]}>
                          <Text style={[styles.reasoningTitle, { color: colors.primary }]}>
                            ⚖️ Verdict Reasoning
                          </Text>
                          <Text style={styles.reasoningPoints}>
                            {c.verdict_reasoning.length > 150
                              ? c.verdict_reasoning.substring(0, 150) + '...'
                              : c.verdict_reasoning}
                          </Text>
                        </View>
                      )}

                      {/* Judge Commentary */}
                      {c.judge_commentary && c.judge_commentary !== 'Not specified' && (
                        <View style={[styles.reasoningBlock, { marginTop: 12, borderLeftColor: '#8B5CF6' }]}>
                          <Text style={[styles.reasoningTitle, { color: '#8B5CF6' }]}>
                            💬 Judge's Commentary
                          </Text>
                          <Text style={styles.reasoningPoints}>
                            {c.judge_commentary.length > 150
                              ? c.judge_commentary.substring(0, 150) + '...'
                              : c.judge_commentary}
                          </Text>
                        </View>
                      )}

                      {/* Appeal Grounds List */}
                      {c.appeal_grounds_list && c.appeal_grounds_list.length > 0 && (
                        <View style={{ marginTop: 12 }}>
                          <Text style={styles.compactSectionLabel}>🔗 Appeal Grounds:</Text>
                          {c.appeal_grounds_list.slice(0, 3).map((g, gIdx) => (
                            <View key={gIdx} style={styles.factorItem}>
                              <Text style={styles.compactValue}>• {g}</Text>
                            </View>
                          ))}
                          {c.appeal_grounds_list.length > 3 && (
                            <Text style={styles.compactLabel}>
                              +{c.appeal_grounds_list.length - 3} more grounds
                            </Text>
                          )}
                        </View>
                      )}

                      {/* Evidence Types */}
                      {c.evidence_types && c.evidence_types.length > 0 && (
                        <View style={{ marginTop: 12 }}>
                          <Text style={styles.compactSectionLabel}>🔬 Evidence Types:</Text>
                          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
                            {c.evidence_types.slice(0, 4).map((ev, eIdx) => (
                              <View
                                key={eIdx}
                                style={{
                                  backgroundColor: colors.bgSection,
                                  paddingHorizontal: spacing.sm,
                                  paddingVertical: 4,
                                  borderRadius: borderRadius.sm,
                                }}
                              >
                                <Text style={styles.compactValue}>{ev}</Text>
                              </View>
                            ))}
                            {c.evidence_types.length > 4 && (
                              <Text style={styles.compactLabel}>
                                +{c.evidence_types.length - 4} more
                              </Text>
                            )}
                          </View>
                        </View>
                      )}

                      {/* Success Rate */}
                      {c.appeal_success_rate != null && (
                        <View style={{ marginTop: 12 }}>
                          <View style={styles.meterRow}>
                            <Text style={styles.meterLabel}>📈 Success Rate (Similar Cases):</Text>
                            <View style={styles.meterTrack}>
                              <View
                                style={[
                                  styles.meterFill,
                                  {
                                    width: `${(c.appeal_success_rate * 100).toFixed(0)}%` as any,
                                    backgroundColor: '#10B981',
                                  },
                                ]}
                              />
                            </View>
                            <Text style={styles.meterPct}>
                              {(c.appeal_success_rate * 100).toFixed(0)}%
                            </Text>
                          </View>
                        </View>
                      )}

                      {/* Precedent Value */}
                      {c.precedent_value && (
                        <View style={{ marginTop: 12, flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                          <Text style={styles.caseInfoLabel}>🏅 Precedent Value:</Text>
                          <View
                            style={{
                              backgroundColor: c.precedent_value.includes('High') ? '#DBEAFE' : '#F3E8FF',
                              paddingHorizontal: spacing.sm,
                              paddingVertical: 4,
                              borderRadius: borderRadius.sm,
                            }}
                          >
                            <Text
                              style={{
                                fontSize: 12,
                                fontWeight: '600',
                                color: c.precedent_value.includes('High') ? '#1E40AF' : '#6D28D9',
                              }}
                            >
                              {c.precedent_value}
                            </Text>
                          </View>
                        </View>
                      )}

                      {/* Year */}
                      {c.year && (
                        <View style={{ marginTop: 8, flexDirection: 'row' }}>
                          <Text style={styles.caseInfoLabel}>📅 Year:</Text>
                          <Text style={styles.caseInfoValue}>{c.year}</Text>
                        </View>
                      )}
                    </View>
                  );
                })}
              </Card>
            </>
          )}

          {analyzing && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={colors.primary} />
              <Text style={styles.loadingText}>Analyzing case with AI...</Text>
            </View>
          )}
        </View>
      </Container>
    </Layout>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  mainCol: {
    flex: 1,
    gap: spacing.lg,
  },

  // ── Input Card ──
  inputCard: {
    marginTop: spacing.sm,
  },
  templateTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.primary,
    marginBottom: spacing.md,
  },
  templateSection: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.md,
    padding: spacing.sm,
    backgroundColor: colors.bgSection,
    borderRadius: borderRadius.md,
  },
  sectionNumber: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.accent,
    marginRight: spacing.sm,
    minWidth: 20,
  },
  sectionContent: {
    flex: 1,
  },
  templateSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  sectionDesc: {
    fontSize: 12,
    color: colors.textSecondary,
    lineHeight: 16,
  },

  // ── Text Input ──
  textArea: {
    marginTop: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    minHeight: 120,
    fontSize: 14,
    color: colors.textPrimary,
    backgroundColor: colors.bgCard,
    textAlignVertical: 'top',
  },
  countRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.sm,
  },
  countText: {
    fontSize: 12,
    color: colors.textMuted,
  },
  warningText: {
    fontSize: 12,
    color: '#F59E0B',
    marginTop: spacing.xs,
  },
  errorText: {
    color: colors.error,
    fontSize: 13,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
  analyzeBtn: {
    width: '100%',
    marginTop: spacing.md,
  },

  // ── Progress ──
  progressCard: {
    marginTop: spacing.md,
  },
  progressContainer: {
    gap: spacing.md,
  },
  progressText: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.primary,
    textAlign: 'center',
  },
  progressSteps: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  progressStep: {
    alignItems: 'center',
    flex: 1,
    opacity: 0.4,
  },
  progressStepActive: {
    opacity: 1,
  },
  progressStepCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.xs,
  },
  progressStepCircleActive: {
    backgroundColor: colors.accent,
  },
  progressStepNum: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textMuted,
  },
  progressStepNumActive: {
    color: 'white',
  },
  progressStepLabel: {
    fontSize: 10,
    color: colors.textMuted,
    textAlign: 'center',
  },
  progressBarContainer: {
    height: 4,
    backgroundColor: colors.border,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: colors.accent,
    borderRadius: 2,
  },

  // ── Results Separator ──
  resultsSeparator: {
    borderTopWidth: 2,
    borderTopColor: colors.border,
    paddingTop: spacing.lg,
    marginTop: spacing.xl,
    alignItems: 'center',
  },
  resultsSeparatorText: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.primary,
    marginBottom: spacing.md,
  },

  // ── Result Cards ──
  resultCard: {
    marginTop: spacing.lg,
    backgroundColor: colors.bgCard,
    borderWidth: 1,
    borderColor: colors.borderStrong,
  },

  // ── Summary Grid ──
  summaryGrid: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  summaryGridItem: {
    flex: 1,
    backgroundColor: colors.bgSection,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    alignItems: 'center',
  },
  summaryGridNum: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.primary,
    marginBottom: spacing.xs,
  },
  summaryGridLabel: {
    fontSize: 11,
    color: colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    textAlign: 'center',
  },

  // ── Feature Detection ──
  enhancedSection: {
    gap: spacing.md,
  },
  legalReasoningBox: {
    backgroundColor: colors.bgSection,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
  },
  legalReasoning: {
    fontSize: 14,
    lineHeight: 20,
    color: colors.textPrimary,
  },
  detectedFeaturesGrid: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.sm,
  },
  featureCol: {
    flex: 1,
  },
  featureSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  featureBadge: {
    backgroundColor: colors.bgSection,
    padding: spacing.xs,
    borderRadius: borderRadius.sm,
    marginBottom: spacing.xs,
  },
  featureBadgeText: {
    fontSize: 12,
    fontWeight: '500',
    color: colors.textPrimary,
  },
  noFeaturesText: {
    fontSize: 11,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
  featuresSuccessRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: spacing.md,
  },
  featuresSuccessText: {
    fontSize: 13,
    color: '#10B981',
  },
  limitedInfoBox: {
    backgroundColor: '#FEF3C7',
    padding: spacing.md,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: '#F59E0B',
  },
  limitedInfoTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#D97706',
    marginBottom: spacing.sm,
  },
  limitedInfoText: {
    fontSize: 12,
    color: '#92400E',
    lineHeight: 18,
  },

  // ── Compact Row ──
  compactRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  compactItem: {
    flex: 1,
    backgroundColor: colors.bgSection,
    padding: spacing.sm,
    borderRadius: borderRadius.sm,
  },
  compactLabel: {
    fontSize: 11,
    color: colors.textMuted,
    marginBottom: spacing.xs,
  },
  compactValue: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  compactSection: {
    marginBottom: spacing.md,
  },
  compactSectionLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  factorItem: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
    backgroundColor: colors.bgSection,
    borderRadius: borderRadius.sm,
    marginBottom: spacing.xs,
  },
  factorName: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.textPrimary,
  },

  // ── Probability Meters ──
  meterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  meterLabel: {
    flex: 1,
    fontSize: 13,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  meterTrack: {
    flex: 2,
    height: 6,
    backgroundColor: colors.border,
    borderRadius: 3,
    overflow: 'hidden',
  },
  meterFill: {
    height: '100%',
    borderRadius: 3,
  },
  meterPct: {
    fontSize: 13,
    fontWeight: '600',
    marginLeft: spacing.sm,
    minWidth: 40,
    textAlign: 'right',
  },

  // ── Context Analysis ──
  contextRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
    flexWrap: 'wrap',
  },
  contextLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textPrimary,
    flex: 1,
    marginRight: spacing.sm,
  },
  contextValues: {
    flex: 2,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
  },
  contextValue: {
    fontSize: 12,
    color: colors.textSecondary,
    marginRight: spacing.sm,
  },

  // ── Grounds / Evidence Analysis ──
  analysisRow: {
    marginBottom: spacing.md,
  },
  analysisRowHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  analysisLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textPrimary,
    flex: 1,
    marginRight: spacing.sm,
  },
  analysisCases: {
    fontSize: 11,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
  analysisBarContainer: {
    flexDirection: 'row',
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
    backgroundColor: colors.border,
    marginBottom: spacing.xs,
  },
  analysisBarSegment: {
    height: '100%',
  },
  analysisLegend: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  legendItem: {
    fontSize: 11,
    fontWeight: '500',
  },

  // ── Why This Prediction ──
  reasoningSection: {
    gap: spacing.md,
  },
  reasoningText: {
    fontSize: 14,
    color: colors.textPrimary,
    lineHeight: 20,
  },
  reasoningBlock: {
    backgroundColor: colors.bgSection,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    borderLeftWidth: 4,
    borderLeftColor: colors.primary,
  },
  reasoningTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
    marginBottom: spacing.sm,
  },
  reasoningPoints: {
    fontSize: 13,
    color: colors.textPrimary,
    lineHeight: 18,
  },

  // ── Zone / Tree ──
  zoneRoot: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.lg,
    padding: spacing.md,
    backgroundColor: colors.bgSection,
    borderRadius: borderRadius.md,
  },
  zoneRootBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  zoneRootBadgeText: {
    fontSize: 18,
    color: colors.textOnPrimary,
  },
  zoneRootTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  zoneRootSub: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  zoneTwoCol: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.lg,
  },
  zoneSection: {
    flex: 1,
  },
  zoneLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  zoneLabelDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: spacing.sm,
  },
  zoneLabel: {
    fontSize: 13,
    fontWeight: '600',
  },
  zoneSideBySide: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  zoneColumn: {
    flex: 1,
  },
  zoneSubLabel: {
    fontSize: 11,
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: spacing.sm,
  },
  treeItem: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.sm,
    borderLeftWidth: 2,
    borderLeftColor: colors.border,
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.sm,
    marginBottom: spacing.xs,
  },
  treeItemTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textPrimary,
    flex: 1,
  },
  emptyState: {
    fontSize: 12,
    color: colors.textMuted,
    fontStyle: 'italic',
    textAlign: 'center',
    padding: spacing.md,
  },

  // ── Similar Cases ──
  sectionSubtitle: {
    fontSize: 13,
    color: colors.textMuted,
    fontStyle: 'italic',
    marginBottom: spacing.md,
  },
  caseCard: {
    backgroundColor: colors.bgSection,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.md,
  },
  caseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  caseId: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  caseSimilarity: {
    fontSize: 12,
    color: colors.textMuted,
  },
  caseOutcome: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
  },
  caseOutcomeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  caseInfo: {
    flexDirection: 'row',
    marginBottom: spacing.xs,
    flexWrap: 'wrap',
  },
  caseInfoLabel: {
    fontSize: 12,
    color: colors.textMuted,
    fontWeight: '600',
    marginRight: spacing.xs,
  },
  caseInfoValue: {
    fontSize: 12,
    color: colors.textSecondary,
    flex: 1,
    flexWrap: 'wrap',
  },
  caseFacts: {
    marginTop: spacing.xs,
  },
  caseFactsLabel: {
    fontSize: 12,
    color: colors.textMuted,
    fontWeight: '600',
    marginBottom: 2,
  },
  caseFactsText: {
    fontSize: 12,
    color: colors.textSecondary,
    lineHeight: 16,
  },

  // ── Loading ──
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  loadingText: {
    marginTop: spacing.md,
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
  },
});