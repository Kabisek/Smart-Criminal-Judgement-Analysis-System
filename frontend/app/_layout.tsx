import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider } from '../components/AuthContext';
import { Comp2Provider } from '../components/Comp2Context';

export default function RootLayout() {
  return (
    <AuthProvider>
      <Comp2Provider>
        <SafeAreaProvider>
          <StatusBar style="light" />
          <Stack
            screenOptions={{
              headerShown: false,
              contentStyle: { backgroundColor: '#FBFBFB' },
              animation: 'fade_from_bottom',
            }}
          />
        </SafeAreaProvider>
      </Comp2Provider>
    </AuthProvider>
  );
}
