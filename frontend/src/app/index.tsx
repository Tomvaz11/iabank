import { FlagsProvider } from './providers/flags';
import { SecurityProvider } from './providers/security';
import { RouterProvider } from './providers/router';
import { TelemetryProvider } from './providers/telemetry';

export const AppRoot = (): JSX.Element => (
  <SecurityProvider>
    <TelemetryProvider>
      <FlagsProvider>
        <RouterProvider />
      </FlagsProvider>
    </TelemetryProvider>
  </SecurityProvider>
);

export default AppRoot;
