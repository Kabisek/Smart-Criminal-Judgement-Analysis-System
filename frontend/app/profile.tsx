import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { Layout } from '../components/Layout';
import { Container, Card, Button } from '../components/ui';
import { colors, spacing, typography } from '../theme';
import { useAuth } from '../components/AuthContext';

export default function ProfileScreen() {
    const { user, logout, role } = useAuth();
    const router = useRouter();

    if (!user) {
        return (
            <Layout>
                <Container style={styles.center}>
                    <Text>Redirecting...</Text>
                </Container>
            </Layout>
        );
    }

    const handleLogout = () => {
        logout();
        router.replace('/');
    };

    return (
        <Layout>
            <Container style={styles.container}>
                <View style={styles.header}>
                    <Text style={styles.title}>My Profile</Text>
                    <Text style={styles.subtitle}>Legal Professional Information</Text>
                </View>

                <Card style={styles.profileCard}>
                    <View style={styles.profileHeader}>
                        <View style={styles.avatar}>
                            <Text style={styles.avatarText}>{user.name.charAt(0)}</Text>
                        </View>
                        <View>
                            <Text style={styles.userName}>{user.name}</Text>
                            <Text style={styles.userRole}>{role === 'lawyer' ? 'Qualified Advocate' : 'Guest'}</Text>
                        </View>
                    </View>

                    <View style={styles.details}>
                        <View style={styles.detailRow}>
                            <Text style={styles.detailLabel}>Email</Text>
                            <Text style={styles.detailValue}>{user.email}</Text>
                        </View>
                        <View style={styles.detailRow}>
                            <Text style={styles.detailLabel}>License Type</Text>
                            <Text style={styles.detailValue}>Criminal Law Practitioner</Text>
                        </View>
                        <View style={styles.detailRow}>
                            <Text style={styles.detailLabel}>Organization</Text>
                            <Text style={styles.detailValue}>Independent Practice</Text>
                        </View>
                    </View>

                    <Button variant="secondary" onPress={handleLogout} style={styles.logoutBtn}>
                        Logout
                    </Button>
                </Card>
            </Container>
        </Layout>
    );
}

const styles = StyleSheet.create({
    container: {
        paddingVertical: spacing.xl,
    },
    center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
    header: {
        marginBottom: spacing.xl,
    },
    title: {
        fontSize: 32,
        fontWeight: 'bold',
        color: colors.primary,
    },
    subtitle: {
        fontSize: 18,
        color: colors.textMuted,
    },
    profileCard: {
        padding: spacing.xl,
    },
    profileHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.lg,
        marginBottom: spacing.xxl,
        borderBottomWidth: 1,
        borderBottomColor: colors.border,
        paddingBottom: spacing.lg,
    },
    avatar: {
        width: 80,
        height: 80,
        borderRadius: 40,
        backgroundColor: colors.primary,
        alignItems: 'center',
        justifyContent: 'center',
    },
    avatarText: {
        color: '#FFFFFF',
        fontSize: 32,
        fontWeight: 'bold',
    },
    userName: {
        fontSize: 24,
        fontWeight: 'bold',
        color: colors.textPrimary,
    },
    userRole: {
        fontSize: 16,
        color: colors.accent,
        fontWeight: '600',
    },
    details: {
        gap: spacing.lg,
        marginBottom: spacing.xl,
    },
    detailRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        paddingBottom: spacing.sm,
        borderBottomWidth: 1,
        borderBottomColor: colors.border,
    },
    detailLabel: {
        fontWeight: '600',
        color: colors.textMuted,
    },
    detailValue: {
        color: colors.textPrimary,
    },
    logoutBtn: {
        marginTop: spacing.md,
        borderWidth: 1,
        borderColor: '#FF4444',
    }
});
