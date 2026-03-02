import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, Alert, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { Layout } from '../components/Layout';
import { Container, Card, Button } from '../components/ui';
import { colors, spacing, typography } from '../theme';
import { useAuth } from '../components/AuthContext';

export default function LoginScreen() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const router = useRouter();

    const handleLogin = async () => {
        if (!email || !password) {
            Alert.alert('Error', 'Please enter both email and password.');
            return;
        }
        setLoading(true);
        try {
            await login({ email, pass: password });
            router.replace('/');
        } catch (e: any) {
            Alert.alert('Authentication Failed', e.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Layout>
            <Container style={styles.container}>
                <Card style={styles.loginCard}>
                    <View style={styles.header}>
                        <Text style={styles.title}>Lawyer Portal</Text>
                        <Text style={styles.subtitle}>Secure access for legal professionals</Text>
                    </View>

                    <View style={styles.form}>
                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>Email Address</Text>
                            <TextInput
                                style={styles.input}
                                placeholder="e.g. perera.advocate@lawyers.lk"
                                value={email}
                                onChangeText={setEmail}
                                autoCapitalize="none"
                                keyboardType="email-address"
                            />
                        </View>

                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>Password</Text>
                            <TextInput
                                style={styles.input}
                                placeholder="••••••••"
                                value={password}
                                onChangeText={setPassword}
                                secureTextEntry
                            />
                        </View>

                        <Button
                            onPress={handleLogin}
                            disabled={loading}
                            style={styles.loginBtn}
                        >
                            {loading ? 'Authenticating...' : 'Sign In as Lawyer'}
                        </Button>

                        <Text style={styles.note}>
                            Note: For demonstration, use any email containing "lawyer".
                        </Text>
                    </View>
                </Card>
            </Container>
        </Layout>
    );
}

const styles = StyleSheet.create({
    container: {
        paddingVertical: spacing.xxl,
        alignItems: 'center',
        justifyContent: 'center',
    },
    loginCard: {
        width: '100%',
        maxWidth: 450,
        padding: spacing.xl,
    },
    header: {
        alignItems: 'center',
        marginBottom: spacing.xl,
    },
    title: {
        fontSize: 28,
        fontWeight: 'bold',
        color: colors.primary,
        marginBottom: 8,
    },
    subtitle: {
        fontSize: 16,
        color: colors.textMuted,
        textAlign: 'center',
    },
    form: {
        gap: spacing.lg,
    },
    inputGroup: {
        gap: 8,
    },
    label: {
        fontSize: 14,
        fontWeight: '600',
        color: colors.textPrimary,
    },
    input: {
        borderWidth: 1,
        borderColor: colors.border,
        borderRadius: 8,
        padding: 12,
        fontSize: 16,
        backgroundColor: '#FAFAFA',
        ...(Platform.OS === 'web' && {
            outlineStyle: 'none',
        } as any),
    },
    loginBtn: {
        width: '100%',
        marginTop: spacing.md,
    },
    note: {
        fontSize: 12,
        color: colors.textMuted,
        textAlign: 'center',
        marginTop: spacing.md,
        fontStyle: 'italic',
    }
});
