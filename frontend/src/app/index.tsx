import { FlagsProvider } from './providers/flags';
import { SecurityProvider } from './providers/security';
import { RouterProvider } from './providers/router';
import { TelemetryProvider } from './providers/telemetry';
import { ThemeProvider } from './providers/theme';

export const AppRoot = (): JSX.Element => (
  <SecurityProvider>
    <TelemetryProvider>
      <FlagsProvider>
        <ThemeProvider>
          <RouterProvider />
        </ThemeProvider>
      </FlagsProvider>
    </TelemetryProvider>
  </SecurityProvider>
);

export default AppRoot;
