import { View, Text, TextInput, Pressable, StyleSheet, Platform, ScrollView, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { Layout } from '../components/Layout';
import { Container, Card, PageHeader, Button } from '../components/ui';
import { CaseIngestion } from '../components/CaseIngestion';
import { colors, typography, spacing, borderRadius } from '../theme';
import React, { useState } from 'react';
import { 
  predictAppealOutcome, 
  predictAppealOutcomeDetailed,
  analyzeCaseForLearning,
  saveComp3History,
  AppealPredictionRequest, 
  DetailedPredictionRequest,
  LearningRequest,
  AppealPredictionResponse,
  DetailedPredictionResponse,
  DetectedFeatures,
  SimilarCase,
  PredictionProbabilities
} from '../api';

export default function Component3Screen() {
  const router = useRouter();
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AppealPredictionResponse | DetailedPredictionResponse | null>(null);
  const [caseDescription, setCaseDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  // Progress tracking state
  const [progressStep, setProgressStep] = useState(0);
  const [progressText, setProgressText] = useState('');

  const handlePredict = async () => {
    if (!caseDescription.trim() || caseDescription.length < 50) {
      setError('Please provide a detailed case description (at least 50 characters)');
      return;
    }

    setAnalyzing(true);
    setError(null);
    setProgressStep(0);
    setProgressText('⏳ Step 1/4: Extracting features...');

    try {
      // Simulate progress steps
      await new Promise(resolve => setTimeout(resolve, 800));
      setProgressStep(1);
      setProgressText('⏳ Step 2/4: Analyzing legal patterns...');
      
      await new Promise(resolve => setTimeout(resolve, 800));
      setProgressStep(2);
      setProgressText('⏳ Step 3/4: Running ensemble model...');

      // Use enhanced prediction API with default values
      const request: DetailedPredictionRequest = {
        case_description: caseDescription,
        user_type: 'general',  // Default value
        analysis_level: 'detailed',  // Default value
        include_precedents: true,  // Default value
        language: 'en'
      };

      const predictionResult = await predictAppealOutcomeDetailed(request);
      
      setProgressStep(3);
      setProgressText('⏳ Step 4/4: Complete!');
      await new Promise(resolve => setTimeout(resolve, 500));
      
      if (predictionResult) {
        setResult(predictionResult);
        
        // Save to history
        await saveComp3History({
          case_id: `case_${Date.now()}`,
          case_name: caseDescription.substring(0, 50) + (caseDescription.length > 50 ? '...' : ''),
          payload: predictionResult,
          user_type: 'general',  // Default value
          analysis_level: 'detailed',  // Default value
          timestamp: new Date().toISOString()
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

  return (
    <Layout>
      <Container>
        <PageHeader
          title="Outcome Prediction Model"
          breadcrumb="Analytical Tools → Probability Analysis"
        />

        <View style={styles.row}>
          <View style={styles.mainCol}>
            <Card style={styles.inputCard} title="📋 Case Analysis Template">
              <View style={styles.templateHeader}>
                <Text style={styles.templateTitle}>Please include the following in your case description:</Text>
              </View>

              {/* Educational Template Sections */}
              <View style={styles.templateSection}>
                <Text style={styles.sectionNumber}>1.</Text>
                <View style={styles.sectionContent}>
                  <Text style={styles.templateSectionTitle}>📄 Basic Information</Text>
                  <Text style={styles.sectionDesc}>Offence type & penal code section, Original sentence/conviction</Text>
                </View>
              </View>

              <View style={styles.templateSection}>
                <Text style={styles.sectionNumber}>2.</Text>
                <View style={styles.sectionContent}>
                  <Text style={styles.templateSectionTitle}>⚖️ Case Facts</Text>
                  <Text style={styles.sectionDesc}>Brief description of the incident, Date, location, parties involved</Text>
                </View>
              </View>

              <View style={styles.templateSection}>
                <Text style={styles.sectionNumber}>3.</Text>
                <View style={styles.sectionContent}>
                  <Text style={styles.templateSectionTitle}>🔬 Evidence</Text>
                  <Text style={styles.sectionDesc}>Eyewitness testimony, Medical/forensic evidence, Documentary evidence, Expert evidence (JMO, analysts)</Text>
                </View>
              </View>

              <View style={styles.templateSection}>
                <Text style={styles.sectionNumber}>4.</Text>
                <View style={styles.sectionContent}>
                  <Text style={styles.templateSectionTitle}>⚖️ Grounds of Appeal</Text>
                  <Text style={styles.sectionDesc}>Contradictions in evidence, Procedural errors, Misdirection on law, Chain of custody issues, Wrong identification</Text>
                </View>
              </View>

              <View style={styles.templateSection}>
                <Text style={styles.sectionNumber}>5.</Text>
                <View style={styles.sectionContent}>
                  <Text style={styles.templateSectionTitle}>🛡️ Defence Position</Text>
                  <Text style={styles.sectionDesc}>Accused's statement, Defence witnesses, Alibi or alternative theories</Text>
                </View>
              </View>

              {/* Example Template */}
              {/* <View style={styles.exampleBox}>
                <Text style={styles.exampleTitle}>Example:</Text>
                <Text style={styles.exampleText}>
                  The accused was convicted by the High Court of Colombo for murder under Section 296 of the Penal Code and sentenced to death. The incident occurred on 15th May 2020 at the victim's residence.
                  {'\n\n'}The High Court convicted based on:
                  {'\n'}- Eyewitness testimony from two witnesses who saw the accused at the scene
                  {'\n'}- Medical evidence showing multiple stab wounds on the victim
                  {'\n'}- Recovery of a knife from the accused's possession
                  {'\n\n'}Grounds of Appeal:
                  {'\n'}1. Material contradictions in the prosecution witnesses' testimonies regarding the time of incident
                  {'\n'}2. Wrong identification - witnesses claim poor lighting conditions at night
                  {'\n'}3. Chain of custody issues with the recovered weapon - no proper documentation
                  {'\n\n'}Additional Information:
                  {'\n'}- No dying declaration was recorded
                  {'\n'}- The accused gave a dock statement denying all charges
                </Text>
              </View> */}

              <TextInput
                style={styles.textArea}
                placeholder="Enter your case description following the template above..."
                value={caseDescription}
                onChangeText={setCaseDescription}
                multiline
                editable={!analyzing}
              />

              {/* Character/Word Count */}
              <View style={styles.countRow}>
                <Text style={styles.countText}>📊 Characters: {caseDescription.length}</Text>
                <Text style={styles.countText}>📊 Words: {caseDescription.split(/\s+/).filter(word => word.length > 0).length}</Text>
              </View>

              {caseDescription.length > 0 && caseDescription.length < 100 && (
                <Text style={styles.warningText}>⚠️ Please provide at least 100 characters for accurate prediction</Text>
              )}

              {error && (
                <Text style={styles.errorText}>{error}</Text>
              )}

              <Button
                onPress={handlePredict}
                disabled={analyzing || !caseDescription.trim()}
                style={styles.analyzeBtn}
              >
                {analyzing ? "Analyzing..." : "🔮 Predict Appeal Outcome"}
              </Button>
            </Card>

            {/* Progress Display */}
            {analyzing && (
              <Card style={styles.progressCard} title="🔄 Processing Analysis">
                <View style={styles.progressContainer}>
                  <Text style={styles.progressText}>{progressText}</Text>
                  
                  {/* Progress Steps */}
                  <View style={styles.progressSteps}>
                    <View style={[styles.progressStep, progressStep >= 0 && styles.progressStepActive]}>
                      <Text style={[styles.progressStepText, progressStep >= 0 && styles.progressStepTextActive]}>1</Text>
                      <Text style={styles.progressStepLabel}>Extract Features</Text>
                    </View>
                    
                    <View style={[styles.progressStep, progressStep >= 1 && styles.progressStepActive]}>
                      <Text style={[styles.progressStepText, progressStep >= 1 && styles.progressStepTextActive]}>2</Text>
                      <Text style={styles.progressStepLabel}>Generate Embeddings</Text>
                    </View>
                    
                    <View style={[styles.progressStep, progressStep >= 2 && styles.progressStepActive]}>
                      <Text style={[styles.progressStepText, progressStep >= 2 && styles.progressStepTextActive]}>3</Text>
                      <Text style={styles.progressStepLabel}>Run Model</Text>
                    </View>
                    
                    <View style={[styles.progressStep, progressStep >= 3 && styles.progressStepActive]}>
                      <Text style={[styles.progressStepText, progressStep >= 3 && styles.progressStepTextActive]}>4</Text>
                      <Text style={styles.progressStepLabel}>Complete</Text>
                    </View>
                  </View>
                  
                  {/* Progress Bar */}
                  <View style={styles.progressBarContainer}>
                    <View style={[styles.progressBar, { width: `${((progressStep + 1) / 4) * 100}%` }]} />
                  </View>
                </View>
              </Card>
            )}

            {result && (
              <>
                <View style={styles.resultsSeparator}>
                  <Text style={styles.resultsSeparatorText}>📊 Prediction Results</Text>
                </View>

                {/* Main Result Card - Following Component 1/2 patterns */}
                <Card style={[
                  styles.resultCard, 
                  result.prediction === 'Appeal_Allowed' && { borderColor: colors.success, borderWidth: 2 },
                  result.prediction === 'Appeal_Dismissed' && { borderColor: colors.error, borderWidth: 2 },
                  result.prediction === 'Partly_Allowed' && { borderColor: colors.accent, borderWidth: 2 }
                ]} title="📊 Prediction Analysis">
                  <View style={styles.summaryGrid}>
                    <View style={styles.summaryGridItem}>
                      <Text style={[
                        styles.summaryGridNum,
                        result.prediction === 'Appeal_Allowed' && { color: colors.success },
                        result.prediction === 'Appeal_Dismissed' && { color: colors.error },
                        result.prediction === 'Partly_Allowed' && { color: colors.accent }
                      ]}>
                        {result.confidence.toFixed(1)}%
                      </Text>
                      <Text style={styles.summaryGridLabel}>Confidence</Text>
                    </View>
                    <View style={styles.summaryGridItem}>
                      <Text style={styles.summaryGridNum}>
                        {'legal_reasoning' in result ? 'Enhanced' : Object.values(result.detected_features || {}).reduce((sum: number, arr: any) => sum + arr.length, 0)}
                      </Text>
                      <Text style={styles.summaryGridLabel}>
                        {'legal_reasoning' in result ? 'Analysis Level' : 'Features Detected'}
                      </Text>
                    </View>
                    <View style={[
                      styles.summaryGridItem,
                      result.prediction === 'Appeal_Allowed' && { backgroundColor: colors.success + '20' },
                      result.prediction === 'Appeal_Dismissed' && { backgroundColor: colors.error + '20' },
                      result.prediction === 'Partly_Allowed' && { backgroundColor: colors.accent + '20' }
                    ]}>
                      <Text style={[
                        styles.summaryGridNum, 
                        { fontSize: 11, fontWeight: '700' },
                        result.prediction === 'Appeal_Allowed' && { color: colors.success },
                        result.prediction === 'Appeal_Dismissed' && { color: colors.error },
                        result.prediction === 'Partly_Allowed' && { color: colors.accent }
                      ]}>
                        {result.prediction.replace('_', ' ')}
                      </Text>
                      <Text style={styles.summaryGridLabel}>Predicted Outcome</Text>
                    </View>
                  </View>
                </Card>

                {/* === DETECTED FEATURES BOX === */}
                <Card style={styles.resultCard} title="🔍 What the AI Detected in Your Case">
                  {'legal_reasoning' in result ? (
                    // Enhanced Analysis Display
                    <View style={styles.enhancedSection}>
                      <Text style={styles.legalReasoning}>{result.legal_reasoning}</Text>
                      
                      <View style={styles.detectedFeaturesGrid}>
                        <View style={styles.featureColumn}>
                          <Text style={styles.featureSectionTitle}>⚖️ Grounds of Appeal</Text>
                          {result.key_factors && result.key_factors.length > 0 ? (
                            result.key_factors.slice(0, 3).map((factor: any, index: number) => (
                              <View key={index} style={styles.featureBadge}>
                                <Text style={styles.featureBadgeText}>🟢 {factor.factor_name}</Text>
                              </View>
                            ))
                          ) : (
                            <Text style={styles.noFeaturesText}>⚠️ No specific grounds detected</Text>
                          )}
                        </View>

                        <View style={styles.featureColumn}>
                          <Text style={styles.featureSectionTitle}>🔬 Evidence Types</Text>
                          {result.detected_features && result.detected_features.evidence && result.detected_features.evidence.length > 0 ? (
                            result.detected_features.evidence.slice(0, 3).map((evidence: string, index: number) => (
                              <View key={index} style={styles.featureBadge}>
                                <Text style={styles.featureBadgeText}>🟡 {evidence}</Text>
                              </View>
                            ))
                          ) : (
                            <Text style={styles.noFeaturesText}>⚠️ No evidence types detected</Text>
                          )}
                        </View>
                      </View>

                      <View style={styles.compactRow}>
                        <View style={styles.compactItem}>
                          <Text style={styles.compactLabel}>⚠️ Risk Assessment</Text>
                          <Text style={styles.compactValue}>{result.risk_assessment ? result.risk_assessment.split(':')[0] : 'Medium'}</Text>
                        </View>
                        <View style={styles.compactItem}>
                          <Text style={styles.compactLabel}>💡 Strategy</Text>
                          <Text style={styles.compactValue}>{result.strategy_recommendations && result.strategy_recommendations[0] ? result.strategy_recommendations[0].recommendation.split(' ')[0] : 'Standard'}</Text>
                        </View>
                      </View>
                    </View>
                  ) : (
                    // Basic Analysis Display
                    <View style={styles.basicFeaturesSection}>
                      {result.detected_features && Object.keys(result.detected_features).length > 0 ? (
                        <>
                          <Text style={styles.featuresSuccessText}>
                            ✅ Successfully detected **{Object.values(result.detected_features).reduce((sum: number, arr: any) => sum + arr.length, 0)} key features** from your case description
                          </Text>
                          
                          <View style={styles.detectedFeaturesGrid}>
                            {result.detected_features.grounds && result.detected_features.grounds.length > 0 && (
                              <View style={styles.featureColumn}>
                                <Text style={styles.featureSectionTitle}>⚖️ Grounds of Appeal</Text>
                                {result.detected_features.grounds.slice(0, 3).map((ground: string, index: number) => (
                                  <View key={index} style={styles.featureBadge}>
                                    <Text style={styles.featureBadgeText}>🟢 {ground}</Text>
                                  </View>
                                ))}
                              </View>
                            )}
                            
                            {result.detected_features.evidence && result.detected_features.evidence.length > 0 && (
                              <View style={styles.featureColumn}>
                                <Text style={styles.featureSectionTitle}>🔬 Evidence Detected</Text>
                                {result.detected_features.evidence.slice(0, 3).map((evidence: string, index: number) => (
                                  <View key={index} style={styles.featureBadge}>
                                    <Text style={styles.featureBadgeText}>🟡 {evidence}</Text>
                                  </View>
                                ))}
                              </View>
                            )}
                            
                            {result.detected_features.offence && result.detected_features.offence.length > 0 && (
                              <View style={styles.featureColumn}>
                                <Text style={styles.featureSectionTitle}>📋 Offence Category</Text>
                                {result.detected_features.offence.slice(0, 2).map((offence: string, index: number) => (
                                  <View key={index} style={styles.featureBadge}>
                                    <Text style={styles.featureBadgeText}>🔵 {offence}</Text>
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
                            The AI couldn't identify specific legal features in your description. For better predictions, please include:
                            {'\n'}• Specific grounds of appeal (contradictions, chain of custody, identification issues)
                            {'\n'}• Evidence types (eyewitness, medical, forensic, confession)
                            {'\n'}• Offence category (murder, rape, drug trafficking, etc.)
                          </Text>
                        </View>
                      )}
                    </View>
                  )}
                </Card>

                {/* Enhanced Analysis Section */}
                {'legal_reasoning' in result && (
                  <Card style={styles.resultCard} title="⚖️ Legal Analysis">
                    <View style={styles.enhancedSection}>
                      <Text style={styles.legalReasoning}>{result.legal_reasoning}</Text>
                      
                      {result.key_factors && result.key_factors.length > 0 && (
                        <View style={styles.compactSection}>
                          <Text style={styles.compactSectionLabel}>🎯 Key Factors</Text>
                          <View style={styles.factorsList}>
                            {result.key_factors.slice(0, 3).map((factor, index) => (
                              <View key={index} style={styles.factorItem}>
                                <Text style={styles.factorName}>{factor.factor_name}</Text>
                              </View>
                            ))}
                          </View>
                        </View>
                      )}

                      <View style={styles.compactRow}>
                        {result.risk_assessment && (
                          <View style={styles.compactItem}>
                            <Text style={styles.compactLabel}>⚠️ Risk</Text>
                            <Text style={styles.compactValue}>{result.risk_assessment.split(':')[0]}</Text>
                          </View>
                        )}
                        {result.strategy_recommendations && result.strategy_recommendations.length > 0 && (
                          <View style={styles.compactItem}>
                            <Text style={styles.compactLabel}>💡 Strategy</Text>
                            <Text style={styles.compactValue}>{result.strategy_recommendations[0].recommendation.split(' ')[0]}</Text>
                          </View>
                        )}
                      </View>
                    </View>
                  </Card>
                )}

                {/* Probability Breakdown - Following Component 2 meter pattern */}
                <Card style={styles.resultCard} title="📊 Probability Distribution">
                  {Object.entries(result.probabilities).map(([key, value]) => {
                    const config = {
                      Appeal_Allowed: { label: 'Appeal Allowed', color: colors.success },
                      Appeal_Dismissed: { label: 'Appeal Dismissed', color: colors.error },
                      Partly_Allowed: { label: 'Partly Allowed', color: colors.accent }
                    }[key] || { label: key, color: colors.textMuted };
                    
                    return (
                      <View key={key} style={styles.meterRow}>
                        <Text style={styles.meterLabel}>{config.label}</Text>
                        <View style={styles.meterTrack}>
                          <View style={[styles.meterFill, { width: `${value}%`, backgroundColor: config.color }]} />
                        </View>
                        <Text style={[styles.meterPct, { color: config.color }]}>{value.toFixed(1)}%</Text>
                      </View>
                    );
                  })}
                </Card>

                {/* Why This Prediction Section - Simple Addition */}
                <Card style={styles.resultCard} title="💡 Why This Prediction?">
                  <View style={styles.reasoningSection}>
                    <Text style={styles.reasoningText}>
                      Based on analysis of **{(() => {
                        const features = result.detected_features as any;
                        const allFeatures = [];
                        if (features?.grounds) allFeatures.push(...features.grounds);
                        if (features?.evidence) allFeatures.push(...features.evidence);
                        if (features?.offence) allFeatures.push(...features.offence);
                        if (features?.other) allFeatures.push(...features.other);
                        return allFeatures.slice(0, 6).join(', ');
                      })()}** and **legal pattern analysis**, the model predicts:
                    </Text>
                    
                    <View style={styles.reasoningDetails}>
                      {result.prediction === "Appeal_Allowed" && result.confidence > 60 && (
                        <View style={styles.reasoningBlock}>
                          <Text style={styles.reasoningTitle}>🟢 Strong indicators for Appeal Allowed:</Text>
                          <Text style={styles.reasoningPoints}>
                            • Detected grounds: {(result as any).detected_features?.grounds?.slice(0, 3).join(', ') || 'Procedural/evidentiary issues'}
                            {'\n'}• Pattern matches similar cases where appeals succeeded
                            {'\n'}• High confidence ({result.confidence.toFixed(1)}%) suggests strong legal grounds
                          </Text>
                        </View>
                      )}
                      
                      {result.prediction === "Appeal_Dismissed" && result.confidence > 60 && (
                        <View style={styles.reasoningBlock}>
                          <Text style={styles.reasoningTitle}>🔴 Strong indicators for Appeal Dismissed:</Text>
                          <Text style={styles.reasoningPoints}>
                            • Evidence pattern: {(result as any).detected_features?.evidence?.slice(0, 3).join(', ') || 'Strong prosecution evidence'}
                            {'\n'}• Similar historical cases were mostly dismissed
                            {'\n'}• High confidence ({result.confidence.toFixed(1)}%) suggests solid conviction basis
                          </Text>
                        </View>
                      )}
                      
                      {result.confidence < 55 && (
                        <View style={styles.reasoningBlock}>
                          <Text style={styles.reasoningTitle}>🟡 Mixed signals detected:</Text>
                          <Text style={styles.reasoningPoints}>
                            • Competing factors make outcome uncertain
                            {'\n'}• Both prosecution strengths and defence grounds present
                            {'\n'}• Medium/low confidence ({result.confidence.toFixed(1)}%) indicates borderline case
                          </Text>
                        </View>
                      )}
                    </View>
                  </View>
                </Card>

                {/* Detected Features - Following Component 1 tree pattern */}
                <Card style={styles.resultCard} title="🔍 Feature Detection">
                  <View style={styles.zoneRoot}>
                    <View style={[styles.zoneRootBadge, { backgroundColor: colors.primary }]}>
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
                        <Text style={[styles.zoneLabel, { color: colors.prosecution }]}>⚖️ Grounds of Appeal</Text>
                      </View>
                      {result.detected_features && result.detected_features.grounds && result.detected_features.grounds.length > 0 ? (
                        result.detected_features.grounds.map((ground: any, idx: number) => (
                          <View key={idx} style={styles.treeItem}>
                            <Text style={styles.treeItemTitle}>{ground}</Text>
                          </View>
                        ))
                      ) : (
                        <Text style={styles.emptyState}>No grounds detected</Text>
                      )}
                    </View>

                    <View style={styles.zoneSection}>
                      <View style={styles.zoneLabelRow}>
                        <View style={[styles.zoneLabelDot, { backgroundColor: colors.defense }]} />
                        <Text style={[styles.zoneLabel, { color: colors.defense }]}>🔬 Evidence Types</Text>
                      </View>
                      {result.detected_features && result.detected_features.evidence && result.detected_features.evidence.length > 0 ? (
                        result.detected_features.evidence.map((evidence: any, idx: number) => (
                          <View key={idx} style={styles.treeItem}>
                            <Text style={styles.treeItemTitle}>{evidence}</Text>
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
                      {result.detected_features && result.detected_features.offence && result.detected_features.offence.length > 0 && (
                        <View style={styles.zoneColumn}>
                          <Text style={styles.zoneSubLabel}>Offence Category</Text>
                          {result.detected_features.offence.map((offence: any, idx: number) => (
                            <View key={idx} style={styles.treeItem}>
                              <Text style={styles.treeItemTitle}>{offence}</Text>
                            </View>
                          ))}
                        </View>
                      )}
                      {result.detected_features && result.detected_features.other && result.detected_features.other.length > 0 && (
                        <View style={styles.zoneColumn}>
                          <Text style={styles.zoneSubLabel}>Other Factors</Text>
                          {result.detected_features.other.slice(0, 3).map((other: any, idx: number) => (
                            <View key={idx} style={styles.treeItem}>
                              <Text style={styles.treeItemTitle}>{other}</Text>
                            </View>
                          ))}
                        </View>
                      )}
                    </View>
                  </View>
                </Card>

                {/* Similar Cases - Following Component 1 resource pattern */}
                <Card style={styles.resultCard} title="📚 Similar Historical Cases">
                  <Text style={styles.sectionSubtitle}>
                    Based on analysis of similar court cases
                  </Text>
                  {result.similar_cases.slice(0, 3).map((case_item, idx) => (
                    <Pressable
                      key={idx}
                      style={styles.treeItem}
                    >
                      <View style={{ flex: 1 }}>
                        <Text style={styles.treeItemTitle}>#{idx + 1} {case_item.case_id}</Text>
                        <Text style={styles.treeItemSub}>
                          {case_item.outcome.replace('_', ' ')} • {'similarity_score' in case_item ? `${(case_item.similarity_score * 100).toFixed(0)}% Similar` : case_item.high_court || ''}
                        </Text>
                        <Text style={[styles.treeItemSub, styles.fullCaseText]}>
                          {'case_summary' in case_item ? 
                            case_item.case_summary :
                            (case_item.facts || '')
                          }
                        </Text>
                      </View>
                      <View style={[styles.scoreBadge, { backgroundColor: colors.primary }]}>
                        <Text style={styles.scoreBadgeText}>
                          {'similarity_score' in case_item ? `${(case_item.similarity_score * 100).toFixed(0)}%` : `${case_item.similarity?.toFixed(0) || 0}%`}
                        </Text>
                      </View>
                    </Pressable>
                  ))}
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

          <Card style={styles.infoCard} title="Understanding Your Results">
            <View style={styles.howItem}>
              <Text style={styles.howTitle}>📋 Case Analysis</Text>
              <Text style={styles.howText}>We analyze your case details and compare them with past court decisions.</Text>
            </View>
            <View style={styles.howItem}>
              <Text style={styles.howTitle}>⚖️ Pattern Recognition</Text>
              <Text style={styles.howText}>Our system identifies similar cases and their outcomes to predict results.</Text>
            </View>
            <View style={styles.howItem}>
              <Text style={styles.howTitle}>🎯 Confidence Score</Text>
              <Text style={styles.howText}>Shows how certain the prediction is based on historical case patterns.</Text>
            </View>

            <Pressable onPress={() => router.push('/')} style={{ marginTop: spacing.xl }}>
              <Text style={styles.backLink}>← Back to Home</Text>
            </Pressable>
          </Card>
        </View>
      </Container>
    </Layout>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: Platform.OS === 'web' ? 'row' : 'column', gap: spacing.xl },
  mainCol: { flex: 3, gap: spacing.lg },
  infoCard: { flex: 0.5, maxWidth: 280 },
  inputCard: { marginTop: spacing.sm },
  
  // Professional Input Section
  sectionTitle: { 
    fontSize: 18, 
    fontWeight: '700', 
    color: colors.textPrimary, 
    marginBottom: spacing.sm 
  },
  para: { 
    color: colors.textSecondary, 
    marginBottom: spacing.md, 
    lineHeight: 22,
    fontSize: 14
  },
  inputLabel: { 
    fontSize: 14, 
    fontWeight: '600', 
    color: colors.textPrimary, 
    marginBottom: spacing.xs 
  },
  inputHint: { 
    fontSize: 12, 
    color: colors.textMuted, 
    marginBottom: spacing.sm,
    fontStyle: 'italic'
  },
  textAreaContainer: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    minHeight: 120,
    maxHeight: 200,
    backgroundColor: colors.bgCard,
    marginBottom: spacing.md,
  },
  textArea: {
    fontSize: 14,
    color: colors.textPrimary,
    minHeight: 100,
    textAlignVertical: 'top',
  },
  
  // Educational Template Styles
  templateHeader: {
    marginBottom: spacing.lg,
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
  exampleBox: {
    backgroundColor: '#F8FAFC',
    padding: spacing.md,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: spacing.md,
  },
  exampleTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.primary,
    marginBottom: spacing.sm,
  },
  exampleText: {
    fontSize: 11,
    color: colors.textSecondary,
    lineHeight: 14,
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

  // Feature Detection Display Styles
  detectedFeaturesGrid: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.md,
  },
  featureColumn: {
    flex: 1,
  },
  featureSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  featureBadge: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.bgSection,
    padding: spacing.xs,
    borderRadius: borderRadius.sm,
    marginBottom: spacing.xs,
  },
  featureBadgeText: {
    fontSize: 12,
    fontWeight: '500',
    color: colors.textPrimary,
    flex: 1,
  },
  noFeaturesText: {
    fontSize: 11,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
  basicFeaturesSection: {
    gap: spacing.md,
  },
  featuresSuccessText: {
    fontSize: 13,
    color: '#10B981',
    fontWeight: '500',
    marginBottom: spacing.md,
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
    lineHeight: 16,
  },

  // Progress Display Styles
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
    marginBottom: spacing.md,
  },
  progressSteps: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  progressStep: {
    alignItems: 'center',
    flex: 1,
    opacity: 0.4,
  },
  progressStepActive: {
    opacity: 1,
  },
  progressStepText: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.border,
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: spacing.xs,
  },
  progressStepTextActive: {
    backgroundColor: colors.accent,
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

  // Professional Button
  analyzeBtn: { 
    width: '100%', 
    marginTop: spacing.md 
  },
  
  // Error Display
  errorContainer: {
    backgroundColor: 'rgba(185, 28, 28, 0.08)',
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    marginTop: spacing.sm,
    borderWidth: 1,
    borderColor: 'rgba(185, 28, 28, 0.2)'
  },
  errorText: { 
    color: colors.error, 
    fontSize: 13,
    textAlign: 'center'
  },
  
  // Enhanced Result Card
  resultCard: {
    marginTop: spacing.lg,
    backgroundColor: colors.bgCard,
    borderWidth: 1,
    borderColor: colors.borderStrong,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    marginBottom: spacing.lg,
  },
  resultTitle: { 
    fontSize: 20, 
    fontWeight: '700', 
    color: colors.textPrimary 
  },
  resultMeta: {
    alignItems: 'flex-end',
  },
  confidenceScore: {
    fontSize: 14,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  outcomeBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
  },
  outcomeText: {
    fontSize: 13,
    fontWeight: '600',
  },
  
  // Section Styling
  section: {
    marginBottom: spacing.lg,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: colors.textMuted,
    fontStyle: 'italic',
    marginBottom: spacing.md,
  },
  
  // Feature Detection
  detectionSummary: {
    backgroundColor: colors.bgSection,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    alignItems: 'center',
  },
  detectionMetric: {
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  detectionNumber: {
    fontSize: 32,
    fontWeight: '700',
    color: colors.primary,
  },
  detectionLabel: {
    fontSize: 12,
    color: colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  detectionDescription: {
    fontSize: 13,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
  },
  
  // Probability Grid
  probabilityGrid: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  probabilityCard: {
    flex: 1,
    backgroundColor: colors.bgSection,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    alignItems: 'center',
  },
  probabilityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  probabilityIcon: {
    fontSize: 16,
    marginRight: spacing.xs,
  },
  probabilityLabel: {
    fontSize: 11,
    color: colors.textSecondary,
    fontWeight: '600',
  },
  probabilityValue: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: spacing.xs,
  },
  probabilityBar: {
    width: '100%',
    height: 4,
    backgroundColor: colors.border,
    borderRadius: 2,
    overflow: 'hidden',
  },
  probabilityFill: {
    height: '100%',
    borderRadius: 2,
  },
  
  // Features Grid
  featuresGrid: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  featureColumn: {
    flex: 1,
  },
  featureCategory: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.primary,
    marginBottom: spacing.sm,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.xs,
  },
  featureBullet: {
    color: colors.primary,
    fontSize: 12,
    marginRight: spacing.xs,
    marginTop: 2,
  },
  featureText: {
    fontSize: 12,
    color: colors.textSecondary,
    flex: 1,
    lineHeight: 16,
  },
  emptyFeature: {
    fontSize: 12,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
  
  // Similar Cases
  casesList: {
    gap: spacing.md,
  },
  caseCard: {
    backgroundColor: colors.bgSection,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
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
  caseDetails: {
    gap: spacing.xs,
  },
  caseInfo: {
    flexDirection: 'row',
  },
  caseInfoLabel: {
    fontSize: 12,
    color: colors.textMuted,
    fontWeight: '600',
    width: 120,
  },
  caseInfoValue: {
    fontSize: 12,
    color: colors.textSecondary,
    flex: 1,
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
  
  // Footer
  footer: {
    marginTop: spacing.lg,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 11,
    color: colors.textMuted,
  },
  
  // Loading State
  loadingCard: {
    marginTop: spacing.lg,
    padding: spacing.xl,
    alignItems: 'center',
  },
  loadingText: {
    marginTop: spacing.md,
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  loadingSubtext: {
    marginTop: spacing.xs,
    fontSize: 13,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  
  // Info Card
  infoTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  infoSection: {
    marginBottom: spacing.md,
  },
  infoItemTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
    marginBottom: spacing.xs,
  },
  infoItemText: {
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 18,
  },

  // Component 1 & 2 Shared Styles
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
  },

  // Meter styles (Component 2)
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

  // Zone styles (Component 1)
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

  // Tree styles (Component 1)
  treeItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.sm,
    borderLeftWidth: 2,
    borderLeftColor: colors.border,
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.sm,
    marginBottom: spacing.xs,
  },
  treeItemSelected: {
    backgroundColor: colors.primary + '10',
    borderLeftColor: colors.primary,
  },
  treeItemTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textPrimary,
    flex: 1,
  },
  treeItemSub: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  fullCaseText: {
    fontSize: 11,
    color: colors.textSecondary,
    marginTop: 2,
    lineHeight: 16,
    flexWrap: 'wrap',
  },
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
  factorName: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.textPrimary,
  },
  scoreBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
    marginLeft: spacing.sm,
  },
  scoreBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.textOnPrimary,
  },

  // Legacy styles for compatibility

  // Empty state
  emptyState: {
    fontSize: 12,
    color: colors.textMuted,
    fontStyle: 'italic',
    textAlign: 'center',
    padding: spacing.md,
  },

  // Legacy styles for compatibility
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  howItem: { marginBottom: spacing.lg },
  howTitle: { fontSize: 15, fontWeight: 'bold', color: colors.primary, marginBottom: 4 },
  howText: { fontSize: 13, color: colors.textSecondary, lineHeight: 18 },
  backLink: { color: colors.primary, fontWeight: '500' },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  zoneItem: {
    marginBottom: spacing.md,
  },
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
  // Enhanced Analysis Compact Styles
  enhancedSection: {
    gap: spacing.md,
  },
  legalReasoning: {
    fontSize: 14,
    lineHeight: 20,
    color: colors.textPrimary,
    marginBottom: spacing.md,
    padding: spacing.sm,
    backgroundColor: colors.bgSection,
    borderRadius: borderRadius.md,
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
  factorsList: {
    gap: spacing.xs,
  },
  factorItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.xs,
    flex: 1,
    padding: spacing.sm,
    backgroundColor: colors.bgSection,
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
  // Enhanced styles for new components
  metricsGrid: {
    gap: spacing.md,
  },
  metricItem: {
    backgroundColor: colors.bgSection,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    gap: spacing.sm,
  },
  metricIcon: {
    fontSize: 20,
    marginBottom: spacing.xs,
  },
  metricLabel: {
    fontSize: 12,
    color: colors.textMuted,
    fontWeight: '500',
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  reasoningSection: {
    gap: spacing.md,
  },
  reasoningText: {
    fontSize: 14,
    color: colors.textPrimary,
    lineHeight: 20,
    marginBottom: spacing.md,
  },
  reasoningDetails: {
    gap: spacing.md,
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
  chartContainer: {
    gap: spacing.lg,
  },
  chartSection: {
    flex: 1,
    alignItems: 'center',
  },
  chartTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  pieChart: {
    width: 120,
    height: 120,
    position: 'relative',
    justifyContent: 'center',
    alignItems: 'center',
  },
  pieSlice: {
    position: 'absolute',
    width: 120,
    height: 120,
    borderRadius: 60,
    overflow: 'hidden',
  },
  pieSliceFill: {
    width: '100%',
    height: '100%',
    borderRadius: 60,
  },
  barChart: {
    flex: 1,
    gap: spacing.sm,
  },
  barItem: {
    gap: spacing.xs,
  },
  barLabel: {
    fontSize: 12,
    color: colors.textMuted,
    fontWeight: '500',
  },
  barTrack: {
    height: 8,
    backgroundColor: colors.border,
    borderRadius: 4,
    overflow: 'hidden',
    flex: 1,
  },
  barFill: {
    height: '100%',
    borderRadius: 4,
    minWidth: 2,
  },
  barValue: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: spacing.sm,
  },
});
