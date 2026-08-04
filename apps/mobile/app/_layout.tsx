import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Stack } from "expo-router";
import { useState } from "react";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { RootErrorBoundary } from "../src/components/ErrorBoundary";
import { PreferenceProvider } from "../src/state/preference";
import { colors } from "../src/theme/colors";

export default function RootLayout() {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { retry: 1 } },
      })
  );

  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <PreferenceProvider>
          <RootErrorBoundary>
            <Stack
              screenOptions={{
                headerShown: false,
                contentStyle: { backgroundColor: colors.pageBackground },
              }}
            />
          </RootErrorBoundary>
        </PreferenceProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
