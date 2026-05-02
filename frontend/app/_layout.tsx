import { Stack } from 'expo-router';
import Head from 'expo-router/head';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider } from '../components/AuthContext';
import { Comp2Provider } from '../components/Comp2Context';

export default function RootLayout() {
  return (
    <>
      <Head>
        <title>Jureka</title>
        <meta name="google-site-verification" content="Ekifbs6xR6C8D6fPNJihbrpOJYDMTioqzECaELXogEY" />
        <link rel="icon" href="/favicon.png" />
        <style dangerouslySetInnerHTML={{ __html: `
          html, body {
            overflow: auto !important;
            height: auto !important;
            min-height: 100vh;
            margin: 0;
            padding: 0;
            -webkit-overflow-scrolling: touch;
          }
          #root, #__next, div[data-reactroot] {
            height: auto !important;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
          }
        ` }} />
      </Head>
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
    </>
  );
}
